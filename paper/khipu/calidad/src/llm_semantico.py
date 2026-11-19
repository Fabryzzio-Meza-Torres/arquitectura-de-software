"""Score semántico con un LLM pequeño local: la mitad "propuesta" de la comparación.

Cada documento (su one-pager) recibe un score de 0 a 1 respecto a la consulta (pointwise: se puntúa uno por uno).
Se puntúan los mismos candidatos que usa la base (salida de candidatos.py).

Modos de lanzarlo; la calidad debe salir igual, solo cambia la latencia. El profe pidió probar batches de 4 y de 10:
  lote4      4 documentos por pasada del modelo (con 20 candidatos: 5 pasadas)   (--modo lote4)
  lote10     10 documentos por pasada (con 20 candidatos: 2 pasadas)             (--modo lote10)
  loteN      cualquier otro tamaño de batch
  paralelo4  (extra) una llamada por documento, 4 a la vez
En todos, cada documento va en SU prompt y recibe su propio score; el batch solo agrupa prompts en una pasada.

Técnica de puntuación (por defecto, backend hf): RG-S, "relevance generation con escala 0 a 4". En vez de pedirle
al modelo que escriba un número (que da valores gruesos y muchos empates), se le pide una etiqueta de 0 a 4 y se leen
las PROBABILIDADES que asigna a cada etiqueta en una sola pasada (sin generar texto). El score es la esperanza
E = sum(k * p_k) / 4, un valor continuo entre 0 y 1. Referencia: Zhuang et al., "Beyond Yes and No: Improving
Zero-Shot LLM Rankers via Scoring Fine-Grained Relevance Labels" (arXiv 2310.14122). Es pointwise: un documento por
prompt. Como no genera texto, es mucho más rápido que escribir el número.
  --backend hf      RG-S con transformers (GPU; el que se recomienda)
  --backend ollama  el modelo escribe un número 0-1 (más simple, pero más empates)

Backend ollama: (http://localhost:11434) por defecto; cualquier modelo que ya esté bajado:
  python calidad/src/llm_semantico.py --candidatos out/fiqa.test.candidatos.jsonl --data-dir data \
      --dataset fiqa --modelo qwen2.5:3b --modo lote10 --out out/fiqa.test.llm_lote10
Escribe <out>.scores.jsonl ({"qid","id","score"}) y <out>.tiempos.tsv (qid, ms, n_docs, estado): con eso se
reporta p50/p95/p99 del paso LLM con `evaluate.py`/`latency.py`. Un score que no se pudo leer queda como 0.0 y se
cuenta en el estado "degraded" (se reporta el %, para no esconder fallas del formato).

Reglas: temperatura 0, semilla fija, el mismo prompt para todos (su huella queda en cada línea).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import force_utf8_output, read_jsonl  # noqa: E402

PROMPT_UNO = (
    "Eres un evaluador de búsqueda. Dada una consulta y un documento, di qué tan bien el documento responde "
    "la consulta.\nResponde SOLO con un número entre 0 y 1 (0 = nada relevante, 1 = responde exactamente).\n\n"
    "Consulta: {query}\n\nDocumento:\n{doc}\n\nScore:"
)
PROMPT_LOTE = (
    "Eres un evaluador de búsqueda. Dada una consulta y {n} documentos numerados, puntúa cada documento por "
    "separado según qué tan bien responde la consulta (0 = nada relevante, 1 = responde exactamente).\n"
    "Responde SOLO con una lista JSON de {n} números, en el mismo orden. Ejemplo: [0.1, 0.9, ...]\n\n"
    "Consulta: {query}\n\n{docs}\n\nLista:"
)
PROMPT_RGS = (
    "You are a search relevance judge. Rate how well the document answers the query on a scale from 0 to 4:\n"
    "0 = not relevant, 1 = related topic but does not answer, 2 = partially answers, 3 = answers well, "
    "4 = answers perfectly.\nReply with a single digit.\n\nQuery: {query}\n\nDocument:\n{doc}\n\nRating (0-4):"
)
ETIQUETAS = 5  # 0..4
MASA_MINIMA = 0.5  # si el modelo reparte menos de esto entre los dígitos 0-4, no estaba respondiendo la escala
MAX_CHARS = 4000  # un one-pager cabe de sobra; se corta igual para que un texto raro no rompa el contexto
Backend = Callable[[str], str]


def prompt_sha() -> str:
    return hashlib.sha256((PROMPT_UNO + PROMPT_LOTE + PROMPT_RGS).encode("utf-8")).hexdigest()[:8]


def esperanza(probs: Sequence[float]) -> float:
    """E[k]/4 con probabilidades de las etiquetas 0..4 (ya normalizadas). Da un valor continuo en [0, 1]."""
    total = float(sum(probs))
    if total <= 0:
        return 0.0
    return sum(k * p for k, p in enumerate(probs)) / total / (len(probs) - 1)


class Rgs:
    """Scorer con un modelo local de transformers. probs(prompts) -> [(probs0..4 normalizadas, masa), ...]."""

    def __init__(self, modelo: str, device: str = "cuda", max_tokens: int = 2048):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch, self.max_tokens = torch, max_tokens
        self.tok = AutoTokenizer.from_pretrained(modelo)
        self.tok.padding_side = "left"
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        dtype = torch.float16 if device.startswith("cuda") else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(modelo, torch_dtype=dtype).to(device).eval()
        self.device = device
        ids = [self.tok.encode(str(k), add_special_tokens=False) for k in range(ETIQUETAS)]
        if any(len(i) != 1 for i in ids):
            raise SystemExit(f"El tokenizador de {modelo} no representa los dígitos 0-4 como un token cada uno: "
                             f"{ids}. Usa otro modelo o cambia la escala.")
        self.label_ids = [i[0] for i in ids]

    def _texto(self, prompt: str) -> str:
        if getattr(self.tok, "chat_template", None):
            return self.tok.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                                add_generation_prompt=True)
        return prompt

    def probs(self, prompts: Sequence[str]) -> List[Tuple[List[float], float]]:
        """Si la GPU se queda sin memoria con este batch, lo parte en dos y sigue (no se cae a mitad de la corrida)."""
        try:
            return self._probs(prompts)
        except self.torch.cuda.OutOfMemoryError:
            self.torch.cuda.empty_cache()
            if len(prompts) == 1:
                raise
            mid = len(prompts) // 2
            return self.probs(prompts[:mid]) + self.probs(prompts[mid:])

    def _probs(self, prompts: Sequence[str]) -> List[Tuple[List[float], float]]:
        enc = self.tok([self._texto(p) for p in prompts], return_tensors="pt", padding=True, truncation=True,
                       max_length=self.max_tokens, add_special_tokens=False).to(self.device)
        with self.torch.inference_mode():
            logits = self.model(**enc).logits[:, -1, :].float()
        full = self.torch.softmax(logits, dim=-1)
        sel = full[:, self.label_ids]
        masa = sel.sum(dim=-1)
        norm = sel / masa.unsqueeze(-1).clamp_min(1e-12)
        return [(norm[i].tolist(), float(masa[i])) for i in range(len(prompts))]


def tam_lote(modo: str) -> int | None:
    m = re.fullmatch(r"lote(\d+)", modo)
    return int(m.group(1)) if m else None


def puntuar_consulta_rgs(query: str, docs: Sequence[Tuple[str, str]], scorer, modo: str,
                         paralelo: int = 4, lote: int = 10) -> Tuple[Dict[str, float], int]:
    """RG-S: cada documento va en SU prompt. paralelo4 = 4 llamadas a la vez de 1 prompt; lote10 = 10 prompts por pasada."""
    prompts = [(d, PROMPT_RGS.format(query=query, doc=t[:MAX_CHARS])) for d, t in docs]
    if modo == "paralelo4":
        with ThreadPoolExecutor(max_workers=paralelo) as ex:
            res = list(ex.map(lambda it: (it[0], scorer.probs([it[1]])[0]), prompts))
    elif tam_lote(modo):
        lote, res = tam_lote(modo), []
        for i in range(0, len(prompts), lote):
            trozo = prompts[i:i + lote]
            res += [(d, r) for (d, _), r in zip(trozo, scorer.probs([p for _, p in trozo]))]
    else:
        raise ValueError(f"modo desconocido: {modo}")
    scores, malos = {}, 0
    for did, (pr, masa) in res:
        scores[did] = esperanza(pr)
        malos += masa < MASA_MINIMA
    return scores, malos


def leer_numero(texto: str) -> float | None:
    m = re.search(r"-?\d+(?:[.,]\d+)?", texto or "")
    if not m:
        return None
    v = float(m.group().replace(",", "."))
    return min(max(v, 0.0), 1.0)


def leer_lista(texto: str, n: int) -> List[float | None]:
    try:
        m = re.search(r"\[.*?\]", texto or "", re.S)
        vals = json.loads(m.group()) if m else []
        out = [min(max(float(v), 0.0), 1.0) for v in vals][:n]
    except (ValueError, TypeError, json.JSONDecodeError):
        out = []
    return out + [None] * (n - len(out))


def puntuar_consulta(query: str, docs: Sequence[Tuple[str, str]], backend: Backend, modo: str,
                     paralelo: int = 4, lote: int = 10) -> Tuple[Dict[str, float], int]:
    """Devuelve ({id: score}, cantidad de scores ilegibles). Un score ilegible vale 0.0."""
    scores: Dict[str, float] = {}
    malos = 0
    if modo == "paralelo4":
        def uno(item):
            did, texto = item
            return did, leer_numero(backend(PROMPT_UNO.format(query=query, doc=texto[:MAX_CHARS])))
        with ThreadPoolExecutor(max_workers=paralelo) as ex:
            res = list(ex.map(uno, docs))
    elif tam_lote(modo):
        lote, res = tam_lote(modo), []
        for i in range(0, len(docs), lote):
            trozo = docs[i:i + lote]
            cuerpo = "\n\n".join(f"[{j + 1}] {t[:MAX_CHARS]}" for j, (_, t) in enumerate(trozo))
            vals = leer_lista(backend(PROMPT_LOTE.format(n=len(trozo), query=query, docs=cuerpo)), len(trozo))
            res += [(d, v) for (d, _), v in zip(trozo, vals)]
    else:
        raise ValueError(f"modo desconocido: {modo}")
    for did, v in res:
        scores[did] = 0.0 if v is None else v
        malos += v is None
    return scores, malos


def ollama(modelo: str, url: str = "http://localhost:11434", seed: int = 42, timeout: float = 120.0) -> Backend:
    def call(prompt: str) -> str:
        body = json.dumps({"model": modelo, "prompt": prompt, "stream": False,
                           "options": {"temperature": 0, "seed": seed, "num_predict": 64}}).encode("utf-8")
        req = urllib.request.Request(f"{url}/api/generate", body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")).get("response", "")
    return call


def textos(data_dir: str, dataset: str) -> Dict[str, str]:
    p = Path(data_dir) / dataset / "corpus.jsonl"
    return {str(r["_id"]): f"{r.get('title') or ''} {r.get('text') or ''}".strip() for r in read_jsonl(p)}


def main() -> None:
    force_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidatos", required=True)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--backend", choices=["hf", "ollama"], default="hf")
    ap.add_argument("--modelo", required=True, help="hf: id de HuggingFace (p. ej. Qwen/Qwen2.5-3B-Instruct); "
                    "ollama: nombre del modelo (p. ej. qwen2.5:3b)")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--modo", default="lote10", help="lote4, lote10 (o loteN) o paralelo4")
    ap.add_argument("--url", default="http://localhost:11434")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-queries", type=int)
    args = ap.parse_args()

    corpus = textos(args.data_dir, args.dataset)
    scorer = Rgs(args.modelo, args.device) if args.backend == "hf" else None
    backend = ollama(args.modelo, args.url) if args.backend == "ollama" else None
    sha = prompt_sha()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    total_malos = total = 0
    parte_s, parte_t = Path(f"{out}.scores.jsonl.part"), Path(f"{out}.tiempos.tsv.part")
    with open(parte_s, "w", encoding="utf-8") as fs, open(parte_t, "w", encoding="utf-8") as ft:
        for n, rec in enumerate(read_jsonl(args.candidatos), start=1):
            if args.max_queries and n > args.max_queries:
                break
            docs = [(d["id"], corpus[d["id"]]) for d in rec["docs"]]
            t0 = time.perf_counter()
            try:
                scores, malos = (puntuar_consulta_rgs(rec["query"], docs, scorer, args.modo) if scorer
                                 else puntuar_consulta(rec["query"], docs, backend, args.modo))
                estado = "degraded" if malos else "ok"
            except Exception as e:  # noqa: BLE001  (timeout, Ollama caído...): se anota y se sigue
                print(f"qid {rec['qid']}: {e}", file=sys.stderr)
                scores, malos, estado = {d: 0.0 for d, _ in docs}, len(docs), "error"
            ms = (time.perf_counter() - t0) * 1000
            total_malos += malos
            total += len(docs)
            for did, s in scores.items():
                fs.write(json.dumps({"qid": rec["qid"], "id": did, "score": s, "modelo": args.modelo,
                                     "modo": args.modo, "backend": args.backend, "prompt_sha": sha}) + "\n")
            ft.write(f"{rec['qid']}\t{ms:.3f}\t{estado}\n")
    parte_s.replace(f"{out}.scores.jsonl")  # solo existe el archivo final si la corrida terminó
    parte_t.replace(f"{out}.tiempos.tsv")
    print(f"listo: {total} documentos puntuados, {total_malos} ilegibles ({100 * total_malos / max(total, 1):.2f} %)")


if __name__ == "__main__":
    main()

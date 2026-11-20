"""Genera los one-pagers (resumen corto) de cada documento de la submuestra con un LLM pequeño local.

Se genera UNA vez, antes de medir, y lo leen las DOS arquitecturas (mismo dataset). No cuenta en la latencia de consulta.
Decodificación voraz (sin muestreo), así que con el mismo modelo y prompt sale lo mismo. Se puede cortar y retomar:
los documentos que ya están en el archivo de salida se saltan.

  python calidad/src/generar_onepagers.py --data-dir data/fiqa-8000 --modelo Qwen/Qwen2.5-3B-Instruct \
      --out data/fiqa-8000.onepagers.jsonl --batch 16
  python calidad/src/generar_onepagers.py ... --max-docs 64      # prueba corta: mide cuántos documentos por segundo
  python calidad/src/generar_onepagers.py ... --shard 2/3        # solo la parte 2 de 3 (cada persona una parte)

Salida (formato de onepagers.py): {"_id","text","model","prompt_sha","seed"}. Imprime el ritmo y el tiempo estimado
restante, para saber si cabe en las horas disponibles. Después: `onepagers.py check` y `onepagers.py build`.
El one-pager NO debe agregar información: revisar a mano unos cuantos con `review_sample.py` antes de medir.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import force_utf8_output, read_jsonl  # noqa: E402
from onepagers import prompt_sha  # noqa: E402

PROMPT_ONEPAGER = (
    "Write a one-page digest of the document below in at most {palabras} words, in English. Include: the main topic, "
    "the key facts, figures and named entities, and what questions the document can answer. Use only information "
    "that is in the document. If the document is already short, keep all of its key details.\n\n"
    "Title: {titulo}\n\nDocument:\n{texto}\n\nDigest:"
)


def prompt_para(doc: dict, palabras: int, max_chars: int = 6000) -> str:
    return PROMPT_ONEPAGER.format(palabras=palabras, titulo=(doc.get("title") or "").strip(),
                                  texto=(doc.get("text") or "").strip()[:max_chars])


def pendientes(corpus_ids: Sequence[str], hechos: Dict[str, dict]) -> List[str]:
    return [i for i in corpus_ids if i not in hechos]


def respaldo(doc: dict, palabras: int) -> str:
    """Si el modelo no devolvió nada útil: las primeras palabras del documento, para no perder la corrida entera."""
    base = f"{(doc.get('title') or '').strip()}. {(doc.get('text') or '').strip()}".strip(" .")
    return " ".join(base.split()[:palabras])


def en_shard(ids: Sequence[str], i: int, n: int) -> List[str]:
    """Reparte los documentos en n partes iguales y estables (por orden de ID): la parte i (1..n)."""
    if not 1 <= i <= n:
        raise ValueError(f"shard {i}/{n} inválido")
    return [d for k, d in enumerate(sorted(ids)) if k % n == i - 1]


def limpiar(texto: str) -> str:
    t = " ".join((texto or "").split())
    return t.removeprefix("Digest:").strip()


def main() -> None:
    force_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True, help="directorio BEIR de la submuestra (con corpus.jsonl)")
    ap.add_argument("--modelo", required=True, help="id de HuggingFace, p. ej. Qwen/Qwen2.5-3B-Instruct")
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--palabras", type=int, default=90)
    ap.add_argument("--max-new-tokens", type=int, default=160)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--shard", help="i/N: genera solo la parte i de N (para repartir entre varias personas)")
    ap.add_argument("--max-docs", type=int)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.manual_seed(args.seed)
    corpus = {str(d["_id"]): d for d in read_jsonl(Path(args.data_dir) / "corpus.jsonl")}
    out = Path(args.out)
    hechos = {str(r["_id"]): r for r in read_jsonl(out)} if out.exists() else {}
    ids = sorted(corpus)
    if args.shard:
        i, n = map(int, args.shard.split("/"))
        ids = en_shard(ids, i, n)
    faltan = pendientes(ids, hechos)
    if args.max_docs:
        faltan = faltan[:args.max_docs]
    print(f"{len(corpus)} documentos, {len(hechos)} ya listos, {len(faltan)} por generar", file=sys.stderr)

    tok = AutoTokenizer.from_pretrained(args.modelo)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    dtype = torch.float16 if args.device.startswith("cuda") else torch.float32
    model = AutoModelForCausalLM.from_pretrained(args.modelo, torch_dtype=dtype).to(args.device).eval()
    sha = prompt_sha_onepager()
    t0, n, respaldos = time.perf_counter(), 0, 0
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8") as f:
        for i in range(0, len(faltan), args.batch):
            ids = faltan[i:i + args.batch]
            prompts = []
            for d in ids:
                p = prompt_para(corpus[d], args.palabras)
                prompts.append(tok.apply_chat_template([{"role": "user", "content": p}], tokenize=False,
                                                       add_generation_prompt=True)
                               if getattr(tok, "chat_template", None) else p)
            enc = tok(prompts, return_tensors="pt", padding=True, truncation=True, max_length=2048,
                      add_special_tokens=False).to(args.device)
            textos = generar(model, tok, enc, args.max_new_tokens, torch)
            for d, t in zip(ids, textos):
                txt = limpiar(t)
                usado = len(txt.split()) >= 5
                if not usado:
                    txt, respaldos = respaldo(corpus[d], args.palabras), respaldos + 1
                f.write(json.dumps({"_id": d, "text": txt, "model": args.modelo, "prompt_sha": sha,
                                    "seed": args.seed, **({} if usado else {"respaldo": True})},
                                   ensure_ascii=False) + "\n")
            f.flush()
            n += len(ids)
            seg = time.perf_counter() - t0
            resto = (len(faltan) - n) * seg / n
            print(f"{n}/{len(faltan)}  {n / seg:.2f} docs/s  faltan ~{resto / 60:.0f} min  (respaldos: {respaldos})",
                  file=sys.stderr)
    if respaldos:
        print(f"AVISO: {respaldos} one-pagers salieron vacíos y se reemplazaron por el inicio del documento "
              f"(marcados con \"respaldo\": true).", file=sys.stderr)


def generar(model, tok, enc, max_new_tokens: int, torch) -> List[str]:
    """Genera por lotes; si no cabe en la GPU, parte el lote en dos."""
    try:
        with torch.inference_mode():
            gen = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tok.pad_token_id)
        return tok.batch_decode(gen[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        n = enc["input_ids"].shape[0]
        if n == 1:
            raise
        mid = n // 2
        a = {k: v[:mid] for k, v in enc.items()}
        b = {k: v[mid:] for k, v in enc.items()}
        return generar(model, tok, a, max_new_tokens, torch) + generar(model, tok, b, max_new_tokens, torch)


def prompt_sha_onepager() -> str:
    """Huella del prompt de los one-pagers (se anota en cada línea)."""
    return prompt_sha(PROMPT_ONEPAGER)


if __name__ == "__main__":
    main()

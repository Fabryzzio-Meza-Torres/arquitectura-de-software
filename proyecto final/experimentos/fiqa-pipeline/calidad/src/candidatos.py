"""Candidatos de la comparación: los mismos del sistema MINION (BM25 + bge), con sus dos scores.

Usa EXACTAMENTE la configuración de `minion_bench.py` (BM25 lucene k1=0.9 b=0.4, stemmer y stopwords en inglés;
bge-base-en-v1.5 con CLS, L2 y el prefijo de consulta; top 10 de cada rama; desempate por ID ascendente).
La unión de los dos top 10 son los candidatos (hasta 20 por consulta). Aquí NO se fusiona ni se reordena nada:
solo se guardan los scores crudos, que después usan base, propuesta y solo léxico.

Salida (JSONL, una consulta por línea):
  {"qid": "8", "query": "texto de la consulta", "docs": [{"id": "123", "lex": 11.2, "sem": 0.71}, ...]}

Uso (en Kaggle/Khipu, con GPU; el corpus puede ser el de one-pagers: --data-dir apunta a donde está <dataset>/):
  python calidad/src/candidatos.py --dataset fiqa --data-dir data --split test --out calidad/out/fiqa
  python calidad/src/candidatos.py --dataset fiqa --data-dir data --split dev  --out calidad/out/fiqa
Con --split dev se usan los qrels de desarrollo (para elegir alfa); con test, los de prueba.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import numpy as np

KHIPU = Path(__file__).resolve().parents[2]  # paper/khipu
sys.path.insert(0, str(KHIPU))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import minion_bench as mb  # noqa: E402  (importar no carga torch ni bm25s)
from io_formats import force_utf8_output  # noqa: E402


def construir(doc_ids: Sequence[str], emb: np.ndarray, queries: Iterable[Tuple[str, str]],
              lex_scores_fn: Callable[[str], np.ndarray], encode_query_fn: Callable[[str], np.ndarray],
              k: int = 10) -> List[dict]:
    """Núcleo sin modelos: recibe funciones de score, así se puede probar con datos de juguete."""
    order = sorted(range(len(doc_ids)), key=lambda i: doc_ids[i])
    id_rank = np.empty(len(order), dtype=np.int64)
    id_rank[order] = np.arange(len(order))
    out = []
    for qid, text in queries:
        lex = np.asarray(lex_scores_fn(text), dtype=np.float32)
        sem = (emb @ np.asarray(encode_query_fn(text), dtype=np.float32)).astype(np.float32)
        top = np.unique(np.concatenate([mb.topk_tiebreak(lex, k, id_rank), mb.topk_tiebreak(sem, k, id_rank)]))
        out.append({"qid": str(qid), "query": text, "docs": [{"id": doc_ids[i], "lex": float(lex[i]), "sem": float(sem[i])}
                                              for i in top]})
    return out


def leer_qids(data_dir: Path, dataset: str, split: str) -> List[str]:
    p = data_dir / dataset / "qrels" / f"{split}.tsv"
    if not p.exists():
        raise SystemExit(f"No existe {p}. {dataset} no trae el split '{split}'.")
    qids: List[str] = []
    with open(p, encoding="utf-8") as f:
        next(f)
        for line in f:
            qid = line.split("\t")[0]
            if qid not in qids:
                qids.append(qid)
    return qids


class Motores:
    """Mismo BM25 y mismo encoder que `minion_bench.Engine`, sin reranker (no hace falta aquí)."""

    def __init__(self, corpus: List[dict], device: str, encode_batch: int):
        import bm25s
        import Stemmer
        import torch
        from sentence_transformers import SentenceTransformer

        self.torch, self.bm25s, self.Stemmer = torch, bm25s, Stemmer
        self.doc_ids = [str(d["_id"]) for d in corpus]
        texts = [f"{d.get('title') or ''} {d.get('text') or ''}" for d in corpus]  # igual que Engine.texts
        self._local = threading.local()
        lc = mb.CONFIG["lexical"]
        tokens = bm25s.tokenize(texts, stopwords=lc["stopwords"], stemmer=self._stemmer(), show_progress=False)
        self.bm25 = bm25s.BM25(method=lc["method"], k1=lc["k1"], b=lc["b"])
        self.bm25.index(tokens, show_progress=False)
        sem = mb.CONFIG["semantic"]
        self.prefix = sem["query_prefix"]
        self.encoder = SentenceTransformer(sem["model"], revision=sem["model_revision"], device=device)
        self.encoder.max_seq_length = sem["max_length"]
        if device.startswith("cuda"):
            self.encoder.half()
        self.emb = self._encode(texts, encode_batch)
        self._n = len(self.doc_ids)

    def _stemmer(self):
        if not hasattr(self._local, "stemmer"):
            self._local.stemmer = self.Stemmer.Stemmer("english")
        return self._local.stemmer

    def _encode(self, texts: List[str], batch: int) -> np.ndarray:
        with self.torch.inference_mode():
            e = self.encoder.encode(texts, batch_size=batch, convert_to_tensor=True,
                                    normalize_embeddings=False, show_progress_bar=False)
            e = self.torch.nn.functional.normalize(e.float(), dim=-1)
        return np.ascontiguousarray(e.cpu().numpy(), dtype=np.float32)

    def lex(self, q: str) -> np.ndarray:
        toks = self.bm25s.tokenize([q], stopwords="en", stemmer=self._stemmer(), return_ids=False,
                                   show_progress=False)[0]
        return np.asarray(self.bm25.get_scores(toks), dtype=np.float32) if toks else np.zeros(self._n, np.float32)

    def encode_query(self, q: str) -> np.ndarray:
        return self._encode([self.prefix + q], 1)[0]


def main() -> None:
    force_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", required=True, choices=list(mb.CONFIG["datasets"]))
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--split", choices=["dev", "test"], default="test")
    ap.add_argument("--out", required=True, help="prefijo de salida; escribe <out>.<split>.candidatos.jsonl")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--encode-batch", type=int, default=64)
    ap.add_argument("--max-queries", type=int)
    args = ap.parse_args()

    corpus, queries, _, _ = mb.load_dataset(args.dataset, args.data_dir)
    qids = [q for q in leer_qids(Path(args.data_dir), args.dataset, args.split) if q in queries]
    if args.max_queries:
        qids = qids[:args.max_queries]
    print(f"{args.dataset}/{args.split}: {len(corpus)} documentos, {len(qids)} consultas", file=sys.stderr)
    m = Motores(corpus, args.device, args.encode_batch)
    rows = construir(m.doc_ids, m.emb, [(q, queries[q]) for q in qids], m.lex, m.encode_query)
    out = Path(f"{args.out}.{args.split}.candidatos.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    parte = out.with_name(out.name + ".part")
    with open(parte, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    parte.replace(out)
    print(f"escrito {out} ({sum(len(r['docs']) for r in rows) / max(len(rows), 1):.1f} candidatos por consulta)")


if __name__ == "__main__":
    main()

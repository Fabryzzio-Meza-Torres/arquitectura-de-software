"""BM25 de referencia (léxico) para validar la evaluación y servir de línea base.

Uso:
  python src/bm25_baseline.py --data-dir data/nfcorpus --split test --out results/nfcorpus/bm25_test

Genera <out>.run (formato TREC, top-k) y <out>.latency.tsv (una fila por query, en ms).
Parámetros: k1=1.2, b=0.75 (valores por defecto de Elasticsearch/Lucene, el BM25 que usa BEIR).
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import time
from array import array
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import load_qrels, read_jsonl, write_run, force_utf8_output  # noqa: E402

TOKEN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset("a an and are as at be but by for if in into is it no not of on or such that the their then there "
                      "these they this to was will with".split())


def tokenize(text: str) -> List[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOPWORDS]


class BM25:
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1, self.b = k1, b
        self.doc_ids: List[str] = []
        self.postings: Dict[str, Tuple[array, array]] = {}
        self.doc_len: np.ndarray = np.zeros(0)
        self.avgdl = 0.0
        self._frozen: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

    def fit(self, docs: Iterable[Tuple[str, str]]) -> "BM25":
        lengths = array("I")
        for idx, (docid, text) in enumerate(docs):
            self.doc_ids.append(docid)
            tokens = tokenize(text)
            lengths.append(len(tokens))
            for term, tf in Counter(tokens).items():
                if term not in self.postings:
                    self.postings[term] = (array("I"), array("I"))
                ids, tfs = self.postings[term]
                ids.append(idx)
                tfs.append(tf)
        self.doc_len = np.frombuffer(lengths, dtype=np.uint32).astype(np.float64) if len(lengths) else np.zeros(0)
        self.avgdl = float(self.doc_len.mean()) if len(self.doc_len) else 0.0
        return self

    def _term(self, term: str):
        if term not in self._frozen:
            ids, tfs = self.postings[term]
            self._frozen[term] = (np.frombuffer(ids, dtype=np.uint32).astype(np.int64),
                                  np.frombuffer(tfs, dtype=np.uint32).astype(np.float64))
        return self._frozen[term]

    def search(self, query: str, k: int = 100) -> List[Tuple[str, float]]:
        n = len(self.doc_ids)
        scores = np.zeros(n)
        for term in set(tokenize(query)):
            if term not in self.postings:
                continue
            ids, tf = self._term(term)
            df = len(ids)
            idf = math.log(1.0 + (n - df + 0.5) / (df + 0.5))  # variante de Lucene: nunca negativa
            norm = self.k1 * (1.0 - self.b + self.b * self.doc_len[ids] / self.avgdl)
            scores[ids] += idf * tf * (self.k1 + 1.0) / (tf + norm)
        positive = np.flatnonzero(scores > 0)
        if len(positive) == 0:
            return []
        if len(positive) > k:
            top = positive[np.argpartition(-scores[positive], k - 1)[:k]]
        else:
            top = positive
        top = top[np.lexsort((top, -scores[top]))]  # score desc; empates por posición, determinista
        return [(self.doc_ids[i], float(scores[i])) for i in top]


def corpus_texts(path: Path) -> Iterable[Tuple[str, str]]:
    for d in read_jsonl(path):
        yield d["_id"], ((d.get("title") or "") + " " + (d.get("text") or ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--split", required=True, help="nombre del archivo de qrels sin .tsv (dev, test)")
    ap.add_argument("--out", required=True, help="prefijo de salida")
    ap.add_argument("--top-k", type=int, default=100)
    args = ap.parse_args()

    data = Path(args.data_dir)
    qrels = load_qrels(data / "qrels" / f"{args.split}.tsv")
    queries = {q["_id"]: q["text"] for q in read_jsonl(data / "queries.jsonl") if q["_id"] in qrels}

    t0 = time.perf_counter()
    bm25 = BM25().fit(corpus_texts(data / "corpus.jsonl"))
    print(f"Índice BM25: {len(bm25.doc_ids):,} documentos en {time.perf_counter() - t0:.1f} s (no cuenta en la latencia)")

    run, latencies = {}, []
    for qid in sorted(queries):
        t = time.perf_counter()
        results = bm25.search(queries[qid], args.top_k)
        latencies.append((qid, (time.perf_counter() - t) * 1000.0))
        run[qid] = dict(results)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_run(f"{out}.run", run, "bm25")
    with open(f"{out}.latency.tsv", "w", encoding="utf-8") as f:
        for qid, ms in latencies:
            f.write(f"{qid}\t{ms:.3f}\tok\n")
    print(f"{len(run)} queries -> {out}.run y {out}.latency.tsv")


if __name__ == "__main__":
    force_utf8_output()
    main()

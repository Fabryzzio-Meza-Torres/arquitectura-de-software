"""Revisión manual de documentos sin juicio (qrels incompletos).

1) sample: elige queries al azar, junta el top-k de uno o más runs y exporta los documentos
   SIN juicio a un CSV para etiquetar a mano (columna `label`: 0, 1 o 2).
2) merge: convierte el CSV etiquetado en un qrels extra (TSV) que evaluate.py une a los originales.

Uso:
  python src/review_sample.py sample --qrels data/nfcorpus/qrels/test.tsv \
      --queries data/nfcorpus/queries.jsonl --corpus data/nfcorpus/corpus.jsonl \
      --runs results/e1_bm25.run results/e1_dense.run --k 10 --n-queries 40 --out results/review.csv
  python src/review_sample.py merge --csv results/review.csv --out results/review.qrels.tsv
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import load_qrels, load_run, read_jsonl, force_utf8_output  # noqa: E402
from metrics import ranked_list, relevant_docs  # noqa: E402


def sample(args: argparse.Namespace) -> None:
    qrels = load_qrels(args.qrels)
    queries = {q["_id"]: q["text"] for q in read_jsonl(args.queries)}
    corpus = {d["_id"]: d for d in read_jsonl(args.corpus)}
    runs = [load_run(p) for p in args.runs]

    eligible = sorted(q for q in qrels if relevant_docs(qrels[q]))
    rng = random.Random(args.seed)
    chosen = sorted(rng.sample(eligible, min(args.n_queries, len(eligible))))

    rows = []
    for qid in chosen:
        seen = {}
        for run in runs:
            for rank, docid in enumerate(ranked_list(run.get(qid, {}))[: args.k], start=1):
                if docid not in qrels[qid]:  # sin juicio
                    seen[docid] = min(rank, seen.get(docid, rank))
        for docid, best_rank in sorted(seen.items(), key=lambda kv: kv[1]):
            d = corpus.get(docid, {})
            rows.append({
                "qid": qid, "query": queries.get(qid, ""), "docid": docid, "best_rank": best_rank,
                "title": d.get("title", ""), "text": (d.get("text", "") or "")[:400].replace("\n", " "), "label": "",
            })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["qid", "query", "docid", "best_rank", "title", "text", "label"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(chosen)} queries, {len(rows)} documentos sin juicio para etiquetar -> {out}")
    print("Etiquetas: 0 = no relevante, 1 = relevante, 2 = muy relevante (misma escala que los qrels).")


def merge(args: argparse.Namespace) -> None:
    n = skipped = 0
    with open(args.csv, encoding="utf-8", newline="") as f, open(args.out, "w", encoding="utf-8") as out:
        for row in csv.DictReader(f):
            label = row["label"].strip()
            if label == "":
                skipped += 1
                continue
            if label not in {"0", "1", "2"}:
                raise ValueError(f"Etiqueta inválida {label!r} (query {row['qid']}, doc {row['docid']}); usar 0, 1 o 2.")
            out.write(f"{row['qid']}\t{row['docid']}\t{label}\n")
            n += 1
    print(f"{n} juicios escritos en {args.out} ({skipped} filas sin etiqueta omitidas).")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--qrels", required=True)
    s.add_argument("--queries", required=True)
    s.add_argument("--corpus", required=True)
    s.add_argument("--runs", nargs="+", required=True)
    s.add_argument("--k", type=int, default=10)
    s.add_argument("--n-queries", type=int, default=40)
    s.add_argument("--seed", type=int, default=42)
    s.add_argument("--out", required=True)
    s.set_defaults(func=sample)
    m = sub.add_parser("merge")
    m.add_argument("--csv", required=True)
    m.add_argument("--out", required=True)
    m.set_defaults(func=merge)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    force_utf8_output()
    main()

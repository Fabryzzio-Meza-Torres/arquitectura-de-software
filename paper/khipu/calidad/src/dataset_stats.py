"""Estadísticas verificables de un dataset en formato BEIR + ejemplos reales.

Uso:
  python src/dataset_stats.py --data-dir data/nfcorpus --out results/nfcorpus/stats.json

Imprime una tabla en Markdown y guarda todo (incluidos ejemplos) en el JSON.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import load_qrels, read_jsonl, force_utf8_output  # noqa: E402

SNIPPET = 300


def _words(d: dict) -> int:
    return len(((d.get("title") or "") + " " + (d.get("text") or "")).split())


def compute_stats(data_dir: Path) -> dict:
    corpus_ids, lengths = set(), []
    for d in read_jsonl(data_dir / "corpus.jsonl"):
        corpus_ids.add(d["_id"])
        lengths.append(_words(d))
    queries = {q["_id"]: q["text"] for q in read_jsonl(data_dir / "queries.jsonl")}

    stats: dict = {
        "dataset": data_dir.name,
        "n_docs": len(corpus_ids),
        "n_queries": len(queries),
        "doc_words_mean": round(statistics.mean(lengths), 1) if lengths else 0,
        "doc_words_median": statistics.median(lengths) if lengths else 0,
        "splits": {},
    }
    qrels_dir = data_dir / "qrels"
    for qpath in sorted(qrels_dir.glob("*.tsv")):
        qrels = load_qrels(qpath)
        rel_counts: List[int] = []
        grades: Counter = Counter()
        n_judgments = missing = 0
        for qid, docs in qrels.items():
            n_rel = sum(1 for g in docs.values() if g > 0)
            rel_counts.append(n_rel)
            for doc, g in docs.items():
                grades[g] += 1
                n_judgments += 1
                missing += doc not in corpus_ids
        with_rel = [c for c in rel_counts if c > 0]
        stats["splits"][qpath.stem] = {
            "n_queries_judged": len(qrels),
            "n_queries_with_relevant": len(with_rel),
            "n_judgments": n_judgments,
            "grades": {str(k): v for k, v in sorted(grades.items())},
            "relevant_per_query": {
                "mean": round(statistics.mean(with_rel), 1) if with_rel else 0,
                "median": statistics.median(with_rel) if with_rel else 0,
                "min": min(with_rel) if with_rel else 0,
                "max": max(with_rel) if with_rel else 0,
            },
            "pct_queries_with_3plus_relevant": round(100 * sum(c >= 3 for c in with_rel) / len(with_rel), 1) if with_rel else 0,
            "judged_docs_missing_from_corpus": missing,
        }
    stats["examples"] = _examples(data_dir, queries)
    return stats


def _examples(data_dir: Path, queries: Dict[str, str]) -> dict:
    """Una query real con un documento relevante y uno juzgado no relevante (si existe)."""
    split = "test" if (data_dir / "qrels" / "test.tsv").exists() else None
    if split is None:
        files = sorted((data_dir / "qrels").glob("*.tsv"))
        if not files:
            return {}
        split = files[0].stem
    qrels = load_qrels(data_dir / "qrels" / f"{split}.tsv")
    chosen = next((q for q in sorted(qrels) if q in queries and sum(g > 0 for g in qrels[q].values()) >= 3), None)
    if chosen is None:
        return {}
    best_rel = max((d for d, g in qrels[chosen].items() if g > 0), key=lambda d: (qrels[chosen][d], d))
    non_rel = next((d for d, g in sorted(qrels[chosen].items()) if g == 0), None)
    wanted = {best_rel, non_rel} - {None}
    found = {d["_id"]: d for d in read_jsonl(data_dir / "corpus.jsonl") if d["_id"] in wanted}

    def pack(docid, grade):
        d = found.get(docid, {})
        text = ((d.get("title") or "") + ". " + (d.get("text") or "")).strip()
        return {"docid": docid, "grade": grade, "text": text[:SNIPPET] + ("…" if len(text) > SNIPPET else "")}

    return {
        "split": split, "qid": chosen, "query": queries[chosen],
        "relevant_doc": pack(best_rel, qrels[chosen][best_rel]),
        "not_relevant_doc": pack(non_rel, 0) if non_rel else None,
    }


def to_markdown(stats: dict) -> str:
    lines = [f"**{stats['dataset']}**: {stats['n_docs']:,} documentos · {stats['n_queries']:,} queries · "
             f"{stats['doc_words_mean']} palabras por documento (media)", "",
             "| Split | Queries con juicios | Juicios | Grados | Relevantes por query (media / mediana / mín / máx) | % con ≥3 relevantes | Juicios sin documento |",
             "| --- | ---: | ---: | --- | --- | ---: | ---: |"]
    for name, s in stats["splits"].items():
        r = s["relevant_per_query"]
        lines.append(f"| {name} | {s['n_queries_with_relevant']} | {s['n_judgments']} | {s['grades']} | "
                     f"{r['mean']} / {r['median']} / {r['min']} / {r['max']} | {s['pct_queries_with_3plus_relevant']} | "
                     f"{s['judged_docs_missing_from_corpus']} |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", help="JSON de salida")
    args = ap.parse_args()
    stats = compute_stats(Path(args.data_dir))
    print(to_markdown(stats))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    force_utf8_output()
    main()

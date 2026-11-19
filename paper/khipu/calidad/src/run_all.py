"""Un solo comando: descarga, verifica, calcula estadísticas, corre BM25 de validación y arma la tabla.

Uso:
  python src/run_all.py                          # NFCorpus, TREC-COVID y FiQA
  python src/run_all.py --datasets nfcorpus      # solo NFCorpus (rápido)
  python src/run_all.py --skip-download          # si los datos ya están en data/

Resultados en results/<dataset>/ y una tabla resumen en results/baseline_bm25.md.
Si algo falla en un dataset, sigue con el siguiente y lo dice al final.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bm25_baseline import BM25, corpus_texts  # noqa: E402
from dataset_stats import compute_stats, to_markdown  # noqa: E402
from download_data import DATASETS, download, update_manifest  # noqa: E402
from evaluate import evaluate_files, print_summary  # noqa: E402
from io_formats import load_qrels, read_jsonl, write_run, force_utf8_output  # noqa: E402
from make_table import build_table, plot  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# nDCG@10 de BM25 "flat" (título y texto en un solo campo, como nuestro BM25), de "Resources for Brewing BEIR"
# (arXiv 2306.07471, tablas 2 y 3). La variante "multifield" (0.325 y 0.656) indexa título y texto por separado: no es comparable.
# Nuestro BM25 no usa stemming ni los parámetros de Anserini, así que se espera quedar algo por debajo. Solo se usa para avisar.
REFERENCE_NDCG10 = {("nfcorpus", "test"): 0.322, ("trec-covid", "test"): 0.595}
# FiQA: no tenemos un valor verificado del BM25 flat; no se compara hasta confirmarlo en la tabla del paper (no se usa uno de memoria).
TOLERANCE = 0.05
SPLITS = ("dev", "test")


def run_dataset(name: str, data_root: Path, results_root: Path, skip_download: bool) -> list:
    if not skip_download and name in DATASETS:
        update_manifest(data_root, [download(name, data_root)])
    data = data_root / name
    if not (data / "corpus.jsonl").exists():
        raise FileNotFoundError(f"No hay datos en {data}. Corre sin --skip-download.")
    out = results_root / name
    out.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {name}: estadísticas ===")
    stats = compute_stats(data)
    (out / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(to_markdown(stats))

    splits = [s for s in SPLITS if (data / "qrels" / f"{s}.tsv").exists()]
    if not splits:
        raise FileNotFoundError(f"{data / 'qrels'} no tiene dev.tsv ni test.tsv")
    print(f"\n=== {name}: índice BM25 ===")
    t0 = time.perf_counter()
    bm25 = BM25().fit(corpus_texts(data / "corpus.jsonl"))
    print(f"{len(bm25.doc_ids):,} documentos indexados en {time.perf_counter() - t0:.1f} s")
    all_queries = {q["_id"]: q["text"] for q in read_jsonl(data / "queries.jsonl")}

    entries = []
    for split in splits:
        qrels_path = data / "qrels" / f"{split}.tsv"
        qids = sorted(q for q in load_qrels(qrels_path) if q in all_queries)
        run, lat = {}, []
        for qid in qids:
            t = time.perf_counter()
            res = bm25.search(all_queries[qid], 100)
            lat.append((qid, (time.perf_counter() - t) * 1000.0))
            run[qid] = dict(res)
        prefix = out / f"bm25_{split}"
        write_run(f"{prefix}.run", run, "bm25")
        Path(f"{prefix}.latency.tsv").write_text("".join(f"{q}\t{ms:.3f}\tok\n" for q, ms in lat), encoding="utf-8")
        print(f"\n--- {name} / {split}: BM25 ---")
        summary = evaluate_files(str(qrels_path), f"{prefix}.run", str(prefix), f"{prefix}.latency.tsv")
        print_summary(summary)
        ref = REFERENCE_NDCG10.get((name, split))
        if ref is not None:
            got = summary["metrics"]["nDCG@10"]
            ok = abs(got - ref) <= TOLERANCE
            print(f"  Control: nDCG@10 = {got:.3f} frente a {ref} publicado (BM25 flat) -> "
                  f"{'OK' if ok else 'REVISAR: diferencia mayor a ' + str(TOLERANCE)}")
            summary["control_ndcg10"] = {"reference": ref, "ok": ok}
        entries.append((f"{name}/{split}", summary))
    return entries


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", nargs="+", default=DATASETS)
    ap.add_argument("--data-root", default=str(ROOT / "data"))
    ap.add_argument("--results-root", default=str(ROOT / "results"))
    ap.add_argument("--skip-download", action="store_true")
    args = ap.parse_args()

    data_root, results_root = Path(args.data_root), Path(args.results_root)
    all_entries, failures = [], []
    for name in args.datasets:
        try:
            all_entries += run_dataset(name, data_root, results_root, args.skip_download)
        except Exception as e:  # sigue con el siguiente dataset
            traceback.print_exc()
            failures.append((name, str(e)))

    if all_entries:
        table = build_table(all_entries)
        results_root.mkdir(parents=True, exist_ok=True)
        (results_root / "baseline_bm25.md").write_text(table + "\n", encoding="utf-8")
        plot(all_entries, str(results_root / "baseline_p3_vs_p99.png"))
        print("\n=== Resumen ===\n" + table)

    print("\n=== Estado final ===")
    controls = [(n, s["control_ndcg10"]["ok"]) for n, s in all_entries if "control_ndcg10" in s]
    for n, ok in controls:
        print(f"  Control BM25 {n}: {'OK' if ok else 'REVISAR'}")
    for name, err in failures:
        print(f"  FALLÓ {name}: {err}")
    if failures or not all(ok for _, ok in controls):
        sys.exit(1)
    print("  Todo listo.")


if __name__ == "__main__":
    force_utf8_output()
    main()

"""Evalúa un run contra los qrels y (opcional) resume su latencia.

Uso:
  python src/evaluate.py --qrels data/nfcorpus/qrels/test.tsv --run results/e1_bm25.run \
      --latency results/e1_bm25.latency.tsv --out results/e1_bm25

Genera:
  <out>.summary.json    promedios, nº de queries, latencia
  <out>.per_query.csv   una fila por query (insumo de significance.py)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from io_formats import Qrels, Run, load_latency, load_qrels, load_run, load_stages, merge_qrels, force_utf8_output  # noqa: E402
from latency import summarize_latency, summarize_stages  # noqa: E402
from metrics import DEFAULT_METRICS, METRICS, ranked_list, relevant_docs  # noqa: E402


def evaluate(run: Run, qrels: Qrels, metric_names: List[str]) -> Dict[str, Dict[str, float]]:
    """Métricas por query. El denominador son TODAS las queries con al menos un relevante en los qrels:
    una query sin resultados en el run puntúa 0 (no se descarta)."""
    per_query: Dict[str, Dict[str, float]] = {}
    for qid in sorted(qrels):
        qrel = qrels[qid]
        if not relevant_docs(qrel):
            continue
        ranked = ranked_list(run.get(qid, {}))
        per_query[qid] = {m: METRICS[m](ranked, qrel) for m in metric_names}
    return per_query


def summarize(per_query: Dict[str, Dict[str, float]], metric_names: List[str]) -> Dict[str, float]:
    n = len(per_query)
    return {m: sum(v[m] for v in per_query.values()) / n for m in metric_names} if n else {}


def evaluate_files(qrels_path: str, run_path: str, out_prefix: str, latency_path: Optional[str] = None,
                   extra_qrels: Optional[str] = None, metric_names: Optional[List[str]] = None,
                   meta: Optional[Dict[str, str]] = None) -> dict:
    """Evalúa y escribe <out>.summary.json y <out>.per_query.csv. Devuelve el resumen.

    `meta` guarda datos libres del experimento (por ejemplo system, group, corpus_size) que report.py usa en los gráficos."""
    metric_names = metric_names or DEFAULT_METRICS
    qrels = load_qrels(qrels_path)
    if extra_qrels:
        qrels = merge_qrels(qrels, load_qrels(extra_qrels))
    run = load_run(run_path)

    per_query = evaluate(run, qrels, metric_names)
    summary = {
        "run": str(run_path),
        "qrels": str(qrels_path),
        "extra_qrels": extra_qrels,
        "n_queries_evaluated": len(per_query),
        "n_queries_missing_in_run": sum(1 for q in per_query if q not in run),
        "n_queries_in_run_not_in_qrels": sum(1 for q in run if q not in qrels),
        "metrics": summarize(per_query, metric_names),
        "meta": meta or {},
    }
    if latency_path:
        rows, extra = load_latency(latency_path, with_extra=True)
        # sin 4.ª columna no sabemos cuántas duplicadas hubo: no se inventa un 0 %
        has_extra_col = any(len(l.rstrip("\n").split("\t")) == 4 for l in open(latency_path, encoding="utf-8"))
        summary["latency"] = summarize_latency(rows, extra if has_extra_col else None)
        stages_path = Path(str(latency_path).replace(".latency.tsv", ".stages.tsv"))
        if stages_path.exists() and stages_path != Path(latency_path):
            summary["stages"] = summarize_stages(load_stages(stages_path))

    out = Path(out_prefix)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}.per_query.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["qid"] + metric_names)
        for qid, vals in per_query.items():
            w.writerow([qid] + [f"{vals[m]:.6f}" for m in metric_names])
    with open(f"{out}.summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return summary


def print_summary(summary: dict) -> None:
    print(f"Queries evaluadas: {summary['n_queries_evaluated']}  (sin resultados en el run: {summary['n_queries_missing_in_run']})")
    for m, v in summary["metrics"].items():
        print(f"  {m:<12} {v:.4f}")
    lat = summary.get("latency")
    if lat:
        print(f"  Latencia  p50={lat['p50_ms']:.1f}  p95={lat['p95_ms']:.1f}  p99={lat['p99_ms']:.1f} ms"
              f"  | ok={lat['frac_ok']:.1%} degraded={lat['frac_degraded']:.1%} "
              f"timeout={lat['frac_timeout']:.1%} error={lat['frac_error']:.1%}")
        p99r = lat.get("p99_with_results_ms")
        if p99r is not None and lat["n_with_results"] < lat["n_requests"]:
            print(f"  p99 solo con resultados = {p99r:.1f} ms ({lat['n_with_results']}/{lat['n_requests']} solicitudes). "
                  f"Si difiere mucho de p99, los timeouts y errores esconden la cola.")
        if "extra_requests_pct" in lat:
            print(f"  Solicitudes adicionales (duplicadas): {lat['extra_requests']} = {lat['extra_requests_pct']:.1f} % (límite del paper: 10 %)")
        for stage, v in summary.get("stages", {}).items():
            print(f"  Etapa {stage:<14} n={v['n']}  p50={v['p50_ms']:.1f}  p95={v['p95_ms']:.1f}  p99={v['p99_ms']:.1f} ms")
        if lat["p99_samples_above"] < 5:
            print(f"  AVISO: el p99 depende de solo {lat['p99_samples_above']} solicitud(es); repetir la corrida para estabilizarlo.")
    else:
        print("  AVISO: sin --latency. La regla del equipo es reportar P@3 y p99 juntos.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--qrels", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--extra-qrels", help="juicios manuales (review_sample.py merge); se unen a los qrels")
    ap.add_argument("--latency", help="TSV qid, latency_ms, status. Obligatorio para reportar P@3 junto con p99")
    ap.add_argument("--metrics", nargs="+", default=DEFAULT_METRICS, choices=sorted(METRICS))
    ap.add_argument("--out", required=True, help="prefijo de salida")
    ap.add_argument("--meta", nargs="*", default=[], metavar="CLAVE=VALOR",
                    help="datos del experimento para los gráficos: system=BM25 group=Retrieval corpus_size=3633")
    args = ap.parse_args()
    meta = dict(kv.split("=", 1) for kv in args.meta)
    print_summary(evaluate_files(args.qrels, args.run, args.out, args.latency, args.extra_qrels, args.metrics, meta))


if __name__ == "__main__":
    force_utf8_output()
    main()

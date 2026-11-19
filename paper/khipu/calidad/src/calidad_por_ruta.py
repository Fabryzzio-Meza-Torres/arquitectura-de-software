"""Calidad (P@3, nDCG@3) por condición y por ruta, a partir de los registros de latencia del equipo.

Cada línea de `results/<dataset>/requests_<dataset>_rep<r>_<COND>.jsonl` guarda `doc_ids` (los 3 devueltos), `qid`
y `route`. Con los qrels del dataset se calcula qué tan buenas fueron las respuestas de cada condición:
  - fitness (ii): P@3 con reranker (L100) contra sin reranker (NORERANK)
  - costo en calidad de las fallas: F1/F2 (respaldo = fusión), F4 (solo léxico), F5 (solo semántico)
Reglas: se descarta el calentamiento (t_sched < 30 s, igual que summary.csv); una solicitud sin 3 resultados vale 0
(las consultas sin resultados cuentan, no se saltan); las consultas se repiten de forma cíclica, así que cada
solicitud cuenta una vez. Los documentos sin juicio cuentan como no relevantes (igual que en evaluate.py).

  python calidad/src/calidad_por_ruta.py --results results/fiqa --qrels data/fiqa/qrels/test.tsv --out calidad/out/fiqa_ruta
Escribe <out>.csv y <out>.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import force_utf8_output, load_qrels  # noqa: E402
from metrics import ndcg_at_k, precision_at_k  # noqa: E402

WARMUP_S = 30.0


def calcular(results_dir: str, qrels_path: str, warmup_s: float = WARMUP_S) -> List[dict]:
    qrels = load_qrels(qrels_path)
    acc: Dict[tuple, Dict[str, list]] = defaultdict(lambda: {"p3": [], "ndcg3": []})
    for f in sorted(Path(results_dir).glob("requests_*_rep*_*.jsonl")):
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if r["t_sched"] < warmup_s or str(r["qid"]) not in qrels:
                continue
            ranked = [str(d) for d in (r.get("doc_ids") or [])][:3]
            q = qrels[str(r["qid"])]
            acc[(r["condition"], r["route"])]["p3"].append(precision_at_k(ranked, q, 3))
            acc[(r["condition"], r["route"])]["ndcg3"].append(ndcg_at_k(ranked, q, 3))
    rows = []
    for (cond, route), v in sorted(acc.items()):
        rows.append({"condition": cond, "route": route, "n": len(v["p3"]),
                     "P@3": float(np.mean(v["p3"])), "nDCG@3": float(np.mean(v["ndcg3"]))})
    return rows


def main() -> None:
    force_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True)
    ap.add_argument("--qrels", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = calcular(args.results, args.qrels)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["condition", "route", "n", "P@3", "nDCG@3"])
        w.writeheader()
        w.writerows(rows)
    lines = ["| condición | ruta | n | P@3 | nDCG@3 |", "| --- | --- | ---: | ---: | ---: |"]
    lines += [f"| {r['condition']} | {r['route']} | {r['n']} | {r['P@3']:.3f} | {r['nDCG@3']:.3f} |" for r in rows]
    Path(f"{out}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

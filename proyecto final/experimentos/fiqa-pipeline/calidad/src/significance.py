"""Comparación pareada entre dos sistemas sobre las mismas queries.

Uso:
  python src/significance.py --a results/e1_bm25.per_query.csv --b results/e1_rrf.per_query.csv \
      --metrics P@3 nDCG@10 --names BM25 RRF

Por cada métrica: diferencia media (B - A), IC 95% por bootstrap pareado y p-valor de la
prueba de aleatorización pareada (sign-flip). Con varias métricas se corrige con Holm.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import read_per_query_csv, force_utf8_output  # noqa: E402


def paired_bootstrap_ci(diff: np.ndarray, n_resamples: int = 10_000, alpha: float = 0.05, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = len(diff)
    idx = rng.integers(0, n, size=(n_resamples, n))
    means = diff[idx].mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def paired_randomization_p(diff: np.ndarray, n_resamples: int = 10_000, seed: int = 42) -> float:
    """p bilateral: ¿qué tan raro es |media| observada si el signo de cada diferencia fuera azaroso?"""
    rng = np.random.default_rng(seed)
    obs = abs(diff.mean())
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_resamples, len(diff)))
    null = np.abs((signs * diff).mean(axis=1))
    return float((np.sum(null >= obs - 1e-12) + 1) / (n_resamples + 1))


def holm(pvalues: List[float]) -> List[float]:
    """Ajuste de Holm-Bonferroni (controla el error familiar entre las métricas comparadas)."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def compare(a: Dict[str, Dict[str, float]], b: Dict[str, Dict[str, float]], metrics: List[str],
            n_resamples: int = 10_000, seed: int = 42) -> List[dict]:
    if set(a) != set(b):
        raise ValueError(f"Los sistemas no tienen las mismas queries (solo A: {len(set(a) - set(b))}, solo B: {len(set(b) - set(a))}).")
    qids = sorted(a)
    rows = []
    for m in metrics:
        xa = np.array([a[q][m] for q in qids])
        xb = np.array([b[q][m] for q in qids])
        diff = xb - xa
        lo, hi = paired_bootstrap_ci(diff, n_resamples, seed=seed)
        rows.append({
            "metric": m, "n": len(qids), "mean_a": float(xa.mean()), "mean_b": float(xb.mean()),
            "diff": float(diff.mean()), "ci95_low": lo, "ci95_high": hi,
            "p_raw": paired_randomization_p(diff, n_resamples, seed=seed),
        })
    for row, p_adj in zip(rows, holm([r["p_raw"] for r in rows])):
        row["p_holm"] = p_adj
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True, help="per_query.csv del sistema base")
    ap.add_argument("--b", required=True, help="per_query.csv del sistema comparado")
    ap.add_argument("--metrics", nargs="+", default=["P@3", "nDCG@3"])
    ap.add_argument("--names", nargs=2, default=["A", "B"])
    ap.add_argument("--resamples", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rows = compare(read_per_query_csv(args.a), read_per_query_csv(args.b), args.metrics, args.resamples, args.seed)
    na, nb = args.names
    print(f"| Métrica | {na} | {nb} | Dif ({nb}-{na}) | IC95% | p | p (Holm) |")
    print("| --- | ---: | ---: | ---: | --- | ---: | ---: |")
    for r in rows:
        print(f"| {r['metric']} | {r['mean_a']:.4f} | {r['mean_b']:.4f} | {r['diff']:+.4f} | "
              f"[{r['ci95_low']:+.4f}, {r['ci95_high']:+.4f}] | {r['p_raw']:.4f} | {r['p_holm']:.4f} |")
    print(f"\nn = {rows[0]['n']} queries pareadas; {args.resamples} remuestreos; semilla {args.seed}.")


if __name__ == "__main__":
    force_utf8_output()
    main()

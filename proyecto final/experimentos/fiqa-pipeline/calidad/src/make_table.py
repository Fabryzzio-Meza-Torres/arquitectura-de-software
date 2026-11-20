"""Tabla de resultados (calidad junto a latencia) y gráfico P@3 contra p99.

Uso:
  python src/make_table.py --summaries results/a.summary.json results/b.summary.json \
      --names BM25 Híbrido --out results/tabla.md --plot results/p3_vs_p99.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import force_utf8_output  # noqa: E402

COLUMNS = ["P@3", "nDCG@3", "nDCG@10", "MRR@10", "R@20"]


def build_table(entries: List[Tuple[str, dict]]) -> str:
    head = ["Sistema", "n queries"] + COLUMNS + ["p50 ms", "p95 ms", "p99 ms", "% no ok"]
    lines = ["| " + " | ".join(head) + " |", "| --- | " + " | ".join(["---:"] * (len(head) - 1)) + " |"]
    for name, s in entries:
        m, lat = s["metrics"], s.get("latency")
        vals = [name, str(s["n_queries_evaluated"])] + [f"{m[c]:.3f}" if c in m else "—" for c in COLUMNS]
        if lat:
            not_ok = 1 - lat["frac_ok"]
            vals += [f"{lat['p50_ms']:.1f}", f"{lat['p95_ms']:.1f}", f"{lat['p99_ms']:.1f}", f"{not_ok:.1%}"]
        else:
            vals += ["—"] * 4
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def plot(entries: List[Tuple[str, dict]], path: str) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    pts = [(n, s["latency"]["p99_ms"], s["metrics"]["P@3"]) for n, s in entries if s.get("latency") and "P@3" in s["metrics"]]
    if not pts:
        return False
    fig, ax = plt.subplots(figsize=(6, 4))
    for name, x, y in pts:
        ax.scatter(x, y)
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
    ax.set_xlabel("p99 de latencia (ms)")
    ax.set_ylabel("Precision@3")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--summaries", nargs="+", required=True)
    ap.add_argument("--names", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--plot")
    args = ap.parse_args()
    names = args.names or [Path(p).name.replace(".summary.json", "") for p in args.summaries]
    if len(names) != len(args.summaries):
        raise SystemExit("--names debe tener el mismo número de elementos que --summaries")
    entries = [(n, json.loads(Path(p).read_text(encoding="utf-8"))) for n, p in zip(names, args.summaries)]
    table = build_table(entries)
    print(table)
    if args.out:
        Path(args.out).write_text(table + "\n", encoding="utf-8")
    if args.plot and not plot(entries, args.plot):
        print("(gráfico omitido: falta matplotlib o no hay latencias)")


if __name__ == "__main__":
    force_utf8_output()
    main()

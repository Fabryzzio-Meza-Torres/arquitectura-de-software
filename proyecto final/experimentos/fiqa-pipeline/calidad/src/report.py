"""Tablas y gráficos listos para el paper (E1 a E6), fáciles de leer.

Uso:
  python src/report.py --from-dir results/e1 --out-dir results/reporte_e1
  python src/report.py --summaries results/a.summary.json results/b.summary.json \
      --names BM25 Híbrido --groups Retrieval Retrieval --out-dir results/reporte

Cada `.summary.json` sale de evaluate.py. Si junto a él está su `.per_query.csv`, se calculan intervalos de confianza.
Para agrupar por color y para la escalabilidad, pasar a evaluate.py:  --meta system=BM25 group=Retrieval corpus_size=3633

Salida en --out-dir:
  tabla_principal.md / .csv     calidad y latencia juntas, mejor valor en negrita
  fig1_calidad_vs_latencia.png  P@3 contra p99 (arriba a la izquierda es mejor)
  fig2_metricas.png             las métricas de calidad por sistema
  fig3_latencia.png             p50, p95 y p99 por sistema
  fig4_escalabilidad.png        latencia y calidad al crecer el corpus (si hay corpus_size)
  fig5_candidatos.png           calidad de los 20 candidatos del retrieval
  figuras.md                    cómo leer cada gráfico
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import read_per_query_csv, force_utf8_output  # noqa: E402

# Paleta de referencia validada (tres primeros colores, modo claro): pasan CVD y distancia entre TODOS los pares.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a"]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e3e2de"
MARKERS = "osD^v<>hpd"  # formas llenas: con el borde blanco, marcadores finos como + o x casi desaparecen
KNOWN_GROUPS = ["Retrieval", "Reranker", "Cascada"]  # color fijo por grupo conocido, igual en todas las figuras
MAIN_METRICS = ["P@3", "nDCG@3", "nDCG@10", "MRR@10", "R@20"]
CAND_METRICS = ["Rcap@20", "Suf3@20", "OracleP3@20"]
LABELS = {"P@3": "Precision@3", "nDCG@3": "nDCG@3", "nDCG@10": "nDCG@10", "MRR@10": "MRR@10", "R@20": "Recall@20",
          "Rcap@20": "Recall@20 con tope", "Suf3@20": "Candidatos suficientes (≥3)", "OracleP3@20": "Techo de P@3"}


@dataclass
class Entry:
    name: str
    group: str
    summary: dict
    per_query: Optional[Dict[str, Dict[str, float]]] = None
    _ci: Dict[str, Optional[Tuple[float, float]]] = field(default_factory=dict)

    @property
    def metrics(self) -> dict:
        return self.summary["metrics"]

    @property
    def lat(self) -> Optional[dict]:
        return self.summary.get("latency")

    def ci(self, metric: str, n_boot: int = 5000, seed: int = 42) -> Optional[Tuple[float, float]]:
        if metric not in self._ci:
            if not self.per_query:
                self._ci[metric] = None
            else:
                v = np.array([q[metric] for q in self.per_query.values() if metric in q])
                if len(v) < 2:
                    self._ci[metric] = None
                else:
                    idx = np.random.default_rng(seed).integers(0, len(v), size=(n_boot, len(v)))
                    m = v[idx].mean(axis=1)
                    self._ci[metric] = (float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975)))
        return self._ci[metric]


def load_entries(paths: List[str], names: Optional[List[str]], groups: Optional[List[str]]) -> List[Entry]:
    entries = []
    for i, p in enumerate(paths):
        path = Path(p)
        summary = json.loads(path.read_text(encoding="utf-8"))
        meta = summary.get("meta", {})
        pq_path = Path(str(path).replace(".summary.json", ".per_query.csv"))
        name = names[i] if names else meta.get("system") or path.name.replace(".summary.json", "")
        group = groups[i] if groups else meta.get("group", "Sistema")
        entries.append(Entry(name, group, summary, read_per_query_csv(pq_path) if pq_path.exists() else None))
    if len({e.group for e in entries}) > len(PALETTE):
        raise SystemExit(f"Máximo {len(PALETTE)} grupos de color; hay {len({e.group for e in entries})}. Usa menos grupos.")
    return entries


def group_color(entries: List[Entry]) -> Dict[str, str]:
    """Retrieval = azul, Reranker = naranja, Cascada = verde; un grupo nuevo toma el primer color libre."""
    present = list(dict.fromkeys(e.group for e in entries))
    colors = {g: PALETTE[KNOWN_GROUPS.index(g)] for g in present if g in KNOWN_GROUPS}
    free = [c for c in PALETTE if c not in colors.values()]
    for g in present:
        if g not in colors:
            colors[g] = free.pop(0)
    return colors


# ------------------------------------------------------------------ tabla
def build_main_table(entries: List[Entry]) -> Tuple[str, List[dict]]:
    quality = MAIN_METRICS
    cols = [("P@3", True)] + [(m, True) for m in quality[1:]] + [("p50_ms", False), ("p95_ms", False), ("p99_ms", False), ("no_ok", False)]
    raw: List[dict] = []
    for e in entries:
        row = {"Sistema": e.name, "Grupo": e.group, "n queries": e.summary["n_queries_evaluated"]}
        for m in quality:
            row[m] = e.metrics.get(m)
        ci = e.ci("P@3")
        row["P@3 IC95 bajo"], row["P@3 IC95 alto"] = (ci if ci else (None, None))
        lat = e.lat
        row["p50_ms"], row["p95_ms"], row["p99_ms"] = (lat["p50_ms"], lat["p95_ms"], lat["p99_ms"]) if lat else (None, None, None)
        row["no_ok"] = (1 - lat["frac_ok"]) if lat else None
        raw.append(row)

    best = {}
    for c, higher in cols:
        vals = [r[c] for r in raw if r[c] is not None]
        best[c] = (max(vals) if higher else min(vals)) if vals else None

    def cell(r, c, text):
        v = r[c]
        return f"**{text}**" if len(raw) > 1 and v is not None and best[c] is not None and abs(v - best[c]) < 1e-12 else text

    header = ["Sistema", "n"] + ["P@3 ↑ (IC 95%)"] + [f"{m} ↑" for m in quality[1:]] + ["p50 ms ↓", "p95 ms ↓", "p99 ms ↓", "% no ok ↓"]
    lines = ["| " + " | ".join(header) + " |", "| --- | ---: | " + " | ".join(["---:"] * (len(header) - 2)) + " |"]
    for r in raw:
        p3 = "—" if r["P@3"] is None else f"{r['P@3']:.3f}" + (f" ({r['P@3 IC95 bajo']:.2f}–{r['P@3 IC95 alto']:.2f})" if r["P@3 IC95 bajo"] is not None else "")
        cells = [r["Sistema"], str(r["n queries"]), cell(r, "P@3", p3)]
        cells += [cell(r, m, "—" if r[m] is None else f"{r[m]:.3f}") for m in quality[1:]]
        cells += [cell(r, "p50_ms", "—" if r["p50_ms"] is None else f"{r['p50_ms']:.1f}"),
                  cell(r, "p95_ms", "—" if r["p95_ms"] is None else f"{r['p95_ms']:.1f}"),
                  cell(r, "p99_ms", "—" if r["p99_ms"] is None else f"{r['p99_ms']:.1f}"),
                  cell(r, "no_ok", "—" if r["no_ok"] is None else f"{r['no_ok']:.1%}")]
        lines.append("| " + " | ".join(cells) + " |")
    note = ("\n\n**Cómo leerla:** ↑ significa que más alto es mejor y ↓ que más bajo es mejor. En **negrita** está el mejor valor de cada columna. "
            "El intervalo entre paréntesis es el IC 95% de P@3 (qué tanto podría moverse por azar entre queries). "
            "`% no ok` es la fracción de solicitudes que terminaron en degradación, timeout o error. Si dos sistemas tienen intervalos que se traslapan mucho, "
            "no los declares distintos sin correr `significance.py`.")
    return "\n".join(lines) + note, raw


def pareto(points: List[Tuple[float, float]]) -> List[int]:
    """Índices de los puntos no dominados (menor x y mayor y son mejores)."""
    keep = []
    for i, (x, y) in enumerate(points):
        if not any((x2 <= x and y2 >= y) and (x2 < x or y2 > y) for j, (x2, y2) in enumerate(points) if j != i):
            keep.append(i)
    return keep


# ------------------------------------------------------------------ gráficos
def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "figure.facecolor": SURFACE,
                         "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE})
    return plt


def _style(ax, grid_axis="both"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _title(ax, title, subtitle, wrap=88):
    """Título en negrita y subtítulo partido en líneas; el subtítulo no entra al cálculo de márgenes (no encoge el gráfico)."""
    import textwrap
    lines = textwrap.wrap(subtitle, wrap) or [""]
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold", color=INK, pad=8 + 11.5 * len(lines))
    t = ax.annotate("\n".join(lines), xy=(0, 1), xycoords="axes fraction", xytext=(0, 5), textcoords="offset points",
                    va="bottom", ha="left", fontsize=8.5, color=INK2, linespacing=1.3)
    t.set_in_layout(False)


def _group_handles(colors):
    from matplotlib.lines import Line2D
    return [Line2D([0], [0], marker="o", color="none", markerfacecolor=c, markeredgecolor=SURFACE, markersize=8, label=g) for g, c in colors.items()]


def _legend_groups(ax, colors, loc="lower right"):
    if len(colors) >= 2:
        ax.legend(handles=_group_handles(colors), loc=loc, frameon=False, fontsize=8.5, labelcolor=INK2)


def _place_labels(ax, pts, prefer_right=False):
    """Etiqueta cada punto con su nombre, evitando que los textos se pisen entre sí o con otros puntos."""
    from matplotlib.transforms import Bbox
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    marker_boxes = []
    for x, y, _ in pts:
        px, py = ax.transData.transform((x, y))
        marker_boxes.append(Bbox([[px - 9, py - 9], [px + 9, py + 9]]))
    placed: List = []
    offsets = [(8, 6, "left"), (8, -14, "left"), (-8, 6, "right"), (-8, -14, "right"),
               (8, 20, "left"), (8, -28, "left"), (-8, 20, "right"), (-8, -28, "right"), (8, 34, "left"), (-8, -42, "right")]
    if prefer_right:  # etiquetas al final de una línea: a la derecha del último punto
        offsets = [(9, -4, "left"), (9, 8, "left"), (9, -16, "left")] + offsets
    for i, (x, y, text) in enumerate(pts):
        chosen = None
        for dx, dy, ha in offsets:
            t = ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va="bottom", fontsize=8.5, color=INK)
            bb = t.get_window_extent(renderer).expanded(1.04, 1.2)
            axbb = ax.get_window_extent(renderer)
            inside = axbb.x0 - 2 <= bb.x0 and bb.x1 <= axbb.x1 + 2 and axbb.y0 - 2 <= bb.y0 and bb.y1 <= axbb.y1 + 2
            clash = any(bb.overlaps(o) for o in placed) or any(bb.overlaps(m) for j, m in enumerate(marker_boxes) if j != i)
            if inside and not clash:
                chosen = bb
                break
            t.remove()
        if chosen is None:  # último recurso: primera posición
            t = ax.annotate(text, (x, y), xytext=offsets[0][:2], textcoords="offset points", ha=offsets[0][2], va="bottom", fontsize=8.5, color=INK)
            chosen = t.get_window_extent(renderer)
        placed.append(chosen)


def _log_if_wide(values: List[float]) -> bool:
    vals = [v for v in values if v and v > 0]
    return bool(vals) and max(vals) / min(vals) >= 10


def fig_quality_vs_latency(entries: List[Entry], path: Path) -> bool:
    es = [e for e in entries if e.lat and "P@3" in e.metrics]
    if not es:
        return False
    plt = _plt()
    colors = group_color(entries)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    pts = [(e.lat["p99_ms"], e.metrics["P@3"]) for e in es]
    for i, (e, (x, y)) in enumerate(zip(es, pts)):
        c = colors[e.group]
        ci = e.ci("P@3")
        if ci:
            ax.vlines(x, ci[0], ci[1], color=c, linewidth=1.5, alpha=0.8, zorder=2)
        ax.plot(x, y, marker=MARKERS[i % len(MARKERS)], color=c, markersize=9, markeredgecolor=SURFACE, markeredgewidth=2, linestyle="none", zorder=3)
    front = sorted(pareto(pts), key=lambda i: pts[i][0])
    if len(front) > 1:
        fx, fy = [pts[i][0] for i in front], [pts[i][1] for i in front]
        ax.plot(fx, fy, color=INK2, linewidth=1, alpha=0.6, drawstyle="steps-post", zorder=1)
    if _log_if_wide([p[0] for p in pts]):
        ax.set_xscale("log")
    ax.set_xlabel("p99 de latencia (ms, escala log si el rango es amplio)")
    ax.set_ylabel("Precision@3")
    ax.margins(x=0.15, y=0.15)
    _style(ax)
    _title(ax, "Calidad frente a latencia", "Cada punto es un sistema; la barra vertical es el IC 95% de P@3. Mejor: arriba a la izquierda. La línea une los sistemas que ningún otro supera en calidad y velocidad a la vez.", wrap=80)
    fig.tight_layout()
    _place_labels(ax, [(x, y, e.name) for e, (x, y) in zip(es, pts)])
    _legend_groups(ax, {g: c for g, c in colors.items() if g in {e.group for e in es}}, loc="lower right")
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return True


def metric_panels(entries: List[Entry], metrics: List[str], title: str, subtitle: str, path: Path, ncols: int = 3) -> bool:
    metrics = [m for m in metrics if all(m in e.metrics for e in entries)]
    if not metrics:
        return False
    plt = _plt()
    colors = group_color(entries)
    order = sorted(entries, key=lambda e: -e.metrics[metrics[0]])
    nrows = -(-len(metrics) // ncols)
    height = max(2.4, 0.38 * len(order) + 1.3)
    fig_h = height * nrows + 0.9
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.6 * min(ncols, len(metrics)) + 1.2, fig_h), squeeze=False)
    for k, m in enumerate(metrics):
        ax = axes[k // ncols][k % ncols]
        ys = np.arange(len(order))[::-1]
        top = 0.0
        for y, e in zip(ys, order):
            v = e.metrics[m]
            ax.barh(y, v, height=0.5, color=colors[e.group], zorder=2)
            ci = e.ci(m)
            end = v
            if ci:
                ax.hlines(y, ci[0], ci[1], color=INK2, linewidth=1, zorder=3)
                end = max(end, ci[1])
            ax.text(end + 0.015, y, f"{v:.3f}", va="center", ha="left", fontsize=8, color=INK)
            top = max(top, end)
        ax.set_xlim(0, min(1.0, top * 1.25) if top <= 0.8 else 1.0)
        ax.set_yticks(ys)
        ax.set_yticklabels([e.name for e in order] if k % ncols == 0 else [])
        ax.set_title(LABELS.get(m, m), loc="left", fontsize=9.5, color=INK, pad=6)
        _style(ax, grid_axis="x")
        ax.tick_params(axis="y", length=0)
    for k in range(len(metrics), nrows * ncols):
        axes[k // ncols][k % ncols].axis("off")
    fig.text(0.01, 1 - 0.10 / fig_h, title, ha="left", va="top", fontsize=11, fontweight="bold", color=INK)
    fig.text(0.01, 1 - 0.38 / fig_h, subtitle, ha="left", va="top", fontsize=8.5, color=INK2)
    if len(colors) >= 2:
        fig.legend(handles=_group_handles(colors), loc="upper right", ncol=len(colors), frameon=False, fontsize=8.5,
                   labelcolor=INK2, bbox_to_anchor=(0.99, 1 - 0.05 / fig_h))
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.75 / fig_h))
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return True


def fig_latency(entries: List[Entry], path: Path) -> bool:
    es = sorted([e for e in entries if e.lat], key=lambda e: e.lat["p99_ms"])
    if not es:
        return False
    plt = _plt()
    from matplotlib.lines import Line2D
    colors = group_color(entries)
    fig, ax = plt.subplots(figsize=(7.2, max(2.6, 0.5 * len(es) + 1.6)))
    ys = np.arange(len(es))[::-1]
    for y, e in zip(ys, es):
        c = colors[e.group]
        vals = [e.lat["p50_ms"], e.lat["p95_ms"], e.lat["p99_ms"]]
        ax.plot([vals[0], vals[2]], [y, y], color=GRID, linewidth=2, zorder=1, solid_capstyle="round")
        for v, mk in zip(vals, ["o", "D", "s"]):
            ax.plot(v, y, marker=mk, color=c, markersize=8, markeredgecolor=SURFACE, markeredgewidth=2, linestyle="none", zorder=3)
        bad = 1 - e.lat["frac_ok"]
        if bad > 0:
            ax.text(1.01, y, f"{bad:.1%} no ok", transform=ax.get_yaxis_transform(), va="center", fontsize=8, color=INK2)
    ax.set_yticks(ys)
    ax.set_yticklabels([e.name for e in es])
    ax.tick_params(axis="y", length=0)
    if _log_if_wide([e.lat["p99_ms"] for e in es] + [e.lat["p50_ms"] for e in es]):
        ax.set_xscale("log")
    ax.set_xlabel("Latencia (ms)")
    ax.margins(x=0.12)
    _style(ax, grid_axis="x")
    _title(ax, "Latencia por sistema", "Círculo = p50 (típico), rombo = p95, cuadrado = p99 (los más lentos). Mientras más corta la línea, más estable. Menos es mejor.", wrap=80)
    shape_handles = [Line2D([0], [0], marker=m, color="none", markerfacecolor=INK2, markeredgecolor=SURFACE, markersize=8, label=l)
                     for m, l in [("o", "p50"), ("D", "p95"), ("s", "p99")]]
    fig.legend(handles=shape_handles, loc="lower center", ncol=3, frameon=False, fontsize=8.5, labelcolor=INK2)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return True


def fig_scalability(entries: List[Entry], path: Path) -> bool:
    series: Dict[str, List[Tuple[float, Entry]]] = {}
    for e in entries:
        meta = e.summary.get("meta", {})
        try:
            size = float(meta["corpus_size"])
        except (KeyError, ValueError):
            continue
        series.setdefault(meta.get("system", e.name), []).append((size, e))
    series = {k: sorted(v, key=lambda t: t[0]) for k, v in series.items() if len(v) >= 2}
    if not series:
        return False
    plt = _plt()
    colors = group_color(entries)
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2))
    for ax, (key, label, fmt) in zip(axes, [("p99", "p99 de latencia (ms)", None), ("P@3", "Precision@3", None)]):
        pts_all = []
        for i, (sysname, items) in enumerate(series.items()):
            xs = [s for s, _ in items]
            ys = [e.lat["p99_ms"] if key == "p99" and e.lat else e.metrics.get("P@3") for _, e in items]
            if any(v is None for v in ys):
                continue
            c = colors[items[0][1].group]
            ax.plot(xs, ys, color=c, linewidth=2, marker=MARKERS[i % len(MARKERS)], markersize=8, markeredgecolor=SURFACE, markeredgewidth=2)
            pts_all.append((xs[-1], ys[-1], sysname))
        ax.set_xscale("log")
        ax.set_xlabel("Documentos en el corpus (escala log)")
        ax.set_ylabel(label)
        ax.margins(x=0.55, y=0.15)  # espacio a la derecha para las etiquetas al final de cada línea
        _style(ax)
        ax._pts_all = pts_all
    _title(axes[0], "Latencia al crecer el corpus", "Una línea por sistema. Menos es mejor; una curva que se despega indica saturación.", wrap=48)
    _title(axes[1], "Calidad al crecer el corpus", "Más es mejor. Compara solo dentro del mismo tamaño: el corpus chico es algo más fácil.", wrap=48)
    fig.tight_layout(w_pad=3)
    for ax in axes:
        _place_labels(ax, ax._pts_all, prefer_right=True)
    present = {items[0][1].group for items in series.values()}
    colors_present = {g: c for g, c in colors.items() if g in present}
    if len(colors_present) >= 2:
        fig.legend(handles=_group_handles(colors_present), loc="lower center", ncol=len(colors_present), frameon=False, fontsize=8.5, labelcolor=INK2)
        fig.subplots_adjust(bottom=0.2)
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return True


# ------------------------------------------------------------------ captions
def write_captions(entries: List[Entry], made: Dict[str, bool], path: Path) -> None:
    lines = ["# Cómo leer los gráficos", ""]
    es = [e for e in entries if e.lat and "P@3" in e.metrics]
    if es:
        best_q = max(es, key=lambda e: e.metrics["P@3"])
        best_l = min(es, key=lambda e: e.lat["p99_ms"])
        pts = [(e.lat["p99_ms"], e.metrics["P@3"]) for e in es]
        front = [es[i].name for i in sorted(pareto(pts), key=lambda i: pts[i][0])]
        lines += ["## Datos clave (calculados, no interpretados)", "",
                  f"- Mayor P@3: **{best_q.name}** ({best_q.metrics['P@3']:.3f}), con p99 de {best_q.lat['p99_ms']:.1f} ms.",
                  f"- Menor p99: **{best_l.name}** ({best_l.lat['p99_ms']:.1f} ms), con P@3 de {best_l.metrics['P@3']:.3f}.",
                  f"- Sistemas que ningún otro supera en calidad y latencia a la vez: {', '.join(front)}.", ""]
    captions = {
        "fig1_calidad_vs_latencia.png": ("Calidad frente a latencia", "Es el gráfico central. Cada punto es un sistema. Arriba es más calidad (P@3) y a la izquierda es más rápido (p99). La barra vertical es el intervalo de confianza del 95%: si dos barras se traslapan mucho, la diferencia de calidad puede ser azar. La línea gris une los sistemas que ningún otro supera en ambas cosas."),
        "fig2_metricas.png": ("Métricas de calidad", "Una barra por sistema en cada métrica; el valor está en la punta y la línea fina es el intervalo del 95%. Todas van de 0 a 1 y más es mejor. Sirve para ver si un sistema que gana en P@3 también gana en el orden (nDCG) y en el primer acierto (MRR)."),
        "fig3_latencia.png": ("Latencia", "Para cada sistema, el círculo es el tiempo típico (p50), el rombo el p95 y el cuadrado el p99. Una línea larga significa que el sistema es inestable: a veces responde mucho más lento. A la derecha aparece el porcentaje de solicitudes que no terminaron bien."),
        "fig4_escalabilidad.png": ("Escalabilidad", "Cómo cambian la latencia y la calidad cuando el corpus crece. Si la curva del p99 sube de golpe, ese sistema se satura. La calidad solo debe compararse entre sistemas del mismo tamaño."),
        "fig5_candidatos.png": ("Calidad de los candidatos", "Evalúa la etapa de retrieval como entrada del reranker. 'Techo de P@3' es el mejor P@3 que lograría un reranker perfecto con esos 20 candidatos: si es bajo, el problema está antes del reranking."),
    }
    for fname, (title, text) in captions.items():
        if made.get(fname):
            lines += [f"## {title} (`{fname}`)", "", text, ""]
    lines += ["## Tabla principal (`tabla_principal.md`)", "",
              "Calidad y latencia en la misma fila. Negrita = mejor valor de la columna. ↑ más es mejor, ↓ menos es mejor."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--summaries", nargs="+")
    ap.add_argument("--from-dir", nargs="+", help="carpetas con archivos *.summary.json")
    ap.add_argument("--names", nargs="+")
    ap.add_argument("--groups", nargs="+")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    paths = list(args.summaries or [])
    for d in args.from_dir or []:
        paths += [str(p) for p in sorted(Path(d).glob("*.summary.json"))]
    if not paths:
        raise SystemExit("No hay resúmenes: usa --summaries o --from-dir")
    for opt, vals in (("--names", args.names), ("--groups", args.groups)):
        if vals and len(vals) != len(paths):
            raise SystemExit(f"{opt} debe tener {len(paths)} elementos (uno por resumen)")
    entries = load_entries(paths, args.names, args.groups)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    table, raw = build_main_table(entries)
    (out / "tabla_principal.md").write_text(table + "\n", encoding="utf-8")
    with open(out / "tabla_principal.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(raw[0].keys()))
        w.writeheader()
        w.writerows(raw)
    print(table)

    made = {
        "fig1_calidad_vs_latencia.png": fig_quality_vs_latency(entries, out / "fig1_calidad_vs_latencia.png"),
        "fig2_metricas.png": metric_panels(entries, MAIN_METRICS, "Calidad por sistema", "Más es mejor. Barra = valor; línea fina = IC 95%.", out / "fig2_metricas.png", ncols=3),
        "fig3_latencia.png": fig_latency(entries, out / "fig3_latencia.png"),
        "fig4_escalabilidad.png": fig_scalability(entries, out / "fig4_escalabilidad.png"),
        "fig5_candidatos.png": metric_panels(entries, CAND_METRICS, "Calidad de los 20 candidatos", "Qué tan bien deja el retrieval al reranker. Más es mejor.", out / "fig5_candidatos.png", ncols=3),
    }
    write_captions(entries, made, out / "figuras.md")
    for k, v in made.items():
        print(("  creado " if v else "  omitido (faltan datos) ") + k)


if __name__ == "__main__":
    force_utf8_output()
    main()

"""Reporte final de una corrida del pipeline: tabla, números de la hipótesis y gráficos, sin que nadie arme nada a mano.

  python calidad/src/reporte_final.py --out-dir <work>/calidad_out --qrels <work>/data1p/fiqa/qrels/test.tsv

Lee lo que dejó `pipeline.py` en calidad_out/ y escribe calidad_out/reporte/:
  reporte.md                 resumen en español: qué se midió, tabla, diferencia propuesta - base con su IC, batches, límites
  fig1_calidad.png           P@3, nDCG@3 y MRR@10 de solo léxico, base y propuesta
  fig2_alfa.png              cuánto pesa el léxico: P@3 de la propuesta según α (en dev)
  fig3_latencia_llm.png      p50, p95 y p99 del paso del sLLM por consulta, batch 4 contra batch 10
  fig4_scores_llm.png        cómo se reparten los scores del sLLM (no deben ser solo 0 y 1)
  resumen.json               los mismos números, para otros scripts
Si hay más de un modelo, se genera un bloque y un juego de figuras por modelo.
La propuesta mejorando a la base es una HIPÓTESIS: el reporte solo dice "mejora" si el IC 95 % de la diferencia queda
por encima de 0; si lo cruza, dice que no es concluyente.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate import evaluate  # noqa: E402
from io_formats import force_utf8_output, load_latency, load_qrels, load_run, read_jsonl  # noqa: E402
from latency import summarize_latency  # noqa: E402
from significance import paired_bootstrap_ci  # noqa: E402

METRICAS = ["P@3", "nDCG@3", "MRR@10"]
NOMBRES = {"lexical": "Solo léxico", "base": "Base (BM25 + embeddings)", "proposed": "Propuesta (BM25 + sLLM)"}
COLORES = {"lexical": "#8a8985", "base": "#2a78d6", "proposed": "#eb6834"}
INK, GRID = "#0b0b0b", "#e3e2de"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _ax(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def etiquetas(out_dir: Path) -> List[str]:
    return sorted(p.name[len("comparacion_"):-len(".comparison.json")] for p in out_dir.glob("comparacion_*.comparison.json"))


def mejor_alfa(path: Path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return rows, max(rows, key=lambda r: (float(r["P@3"]), float(r["nDCG@3"])))


def veredicto(lo: float, hi: float) -> str:
    if lo > 0:
        return "mejora (el IC 95 % queda por encima de 0)"
    if hi < 0:
        return "empeora (el IC 95 % queda por debajo de 0)"
    return "no es concluyente (el IC 95 % cruza el 0)"


def bloque(out_dir: Path, tag: str, qrels, fig_dir: Path) -> dict:
    plt = _plt()
    runs = {n: load_run(out_dir / f"test_{tag}" / f"{n}.run") for n in ("lexical", "base", "proposed")}
    per_q = {n: evaluate(r, qrels, METRICAS) for n, r in runs.items()}
    qids = sorted(per_q["base"])
    medias = {n: {m: float(np.mean([per_q[n][q][m] for q in qids])) for m in METRICAS} for n in runs}
    dif = {}
    for m in METRICAS:
        d = np.array([per_q["proposed"][q][m] - per_q["base"][q][m] for q in qids])
        lo, hi = paired_bootstrap_ci(d)
        dif[m] = {"media": float(d.mean()), "ic95": [lo, hi], "gana": int((d > 0).sum()), "empata": int((d == 0).sum()),
                  "pierde": int((d < 0).sum()), "veredicto": veredicto(lo, hi)}
    res = {"modelo": tag, "n_consultas": len(qids), "medias": medias, "propuesta_menos_base": dif}

    # fig1: calidad por arquitectura
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    w = 0.26
    for i, n in enumerate(("lexical", "base", "proposed")):
        xs = np.arange(len(METRICAS)) + (i - 1) * w
        vals = [medias[n][m] for m in METRICAS]
        ax.bar(xs, vals, w * 0.92, color=COLORES[n], label=NOMBRES[n])
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.005, f"{v:.3f}", ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_xticks(range(len(METRICAS)), METRICAS)
    ax.set_ylabel("Promedio sobre las consultas de test")
    ax.set_title(f"Calidad por arquitectura ({tag}, {len(qids)} consultas)", loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=8)
    _ax(ax)
    fig.tight_layout()
    fig.savefig(fig_dir / f"fig1_calidad_{tag}.png", dpi=160)
    plt.close(fig)

    # fig2: α en dev
    alfa_csv = out_dir / f"alpha_{tag}.alpha.csv"
    if alfa_csv.exists():
        rows, best = mejor_alfa(alfa_csv)
        res["alfa_elegido"] = float(best["alpha"])
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        ax.plot([float(r["alpha"]) for r in rows], [float(r["P@3"]) for r in rows], color=COLORES["proposed"], lw=2)
        ax.axvline(float(best["alpha"]), color=INK, lw=1, ls=":")
        ax.set_xlabel("α (0 = solo léxico, 1 = solo sLLM)")
        ax.set_ylabel("P@3 en dev")
        ax.set_title(f"Peso del léxico en la propuesta ({tag})", loc="left", fontsize=11)
        _ax(ax)
        fig.tight_layout()
        fig.savefig(fig_dir / f"fig2_alfa_{tag}.png", dpi=160)
        plt.close(fig)

    # latencia por batch y scores
    lat = {}
    for t in sorted(out_dir.glob(f"fiqa.test.{tag}.lote*.tiempos.tsv")):
        modo = t.name.split(".")[-3]
        filas = load_latency(t)
        s = summarize_latency(filas)
        lat[modo] = {"p50_ms": s["p50_ms"], "p95_ms": s["p95_ms"], "p99_ms": s["p99_ms"], "n": len(filas),
                     "degraded_pct": 100.0 * sum(1 for f in filas if f[2] != "ok") / max(len(filas), 1)}
    res["latencia_llm"] = lat
    if lat:
        modos = sorted(lat, key=lambda m: int(m[4:]))
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        w = 0.8 / len(modos)
        for i, m in enumerate(modos):
            xs = np.arange(3) + i * w
            vals = [lat[m]["p50_ms"], lat[m]["p95_ms"], lat[m]["p99_ms"]]
            ax.bar(xs, vals, w * 0.92, color=["#2a78d6", "#eb6834", "#1baf7a"][i % 3], label=f"batch {m[4:]}")
            for x, v in zip(xs, vals):
                ax.text(x, v, f"{v:.0f}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(np.arange(3) + w * (len(modos) - 1) / 2, ["p50", "p95", "p99"])
        ax.set_ylabel("ms por consulta (≈20 candidatos)")
        ax.set_title(f"Latencia del sLLM por batch ({tag})", loc="left", fontsize=11)
        ax.legend(frameon=False, fontsize=8)
        _ax(ax)
        fig.tight_layout()
        fig.savefig(fig_dir / f"fig3_latencia_llm_{tag}.png", dpi=160)
        plt.close(fig)

    scores = {m: {(r["qid"], r["id"]): float(r["score"]) for r in read_jsonl(p)}
              for m, p in ((p.name.split(".")[-3], p) for p in sorted(out_dir.glob(f"fiqa.test.{tag}.lote*.scores.jsonl")))}
    if scores:
        base_m = sorted(scores, key=lambda m: int(m[4:]))[0]
        vals = np.array(list(scores[base_m].values()))
        res["scores_llm"] = {"distintos": int(len(np.unique(np.round(vals, 4)))), "media": float(vals.mean()),
                             "pct_exactamente_0_o_1": float(100 * np.mean((vals == 0) | (vals == 1)))}
        if len(scores) > 1:
            otro = sorted(scores, key=lambda m: int(m[4:]))[1]
            comunes = set(scores[base_m]) & set(scores[otro])
            res["dif_max_entre_batches"] = float(max((abs(scores[base_m][k] - scores[otro][k]) for k in comunes), default=0.0))
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        ax.hist(vals, bins=20, range=(0, 1), color=COLORES["proposed"])
        ax.set_xlabel("score del sLLM (0 a 1)")
        ax.set_ylabel("pares consulta-documento")
        ax.set_title(f"Reparto de los scores del sLLM ({tag})", loc="left", fontsize=11)
        _ax(ax)
        fig.tight_layout()
        fig.savefig(fig_dir / f"fig4_scores_llm_{tag}.png", dpi=160)
        plt.close(fig)
    return res


def redactar(out_dir: Path, bloques: List[dict]) -> str:
    entorno = json.loads((out_dir / "entorno.json").read_text(encoding="utf-8")) if (out_dir / "entorno.json").exists() else {}
    ops = next(iter(out_dir.glob("onepagers_*.jsonl")), None)
    op0 = next(iter(read_jsonl(ops)), {}) if ops else {}
    L = ["# Reporte: base contra propuesta (FiQA, one-pagers)", ""]
    if entorno.get("smoke"):
        L += ["> **ATENCIÓN: esta fue una prueba corta (`smoke`).** Usa 64 documentos y 20 consultas; los números no valen.", ""]
    L += ["## Qué se midió", "",
          "Las dos arquitecturas leen los mismos one-pagers, las mismas consultas y los mismos candidatos (unión de los top 10 de "
          "BM25 y de embeddings). Solo cambia el score semántico: embeddings (base) o un sLLM local con la técnica RG-S, un número "
          "continuo de 0 a 1 (propuesta). El léxico es el mismo BM25 en las dos. «Solo léxico» es la referencia: si le gana a alguna, "
          "el score semántico no está aportando.", "",
          f"- GPU: {entorno.get('gpu') or 'no registrada'} · plataforma: {entorno.get('plataforma', '?')}",
          f"- One-pagers generados con: {op0.get('model', '?')} (huella del prompt {op0.get('prompt_sha', '?')})", ""]
    for b in bloques:
        L += [f"## Modelo: {b['modelo']}", "", f"Consultas de test evaluadas: {b['n_consultas']}.", "",
              "| Ranking | " + " | ".join(METRICAS) + " |", "| --- | " + " | ".join("---:" for _ in METRICAS) + " |"]
        for n in ("lexical", "base", "proposed"):
            L.append(f"| {NOMBRES[n]} | " + " | ".join(f"{b['medias'][n][m]:.3f}" for m in METRICAS) + " |")
        L += ["", "**Propuesta menos base** (IC 95 % por bootstrap pareado, 10.000 remuestreos):", "",
              "| Métrica | Diferencia | IC 95 % | Consultas que gana / empata / pierde | Lectura |", "| --- | ---: | --- | --- | --- |"]
        for m in METRICAS:
            d = b["propuesta_menos_base"][m]
            L.append(f"| {m} | {d['media']:+.3f} | [{d['ic95'][0]:+.3f}, {d['ic95'][1]:+.3f}] | {d['gana']} / {d['empata']} / {d['pierde']} | {d['veredicto']} |")
        if "alfa_elegido" in b:
            L += ["", f"α de la propuesta (elegido con dev): {b['alfa_elegido']:.2f}. Cerca de 0 significa que el léxico domina la propuesta."]
        s = b.get("scores_llm")
        if s:
            L += ["", f"Scores del sLLM: {s['distintos']} valores distintos, media {s['media']:.2f}; "
                      f"{s['pct_exactamente_0_o_1']:.1f} % valen exactamente 0 o 1. Si ese porcentaje es muy alto, el score es casi binario y aporta poco."]
        if b.get("latencia_llm"):
            L += ["", "Latencia del paso del sLLM por consulta (≈20 candidatos) según el batch:", "",
                  "| Batch | p50 (ms) | p95 (ms) | p99 (ms) | Consultas | % degradadas |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
            for m in sorted(b["latencia_llm"], key=lambda x: int(x[4:])):
                t = b["latencia_llm"][m]
                L.append(f"| {m[4:]} | {t['p50_ms']:.0f} | {t['p95_ms']:.0f} | {t['p99_ms']:.0f} | {t['n']} | {t['degraded_pct']:.1f} |")
            if "dif_max_entre_batches" in b:
                L += ["", f"Diferencia máxima de score entre los dos batches: {b['dif_max_entre_batches']:.4f}. "
                          "Debe ser casi 0 (cada documento va en su prompt); si no, hay un error."]
            L += ["", "El presupuesto del reranking es 1,2 s por consulta: el batch que lo supere en el p99 no cabe."]
        L += ["", f"Gráficos: `fig1_calidad_{b['modelo']}.png`, `fig2_alfa_{b['modelo']}.png`, "
                  f"`fig3_latencia_llm_{b['modelo']}.png`, `fig4_scores_llm_{b['modelo']}.png`.", ""]
    L += ["## Cómo leerlo y sus límites", "",
          "- Que la propuesta mejore a la base es una **hipótesis**. Solo se dice «mejora» si el IC 95 % de la diferencia queda por encima de 0.",
          "- La submuestra de 8.000 documentos es más fácil que el corpus completo: los números no son comparables con los publicados de BEIR.",
          "- Los documentos sin juicio cuentan como no relevantes, así que un buen ranking puede verse castigado si trae documentos que nadie evaluó.",
          "- Los one-pagers los generó un modelo pequeño: pueden perder detalles. Conviene revisar unos cuantos a mano.",
          "- Una sola corrida: otra persona con otra GPU puede obtener one-pagers algo distintos. Las réplicas sirven para ver esa variación.", ""]
    return "\n".join(L)


def generar(out_dir: str, qrels_path: str) -> Path:
    out = Path(out_dir)
    fig_dir = out / "reporte"
    fig_dir.mkdir(parents=True, exist_ok=True)
    qrels = load_qrels(qrels_path)
    tags = etiquetas(out)
    if not tags:
        raise SystemExit(f"No hay comparaciones en {out}. Corre antes el pipeline (pasos 'comparación').")
    bloques = [bloque(out, t, qrels, fig_dir) for t in tags]
    (fig_dir / "resumen.json").write_text(json.dumps(bloques, indent=2, ensure_ascii=False), encoding="utf-8")
    (fig_dir / "reporte.md").write_text(redactar(out, bloques), encoding="utf-8")
    return fig_dir / "reporte.md"


def main() -> None:
    force_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--qrels", required=True)
    args = ap.parse_args()
    print(f"Reporte en {generar(args.out_dir, args.qrels)}")


if __name__ == "__main__":
    main()

"""Compara las arquitecturas: base (léxico + embeddings), propuesta (léxico + LLM) y la referencia solo léxico.

Subcomando `compare`: une (join) los tres rankings por (consulta, documento) y responde:
  - ¿cuál tiene mejor P@3, nDCG@3 y MRR@10?
  - ¿en cuántas consultas el léxico solo supera a la base o a la propuesta?
  - análisis por documento (pointwise): ¿el score separa los relevantes de los que no lo son? (AUC y Spearman)

  python src/compare_rankings.py compare --qrels data/fiqa-8000-onepager/qrels/test.tsv \
      --lexical results/lexico.run --base results/base.run --proposed results/propuesta.run --out results/comparacion

Subcomando `alpha`: barre el peso α de la unión convexa, de 0 (solo léxico) a 1 (solo semántico).
Si el mejor α queda cerca de 0, el léxico domina. Se hace con los qrels de DESARROLLO, nunca con los de prueba.

  python src/compare_rankings.py alpha --qrels data/fiqa-8000-onepager/qrels/dev.tsv \
      --lexical results/lexico_dev.run --semantic results/llm_dev.run --out results/alpha_llm

Reglas:
- Cada run debe traer los scores de TODOS los candidatos (al menos 20 por consulta), con el mismo conjunto de candidatos.
- En el análisis por documento, los documentos sin juicio se EXCLUYEN (no se cuentan como no relevantes), porque
  castigar a un score por documentos que nadie evaluó no tiene sentido. Con --unjudged-as-negative se cuentan como 0.
  Ojo: si un dataset no trae juicios con grado 0 (NFCorpus, y probablemente FiQA), sin negativos el AUC no se puede calcular.
- Normalización de la unión: min-max por consulta sobre los candidatos de cada run. Un candidato ausente de un run recibe 0.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate import evaluate  # noqa: E402
from io_formats import Qrels, Run, force_utf8_output, load_qrels, load_run  # noqa: E402

METRICS_USED = ["P@3", "nDCG@3", "MRR@10"]
NAMES = {"lexical": "Solo léxico", "base": "Base (léxico + embeddings)", "proposed": "Propuesta (léxico + LLM)"}


# ----------------------------------------------------------------------------- utilidades numéricas
def _rank_avg(x: np.ndarray) -> np.ndarray:
    """Rangos 1..n con promedio en empates."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def auc(scores: np.ndarray, positive: np.ndarray) -> float:
    """Prob. de que un relevante reciba más score que uno no relevante (Mann-Whitney). NaN si falta una clase."""
    n_pos, n_neg = int(positive.sum()), int((~positive).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    r = _rank_avg(scores)
    return float((r[positive].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return float("nan")
    return float(np.corrcoef(_rank_avg(a), _rank_avg(b))[0, 1])


# ----------------------------------------------------------------------------- compare
def join_runs(runs: Dict[str, Run], qrels: Qrels) -> List[dict]:
    """Una fila por (consulta, documento) que aparezca en algún run, con posición y score de cada uno."""
    rows: List[dict] = []
    ranks = {name: {q: {d: i for i, (d, _) in enumerate(sorted(docs.items(), key=lambda kv: (-kv[1], kv[0])), 1)}
                    for q, docs in run.items()} for name, run in runs.items()}
    qids = sorted(set().union(*[set(r) for r in runs.values()]))
    for q in qids:
        docs = set().union(*[set(r.get(q, {})) for r in runs.values()])
        for d in sorted(docs):
            row = {"qid": q, "docid": d, "grade": qrels.get(q, {}).get(d)}
            for name, run in runs.items():
                row[f"{name}_rank"] = ranks[name].get(q, {}).get(d)
                row[f"{name}_score"] = run.get(q, {}).get(d)
            rows.append(row)
    return rows


def wins(per_a: Dict[str, Dict[str, float]], per_b: Dict[str, Dict[str, float]], metric: str) -> Dict[str, int]:
    out = {"a_gana": 0, "empate": 0, "b_gana": 0}
    for q in per_a:
        x, y = per_a[q][metric], per_b[q][metric]
        out["a_gana" if x > y + 1e-12 else "b_gana" if y > x + 1e-12 else "empate"] += 1
    return out


def pointwise(rows: List[dict], names: List[str], unjudged_as_negative: bool) -> Dict[str, dict]:
    result: Dict[str, dict] = {}
    for name in names:
        pairs = []
        for r in rows:
            s = r[f"{name}_score"]
            if s is None:
                continue
            g = r["grade"]
            if g is None:
                if not unjudged_as_negative:
                    continue
                g = 0
            pairs.append((r["qid"], float(s), g))
        if not pairs:
            result[name] = {"n_pairs": 0, "auc_pooled": float("nan"), "auc_mean_per_query": float("nan"), "spearman": float("nan")}
            continue
        scores = np.array([p[1] for p in pairs])
        grades = np.array([max(p[2], 0) for p in pairs], dtype=float)
        per_q: Dict[str, List[Tuple[float, int]]] = {}
        for q, s, g in pairs:
            per_q.setdefault(q, []).append((s, g))
        aucs = []
        for vals in per_q.values():
            a = auc(np.array([v[0] for v in vals]), np.array([v[1] > 0 for v in vals]))
            if not np.isnan(a):
                aucs.append(a)
        result[name] = {
            "n_pairs": len(pairs),
            "auc_pooled": auc(scores, grades > 0),
            "auc_mean_per_query": float(np.mean(aucs)) if aucs else float("nan"),
            "queries_with_auc": len(aucs),
            "spearman": spearman(scores, grades),
        }
    return result


def _fmt(x: float) -> str:
    return "n/d" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.3f}"


def compare(qrels_path: str, runs_paths: Dict[str, str], out_prefix: str, unjudged_as_negative: bool = False) -> dict:
    qrels = load_qrels(qrels_path)
    runs = {name: load_run(p) for name, p in runs_paths.items()}
    names = list(runs)
    per_q = {name: evaluate(run, qrels, METRICS_USED) for name, run in runs.items()}
    rows = join_runs(runs, qrels)

    out = Path(out_prefix)
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["qid", "docid", "grade"] + [f"{n}_{k}" for n in names for k in ("rank", "score")]
    with open(f"{out}.join.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r[k] is None else r[k]) for k in cols})

    means = {n: {m: float(np.mean([v[m] for v in per_q[n].values()])) for m in METRICS_USED} for n in names}
    pairs: Dict[str, Dict[str, Dict[str, int]]] = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pairs[f"{a} vs {b}"] = {m: wins(per_q[a], per_q[b], m) for m in METRICS_USED}
    pw = pointwise(rows, names, unjudged_as_negative)
    summary = {"n_queries": len(per_q[names[0]]), "means": means, "pairwise_wins": pairs, "pointwise": pw,
               "unjudged_as_negative": unjudged_as_negative}
    Path(f"{out}.comparison.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=float), encoding="utf-8")

    md = [f"Consultas evaluadas: {summary['n_queries']}", "", "| Ranking | " + " | ".join(METRICS_USED) + " |",
          "| --- | " + " | ".join("---:" for _ in METRICS_USED) + " |"]
    for n in names:
        md.append(f"| {NAMES.get(n, n)} | " + " | ".join(f"{means[n][m]:.3f}" for m in METRICS_USED) + " |")
    md += ["", "Consultas ganadas en P@3 (primero gana / empate / segundo gana):", "",
           "| Comparación | Gana el primero | Empate | Gana el segundo |", "| --- | ---: | ---: | ---: |"]
    for key, d in pairs.items():
        a, b = key.split(" vs ")
        w = d["P@3"]
        md.append(f"| {NAMES.get(a, a)} vs {NAMES.get(b, b)} | {w['a_gana']} | {w['empate']} | {w['b_gana']} |")
    md += ["", "Análisis por documento (solo documentos con juicio" + (", sin juicio como no relevante" if unjudged_as_negative else "") + "):", "",
           "| Score | Pares | AUC global | AUC medio por consulta | Spearman con el grado |", "| --- | ---: | ---: | ---: | ---: |"]
    for n in names:
        p = pw[n]
        md.append(f"| {NAMES.get(n, n)} | {p['n_pairs']} | {_fmt(p['auc_pooled'])} | {_fmt(p['auc_mean_per_query'])} | {_fmt(p['spearman'])} |")
    if all(np.isnan(pw[n]["auc_pooled"]) for n in names):
        md.append("\nAUC no definido: no hay documentos juzgados como no relevantes. Usa --unjudged-as-negative (con cuidado) o solo Spearman.")
    Path(f"{out}.comparison.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return summary


# ----------------------------------------------------------------------------- alpha
def _minmax(scores: Dict[str, float]) -> Dict[str, float]:
    if not scores:
        return {}
    lo, hi = min(scores.values()), max(scores.values())
    # score constante -> 1.0, igual que la fusión del sistema (alpha.json: "constant scores -> 1.0")
    return {d: (s - lo) / (hi - lo) if hi > lo else 1.0 for d, s in scores.items()}


def fuse(lex: Dict[str, float], sem: Dict[str, float], alpha: float) -> Dict[str, float]:
    """(1 - alpha) * léxico normalizado + alpha * semántico normalizado, sobre la unión de candidatos."""
    ln, sn = _minmax(lex), _minmax(sem)
    return {d: (1 - alpha) * ln.get(d, 0.0) + alpha * sn.get(d, 0.0) for d in set(ln) | set(sn)}


def alpha_sweep(qrels_path: str, lex_path: str, sem_path: str, out_prefix: str, step: float = 0.05) -> List[dict]:
    qrels, lex, sem = load_qrels(qrels_path), load_run(lex_path), load_run(sem_path)
    qids = sorted(set(lex) | set(sem))
    missing = sum(1 for q in qids for d in set(lex.get(q, {})) ^ set(sem.get(q, {})))
    table = []
    for k in range(int(round(1 / step)) + 1):
        a = round(k * step, 6)
        run = {q: fuse(lex.get(q, {}), sem.get(q, {}), a) for q in qids}
        per_q = evaluate(run, qrels, ["P@3", "nDCG@3"])
        table.append({"alpha": a, **{m: float(np.mean([v[m] for v in per_q.values()])) for m in ("P@3", "nDCG@3")}})
    best = max(table, key=lambda r: (r["P@3"], r["nDCG@3"]))
    out = Path(out_prefix)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{out}.alpha.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["alpha", "P@3", "nDCG@3"])
        w.writeheader()
        w.writerows(table)
    print("| alfa | P@3 | nDCG@3 |\n| ---: | ---: | ---: |")
    for r in table:
        print(f"| {r['alpha']:.2f} | {r['P@3']:.3f} | {r['nDCG@3']:.3f} |")
    print(f"\nMejor alfa (por P@3): {best['alpha']:.2f}. alfa=0 es solo léxico y alfa=1 es solo semántico.")
    if missing:
        print(f"AVISO: {missing} candidatos no están en los dos runs; recibieron 0 en el que falta. Mejor que ambos traigan los mismos candidatos.")
    return table


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--qrels", required=True)
    c.add_argument("--lexical", required=True, help="run solo léxico (BM25)")
    c.add_argument("--base", required=True, help="run base: léxico + embeddings")
    c.add_argument("--proposed", required=True, help="run propuesta: léxico + LLM")
    c.add_argument("--out", required=True)
    c.add_argument("--unjudged-as-negative", action="store_true")
    a = sub.add_parser("alpha")
    a.add_argument("--qrels", required=True, help="qrels de DESARROLLO")
    a.add_argument("--lexical", required=True)
    a.add_argument("--semantic", required=True, help="run con scores semánticos (embeddings o LLM)")
    a.add_argument("--out", required=True)
    a.add_argument("--step", type=float, default=0.05)
    args = ap.parse_args()
    if args.cmd == "compare":
        compare(args.qrels, {"lexical": args.lexical, "base": args.base, "proposed": args.proposed}, args.out, args.unjudged_as_negative)
    else:
        alpha_sweep(args.qrels, args.lexical, args.semantic, args.out, args.step)


if __name__ == "__main__":
    force_utf8_output()
    main()

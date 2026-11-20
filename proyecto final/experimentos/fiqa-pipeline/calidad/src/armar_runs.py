"""Arma los rankings de la comparación a partir de los candidatos y los scores del LLM.

Entradas:
  --candidatos  salida de candidatos.py (scores BM25 y de embeddings de la unión de candidatos)
  --llm         (opcional) salida de llm_semantico.py (.scores.jsonl); sin esto solo salen léxico y base
Salidas en <out>/ (formato TREC de 6 columnas, con los scores de TODOS los candidatos):
  lexical.run     solo léxico: la unión ordenada por el score BM25 crudo   (la referencia)
  embeddings.run  score crudo de embeddings (coseno)                        (insumo del barrido de alfa)
  llm.run         score crudo del LLM                                       (insumo del barrido de alfa)
  base.run        (1-alfa)*léxico_norm + alfa*embeddings_norm
  proposed.run    (1-alfa)*léxico_norm + alfa*llm_norm
Normalización: min-max por consulta sobre los candidatos; si todos valen igual, 1.0 (igual que el sistema).
Alfa: la base usa el de alpha.json (0.85, elegido con dev de FiQA); la propuesta usa --alpha-llm, que se elige con
dev (`compare_rankings.py alpha`) y se congela antes de mirar test. Si no se da, se usa el mismo de la base y el
script lo avisa, porque los scores del LLM tienen otra escala.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_rankings import fuse  # noqa: E402
from io_formats import Run, force_utf8_output, read_jsonl, write_run  # noqa: E402


def cargar_candidatos(path: str) -> Dict[str, Dict[str, dict]]:
    return {r["qid"]: {d["id"]: d for d in r["docs"]} for r in read_jsonl(path)}


def cargar_llm(path: str) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for r in read_jsonl(path):
        out.setdefault(r["qid"], {})[r["id"]] = float(r["score"])
    return out


def armar(cands: Dict[str, Dict[str, dict]], llm: Dict[str, Dict[str, float]] | None,
          alpha_base: float, alpha_llm: float) -> Dict[str, Run]:
    lex: Run = {q: {i: d["lex"] for i, d in ds.items()} for q, ds in cands.items()}
    emb: Run = {q: {i: d["sem"] for i, d in ds.items()} for q, ds in cands.items()}
    runs: Dict[str, Run] = {"lexical": lex, "embeddings": emb,
                            "base": {q: fuse(lex[q], emb[q], alpha_base) for q in cands}}
    if llm is not None:
        faltan = [(q, i) for q, ds in cands.items() for i in ds if i not in llm.get(q, {})]
        if faltan:
            raise SystemExit(f"Faltan {len(faltan)} scores del LLM (ej. {faltan[0]}). Base y propuesta deben "
                             "puntuar los MISMOS candidatos; vuelve a correr llm_semantico.py.")
        runs["llm"] = {q: {i: llm[q][i] for i in ds} for q, ds in cands.items()}
        runs["proposed"] = {q: fuse(lex[q], runs["llm"][q], alpha_llm) for q in cands}
    return runs


def main() -> None:
    force_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidatos", required=True)
    ap.add_argument("--llm")
    ap.add_argument("--alpha-json", default=str(Path(__file__).resolve().parents[2] / "alpha.json"))
    ap.add_argument("--alpha-llm", type=float)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    alpha_base = float(json.loads(Path(args.alpha_json).read_text(encoding="utf-8"))["alpha"])
    alpha_llm = args.alpha_llm
    if args.llm and alpha_llm is None:
        alpha_llm = alpha_base
        print(f"AVISO: no diste --alpha-llm; uso alfa={alpha_base} de la base. Elígelo con dev antes de mirar test.",
              file=sys.stderr)
    runs = armar(cargar_candidatos(args.candidatos), cargar_llm(args.llm) if args.llm else None,
                 alpha_base, alpha_llm if alpha_llm is not None else alpha_base)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, run in runs.items():
        write_run(out / f"{name}.run", run, tag=name)
    print(f"escritos {', '.join(f'{n}.run' for n in runs)} en {out} (alfa base={alpha_base}"
          + (f", alfa LLM={alpha_llm}" if "proposed" in runs else "") + ")")


if __name__ == "__main__":
    main()

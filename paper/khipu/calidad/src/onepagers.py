"""One-pagers: el resumen de una hoja de cada documento, que leen las DOS arquitecturas.

El profe pidió que base y propuesta usen el mismo dataset. Por eso cada documento de la submuestra necesita
un one-pager, y los índices de ambas arquitecturas se construyen sobre esos one-pagers.

Formato del archivo (JSONL, un documento por línea):
  {"_id": "123", "text": "<one-pager>", "model": "nombre-del-modelo", "prompt_sha": "ab12cd34", "seed": 42}

Uso:
  python src/onepagers.py check --data-dir data/fiqa-8000 --onepagers data/fiqa-8000.onepagers.jsonl
      Dice qué documentos de la submuestra no tienen one-pager (la cobertura debe ser 100 %).
  python src/onepagers.py build --data-dir data/fiqa-8000 --onepagers data/fiqa-8000.onepagers.jsonl
      Crea data/fiqa-8000-onepager/ con el mismo formato BEIR: el texto de cada documento es su one-pager;
      el título, las consultas y los juicios no cambian. Ese directorio es el que usan A y B.
  python src/onepagers.py merge --inputs a.jsonl b.jsonl c.jsonl --out onepagers_fiqa_8000.jsonl
      Une los one-pagers que generó cada persona (shards). Se niega si mezclan modelos o prompts distintos.
  python src/onepagers.py prompt-sha --prompt-file prompt_onepager.txt
      Calcula la huella del prompt, para anotarla en cada one-pager.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Set

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import force_utf8_output, read_jsonl  # noqa: E402

REQUIRED = ("_id", "text")


def load_onepagers(path: str | Path) -> Dict[str, dict]:
    """Lee el archivo y valida: campos obligatorios, ids sin repetir, texto no vacío."""
    out: Dict[str, dict] = {}
    for n, rec in enumerate(read_jsonl(path), start=1):
        for k in REQUIRED:
            if k not in rec:
                raise ValueError(f"{path}: registro {n} sin el campo {k!r}")
        if not str(rec["text"]).strip():
            raise ValueError(f"{path}: el one-pager del documento {rec['_id']} está vacío")
        if rec["_id"] in out:
            raise ValueError(f"{path}: documento repetido: {rec['_id']}")
        out[rec["_id"]] = rec
    return out


def coverage(corpus_ids: Set[str], onepagers: Dict[str, dict]) -> dict:
    missing = sorted(corpus_ids - set(onepagers))
    extra = sorted(set(onepagers) - corpus_ids)
    return {"corpus": len(corpus_ids), "with_onepager": len(corpus_ids) - len(missing),
            "missing": missing, "not_in_corpus": extra,
            "coverage": (len(corpus_ids) - len(missing)) / len(corpus_ids) if corpus_ids else 1.0}


def build(data_dir: Path, onepagers: Dict[str, dict], out_dir: Path | None = None) -> Path:
    """Crea <data_dir>-onepager/ con el mismo formato BEIR. Falla si falta algún one-pager."""
    ids = {d["_id"] for d in read_jsonl(data_dir / "corpus.jsonl")}
    cov = coverage(ids, onepagers)
    if cov["missing"]:
        raise ValueError(f"Faltan {len(cov['missing'])} one-pagers (primeros: {cov['missing'][:5]}). "
                         "Sin cobertura completa la comparación queda sesgada.")
    out = out_dir or data_dir.with_name(data_dir.name + "-onepager")
    (out / "qrels").mkdir(parents=True, exist_ok=True)
    with open(out / "corpus.jsonl", "w", encoding="utf-8") as f:
        for d in read_jsonl(data_dir / "corpus.jsonl"):
            rec = {"_id": d["_id"], "title": d.get("title", ""), "text": onepagers[d["_id"]]["text"]}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    shutil.copy(data_dir / "queries.jsonl", out / "queries.jsonl")
    for q in (data_dir / "qrels").glob("*.tsv"):
        shutil.copy(q, out / "qrels" / q.name)
    models = sorted({str(r.get("model", "?")) for r in onepagers.values()})
    shas = sorted({str(r.get("prompt_sha", "?")) for r in onepagers.values()})
    (out / "ONEPAGERS.json").write_text(json.dumps({
        "source": data_dir.name, "documents": len(ids), "models": models, "prompt_sha": shas,
        "words_mean_onepager": sum(len(r["text"].split()) for r in onepagers.values()) / max(len(onepagers), 1),
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def merge(paths: List[str], out: str | Path) -> int:
    """Une los one-pagers de varias personas (shards). Falla si un documento aparece dos veces con texto distinto
    o si los archivos usan modelos o prompts distintos (así todo el corpus queda generado con lo mismo)."""
    merged: Dict[str, dict] = {}
    for path in paths:
        for rec in load_onepagers(path).values():
            if rec["_id"] in merged and merged[rec["_id"]]["text"] != rec["text"]:
                raise ValueError(f"{rec['_id']} está en dos archivos con texto distinto")
            merged[rec["_id"]] = rec
    firmas = {(r.get("model"), r.get("prompt_sha")) for r in merged.values()}
    if len(firmas) > 1:
        raise ValueError(f"los archivos mezclan modelos/prompts distintos: {sorted(map(str, firmas))}")
    with open(out, "w", encoding="utf-8") as f:
        for _id in sorted(merged):
            f.write(json.dumps(merged[_id], ensure_ascii=False) + "\n")
    return len(merged)


def prompt_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "build"):
        sp = sub.add_parser(name)
        sp.add_argument("--data-dir", required=True)
        sp.add_argument("--onepagers", required=True)
    sp = sub.add_parser("merge")
    sp.add_argument("--inputs", nargs="+", required=True)
    sp.add_argument("--out", required=True)
    sp = sub.add_parser("prompt-sha")
    sp.add_argument("--prompt-file", required=True)
    args = ap.parse_args()

    if args.cmd == "prompt-sha":
        print(prompt_sha(Path(args.prompt_file).read_text(encoding="utf-8")))
        return
    if args.cmd == "merge":
        print(f"Listo: {merge(args.inputs, args.out)} one-pagers en {args.out}")
        return
    data_dir = Path(args.data_dir)
    ops = load_onepagers(args.onepagers)
    if args.cmd == "check":
        cov = coverage({d["_id"] for d in read_jsonl(data_dir / "corpus.jsonl")}, ops)
        print(f"Cobertura: {cov['with_onepager']}/{cov['corpus']} ({cov['coverage']:.1%})")
        if cov["missing"]:
            print(f"  Faltan {len(cov['missing'])}. Primeros: {cov['missing'][:10]}")
        if cov["not_in_corpus"]:
            print(f"  Sobran {len(cov['not_in_corpus'])} one-pagers que no están en el corpus (se ignoran).")
        sys.exit(0 if not cov["missing"] else 1)
    out = build(data_dir, ops)
    print(f"Listo: {out}")


if __name__ == "__main__":
    force_utf8_output()
    try:
        main()
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

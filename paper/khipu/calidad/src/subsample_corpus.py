"""Submuestras anidadas de un corpus BEIR, para medir cómo cambia la latencia al crecer (E6).

Uso:
  python src/subsample_corpus.py --data-dir data/trec-covid --sizes 40000 80000 --seed 42

Crea data/trec-covid-40000/ y data/trec-covid-80000/ con el mismo formato BEIR.
Reglas:
- Siempre se conservan los documentos que cuentan como relevantes (--keep relevant, por defecto),
  para que la calidad siga siendo medible. Con --keep judged se conservan todos los juzgados; con --keep none, ninguno.
- El resto se completa al azar con la semilla indicada. Las submuestras están anidadas: la de 40 000 está dentro de la de 80 000.
- Los juicios que apuntan a documentos que ya no están se descartan, y eso queda anotado en SUBSAMPLE.json.
- Aviso: al conservar todos los relevantes, un corpus más chico tiene proporcionalmente MÁS relevantes y es algo más fácil.
  Hay que comparar calidad solo entre sistemas dentro del mismo tamaño, y usar el tamaño para mirar latencia.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path
from typing import List, Set

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import load_qrels, read_jsonl, force_utf8_output  # noqa: E402


def kept_ids(data_dir: Path, keep: str, splits: List[str] | None = None) -> Set[str]:
    if keep == "none":
        return set()
    kept: Set[str] = set()
    for q in sorted((data_dir / "qrels").glob("*.tsv")):
        if splits and q.stem not in splits:
            continue
        for docs in load_qrels(q).values():
            kept |= {d for d, g in docs.items() if (g > 0 if keep == "relevant" else True)}
    return kept


def make_subsamples(data_dir: Path, sizes: List[int], seed: int, keep: str, out_root: Path,
                    keep_splits: List[str] | None = None) -> List[Path]:
    all_ids = [d["_id"] for d in read_jsonl(data_dir / "corpus.jsonl")]
    present = set(all_ids)
    kept = kept_ids(data_dir, keep, keep_splits) & present
    others = sorted(present - kept)
    random.Random(seed).shuffle(others)  # un único orden aleatorio => submuestras anidadas

    outputs = []
    for size in sorted(sizes):
        if size < len(kept):
            raise ValueError(f"size={size} es menor que los {len(kept)} documentos que hay que conservar (--keep {keep}).")
        if size > len(present):
            raise ValueError(f"size={size} supera el corpus completo ({len(present)}).")
        chosen = kept | set(others[: size - len(kept)])
        out = out_root / f"{data_dir.name}-{size}"
        (out / "qrels").mkdir(parents=True, exist_ok=True)
        with open(out / "corpus.jsonl", "w", encoding="utf-8") as f:
            for d in read_jsonl(data_dir / "corpus.jsonl"):
                if d["_id"] in chosen:
                    f.write(json.dumps(d, ensure_ascii=False) + "\n")
        shutil.copy(data_dir / "queries.jsonl", out / "queries.jsonl")
        dropped = 0
        for q in (data_dir / "qrels").glob("*.tsv"):
            with open(q, encoding="utf-8") as src, open(out / "qrels" / q.name, "w", encoding="utf-8") as dst:
                for i, line in enumerate(src):
                    parts = line.rstrip("\n").split("\t")
                    if i == 0 and not parts[-1].lstrip("-").isdigit():
                        dst.write(line)  # encabezado
                    elif len(parts) >= 3 and parts[1] in chosen:
                        dst.write(line)
                    else:
                        dropped += 1
        (out / "SUBSAMPLE.json").write_text(json.dumps({
            "source": data_dir.name, "size": len(chosen), "seed": seed, "keep": keep,
            "keep_splits": keep_splits or "all", "kept_documents": len(kept), "random_fill": len(chosen) - len(kept), "judgments_dropped": dropped,
        }, indent=2), encoding="utf-8")
        outputs.append(out)
        print(f"{out}: {len(chosen):,} documentos ({len(kept):,} conservados + {len(chosen) - len(kept):,} al azar), "
              f"{dropped} juicios descartados")
    return outputs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--sizes", type=int, nargs="+", required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--keep", choices=["relevant", "judged", "none"], default="relevant")
    ap.add_argument("--keep-splits", nargs="+", help="conservar solo los de estos splits (p. ej. dev test). "
                    "En FiQA el train tiene ~14 mil juicios: sin esto no cabe en 8.000 documentos")
    ap.add_argument("--out-root", help="por defecto, la carpeta que contiene a --data-dir")
    args = ap.parse_args()
    data_dir = Path(args.data_dir)
    make_subsamples(data_dir, args.sizes, args.seed, args.keep, Path(args.out_root) if args.out_root else data_dir.parent,
                    args.keep_splits)


if __name__ == "__main__":
    force_utf8_output()
    main()

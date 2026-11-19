"""Lectura/escritura de los formatos compartidos por todo el equipo.

qrels   : TSV  qid <TAB> docid <TAB> grado         (formato BEIR; también acepta 4 columnas estilo TREC)
run     : TREC  qid Q0 docid rank score tag        (una línea por documento recuperado)
latency : TSV  qid <TAB> latency_ms <TAB> status   (status: ok | degraded | timeout | error)
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

Qrels = Dict[str, Dict[str, int]]
Run = Dict[str, Dict[str, float]]

VALID_STATUS = {"ok", "degraded", "timeout", "error"}


def load_qrels(path: str | Path) -> Qrels:
    qrels: Qrels = defaultdict(dict)
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            parts = line.strip().split("\t") if "\t" in line else line.split()
            if not parts or parts == [""]:
                continue
            if len(parts) == 4:  # estilo TREC: qid 0 docid grado
                qid, docid, grade = parts[0], parts[2], parts[3]
            elif len(parts) == 3:  # estilo BEIR
                qid, docid, grade = parts
            else:
                raise ValueError(f"{path}:{line_no}: se esperaban 3 o 4 columnas, hay {len(parts)}")
            try:
                g = int(float(grade))
            except ValueError:
                if line_no == 1:  # encabezado (query-id corpus-id score)
                    continue
                raise ValueError(f"{path}:{line_no}: grado no numérico: {grade!r}")
            qrels[qid][docid] = g
    return dict(qrels)


def merge_qrels(base: Qrels, extra: Qrels) -> Qrels:
    """Une juicios manuales sobre los originales; el juicio manual gana si hay conflicto."""
    merged = {q: dict(d) for q, d in base.items()}
    for q, docs in extra.items():
        merged.setdefault(q, {}).update(docs)
    return merged


def load_run(path: str | Path) -> Run:
    run: Run = defaultdict(dict)
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            parts = line.split()
            if not parts:
                continue
            if len(parts) != 6:
                raise ValueError(f"{path}:{line_no}: formato TREC de 6 columnas (qid Q0 docid rank score tag)")
            qid, _, docid, _, score, _ = parts
            if docid in run[qid]:
                raise ValueError(f"{path}:{line_no}: documento repetido para la query {qid}: {docid}")
            run[qid][docid] = float(score)
    return dict(run)


def write_run(path: str | Path, run: Run, tag: str = "run") -> None:
    """Escribe un run en formato TREC (ordenado por score desc, rank 1..n)."""
    with open(path, "w", encoding="utf-8") as f:
        for qid in sorted(run):
            ordered = sorted(run[qid].items(), key=lambda kv: (-kv[1], kv[0]))
            for rank, (docid, score) in enumerate(ordered, start=1):
                f.write(f"{qid} Q0 {docid} {rank} {score:.6f} {tag}\n")


def load_latency(path: str | Path, with_extra: bool = False):
    """Lee qid, latency_ms, status. La 4.ª columna opcional es el nº de solicitudes duplicadas (hedged) de esa consulta.

    Devuelve filas de 3 valores; con with_extra=True devuelve (filas, total_de_duplicadas)."""
    rows = []
    extra_total = 0
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 1 and not parts[0]:
                continue
            if len(parts) not in (3, 4):
                raise ValueError(f"{path}:{line_no}: se esperaban 3 o 4 columnas (qid, latency_ms, status[, extra])")
            qid, ms, status = parts[:3]
            try:
                ms_f = float(ms)
            except ValueError:
                if line_no == 1:  # encabezado
                    continue
                raise ValueError(f"{path}:{line_no}: latencia no numérica: {ms!r}")
            if status not in VALID_STATUS:
                raise ValueError(f"{path}:{line_no}: status inválido {status!r}; usar {sorted(VALID_STATUS)}")
            rows.append((qid, ms_f, status))
            if len(parts) == 4:
                try:
                    extra_total += int(parts[3])
                except ValueError:
                    raise ValueError(f"{path}:{line_no}: la columna extra debe ser un entero: {parts[3]!r}")
    return (rows, extra_total) if with_extra else rows


def load_stages(path: str | Path) -> List[Tuple[str, str, float]]:
    """Lee qid, etapa, ms (archivo <prefijo>.stages.tsv que escribe ResultWriter)."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            try:
                rows.append((parts[0], parts[1], float(parts[2])))
            except ValueError:
                if line_no > 1:
                    raise ValueError(f"{path}:{line_no}: ms no numérico: {parts[2]!r}")
    return rows


def read_jsonl(path: str | Path) -> Iterator[dict]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_per_query_csv(path: str | Path) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            qid = row.pop("qid")
            out[qid] = {k: float(v) for k, v in row.items()}
    return out


def force_utf8_output() -> None:
    """En Windows, la salida redirigida usa la codificación local (cp1252) y falla con símbolos como ↑ o ≥. Se fuerza UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

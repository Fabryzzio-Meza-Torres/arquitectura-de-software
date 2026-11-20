"""Métricas de evaluación del paper (retrieval y reranking).

Todas las funciones reciben:
  ranked : lista de docids ya ordenada de mejor a peor
  qrel   : dict {docid: grado} con los juicios de UNA query (grado > 0 = relevante)

Las convenciones (por qué cada una) están en docs/02-reglas-evaluacion.md.
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List

Qrel = Dict[str, int]


def ranked_list(scores: Dict[str, float]) -> List[str]:
    """Ordena por score descendente; empates por docid (resultado determinista)."""
    return [d for d, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))]


def relevant_docs(qrel: Qrel) -> set:
    return {d for d, g in qrel.items() if g > 0}


def precision_at_k(ranked: List[str], qrel: Qrel, k: int) -> float:
    """Relevantes en el top-k / k. Si la lista es más corta que k, lo que falta cuenta como no relevante."""
    return sum(1 for d in ranked[:k] if qrel.get(d, 0) > 0) / k


def recall_at_k(ranked: List[str], qrel: Qrel, k: int) -> float:
    """Relevantes recuperados en el top-k / total de relevantes de la query."""
    rel = relevant_docs(qrel)
    return len(rel & set(ranked[:k])) / len(rel)


def capped_recall_at_k(ranked: List[str], qrel: Qrel, k: int) -> float:
    """Recall con tope: relevantes en el top-k / min(total de relevantes, k).

    Con queries de decenas de relevantes (NFCorpus) el recall clásico @20 nunca llega a 1;
    esta versión sí vale 1 cuando el top-k está lleno de relevantes.
    """
    rel = relevant_docs(qrel)
    return len(rel & set(ranked[:k])) / min(len(rel), k)


def reciprocal_rank_at_k(ranked: List[str], qrel: Qrel, k: int = 10) -> float:
    for i, d in enumerate(ranked[:k], start=1):
        if qrel.get(d, 0) > 0:
            return 1.0 / i
    return 0.0


def _dcg(gains: List[float]) -> float:
    # Ganancia lineal y descuento log2(i+1): misma definición que pytrec_eval / BEIR.
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_at_k(ranked: List[str], qrel: Qrel, k: int) -> float:
    gains = [max(qrel.get(d, 0), 0) for d in ranked[:k]]
    ideal = sorted((g for g in qrel.values() if g > 0), reverse=True)[:k]
    idcg = _dcg(ideal)
    return _dcg(gains) / idcg if idcg > 0 else 0.0


def sufficiency_at_k(ranked: List[str], qrel: Qrel, pool: int = 20, m: int = 3) -> float:
    """1.0 si los `pool` candidatos contienen al menos min(m, #relevantes) relevantes.

    Mide si la etapa de retrieval entrega material suficiente para que el reranker
    pueda llenar el top-m.
    """
    rel = relevant_docs(qrel)
    need = min(m, len(rel))
    return 1.0 if len(rel & set(ranked[:pool])) >= need else 0.0


def oracle_precision(ranked: List[str], qrel: Qrel, k: int = 3, pool: int = 20) -> float:
    """Techo de precision@k que un reranker perfecto podría alcanzar con esos `pool` candidatos."""
    hits = len(relevant_docs(qrel) & set(ranked[:pool]))
    return min(k, hits) / k


def hole_at_k(ranked: List[str], qrel: Qrel, k: int = 10) -> float:
    """Fracción del top-k sin ningún juicio (ni relevante ni no relevante). Diagnóstico de qrels incompletos."""
    top = ranked[:k]
    if not top:
        return 0.0
    return sum(1 for d in top if d not in qrel) / len(top)


# Registro: nombre del reporte -> función(ranked, qrel)
METRICS: Dict[str, Callable[[List[str], Qrel], float]] = {
    "P@3": lambda r, q: precision_at_k(r, q, 3),
    "nDCG@3": lambda r, q: ndcg_at_k(r, q, 3),
    "nDCG@10": lambda r, q: ndcg_at_k(r, q, 10),
    "MRR@10": lambda r, q: reciprocal_rank_at_k(r, q, 10),
    "R@20": lambda r, q: recall_at_k(r, q, 20),
    "Rcap@20": lambda r, q: capped_recall_at_k(r, q, 20),
    "Suf3@20": lambda r, q: sufficiency_at_k(r, q, 20, 3),
    "OracleP3@20": lambda r, q: oracle_precision(r, q, 3, 20),
    "Hole@10": lambda r, q: hole_at_k(r, q, 10),
}

# Métricas que se reportan por defecto (las del PDF primero).
DEFAULT_METRICS = ["P@3", "nDCG@3", "MRR@10", "R@20", "nDCG@10", "Rcap@20", "Suf3@20", "OracleP3@20", "Hole@10"]

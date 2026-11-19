"""Resumen de latencia: p50, p95, p99 y fracción de solicitudes por estado."""
from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List, Tuple


def percentile_nearest_rank(values: List[float], p: float) -> float:
    """Percentil por rango más cercano (nearest-rank): el valor real que deja al p% por debajo o igual.

    Es la convención conservadora para colas: p99 de 100 muestras es la 99.ª más lenta ordenada, no una interpolación.
    """
    if not values:
        raise ValueError("sin muestras")
    s = sorted(values)
    idx = max(math.ceil(p / 100.0 * len(s)) - 1, 0)
    return s[idx]


def summarize_latency(rows: List[Tuple[str, float, str]], extra_requests: int | None = None) -> Dict[str, float]:
    """rows: (qid, latency_ms, status). Todas las solicitudes cuentan, también las fallidas.

    Se reportan dos p99: `p99_ms` (todas las solicitudes, regla del equipo) y `p99_with_results_ms`
    (solo las que entregan resultados, `ok` y `degraded`, como lo define el texto del paper). Si difieren mucho,
    los timeouts y errores están escondiendo la cola.
    `extra_requests`: solicitudes duplicadas enviadas (hedged); se reporta como % sobre las solicitudes originales."""
    lat = [ms for _, ms, _ in rows]
    n = len(lat)
    status = Counter(s for _, _, s in rows)
    summary = {
        "n_requests": n,
        "p50_ms": percentile_nearest_rank(lat, 50),
        "p95_ms": percentile_nearest_rank(lat, 95),
        "p99_ms": percentile_nearest_rank(lat, 99),
        "mean_ms": sum(lat) / n,
        "max_ms": max(lat),
    }
    for s in ("ok", "degraded", "timeout", "error"):
        summary[f"frac_{s}"] = status.get(s, 0) / n
    # Con pocas muestras el p99 lo determinan muy pocas solicitudes: se avisa en el reporte.
    summary["p99_samples_above"] = n - math.ceil(0.99 * n) + 1
    with_results = [ms for _, ms, s in rows if s in ("ok", "degraded")]
    summary["n_with_results"] = len(with_results)
    summary["p99_with_results_ms"] = percentile_nearest_rank(with_results, 99) if with_results else None
    if extra_requests is not None:
        summary["extra_requests"] = extra_requests
        summary["extra_requests_pct"] = 100.0 * extra_requests / n
    return summary


def summarize_stages(rows: List[Tuple[str, str, float]]) -> Dict[str, Dict[str, float]]:
    """rows: (qid, etapa, ms). Resume cada etapa (por ejemplo llm_ronda, fusion, rerank) con p50, p95 y p99."""
    by_stage: Dict[str, List[float]] = {}
    for _, stage, ms in rows:
        by_stage.setdefault(stage, []).append(ms)
    return {s: {"n": len(v), "p50_ms": percentile_nearest_rank(v, 50), "p95_ms": percentile_nearest_rank(v, 95),
                "p99_ms": percentile_nearest_rank(v, 99), "total_ms": sum(v)} for s, v in sorted(by_stage.items())}

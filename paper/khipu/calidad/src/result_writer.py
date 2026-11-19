"""Guardar resultados y latencias en el formato del equipo, sin escribir archivos a mano.

Uso (en el código de cada experimento):

    from result_writer import ResultWriter

    with ResultWriter("results/e3_cross_encoder") as rw:
        for qid, texto in queries:
            with rw.request(qid) as r:          # mide el tiempo de esta consulta
                ranking = mi_sistema(texto)     # dict {id_documento: puntaje}
                r.set_results(ranking)
                # if usó_el_plan_b:   r.mark_degraded()
                # if se_pasó_del_plazo: r.mark_timeout()
                # r.add_extra()                  # envió una solicitud duplicada (hedged)
                # with r.stage("llm"):           # mide una etapa aparte (llm, fusion, rerank...)
                #     scores = llm(...)

Al salir se escriben results/e3_cross_encoder.run y results/e3_cross_encoder.latency.tsv
(y .stages.tsv si usaste r.stage(...)). La 4.ª columna de latency.tsv (solicitudes duplicadas) solo aparece si usaste r.add_extra().

Reglas:
- Si dentro del bloque ocurre un error, se registra como `error` y se sigue con la siguiente consulta.
- `timeout` y `error`: no se guardan resultados (la consulta cuenta como 0 en calidad).
- `degraded`: se guardan los resultados que haya (por ejemplo, el ranking del retrieval sin reranker).
- Es seguro llamarlo desde varios hilos (para pruebas de carga).
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from io_formats import write_run  # noqa: E402


class _Stage:
    def __init__(self, req: "Request", name: str):
        self._req, self._name, self._t0 = req, name, 0.0

    def __enter__(self) -> "_Stage":
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._req._stages.append((self._name, (time.perf_counter() - self._t0) * 1000.0))
        return False


class Request:
    def __init__(self, writer: "ResultWriter", qid: str):
        self._writer, self.qid = writer, qid
        self._results: Dict[str, float] = {}
        self._status = "ok"
        self._start = 0.0
        self._extra = 0
        self._stages: List[Tuple[str, float]] = []

    def add_extra(self, n: int = 1) -> None:
        """Cuenta solicitudes duplicadas (hedged) enviadas en esta consulta."""
        self._extra += n

    def stage(self, name: str) -> "_Stage":
        """Mide una etapa dentro de la consulta. Se puede repetir el mismo nombre (por ejemplo, una vez por ronda)."""
        return _Stage(self, name)

    def set_results(self, ranking: Dict[str, float]) -> None:
        self._results = dict(ranking)

    def mark_degraded(self) -> None:
        if self._status == "ok":
            self._status = "degraded"

    def mark_timeout(self) -> None:
        self._status = "timeout"

    def mark_error(self) -> None:
        self._status = "error"

    def __enter__(self) -> "Request":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        ms = (time.perf_counter() - self._start) * 1000.0
        if exc_type is not None:
            self._status = "error"
            self._writer._note_error(self.qid, exc)
        results = self._results if self._status in ("ok", "degraded") else {}
        self._writer._record(self.qid, ms, self._status, results, self._extra, self._stages)
        return exc_type is not None and issubclass(exc_type, Exception)  # el error se registra y no detiene el experimento


class ResultWriter:
    def __init__(self, prefix: str, tag: Optional[str] = None, top_k: int = 100):
        self.prefix, self.top_k = Path(prefix), top_k
        self.tag = tag or self.prefix.name
        self._lock = threading.Lock()
        self._run: Dict[str, Dict[str, float]] = {}
        self._latency: List[Tuple[str, float, str, int]] = []
        self._stages: List[Tuple[str, str, float]] = []
        self._errors: List[Tuple[str, str]] = []

    def request(self, qid: str) -> Request:
        return Request(self, qid)

    def _record(self, qid: str, ms: float, status: str, results: Dict[str, float], extra: int = 0,
                stages: Optional[List[Tuple[str, float]]] = None) -> None:
        with self._lock:
            self._latency.append((qid, ms, status, extra))
            self._stages += [(qid, name, sms) for name, sms in (stages or [])]
            if results:
                top = sorted(results.items(), key=lambda kv: (-kv[1], kv[0]))[: self.top_k]
                self._run[qid] = dict(top)

    def _note_error(self, qid: str, exc: BaseException) -> None:
        with self._lock:
            self._errors.append((qid, f"{type(exc).__name__}: {exc}"))

    def close(self) -> Tuple[Path, Path]:
        self.prefix.parent.mkdir(parents=True, exist_ok=True)
        run_path = Path(f"{self.prefix}.run")
        lat_path = Path(f"{self.prefix}.latency.tsv")
        write_run(run_path, self._run, self.tag)
        with_extra = any(e for *_, e in self._latency)
        with open(lat_path, "w", encoding="utf-8") as f:
            for qid, ms, status, extra in self._latency:
                f.write(f"{qid}\t{ms:.3f}\t{status}" + (f"\t{extra}" if with_extra else "") + "\n")
        if self._stages:
            with open(f"{self.prefix}.stages.tsv", "w", encoding="utf-8") as f:
                for qid, name, sms in self._stages:
                    f.write(f"{qid}\t{name}\t{sms:.3f}\n")
        if self._errors:
            print(f"AVISO: {len(self._errors)} consulta(s) con error. Primera: {self._errors[0][0]} -> {self._errors[0][1]}", file=sys.stderr)
        return run_path, lat_path

    def __enter__(self) -> "ResultWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

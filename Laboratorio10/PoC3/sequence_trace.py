"""Capture two teaching requests separately from the 61,000-request benchmark."""
import asyncio
import json
import time

import simcore as sc
from improved_api import ImprovedAPI
from volume_benchmark import TwoSlowBackend, TwoSlowConfig, timer_resolution


class TraceBackend(TwoSlowBackend):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.events = []
        self.origin = time.perf_counter()

    def event(self, kind, **data):
        self.events.append({"event": kind, "ms": (time.perf_counter() - self.origin) * 1000, **data})

    async def call(self, req, svc, replica, attempt):
        data = {"svc": svc, "replica": replica, "attempt": attempt}
        self.event("send", **data)
        try:
            result = await super().call(req, svc, replica, attempt)
        except asyncio.CancelledError:
            self.event("cancel", **data)
            raise
        except Exception:
            self.event("error", **data)
            raise
        self.event("return", **data)
        return result


class TraceAPI(ImprovedAPI):
    async def _attempt(self, req, svc, attempt):
        alpha, beta = self.thresholds(svc)
        self.backend.event("thresholds", svc=svc, attempt=attempt,
                           alpha_ms=alpha * 1000, beta_ms=beta * 1000)
        return await super()._attempt(req, svc, attempt)

    async def call_service(self, req, svc):
        outcome = await super().call_service(req, svc)
        self.backend.event("service_outcome", svc=svc, outcome=outcome)
        return outcome


async def capture(kind, seed=606, req=0):
    backend = TraceBackend(TwoSlowConfig(seed=seed))
    backend.warm_up()
    api = sc.BaselineAPI(backend) if kind == "baseline" else TraceAPI(backend, 17, 34.1)
    selected = backend.slow_services(req)
    backend.origin = time.perf_counter()
    outcome = await api.handle(req)
    elapsed = (time.perf_counter() - backend.origin) * 1000
    return {"variant": kind, "seed": seed, "request": req, "outcome": outcome,
            "initial_cache_services": list(getattr(api, "initial_cache_services", ())),
            "total_ms": elapsed, "slow_services": selected,
            "alpha_ms": None if kind == "baseline" else 17,
            "beta_ms": None if kind == "baseline" else 34.1,
            "backend_calls": backend.calls, "events": backend.events}


def mermaid(case):
    slow = set(case["slow_services"])
    messages = [(0.0, "Cliente", "API", "->>+", "Solicitar datos de 10 servicios")]
    others = [e for e in case["events"] if e.get("svc") not in slow]
    starts = [e for e in others if e["event"] == "send"]
    finishes = [e for e in others if e["event"] in ("service_outcome", "return")]
    if starts:
        messages.append((min(e["ms"] for e in starts), "API", "Otros8", "->>", "8 consultas en paralelo"))
    if finishes:
        messages.append((max(e["ms"] for e in finishes), "Otros8", "API", "-->>", "Finaliza el grupo de otros 8"))
    for svc in case["slow_services"]:
        participant = f"Servicio{svc}"
        events = [e for e in case["events"] if e.get("svc") == svc]
        for event in events:
            if event.get("attempt") != 1:
                continue
            if event["event"] == "send":
                replica = event["replica"] == 1
                messages.append((event["ms"], "API", "Replicas" if replica else participant, "->>",
                                 f"Replica de S{svc} tras alpha" if replica else f"Consulta original S{svc} lenta"))
            elif event["event"] == "cancel" and event["replica"] == 0:
                messages.append((event["ms"], "API", participant, "-x", f"Cancelar original S{svc}"))
        retries = [e for e in events if e["event"] == "send" and e.get("attempt", 1) > 1 and e.get("replica") == 0]
        if retries:
            messages.append((min(e["ms"] for e in retries), "API", "API", "->>",
                             f"Reintentos de S{svc} agrupados: {len(retries)}"))
        completed = [e for e in events if e["event"] == "return"]
        outcomes = [e for e in events if e["event"] == "service_outcome"]
        if completed and (not outcomes or outcomes[-1]["outcome"] == "ok"):
            winner = max(completed, key=lambda e: e["ms"])
            messages.append((winner["ms"], "Replicas" if winner["replica"] else participant,
                             "API", "-->>", f"Respuesta S{svc}, intento {winner['attempt']}"))
        elif outcomes:
            last = outcomes[-1]
            label = "Dato de cache" if last["outcome"] == "cache" else "Sin dato tras agotar la politica"
            messages.append((last["ms"], "API", "API", "->>", f"{label}: S{svc}"))
    messages.append((case["total_ms"], "API", "Cliente", "-->>-", f"Respuesta final: {case['outcome']}"))
    lines = ["sequenceDiagram", "    participant Cliente", "    participant API", "    participant Otros8"]
    lines += [f"    participant Servicio{svc}" for svc in case["slow_services"]]
    if case["variant"] != "baseline":
        lines += ["    participant Replicas"]
    if case.get("initial_cache_services"):
        ids = ", ".join(f"S{s}" for s in case["initial_cache_services"])
        lines[2] = f"    participant API as API (cache inicial {ids})"
    for ms, source, target, arrow, label in sorted(messages, key=lambda m: m[0]):
        lines.append(f"    {source}{arrow}{target}: t={ms:.1f} ms - {label}")
    return "\n".join(lines) + "\n"


def create_sequence_sources(here):
    output = here / "results/sequence"
    output.mkdir(parents=True, exist_ok=True)
    cases = []
    with timer_resolution():
        for kind in ("baseline", "poc3"):
            case = asyncio.run(capture(kind))
            cases.append(case)
            (output / f"{kind}.mmd").write_text(mermaid(case), encoding="utf-8")
    assert cases[0]["slow_services"] == cases[1]["slow_services"]
    (output / "trace.json").write_text(json.dumps({
        "purpose": "single-request teaching trace; not a percentile benchmark",
        "additional_demo_requests": 2, "included_in_volume_totals": False,
        "vertical_spacing": "message order, not proportional elapsed time",
        "grouping": "other eight services and repeated attempts are condensed; full events retained",
        "cases": cases}, indent=2), encoding="utf-8")
    lines = ["# Measured request sequence", "",
             "Two additional demonstration requests, separate from the 61000 benchmark requests. "
             "Times are elapsed wall-clock milliseconds from one example, not p50/p95/p99. "
             "Vertical spacing shows message order, not proportional elapsed time. "
             "The other eight services and retry sends are grouped; all events remain in trace.json.", "",
             "| Variant | Slow services | Response time ms | Outcome |", "|---|---|---:|---|"]
    for c in cases:
        lines.append(f"| {c['variant']} | {c['slow_services']} | {c['total_ms']:.1f} | {c['outcome']} |")
    lines += ["", f"PoC3 initially preloads cache for services {cases[1]['initial_cache_services']}, independently of slow services. "
              "All ten services can subsequently refresh cached data. Cache is a fallback after an unsuccessful attempt. "
              "PoC3 starts with alpha=17 ms and beta=34.1 ms. "
              "A replica is another instance of the same service; it may answer faster. "
              "Pending original calls are cancelled when an attempt finishes or reaches its timeout. "
              "Both replicas being slow is still possible; the trace shows the actual outcome.", "",
              "![Baseline](baseline.png)", "", "![PoC3](poc3.png)"]
    (output / "sequence-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output

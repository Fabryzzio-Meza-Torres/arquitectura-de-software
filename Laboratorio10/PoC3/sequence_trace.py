"""Capture three teaching requests plus six setup calls outside the benchmark."""
import asyncio
import json
import time

import simcore as sc
from mechanism_study import InstrumentedAPI, StudyBackend
from volume_benchmark import TwoSlowBackend, TwoSlowConfig, timer_resolution


class TraceBackend(TwoSlowBackend):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.events = []
        self.origin = time.perf_counter()

    def event(self, kind, **data):
        self.events.append({"event": kind, "ms": (time.perf_counter() - self.origin) * 1000, **data})

    async def call(self, req, svc, replica, attempt):
        data = {"req": req, "svc": svc, "replica": replica, "attempt": attempt}
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


class TraceAPI(InstrumentedAPI):
    pass


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
    events = case["events"]
    protected = case["variant"] != "baseline"
    messages = [(0.0, "Cliente", "API", "->>+", "Solicitar datos de 10 servicios")]
    def add(ms, source, target, arrow, label):
        messages.append((ms, source, target, arrow, label))
    others = [e for e in events if e.get("svc") not in slow]
    starts = [e for e in others if e["event"] == "send"]
    finishes = [e for e in others if e["event"] in ("service_outcome", "return")]
    if starts:
        add(min(e["ms"] for e in starts), "API", "Otros8", "->>", "8 consultas en paralelo")
    if finishes:
        add(max(e["ms"] for e in finishes), "Otros8", "API", "-->>", "Otros 8 completados")
    selected = [e for e in events if e.get("svc") in slow]
    decisions = [e for e in selected if e["event"] == "breaker_decision"]
    if decisions:
        add(min(e["ms"] for e in decisions), "API", "Circuito", "->>", "Consultar circuit breaker")
        first = {svc: next(e for e in decisions if e["svc"] == svc) for svc in slow
                 if any(e["svc"] == svc for e in decisions)}
        allowed = sum(e["allowed"] for e in first.values())
        label = (f"Cerrado: permite {allowed} consultas" if allowed == len(first) else
                 f"Abierto: evita {len(first)-allowed} consultas")
        add(max(e["ms"] for e in first.values()), "Circuito", "API", "-->>", label)
    primaries = [e for e in selected if e["event"] == "send" and e["replica"] == 0 and e["attempt"] == 1]
    if primaries:
        ids = ", ".join(f"S{e['svc']}" for e in primaries)
        add(min(e["ms"] for e in primaries), "API", "Problema", "->>", f"{len(primaries)} consultas lentas: {ids}")
    hedges = [e for e in selected if e["event"] == "send" and e["replica"] == 1 and e["attempt"] == 1]
    if hedges:
        add(min(e["ms"] for e in hedges), "API", "Replicas", "->>", f"Superado alpha: activar {len(hedges)} replicas")
    for svc in case["slow_services"]:
        own = [e for e in selected if e["svc"] == svc]
        outcomes = [e for e in own if e["event"] == "service_outcome"]
        completed = [e for e in own if e["event"] == "return"]
        if completed and (not outcomes or outcomes[-1]["outcome"] == "ok"):
            winner = max(completed, key=lambda e: e["ms"])
            add(winner["ms"], "Replicas" if winner["replica"] else "Problema", "API", "-->>",
                f"Respuesta valida S{svc}, intento {winner['attempt']}")
        elif outcomes and outcomes[-1]["outcome"] == "failed":
            add(outcomes[-1]["ms"], "API", "API", "->>", f"Sin dato valido S{svc}")
    cancelled = [e for e in selected if e["event"] == "cancel" and e.get("replica") == 0]
    if cancelled:
        add(max(e["ms"] for e in cancelled), "API", "Problema", "-x", "Originales pendientes cancelados")
    retries = [e for e in selected if e["event"] == "send" and e["replica"] == 0 and e["attempt"] > 1]
    if retries:
        add(min(e["ms"] for e in retries), "API", "Problema", "->>", f"{len(retries)} reintentos tras presupuesto y backoff")
    hits = [e for e in selected if e["event"] == "cache_hit"]
    cache_outcomes = [e for e in selected if e["event"] == "service_outcome" and e["outcome"] == "cache"]
    if hits:
        add(min(e["ms"] for e in hits), "API", "Cache", "->>", "Consultar datos dentro del TTL")
        add(max(e["ms"] for e in cache_outcomes), "Cache", "API", "-->>", f"{len(hits)} respuestas con cache vigente")
    success = [e for e in selected if e["event"] == "breaker_success"]
    if success:
        add(max(e["ms"] for e in success), "API", "Circuito", "->>", "Registrar respuestas validas")
    add(case["total_ms"], "API", "Cliente", "-->>-", f"Respuesta final: {case['outcome']}")
    lines = ["sequenceDiagram", "    participant Cliente", "    participant API"]
    if protected:
        lines.append("    participant Circuito as Circuit breaker")
    lines += ["    participant Otros8 as Otros 8 servicios", "    participant Problema as Servicio problematico"]
    if protected:
        lines += ["    participant Replicas", "    participant Cache as Cache (TTL 1 s / 5 s)"]
    for ms, source, target, arrow, label in sorted(messages, key=lambda m: m[0]):
        lines.append(f"    {source}{arrow}{target}: t={ms:.1f} ms - {label}")
    return "\n".join(lines) + "\n"


async def capture_open_breaker(seed=606):
    backend = StudyBackend(TwoSlowConfig(seed=seed), "persistent_two")
    api = InstrumentedAPI(backend)
    await api.handle(0)  # Healthy traffic naturally fills all ten caches.
    for req in range(10, 15):
        await api.handle(req)  # Five failed attempts per affected service open its circuit.
    backend.events.clear()
    backend.origin = time.perf_counter()
    outcome = await api.handle(15)
    elapsed = (time.perf_counter() - backend.origin) * 1000
    return {"variant": "breaker_open", "seed": seed, "request": 15, "outcome": outcome,
            "total_ms": elapsed, "slow_services": backend.fault_services,
            "initial_cache_services": api.initial_cache_services,
            "cache_services_at_capture": sorted(api.cache), "setup_requests": 6,
            "scenario": "separate persistent-delay diagnostic after healthy traffic",
            "backend_calls": sum(e["event"] == "send" for e in backend.events), "events": backend.events}


def create_sequence_sources(here):
    output = here / "results/sequence"
    output.mkdir(parents=True, exist_ok=True)
    cases = []
    with timer_resolution():
        for kind in ("baseline", "poc3"):
            case = asyncio.run(capture(kind))
            cases.append(case)
            (output / f"{kind}.mmd").write_text(mermaid(case), encoding="utf-8")
        opened = asyncio.run(capture_open_breaker())
        cases.append(opened)
        (output / "breaker_open.mmd").write_text(mermaid(opened), encoding="utf-8")
    assert cases[0]["slow_services"] == cases[1]["slow_services"]
    (output / "trace.json").write_text(json.dumps({
        "purpose": "single-request teaching trace; not a percentile benchmark",
        "additional_demo_requests": 9, "measured_demo_requests": 3, "setup_requests": 6, "included_in_volume_totals": False,
        "vertical_spacing": "message order, not proportional elapsed time",
        "grouping": "other eight services and repeated attempts are condensed; full events retained",
        "cases": cases}, indent=2), encoding="utf-8")
    lines = ["# Measured request sequence", "",
             "Three measured demonstration requests plus six setup requests, separate from the 61000 benchmark requests. "
             "Times are elapsed wall-clock milliseconds from one example, not p50/p95/p99. "
             "Vertical spacing shows message order, not proportional elapsed time. "
             "The other eight services and retry sends are grouped; all events remain in trace.json.", "",
             "| Variant | Slow services | Response time ms | Outcome |", "|---|---|---:|---|"]
    for c in cases:
        lines.append(f"| {c['variant']} | {c['slow_services']} | {c['total_ms']:.1f} | {c['outcome']} |")
    lines += ["", "The single Servicio problematico block groups the two slow services; both remain in the simulation. "
              "breaker_open is a separate persistent-delay example: one healthy request fills caches, then five fault requests open both circuits. "
              "The API still waits for the other eight services. Circuit-open service latency is not the whole API latency.", "", f"PoC3 initially preloads cache for services {cases[1]['initial_cache_services']}, independently of slow services. "
              "All ten services can subsequently refresh cached data. Cache is a fallback after an unsuccessful attempt. "
              "PoC3 starts with alpha=17 ms and beta=34.1 ms. "
              "A replica is another instance of the same service; it may answer faster. "
              "Pending original calls are cancelled when an attempt finishes or reaches its timeout. "
              "Both replicas being slow is still possible; the trace shows the actual outcome.", "",
              "![Baseline](baseline.png)", "", "![PoC3](poc3.png)", "", "![Open circuit](breaker_open.png)"]
    (output / "sequence-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output

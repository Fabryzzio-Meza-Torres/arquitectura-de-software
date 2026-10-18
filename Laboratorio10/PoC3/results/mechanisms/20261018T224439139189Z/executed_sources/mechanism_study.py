"""Diagnostic component comparisons; the production PoC3 policy stays unchanged."""
import asyncio
import contextvars
import hashlib
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from experiment import load, metric, fingerprint, summarize
from improved_api import ImprovedAPI, HalfOpenBreaker
from volume_benchmark import TwoSlowBackend, TwoSlowConfig, timer_resolution

REQUEST = contextvars.ContextVar("diagnostic_request", default=None)
SERVICE = contextvars.ContextVar("diagnostic_service", default=None)
VARIANTS = ("full", "no_breaker", "no_hedging", "no_cache", "no_retries",
            "no_preload", "fixed_thresholds")
LABELS = {"full": "PoC3 completo", "no_breaker": "Sin circuit breaker",
          "no_hedging": "Sin replicas", "no_cache": "Sin cache",
          "no_retries": "Sin reintentos", "no_preload": "Sin precarga inicial",
          "fixed_thresholds": "Sin adaptacion de alpha/beta"}


class ObservedBreaker:
    """Delegate every decision to the original breaker, recording its real state."""
    def __init__(self, original, backend, svc, disabled=False):
        self.original, self.backend, self.svc = original, backend, svc
        self.disabled = disabled

    def state(self, now):
        if self.disabled:
            return "disabled"
        if now < self.original.open_until:
            return "open"
        return "half_open" if self.original.fail >= self.original.threshold else "closed"

    def allow(self, now):
        state = self.state(now)
        allowed = True if self.disabled else self.original.allow(now)
        self.backend.event("breaker_decision", req=REQUEST.get(), svc=self.svc,
                           state=state, allowed=allowed)
        return allowed

    def is_open(self, now):
        return False if self.disabled else self.original.is_open(now)

    def on_failure(self, now):
        before = self.state(now)
        if not self.disabled:
            self.original.on_failure(now)
        self.backend.event("breaker_failure", req=REQUEST.get(), svc=self.svc,
                           before=before, state=self.state(now), failures=self.original.fail)

    def on_success(self):
        before = self.state(time.monotonic())
        if not self.disabled:
            self.original.on_success()
        self.backend.event("breaker_success", req=REQUEST.get(), svc=self.svc,
                           before=before, state=self.state(time.monotonic()))


class ObservedBudget:
    def __init__(self, original, backend):
        self.original, self.backend = original, backend

    def deposit(self):
        self.original.deposit()

    def try_spend(self):
        allowed = self.original.try_spend()
        self.backend.event("retry_budget", req=REQUEST.get(), svc=SERVICE.get(),
                           allowed=allowed, tokens=self.original.tokens)
        return allowed


class InstrumentedAPI(ImprovedAPI):
    def __init__(self, backend, alpha_ms=17, beta_ms=34.1, variant="full"):
        if variant not in VARIANTS:
            raise ValueError(variant)
        self.variant = variant
        super().__init__(backend, alpha_ms, beta_ms, max_attempts=1 if variant == "no_retries" else 3)
        if variant in ("no_cache", "no_preload"):
            self.cache.clear()
            self.initial_cache_services = ()
        self.breakers = {s: ObservedBreaker(br, backend, s, variant == "no_breaker")
                         for s, br in self.breakers.items()}
        self.budget = ObservedBudget(self.budget, backend)
        self.service_records = []

    def _cacheable(self, svc):
        return self.variant != "no_cache" and super()._cacheable(svc)

    def thresholds(self, svc):
        if self.variant == "fixed_thresholds":
            return self.alpha0, self.beta0
        return super().thresholds(svc)

    def _serve_cache(self, svc, age, tier):
        self.backend.event("cache_hit", req=REQUEST.get(), svc=svc, age_s=age, tier=tier)
        return super()._serve_cache(svc, age, tier)

    async def _attempt(self, req, svc, attempt):
        alpha, beta = self.thresholds(svc)
        start = time.perf_counter()
        self.backend.event("attempt_start", req=req, svc=svc, attempt=attempt,
                           alpha_ms=alpha * 1000, beta_ms=beta * 1000)
        if self.variant == "no_hedging":
            try:
                await asyncio.wait_for(self.backend.call(req, svc, 0, attempt), beta)
                self._observe(svc, time.perf_counter() - start)
                outcome = "ok"
            except asyncio.TimeoutError:
                outcome = "timeout"
            except Exception:
                self.backend_errors += 1
                outcome = "error"
        else:
            outcome = await super()._attempt(req, svc, attempt)
        self.backend.event("attempt_end", req=req, svc=svc, attempt=attempt,
                           outcome=outcome, duration_ms=(time.perf_counter() - start) * 1000)
        return outcome

    async def call_service(self, req, svc):
        token = SERVICE.set(svc)
        start = time.perf_counter()
        try:
            outcome = await super().call_service(req, svc)
            duration = (time.perf_counter() - start) * 1000
            self.service_records.append({"request": req, "svc": svc,
                                         "latency_ms": duration, "outcome": outcome})
            self.backend.event("service_outcome", req=req, svc=svc, outcome=outcome,
                               duration_ms=duration)
            return outcome
        finally:
            SERVICE.reset(token)

    async def handle(self, req):
        token = REQUEST.set(req)
        try:
            return await super().handle(req)
        finally:
            REQUEST.reset(token)


class StudyBackend(TwoSlowBackend):
    def __init__(self, cfg, scenario="random_two"):
        super().__init__(cfg)
        self.scenario, self.events = scenario, []
        self.origin = time.perf_counter()
        self.fault_services = tuple(sorted(random.Random(f"{cfg.seed}|persistent-two").sample(range(1, 11), 2)))

    def event(self, kind, **data):
        self.events.append({"event": kind, "ms": (time.perf_counter() - self.origin) * 1000, **data})

    def latency_ms(self, req, svc, replica, attempt):
        if self.scenario == "random_two":
            return super().latency_ms(req, svc, replica, attempt)
        # Separate diagnostic: healthy -> persistent delay of two services -> recovery.
        rng = random.Random(f"{self.cfg.seed}|persistent-latency|{req}|{svc}|{replica}|{attempt}")
        return rng.uniform(1000, 1500) if 10 <= req < 130 and svc in self.fault_services else rng.uniform(7, 15)

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


def phase(req):
    return "healthy" if req < 10 else "persistent_delay" if req < 130 else "recovery"


def trial(variant, seed, scenario, n, rps):
    backend = StudyBackend(TwoSlowConfig(seed=seed), scenario)
    api = InstrumentedAPI(backend, variant=variant)
    backend.origin = time.perf_counter()
    records, lag, wall = asyncio.run(load(api, n, rps))
    counters = {name: getattr(api, name) for name in (
        "hedges", "retries", "retries_denied", "breaker_short_circuits", "timeouts",
        "backend_errors", "degraded_fresh", "degraded_stale", "failed_calls")}
    digest = hashlib.sha256()
    for req in range(n):
        for svc in range(1, 11):
            digest.update(backend.latency_ms(req, svc, 0, 1).hex().encode("ascii"))
    return {"variant": variant, "seed": seed, "scenario": scenario, "n": n,
            "rps": rps, "wall_s": wall, "loop_lag_max_ms": max(lag, default=0),
            "measurement_valid": max(lag, default=0) <= 20, "lag_limit_ms": 20,
            "initial_cache_services": api.initial_cache_services,
            "fault_services": backend.fault_services if scenario != "random_two" else None,
            "primary_samples_sha256": digest.hexdigest(),
            "backend_calls": backend.calls, "counters": counters,
            "records": records, "metrics": summarize(records),
            "service_records": api.service_records, "events": backend.events}


def compare(trials, variant, scenario):
    selected = [t for t in trials if t["scenario"] == scenario and t["variant"] == variant]
    full = {t["seed"]: t for t in trials if t["scenario"] == scenario and t["variant"] == "full"}
    clean = [t for t in selected if t["measurement_valid"] and full[t["seed"]]["measurement_valid"]]
    used = clean or selected
    records = [r for t in used for r in t["records"]]
    all_records = [r for t in selected for r in t["records"]]
    return {"variant": variant, "scenario": scenario, "clean_pairs": len(clean),
            "pairs": len(selected), "latency_source": "clean_pairs" if clean else "noisy_observations",
            "latency": metric([r["latency_ms"] for r in records]),
            "executed": len(all_records),
            "failed_pct": 100 * sum(r["outcome"] == "failed" for r in all_records) / len(all_records),
            "cache_pct": 100 * sum(r["outcome"] == "degraded" for r in all_records) / len(all_records),
            "backend_calls": sum(t["backend_calls"] for t in selected),
            "counters": {name: sum(t["counters"][name] for t in selected) for name in selected[0]["counters"]}}


def run_study(here, seeds=(101, 202, 303), n=200, rps=50):
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = here / "results/mechanisms" / run_id
    output.mkdir(parents=True)
    sources = output / "executed_sources"
    sources.mkdir()
    names = ("mechanism_study.py", "improved_api.py", "simcore.py", "volume_benchmark.py", "experiment.py")
    digests = {}
    for name in names:
        data = (here / name).read_bytes()
        (sources / name).write_bytes(data)
        digests[name] = hashlib.sha256(data).hexdigest()
    result = {"purpose": "component diagnostics, separate from the official 61000-request benchmark",
              "seeds": list(seeds), "rps": rps, "lag_limit_ms": 20, "source_sha256": digests,
              "random_two_n_per_variant_per_seed": n, "persistent_n_per_variant_per_seed": 210,
              "persistent_scenario": "requests 0-9 healthy, 10-129 same two random services slow on both replicas, 130-209 healthy",
              "trials": [], "status": "running"}
    def save():
        (output / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with timer_resolution() as timer:
        result["timer_resolution"] = timer
        for scenario, variants, count in (("random_two", VARIANTS, n),
                                           ("persistent_two", ("full", "no_breaker"), 210)):
            for index, seed in enumerate(seeds):
                # Rotate order to avoid always assigning startup/order effects to one variant.
                order = list(variants[index % len(variants):] + variants[:index % len(variants)])
                for variant in order:
                    t = trial(variant, seed, scenario, count, rps)
                    result["trials"].append(t)
                    print(f"{scenario} seed={seed} {variant}: p99={t['metrics']['all']['p99_ms']:.1f} "
                          f"valid={t['measurement_valid']} breaker_skips={t['counters']['breaker_short_circuits']}", flush=True)
                    save()
                hashes = {t["primary_samples_sha256"] for t in result["trials"]
                          if t["scenario"] == scenario and t["seed"] == seed}
                assert len(hashes) == 1
    result["summary"] = [compare(result["trials"], v, s) for s, variants in
                         (("random_two", VARIANTS), ("persistent_two", ("full", "no_breaker"))) for v in variants]
    result["requests_executed"] = sum(t["n"] for t in result["trials"])
    result["status"] = "complete"
    save()
    (output.parent / "latest.json").write_text(json.dumps({"results": f"{run_id}/results.json"}), encoding="utf-8")
    return output


if __name__ == "__main__":
    print(run_study(Path(__file__).resolve().parent))

# Simulation model inherited from PoC 2; local to PoC3.
import asyncio, bisect, json, math, os, random, re, time
from dataclasses import dataclass, asdict
from collections import Counter
from typing import Optional

N_SERVICES = 10
PROBLEM_SERVICES = (8, 9, 10)
BETA_CAP_MS = 100.0


@dataclass
class SimConfig:
    seed: int = 42
    base_median_ms: float = 10.0
    base_sigma: float = 0.35
    p_slow_normal: float = 0.01       # cada llamada de cualquier servicio es lenta con 1%
    p_slow_problem: float = 0.01       # igual para los servicios 8-10 (modelo del profe)
    slow_min_ms: float = 900.0        # llamada lenta: ~1000 ms (900 a 1100)
    slow_max_ms: float = 1100.0
    cold_start_ms: float = 400.0
    cold_calls: int = 5
    outage: Optional[tuple] = None
    outage_ms: float = 2000.0
    drift: Optional[tuple] = None
    drift_factor: float = 2.5


def _rng(cfg, *key):
    return random.Random(f"{cfg.seed}|" + "|".join(map(str, key)))


class Backend:

    def __init__(self, cfg):
        self.cfg = cfg
        self.calls = 0
        self.cold = {(s, r): cfg.cold_calls for s in PROBLEM_SERVICES for r in (0, 1)}

    def warm_up(self):
        for k in self.cold:
            self.cold[k] = 0

    def latency_ms(self, req, svc, replica, attempt):
        cfg = self.cfg
        if cfg.outage and cfg.outage[0] == svc and cfg.outage[1] <= req < cfg.outage[2]:
            return cfg.outage_ms
        r = _rng(cfg, req, svc, replica, attempt)
        median = cfg.base_median_ms
        if cfg.drift and cfg.drift[0] == svc and cfg.drift[1] <= req < cfg.drift[2]:
            median *= cfg.drift_factor
        lat = r.lognormvariate(math.log(median), cfg.base_sigma)
        p = cfg.p_slow_problem if svc in PROBLEM_SERVICES else cfg.p_slow_normal
        if r.random() < p:
            lat = r.uniform(cfg.slow_min_ms, cfg.slow_max_ms)
        left = self.cold.get((svc, replica), 0)
        if left > 0:
            self.cold[(svc, replica)] = left - 1
            lat += cfg.cold_start_ms
        return lat

    async def call(self, req, svc, replica, attempt):
        self.calls += 1
        await asyncio.sleep(self.latency_ms(req, svc, replica, attempt) / 1000.0)


class BaselineAPI:
    name = "Baseline"

    def __init__(self, backend):
        self.backend = backend

    async def handle(self, req):
        outcomes = await asyncio.gather(
            *(self.backend.call(req, s, 0, 1) for s in range(1, N_SERVICES + 1)),
            return_exceptions=True,
        )
        return "failed" if any(isinstance(x, BaseException) for x in outcomes) else "ok"


class Breaker:

    def __init__(self, threshold=5, cooldown=1.0):
        self.threshold, self.cooldown = threshold, cooldown
        self.fail, self.open_until = 0, 0.0

    def allow(self, now):
        return now >= self.open_until

    def is_open(self, now):
        return now < self.open_until

    def on_success(self):
        self.fail, self.open_until = 0, 0.0

    def on_failure(self, now):
        self.fail += 1
        if self.fail >= self.threshold:
            self.open_until = now + self.cooldown


def scenarios(n, seed):
    return {
        "tails": SimConfig(seed=seed),
        "tails_heavy": SimConfig(seed=seed, p_slow_problem=0.10, slow_min_ms=500.0, slow_max_ms=1500.0),
        "outage_svc9": SimConfig(seed=seed, outage=(9, int(n * 0.30), int(n * 0.60))),
        "outage_long_svc9": SimConfig(seed=seed, outage=(9, int(n * 0.20), int(n * 0.85))),
        "drift_svc3": SimConfig(seed=seed, drift=(3, int(n * 0.30), int(n * 0.70)), drift_factor=2.5),
    }


SCENARIO_TITLES = {
    "tails": "1. Colas (modelo del profe: 10 servicios al 1%)",
    "tails_heavy": "2. Estres: servicios 8-10 al 10%, colas de 0.5-1.5 s",
    "outage_svc9": "3. Service 9 caido (30% central)",
    "outage_long_svc9": "4. Service 9 caido, prolongado (65%)",
    "drift_svc3": "5. Service 3 degradado x2.5 (40% central)",
}


def pct(sorted_vals, p):
    k = (len(sorted_vals) - 1) * p / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


# cvar de la foto: min sobre tau de tau + E[(T-tau)+]/(1-q). se busca tau por biseccion sobre la derivada
def cvar_ru(samples, q=0.99, tol=1e-3):
    xs = sorted(samples)
    n = len(xs)
    lo, hi = xs[0], xs[-1]
    while hi - lo > tol:
        mid = (lo + hi) / 2
        p_exceed = (n - bisect.bisect_right(xs, mid)) / n
        if 1 - p_exceed / (1 - q) < 0:
            lo = mid
        else:
            hi = mid
    tau = (lo + hi) / 2
    cvar = tau + sum(max(x - tau, 0.0) for x in xs) / n / (1 - q)
    k = max(1, round(n * (1 - q)))
    return cvar, tau, sum(xs[-k:]) / k


async def _lag_monitor(stop, samples):
    while not stop.is_set():
        t = time.perf_counter()
        await asyncio.sleep(0.005)
        samples.append((time.perf_counter() - t - 0.005) * 1000)



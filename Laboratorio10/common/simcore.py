# nucleo comun de las dos poc: simulador, carga, metricas y entrenamiento
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
    p_slow_normal: float = 0.01
    p_slow_problem: float = 0.10
    slow_min_ms: float = 500.0
    slow_max_ms: float = 1500.0
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
        await asyncio.gather(*(self.backend.call(req, s, 0, 0) for s in range(1, N_SERVICES + 1)))
        return "ok"


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
        "outage_svc9": SimConfig(seed=seed, outage=(9, int(n * 0.30), int(n * 0.60))),
        "outage_long_svc9": SimConfig(seed=seed, outage=(9, int(n * 0.20), int(n * 0.85))),
        "drift_svc3": SimConfig(seed=seed, drift=(3, int(n * 0.30), int(n * 0.70)), drift_factor=2.5),
    }


SCENARIO_TITLES = {
    "tails": "1. Colas independientes",
    "outage_svc9": "2. Service 9 caido (30% central)",
    "outage_long_svc9": "3. Service 9 caido, prolongado (65%)",
    "drift_svc3": "4. Service 3 degradado x2.5 (40% central)",
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


async def _run_load(api, n, rps):
    lat, labels, lag, stop = [], [], [], asyncio.Event()
    mon = asyncio.create_task(_lag_monitor(stop, lag))

    async def one(i, sched):
        label = await api.handle(i)
        lat.append((time.perf_counter() - sched) * 1000)
        labels.append(label)

    t0 = time.perf_counter()
    tasks = []
    for i in range(n):
        sched = t0 + i / rps
        d = sched - time.perf_counter()
        if d > 0:
            await asyncio.sleep(d)
        tasks.append(asyncio.create_task(one(i, sched)))
    await asyncio.gather(*tasks)
    wall = time.perf_counter() - t0
    stop.set()
    await mon
    return lat, labels, wall, sorted(lag)


def summarize(api, be, lat, labels, wall, lag, n, q=0.99):
    s = sorted(lat)
    cv, _, direct = cvar_ru(lat, q)
    g = lambda a, d=0: getattr(api, a, d)
    ages = g("cache_ages", None)
    out = {
        "name": api.name, "requests": n, "backend_calls": be.calls,
        "extra_load_pct": round((be.calls / (n * N_SERVICES) - 1) * 100, 2),
        "p50_ms": round(pct(s, 50), 1), "p95_ms": round(pct(s, 95), 1), "p99_ms": round(pct(s, 99), 1),
        "p999_ms": round(pct(s, 99.9), 1), "max_ms": round(s[-1], 1),
        "cvar99_ms": round(cv, 1), "cvar99_direct_ms": round(direct, 1),
        "degraded_requests": labels.count("degraded"), "failed_requests": labels.count("failed"),
        "degraded_pct": round(labels.count("degraded") / n * 100, 2),
        "failed_pct": round(labels.count("failed") / n * 100, 2),
        "hedges": g("hedges"), "retries": g("retries"), "retries_denied": g("retries_denied"),
        "timeouts": g("timeouts"), "timeout_rate_pct": round(g("timeouts") / (n * N_SERVICES) * 100, 3),
        "breaker_short_circuits": g("breaker_short_circuits"), "failed_calls_GG": g("failed_calls"),
        "cache_served_calls": g("degraded"),
        "cache_age_max_s": None if ages is None else round(max(ages or [0]), 2),
        "wall_s": round(wall, 1), "loop_lag_p99_ms": round(pct(lag, 99), 2),
    }
    return out


def run_variant(factory, cfg, n, rps, q=0.99):
    api, be = factory(cfg)
    lat, labels, wall, lag = asyncio.run(_run_load(api, n, rps))
    return summarize(api, be, lat, labels, wall, lag, n, q), lat, api


def bisect_smallest_feasible(lo, hi, feasible, tol, label):
    trace = []
    while hi - lo > tol:
        mid = (lo + hi) / 2
        ok, info = feasible(mid)
        trace.append({label: round(mid, 2), "feasible": ok, **info})
        print(f"   {label}={mid:6.2f} -> {'ok ' if ok else 'NO '} {info}", flush=True)
        if ok:
            hi = mid
        else:
            lo = mid
    return hi, trace


# alpha: menor valor con carga extra <= presupuesto. beta: menor valor con timeouts <= presupuesto
# (en el escenario normal y en los de estres). los dos son busqueda binaria
def train_params(make_factory, load_budget=0.05, timeout_budget=0.005, safety=None, stress_cfgs=(),
                 beta_lo_margin_ms=5.0, n_cal=1000, rps_cal=500, q=0.99, seed=7):
    nominal = SimConfig(seed=seed)

    def cal(alpha, beta, cfg):
        return run_variant(make_factory(alpha, beta), cfg, n_cal, rps_cal, q)[0]

    def feas_alpha(a):
        r = cal(a, BETA_CAP_MS, nominal)
        return r["extra_load_pct"] / 100 <= load_budget, {"extra_load%": r["extra_load_pct"], "cvar99": r["cvar99_ms"]}

    alpha, tr_a = bisect_smallest_feasible(5.0, 60.0, feas_alpha, 1.0, "alpha")
    cfgs = [nominal] + list(stress_cfgs)

    def feas_beta(b):
        rs = [cal(alpha, b, c) for c in cfgs]
        ok = all(r["timeout_rate_pct"] / 100 <= timeout_budget for r in rs) and rs[0]["extra_load_pct"] / 100 <= load_budget
        return ok, {"timeouts%": [r["timeout_rate_pct"] for r in rs], "extra_load%": rs[0]["extra_load_pct"],
                    "cvar99": [r["cvar99_ms"] for r in rs]}

    beta_star, tr_b = bisect_smallest_feasible(alpha + beta_lo_margin_ms, BETA_CAP_MS, feas_beta, 2.0, "beta")
    beta = beta_star if safety is None else min(BETA_CAP_MS, beta_star * safety)
    print(f"   => alpha*={alpha:.1f} ms  beta*={beta_star:.1f} ms  beta usado={beta:.1f} ms")
    return {"alpha_ms": round(alpha, 1), "beta_star_ms": round(beta_star, 1), "beta_ms": round(beta, 1),
            "safety": safety, "stress": bool(stress_cfgs), "q": q, "load_budget": load_budget,
            "timeout_budget": timeout_budget, "trace_alpha": tr_a, "trace_beta": tr_b}


def run_experiment(variants, scenario, n, rps, seed, results_path, params):
    R = json.load(open(results_path)) if os.path.exists(results_path) else {"scenarios": {}}
    R["params"] = {"n": n, "rps": rps, "seed": seed, **params}
    R["labels"] = {k: v[0] for k, v in variants.items()}
    for sc, cfg in scenarios_for(scenario, n, seed).items():
        R["scenarios"][sc] = {}
        for key, (label, factory) in variants.items():
            res, lat, api = run_variant(factory, cfg, n, rps)
            res["latencies_ms"] = [round(x, 2) for x in lat]
            R["scenarios"][sc][key] = res
            print(f"[{sc:16s}] {key:9s} p50={res['p50_ms']:7.1f} p95={res['p95_ms']:7.1f} p99={res['p99_ms']:7.1f} "
                  f"cvar99={res['cvar99_ms']:7.1f} extra={res['extra_load_pct']:5.2f}% degr={res['degraded_pct']}% "
                  f"fail={res['failed_pct']}% maxage={res['cache_age_max_s']} lag={res['loop_lag_p99_ms']}", flush=True)
        json.dump(R, open(results_path, "w"))
    return R


def scenarios_for(which, n, seed):
    sc = scenarios(n, seed)
    return sc if which == "all" else {which: sc[which]}


COLORS = {"baseline": "#d1495b", "poc1": "#30638e", "poc2": "#2a9d8f", "B": "#edae49"}


def plot_results(R, kinds, out_png, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    scs = [s for s in SCENARIO_TITLES if s in R["scenarios"]]
    fig, ax = plt.subplots(len(scs), 2, figsize=(13, 3.6 * len(scs)), squeeze=False)
    for row, sc in enumerate(scs):
        S = R["scenarios"][sc]
        a = ax[row][0]
        for k in kinds:
            v = sorted(S[k]["latencies_ms"]); n = len(v)
            a.plot(v, [(i + 1) / n * 100 for i in range(n)], label=R["labels"][k], color=COLORS.get(k), lw=2)
        a.set_xscale("log"); a.set_ylim(90, 100.2); a.grid(alpha=.3)
        a.set_xlabel("Latencia por request (ms, log)"); a.set_ylabel("Percentil (%)")
        a.set_title(SCENARIO_TITLES[sc] + " - CDF (zoom a la cola)", fontsize=10)
        a.legend(loc="lower right", fontsize=8)
        b = ax[row][1]
        w = 0.8 / len(kinds)
        metrics = [("p50_ms", "p50"), ("p95_ms", "p95"), ("p99_ms", "p99"), ("cvar99_ms", "CVaR99")]
        for j, k in enumerate(kinds):
            xs = [i + (j - (len(kinds) - 1) / 2) * w for i in range(len(metrics))]
            vals = [S[k][m] for m, _ in metrics]
            b.bar(xs, vals, w, color=COLORS.get(k), label=R["labels"][k])
            for x, v in zip(xs, vals):
                b.text(x, v * 1.06, f"{v:.0f}", ha="center", fontsize=7)
        b.set_xticks(range(len(metrics))); b.set_xticklabels([l for _, l in metrics]); b.set_yscale("log")
        b.set_ylabel("ms (log)"); b.grid(alpha=.3, axis="y")
        b.set_title(SCENARIO_TITLES[sc] + " - percentiles y CVaR", fontsize=10)
    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(out_png, dpi=120)
    plt.close(fig)


def table_md(R, kinds, scenario):
    S = R["scenarios"][scenario]
    L = [f"| Metrica | " + " | ".join(R["labels"][k] for k in kinds) + " |", "|---|" + "---:|" * len(kinds)]

    def row(name, f):
        L.append(f"| {name} | " + " | ".join(f(S[k]) for k in kinds) + " |")
    row("p50 (ms)", lambda r: f"{r['p50_ms']}")
    row("p95 (ms)", lambda r: f"{r['p95_ms']}")
    row("p99 (ms)", lambda r: f"{r['p99_ms']}")
    row("CVaR99 (ms)", lambda r: f"{r['cvar99_ms']}")
    row("Requests ejecutadas", lambda r: f"{r['requests']}")
    row("Llamadas a backend", lambda r: f"{r['backend_calls']}")
    row("Carga extra", lambda r: f"{r['extra_load_pct']}%")
    row("Requests degradadas (dato de cache)", lambda r: f"{r['degraded_requests']} ({r['degraded_pct']}%)")
    row("Requests con llamada fallida (GG)", lambda r: f"{r['failed_requests']} ({r['failed_pct']}%)")
    row("Hedges / retries / timeouts", lambda r: f"{r['hedges']} / {r['retries']} / {r['timeouts']}")
    row("Antiguedad max. del dato de cache (s)", lambda r: "-" if r["cache_age_max_s"] is None else f"{r['cache_age_max_s']}")
    row("Lag p99 del event loop (ms)", lambda r: f"{r['loop_lag_p99_ms']}")
    return "\n".join(L)


def update_readme(path, md, name="RESULTS"):
    s = open(path).read()
    block = f"<!-- {name}:START -->\n{md}\n<!-- {name}:END -->"
    pat = re.compile(rf"<!-- {name}:START -->.*?<!-- {name}:END -->", re.S)
    assert pat.search(s), f"faltan marcadores {name} en {path}"
    open(path, "w").write(pat.sub(lambda m: block, s))

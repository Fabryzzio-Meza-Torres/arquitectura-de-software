"""Paired, repeated experiments. Every observation is retained, including noise."""
import asyncio
import hashlib
import json
import statistics
import time
from dataclasses import asdict

import simcore as sc
from improved_api import ImprovedAPI


def metric(values):
    if not values:
        return {"count": 0, "p50_ms": None, "p95_ms": None,
                "p99_ms": None, "cvar99_ms": None}
    xs = sorted(values)
    return {"count": len(xs), **{
        f"p{p}_ms": round(sc.pct(xs, p), 3) for p in (50, 95, 99)},
        "cvar99_ms": round(sc.cvar_ru(xs)[0], 3)}


def summarize(records):
    return {label: metric([r["latency_ms"] for r in records
                           if label == "all" or r["outcome"] == label])
            for label in ("all", "ok", "degraded", "failed")}


def fingerprint(cfg, n, backend_factory=sc.Backend):
    """Both variants start warm and use identical primary attempt-1 samples."""
    backend = backend_factory(cfg)
    backend.warm_up()
    digest = hashlib.sha256()
    for req in range(n):
        for svc in range(1, sc.N_SERVICES + 1):
            digest.update(backend.latency_ms(req, svc, 0, 1).hex().encode("ascii"))
    return digest.hexdigest()


async def load(api, n, rps):
    records, lag = [], []
    stop = asyncio.Event()
    monitor = asyncio.create_task(sc._lag_monitor(stop, lag))
    tasks = []

    async def one(req, scheduled):
        outcome = await api.handle(req)
        records.append({"request": req, "outcome": outcome,
                        "latency_ms": (time.perf_counter() - scheduled) * 1000})

    start = time.perf_counter()
    try:
        for req in range(n):
            scheduled = start + req / rps
            await asyncio.sleep(max(0.0, scheduled - time.perf_counter()))
            tasks.append(asyncio.create_task(one(req, scheduled)))
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        stop.set()
        await monitor
    return sorted(records, key=lambda r: r["request"]), lag, time.perf_counter() - start


def run_trial(kind, cfg, n, rps, alpha, beta, lag_limit, backend_factory=sc.Backend):
    backend = backend_factory(cfg)
    backend.warm_up()  # Equal cold-start condition; no warm-up mechanism redesign.
    api = sc.BaselineAPI(backend) if kind == "baseline" else ImprovedAPI(backend, alpha, beta)
    initial_cache_services = list(getattr(api, "initial_cache_services", ()))
    records, lag, wall = asyncio.run(load(api, n, rps))
    maximum = max(lag, default=0.0)
    return {
        "variant": kind, "config": asdict(cfg), "n": n, "rps": rps,
        "alpha_ms": None if kind == "baseline" else alpha,
        "beta_ms": None if kind == "baseline" else beta,
        "primary_samples_sha256": fingerprint(cfg, n, backend_factory),
        "measurement_valid": maximum <= lag_limit,
        "invalid_reason": None if maximum <= lag_limit else "event_loop_lag_exceeded",
        "lag_limit_ms": lag_limit, "loop_lag_max_ms": maximum,
        "loop_lag_p99_ms": sc.pct(sorted(lag), 99) if lag else 0.0,
        "wall_s": wall, "metrics": summarize(records),
        "backend_calls": backend.calls,
        "extra_load_pct": (backend.calls / (n * sc.N_SERVICES) - 1) * 100,
        "timeouts": getattr(api, "timeouts", 0),
        "backend_errors": getattr(api, "backend_errors", 0),
        "hedges": getattr(api, "hedges", 0), "retries": getattr(api, "retries", 0),
        "initial_cache_services": initial_cache_services,
        "cache_preload_policy": "three_random_services_per_seed" if kind != "baseline" else "none",
        "cache_age_max_s": max(getattr(api, "cache_ages", []), default=None),
        "records": records,
    }


def distribution(values):
    return {"count": len(values), "mean": statistics.mean(values),
            "min": min(values), "max": max(values),
            "sd": statistics.stdev(values) if len(values) > 1 else None}


def aggregate(pairs):
    """Descriptive spread of seed means; repeats are not independent seeds."""
    accepted = [p for p in pairs if p["paired_valid"]]
    result = {"pairs_total": len(pairs), "pairs_valid": len(accepted),
              "seeds_valid": sorted({p["seed"] for p in accepted}),
              "paired_p99_delta_ms": {}, "outcomes": {}}
    for kind in ("baseline", "poc3"):
        result["outcomes"][kind] = {}
        for label in ("all", "ok", "degraded", "failed"):
            result["outcomes"][kind][label] = {}
            for field in ("p50_ms", "p95_ms", "p99_ms", "cvar99_ms"):
                means = []
                for seed in result["seeds_valid"]:
                    vals = [p["trials"][kind]["metrics"][label][field]
                            for p in accepted if p["seed"] == seed]
                    vals = [v for v in vals if v is not None]
                    if vals:
                        means.append(statistics.mean(vals))
                result["outcomes"][kind][label][field] = distribution(means) if means else None
    for label in ("all", "ok", "degraded", "failed"):
        deltas = []
        for seed in result["seeds_valid"]:
            values = []
            for pair in accepted:
                if pair["seed"] != seed:
                    continue
                a = pair["trials"]["baseline"]["metrics"][label]["p99_ms"]
                b = pair["trials"]["poc3"]["metrics"][label]["p99_ms"]
                if a is not None and b is not None:
                    values.append(b - a)
            if values:
                deltas.append(statistics.mean(values))
        result["paired_p99_delta_ms"][label] = distribution(deltas) if deltas else None
    return result


def experiment(which, n, rps, seeds, repetitions, alpha, beta, lag_limit, output):
    result = {"schema": 1, "n": n, "rps": rps, "seeds": seeds,
              "repetitions": repetitions, "alpha_ms": alpha, "beta_ms": beta,
              "lag_limit_ms": lag_limit, "scenarios": {}}
    for name in sc.SCENARIO_TITLES:
        if which != "all" and name != which:
            continue
        pairs = []
        for seed_index, seed in enumerate(seeds):
            cfg = sc.scenarios(n, seed)[name]
            for repeat in range(repetitions):
                order = ("baseline", "poc3") if (seed_index + repeat) % 2 == 0 else ("poc3", "baseline")
                pair = {"seed": seed, "repeat": repeat, "order": order, "trials": {}}
                for kind in order:
                    trial = run_trial(kind, cfg, n, rps, alpha, beta, lag_limit)
                    pair["trials"][kind] = trial
                    print(f"{name} seed={seed} repeat={repeat} {kind}: "
                          f"p99={trial['metrics']['all']['p99_ms']} "
                          f"valid={trial['measurement_valid']}", flush=True)
                a, b = pair["trials"]["baseline"], pair["trials"]["poc3"]
                assert a["primary_samples_sha256"] == b["primary_samples_sha256"]
                pair["paired_valid"] = a["measurement_valid"] and b["measurement_valid"]
                pairs.append(pair)
                result["scenarios"][name] = {"pairs": pairs, "summary": aggregate(pairs)}
                output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def calibrate(n, rps, seeds, lag_limit, candidates=None):
    """Finite candidate evaluation; no monotonicity or global optimum claims."""
    candidates = candidates or [(18.0, 40.0), (24.0, 55.0), (32.0, 70.0)]
    trace = []
    for alpha, beta in candidates:
        trials = []
        for seed in seeds:
            for sigma in (0.35, 0.55):
                cfg = sc.SimConfig(seed=seed, base_sigma=sigma)
                trials.append(run_trial("poc3", cfg, n, rps, alpha, beta, lag_limit))
        valid = all(t["measurement_valid"] for t in trials)
        feasible = valid and all(
            t["extra_load_pct"] <= 5.0
            and t["timeouts"] / (n * sc.N_SERVICES) <= 0.005
            and t["metrics"]["failed"]["count"] / n <= 0.005
            and t["metrics"]["ok"]["count"] > 0 for t in trials)
        score = statistics.mean(t["metrics"]["ok"]["cvar99_ms"] for t in trials
                                if t["metrics"]["ok"]["count"]) if feasible else None
        trace.append({"alpha_ms": alpha, "beta_ms": beta, "feasible": feasible,
                      "mean_fresh_success_cvar99_ms": score, "trials": trials})
    feasible = [c for c in trace if c["feasible"]]
    winner = min(feasible, key=lambda c: c["mean_fresh_success_cvar99_ms"]) if feasible else None
    return {"status": "selected" if winner else "no_valid_feasible_candidate",
            "method": "finite_candidate_search", "seeds": seeds,
            "objective": "mean_CVaR99_of_fresh_successes_subject_to_constraints",
            "alpha_ms": winner["alpha_ms"] if winner else None,
            "beta_ms": winner["beta_ms"] if winner else None,
            "trace": trace}

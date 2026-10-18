"""Exactly two slow primary services, with three explicit total-request budgets."""
import ctypes
import hashlib
import json
import math
import platform
import random
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import simcore as sc
from experiment import metric, run_trial


@dataclass
class TwoSlowConfig(sc.SimConfig):
    slow_min_ms: float = 1000.0
    slow_max_ms: float = 1500.0
    cold_calls: int = 0
    primary_slow_count: int = 2
    replica_slow_probability: float = 0.01

    def __post_init__(self):
        if self.primary_slow_count != 2 or not 0 <= self.replica_slow_probability <= 1:
            raise ValueError("Exactly two slow primaries and a replica probability in [0, 1] are required")


class TwoSlowBackend(sc.Backend):
    """Exactly two of ten primaries are slow; independent replicas retain 1% tails."""
    def __init__(self, cfg):
        super().__init__(cfg)
        self._selected = {}

    def slow_services(self, req):
        if req not in self._selected:
            rng = random.Random(f"{self.cfg.seed}|two-slow-services|{req}")
            self._selected[req] = tuple(rng.sample(range(1, sc.N_SERVICES + 1), 2))
        return self._selected[req]

    def latency_ms(self, req, svc, replica, attempt):
        rng = sc._rng(self.cfg, req, svc, replica, attempt)
        healthy = min(50.0, rng.lognormvariate(math.log(self.cfg.base_median_ms), self.cfg.base_sigma))
        slow = svc in self.slow_services(req) if replica == 0 else rng.random() < self.cfg.replica_slow_probability
        return rng.uniform(self.cfg.slow_min_ms, self.cfg.slow_max_ms) if slow else healthy


@contextmanager
def timer_resolution():
    """Scope the Windows timer request to this benchmark and always release it."""
    metadata = {"requested_ms": None, "active": False}
    timer = None
    if sys.platform == "win32":
        timer = ctypes.WinDLL("winmm")
        metadata["requested_ms"] = 1
        metadata["begin_return_code"] = timer.timeBeginPeriod(1)
        metadata["active"] = metadata["begin_return_code"] == 0
    try:
        yield metadata
    finally:
        if timer is not None and metadata["active"]:
            metadata["end_return_code"] = timer.timeEndPeriod(1)


def allocation(total, seeds):
    if total <= 0 or len(set(seeds)) != len(seeds) or len(seeds) < 2:
        raise ValueError("Use a positive total and at least two distinct seeds")
    divisor = 2 * len(seeds)
    if total % divisor:
        raise ValueError(f"Total must be divisible by {divisor}: two variants and {len(seeds)} repetitions")
    return total // divisor


def summarize_level(pairs):
    clean = [p for p in pairs if p["paired_valid"]]
    summary = {"pairs_executed": len(pairs), "pairs_clean": len(clean), "variants": {}}
    for kind in ("baseline", "poc3"):
        all_trials = [pair["trials"][kind] for pair in pairs]
        valid_trials = [pair["trials"][kind] for pair in clean]
        raw_records = [r for trial in all_trials for r in trial["records"]]
        clean_records = [r for trial in valid_trials for r in trial["records"]]
        summary["variants"][kind] = {
            "executed": len(raw_records), "used_for_clean_latency": len(clean_records),
            "observed_latency": metric([r["latency_ms"] for r in raw_records]),
            "clean_latency": metric([r["latency_ms"] for r in clean_records]),
            "outcomes": {label: sum(r["outcome"] == label for r in raw_records)
                         for label in ("ok", "degraded", "failed")},
            "backend_calls": sum(trial["backend_calls"] for trial in all_trials),
            "max_loop_lag_ms": max(trial["loop_lag_max_ms"] for trial in all_trials),
            "p99_range_by_seed_ms": [min(t["metrics"]["all"]["p99_ms"] for t in all_trials),
                                     max(t["metrics"]["all"]["p99_ms"] for t in all_trials)],
            "clean_p99_by_seed_ms": [t["metrics"]["all"]["p99_ms"] for t in valid_trials],
        }
    return summary


def run_benchmark(here, totals, seeds, rps=250, lag_limit=20):
    if not totals or len(set(totals)) != len(totals):
        raise ValueError("Provide distinct total-request levels")
    if set(seeds) & {7, 11}:
        raise ValueError("Use evaluation seeds distinct from calibration seeds 7 and 11")
    for total in totals:
        allocation(total, seeds)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    base = here / "results/volumes"
    output = base / run_id
    output.mkdir(parents=True)
    manifest = {
        "schema": 2, "run_id": run_id, "status": "running", "totals": totals,
        "seeds": seeds, "rps": rps, "lag_limit_ms": lag_limit,
        "model": "exactly_two_random_slow_primaries_per_request",
        "cache_preload": {"count": 3, "selection": "random_once_per_seed_independent_of_slow_selection",
                          "cacheable_services": list(range(1, 11)), "usage": "fallback_after_unsuccessful_attempt",
                          "fresh_ttl_s": 1.0, "max_ttl_s": 5.0, "baseline_cache": False},
        "replica_assumption": "independent latency; 1% chance of a slow replica call",
        "primary_slow_ms": [1000, 1500], "healthy_ms": "lognormal median 10, capped at 50",
        "alpha_ms": 17.0, "beta_ms": 34.1,
        "parameter_source": "inherited_initial_values_with_existing_moving_median_adaptation",
        "environment": {"python": sys.version, "platform": platform.platform()}, "levels": [],
        "source_sha256": {name: hashlib.sha256((here / name).read_bytes()).hexdigest()
                          for name in ("volume_benchmark.py", "experiment.py", "improved_api.py", "simcore.py")},
    }
    snapshot = output / "executed_sources"
    snapshot.mkdir()
    for name in manifest["source_sha256"]:
        (snapshot / name).write_bytes((here / name).read_bytes())

    def checkpoint():
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with timer_resolution() as timer:
        manifest["timer_resolution"] = timer
        checkpoint()
        for total in totals:
            n = allocation(total, seeds)
            level = {"total_requested": total, "n_per_variant_per_seed": n, "pairs": []}
            level_file = f"level_{total}.json"
            for index, seed in enumerate(seeds):
                cfg = TwoSlowConfig(seed=seed)
                pair = {"seed": seed, "trials": {},
                        "order": ["baseline", "poc3"] if index % 2 == 0 else ["poc3", "baseline"]}
                for kind in pair["order"]:
                    trial = run_trial(kind, cfg, n, rps, 17.0, 34.1, lag_limit, TwoSlowBackend)
                    pair["trials"][kind] = trial
                    print(f"total={total} seed={seed} {kind} N={n} "
                          f"p99={trial['metrics']['all']['p99_ms']:.1f} "
                          f"lag_max={trial['loop_lag_max_ms']:.1f} valid={trial['measurement_valid']}", flush=True)
                a, b = pair["trials"]["baseline"], pair["trials"]["poc3"]
                assert a["primary_samples_sha256"] == b["primary_samples_sha256"]
                pair["paired_valid"] = a["measurement_valid"] and b["measurement_valid"]
                level["pairs"].append(pair)
                level["summary"] = summarize_level(level["pairs"])
                (output / level_file).write_text(json.dumps(level, indent=2), encoding="utf-8")
            executed = sum(v["executed"] for v in level["summary"]["variants"].values())
            assert executed == total
            manifest["levels"].append({"total": total, "file": level_file,
                                       "summary": level["summary"]})
            checkpoint()
    manifest["status"] = "complete"
    manifest["requests_executed"] = sum(totals)
    checkpoint()
    (base / "latest.json").write_text(json.dumps({"manifest": f"{run_id}/manifest.json"}), encoding="utf-8")
    return output


def create_volume_plots(here):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    base = here / "results/volumes"
    latest = json.loads((base / "latest.json").read_text(encoding="utf-8"))
    source = base / latest["manifest"]
    manifest = json.loads(source.read_text(encoding="utf-8"))
    if manifest["status"] != "complete":
        raise ValueError("The benchmark has not completed")
    output = source.parent / "presentation"
    output.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    rows = []
    for level in manifest["levels"]:
        summary, total = level["summary"], level["total"]
        use_clean = summary["pairs_clean"] > 0
        key = "clean_latency" if use_clean else "observed_latency"
        fig, ax = plt.subplots(figsize=(9, 5.2))
        for i, (kind, color, label) in enumerate((("baseline", "#747b87", "Baseline"),
                                                  ("poc3", "#16877b", "PoC3"))):
            variant = summary["variants"][kind]
            values = [variant[key][f"p{p}_ms"] for p in (50, 95, 99)]
            bars = ax.bar([x + (i - 0.5) * 0.34 for x in range(3)], values,
                          width=0.34, color=color, label=f"{label}: {variant['executed']:,} solicitudes",
                          hatch=None if use_clean else "//")
            ax.bar_label(bars, labels=[f"{v:.1f}" for v in values], padding=4)
            rows.append({"total": total, "variant": kind, **variant[key],
                         "latency_source": key,
                         "requests_executed": variant["executed"],
                         "failed_pct": 100 * variant["outcomes"]["failed"] / variant["executed"],
                         "extra_backend_load_pct": 100 * (variant["backend_calls"] / (variant["executed"] * 10) - 1)})
        ax.set_xticks(range(3), ["p50", "p95", "p99"])
        ax.set_ylabel("Tiempo de respuesta (ms) Â· menor es mejor")
        ax.set_title(f"{total:,} solicitudes totales Â· exactamente 2 servicios lentos", fontweight="bold", pad=18)
        ax.set_ylim(0, max(p.get_height() for p in ax.patches) * 1.3)
        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)
        ax.legend(loc="upper left", frameon=False)
        clean_text = (f"Latencias calculadas con {summary['pairs_clean']} de {summary['pairs_executed']} repeticiones sin ruido excesivo."
                      if use_clean else "Sin repeticiones limpias: valores observados con ruido; no prueban una mejora de rendimiento.")
        rates = {kind: 100 * summary["variants"][kind]["outcomes"]["failed"]
                 / summary["variants"][kind]["executed"] for kind in ("baseline", "poc3")}
        cached_pct = 100 * summary["variants"]["poc3"]["outcomes"]["degraded"] / summary["variants"]["poc3"]["executed"]
        used_count = summary["variants"]["poc3"][key]["count"]
        fig.text(0.5, 0.035,
                 f"{summary['pairs_executed']} repeticiones independientes; {manifest['rps']:g} solicitudes/s. "
                 "Dos servicios se eligen entre los diez en cada solicitud.\n" + clean_text +
                 f" Muestras por versiÃ³n: {used_count}.\n"
                 f"Fallos observados: baseline {rates['baseline']:.2f}% Â· PoC3 {rates['poc3']:.2f}%. "
                 f"PoC3 respondiÃ³ con cachÃ© en {cached_pct:.2f}% de las solicitudes.",
                 ha="center", fontsize=9)
        fig.tight_layout(rect=[0.02, 0.21, 0.98, 1])
        for extension in ("png", "svg"):
            fig.savefig(output / f"requests_{total}.{extension}", dpi=160, facecolor="white")
        plt.close(fig)
    lines = ["# Two-slow-service benchmark", "",
             "Exactly two random primary services per request take 1000â€“1500 ms. The other eight are fast. "
             "Independent replicas retain a 1% slow-call probability; hedging can therefore find a faster answer. "
             "This is a model assumption, not a guarantee for real shared failures.", "",
             "PoC3 starts each repetition with cached data for exactly three randomly selected services. "
             "Selection uses a separate seeded stream and does not depend on the two slow services. "
             "All ten services can refresh their cache after success; existing 1 s fresh/5 s maximum TTLs apply. "
             "Cache is a fallback after an unsuccessful attempt, not an unconditional immediate answer. "
             "Baseline has no cache. This preloaded state is simulated; no extra warm-up requests are generated.", "",
             "Totals include both variants and all five repetitions: 500/500, 5000/5000 and 25000/25000. "
             "The three levels total 61000 API requests. Backend fan-out/hedge calls are counted separately.", "",
             "| Total | Variant | p50 ms | p95 ms | p99 ms | Executed | Failed % (all runs) | Extra backend load % |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['total']} | {r['variant']} | {r['p50_ms']:.1f} | {r['p95_ms']:.1f} | "
                     f"{r['p99_ms']:.1f} | {r['requests_executed']} | {r['failed_pct']:.2f} | {r['extra_backend_load_pct']:.2f} |")
    lines += ["", "Latency uses complete clean pairs where available; otherwise hatched bars are descriptive noisy observations only. "
              "Raw repetitions, source fingerprints and measurement quality remain in each level JSON. "
              "Different total counts test sample-size stability at a fixed arrival rate; they are not a test of increasing RPS capacity.", "",
              "Five independent seeds supply repetition; a larger request count alone does not establish statistical significance. "
              "The per-seed p99 range and outcomes are retained in the manifest; no confidence or significance claim is made. "
              "Each repetition starts a fresh adaptive controller: short runs expose startup learning, while longer runs include more time after adaptation. "
              "Lower latency does not compensate for failed responses; interpret the failure percentage printed on each chart.", ""]
    for level in manifest["levels"]:
        lines += [f"![{level['total']} requests](requests_{level['total']}.png)", ""]
    lines += ["PoC1 has fixed thresholds; PoC2 adds adaptation and freshness controls; PoC3 retains that policy with corrected failures and measurement. "
              "Old PoC1/2 experiments did not force exactly two slow primaries and cannot be ranked against this new benchmark.", "",
              "Windows timer resolution is requested only during this benchmark and released afterward; "
              "see [Microsoft documentation](https://learn.microsoft.com/en-us/windows/win32/api/timeapi/nf-timeapi-timebeginperiod). "
              "The 20 ms lag limit remains unchanged."]
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "chart-data.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return output

"""PoC3 command line. All generated files stay under PoC3/results/."""
import argparse
import json
from pathlib import Path

import simcore as sc
from experiment import calibrate, experiment

HERE = Path(__file__).resolve().parent


def positive(value):
    value = float(value)
    if not 0 < value < float("inf"):
        raise argparse.ArgumentTypeError("must be finite and positive")
    return value


def positive_int(value):
    if not value.isdecimal() or int(value) < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return int(value)


def report(result):
    lines = ["# PoC3 results", "", "All trials retained; noisy pairs excluded from summaries.",
             "Seed means: descriptive spread, not a confidence interval.", ""]
    for name, scenario in result["scenarios"].items():
        summary = scenario["summary"]
        lines += [f"## {name}", "", f"Valid pairs: {summary['pairs_valid']}/{summary['pairs_total']}", "",
                  "| Seed/repeat | Variant | Valid | Outcome | N | % requests | p50 | p95 | p99 | CVaR99 |",
                  "|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
        for pair in scenario["pairs"]:
            for kind, trial in pair["trials"].items():
                for outcome, m in trial["metrics"].items():
                    fmt = lambda x: "—" if x is None else f"{x:.2f}"
                    lines.append(f"| {pair['seed']}/{pair['repeat']} | {kind} | "
                                 f"{trial['measurement_valid']} | {outcome} | {m['count']} | "
                                 f"{100 * m['count'] / trial['n']:.2f} | "
                                 + " | ".join(fmt(m[k]) for k in ("p50_ms", "p95_ms", "p99_ms", "cvar99_ms")) + " |")
        lines.append("")
        if not summary["pairs_valid"]:
            lines += ["No clean paired measurement; no performance conclusion.", ""]
        else:
            for outcome in ("all", "ok", "degraded", "failed"):
                spread = summary["paired_p99_delta_ms"][outcome]
                if spread:
                    lines += [f"Paired p99 delta (PoC3 − baseline), {outcome}: "
                              f"mean {spread['mean']:.2f} ms; seed range "
                              f"[{spread['min']:.2f}, {spread['max']:.2f}] ms; "
                              f"{spread['count']} seeds.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    cal = commands.add_parser("calibrate", aliases=["train"])
    exp = commands.add_parser("experiment")
    for command in (cal, exp):
        command.add_argument("--n", type=positive_int, default=1000 if command is cal else 4000)
        command.add_argument("--rps", type=positive, default=250)
        command.add_argument("--seeds", nargs="+", type=int, default=[7, 11] if command is cal else [42, 43, 44])
        command.add_argument("--max-lag-ms", type=positive, default=20)
    exp.add_argument("--scenario", choices=["all", *sc.SCENARIO_TITLES], default="all")
    exp.add_argument("--repetitions", type=positive_int, default=2)
    commands.add_parser("report")
    commands.add_parser("sequence")
    volume = commands.add_parser("benchmark")
    volume.add_argument("--totals", nargs="+", type=positive_int, default=[1000, 10000, 50000])
    volume.add_argument("--seeds", nargs="+", type=int, default=[101, 202, 303, 404, 505])
    volume.add_argument("--rps", type=positive, default=250)
    volume.add_argument("--max-lag-ms", type=positive, default=20)
    plots = commands.add_parser("plot")
    plots.add_argument("--advanced", action="store_true", help="historical and diagnostic plots")
    plots.add_argument("--legacy", action="store_true", help="previous occasional-tail presentation")
    args = parser.parse_args()
    if args.command == "sequence":
        from sequence_trace import create_sequence_sources
        print(create_sequence_sources(HERE))
        return 0
    if args.command == "benchmark":
        from volume_benchmark import run_benchmark, create_volume_plots
        print(run_benchmark(HERE, args.totals, args.seeds, args.rps, args.max_lag_ms))
        print(create_volume_plots(HERE))
        return 0
    if args.command == "plot":
        if args.advanced:
            from plot_results import create_plots
            print(create_plots(HERE))
        elif args.legacy or not (HERE / "results/volumes/latest.json").exists():
            from simple_plots import create_simple_plots
            print(create_simple_plots(HERE))
        else:
            from volume_benchmark import create_volume_plots
            print(create_volume_plots(HERE))
        return 0
    results = HERE / "results"
    results.mkdir(exist_ok=True)
    if args.command in ("train", "calibrate"):
        if len(set(args.seeds)) != len(args.seeds) or len(args.seeds) < 2:
            parser.error("calibration requires at least two distinct seeds")
        result = calibrate(args.n, args.rps, args.seeds, args.max_lag_ms)
        (results / "calibration.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(result["status"])
        return 0 if result["status"] == "selected" else 2
    if args.command == "experiment":
        if len(set(args.seeds)) != len(args.seeds) or len(args.seeds) < 2:
            parser.error("use at least two distinct evaluation seeds")
        path = results / "calibration.json"
        params = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
            "status": "inherited_from_poc2_not_recalibrated", "alpha_ms": 17.0, "beta_ms": 34.1, "seeds": [7]}
        if params["status"] == "no_valid_feasible_candidate":
            parser.error("calibration has no valid feasible candidate; inspect calibration.json")
        if set(params["seeds"]) & set(args.seeds):
            parser.error("evaluation seeds must differ from calibration seeds")
        result = experiment(args.scenario, args.n, args.rps, args.seeds, args.repetitions,
                            params["alpha_ms"], params["beta_ms"], args.max_lag_ms,
                            results / "results.json")
        result["parameter_source"] = {k: v for k, v in params.items() if k != "trace"}
        (results / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    else:
        result = json.loads((results / "results.json").read_text(encoding="utf-8"))
    (results / "report.md").write_text(report(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

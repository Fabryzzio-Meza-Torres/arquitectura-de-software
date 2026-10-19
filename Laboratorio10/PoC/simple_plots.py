"""The lab's four requested measures, presented without advanced plot notation."""
import hashlib
import json
from pathlib import Path

from experiment import metric


def lab_summary(result):
    pairs = result["scenarios"].get("tails", {}).get("pairs", [])
    accepted = [pair for pair in pairs if pair["paired_valid"]]
    if not accepted:
        raise ValueError("No clean baseline/proposal comparison in tails; rerun the experiment before plotting.")
    summary = {"scenario": "tails", "n_per_run": result["n"], "rps": result["rps"],
               "runs_executed_per_variant": len(pairs), "runs_used_per_variant": len(accepted),
               "variants": {}}
    for variant in ("baseline", "poc3"):
        trials = [pair["trials"][variant] for pair in accepted]
        records = [record for trial in trials for record in trial["records"]]
        measures = metric([record["latency_ms"] for record in records])
        summary["variants"][variant] = {
            "p50_ms": measures["p50_ms"], "p95_ms": measures["p95_ms"], "p99_ms": measures["p99_ms"],
            "requests_executed": sum(pair["trials"][variant]["n"] for pair in pairs),
            "latency_samples_used": len(records),
            "failed_in_used_samples": sum(r["outcome"] == "failed" for r in records),
            "degraded_in_used_samples": sum(r["outcome"] == "degraded" for r in records),
        }
    return summary


def create_simple_plots(here):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    source = here / "results/results.json"
    raw = source.read_bytes()
    summary = lab_summary(json.loads(raw.decode("utf-8")))
    summary["source_sha256"] = hashlib.sha256(raw).hexdigest()
    out = here / "results/presentation"
    out.mkdir(parents=True, exist_ok=True)
    colors = ["#6b7280", "#16877b"]
    names = ["Baseline\n(sin la estrategia)", "PoC3\n(con la estrategia)"]
    variants = [summary["variants"][k] for k in ("baseline", "poc3")]
    used = variants[0]["latency_samples_used"]
    executed = variants[0]["requests_executed"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})

    def save(fig, name):
        for extension in ("png", "svg"):
            fig.savefig(out / f"{name}.{extension}", dpi=160, facecolor="white")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, (variant, color, name) in enumerate(zip(variants, colors, names)):
        bars = ax.bar([x + (i - 0.5) * 0.34 for x in range(3)],
                      [variant[f"p{p}_ms"] for p in (50, 95, 99)],
                      width=0.34, color=color, label=name.replace("\n", " "))
        ax.bar_label(bars, labels=[f"{variant[f'p{p}_ms']:.1f}" for p in (50, 95, 99)], padding=4)
    ax.set_xticks(range(3), ["p50", "p95", "p99"])
    ax.set_ylabel("Tiempo de respuesta (ms) · menor es mejor")
    ax.set_title("Baseline frente a PoC3: tiempos de respuesta", pad=18, fontweight="bold")
    ax.set_ylim(0, max(v[f"p{p}_ms"] for v in variants for p in (50, 95, 99)) * 1.22)
    ax.grid(axis="y", alpha=0.15)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=False)
    fig.text(0.5, 0.045,
             f"Prueba habitual: 10 servicios con demoras ocasionales. {used} mediciones utilizadas por versión.\n"
             f"Se agrupan {summary['runs_used_per_variant']} corridas sin ruido excesivo, "
             f"de {summary['n_per_run']} solicitudes a {summary['rps']:g} solicitudes/s cada una.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=[0.02, 0.15, 0.98, 1])
    save(fig, "01_lab_latency")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(names, [v["requests_executed"] for v in variants], color=colors, width=0.48)
    ax.bar_label(bars, labels=[str(v["requests_executed"]) for v in variants], padding=5)
    ax.set_ylabel("Número de solicitudes")
    ax.set_title("Solicitudes ejecutadas en la prueba habitual", pad=18, fontweight="bold")
    ax.set_ylim(0, max(v["requests_executed"] for v in variants) * 1.2)
    ax.grid(axis="y", alpha=0.15)
    ax.set_axisbelow(True)
    fig.text(0.5, 0.035,
             f"Se ejecutaron {executed} solicitudes por versión. Los tiempos del gráfico 1 usan {used} mediciones por versión;\n"
             "las demás se conservan, pero no se usan por el ruido del equipo durante su medición.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=[0.02, 0.14, 0.98, 1])
    save(fig, "02_lab_requests")

    b, p = variants
    lines = ["# Lab presentation", "", "Baseline: parallel calls without the proposed strategy. "
             "PoC3: the same simulation with the strategy enabled.", "",
             "| Required measure | Baseline | PoC3 |", "|---|---:|---:|"]
    for percentile in (50, 95, 99):
        key = f"p{percentile}_ms"
        lines.append(f"| p{percentile} (ms) | {b[key]:.1f} | {p[key]:.1f} |")
    lines += [f"| Requests executed | {b['requests_executed']} | {p['requests_executed']} |", "",
              f"Latency percentiles pool {used} usable measurements per version. "
              f"All {executed} executed requests per version remain recorded; measurements affected by excessive machine noise are excluded from latency calculations. "
              "These pooled percentiles differ slightly from the advanced report's mean of per-seed percentiles.", "",
              "![Latency](01_lab_latency.png)", "", "![Requests](02_lab_requests.png)", "",
              "p50/p95/p99: time within which 50%/95%/99% of requests finish. "
              "A lower p99 means shorter waits for the slowest part of the experience.", "",
              f"Failed responses among the latency samples: baseline {b['failed_in_used_samples']}; "
              f"PoC3 {p['failed_in_used_samples']}. Cached responses in PoC3: {p['degraded_in_used_samples']}.", "",
              "## What the five scenarios test", "", "| Scenario | What changes | What it checks |",
              "|---|---|---|",
              "| Usual case (`tails`) | Ten services, each with 1% slow calls around one second; otherwise typically 10 ms. | Reduction of occasional long waits; the core lab demonstration. |",
              "| Stress (`tails_heavy`) | Services 8–10 have 10% slow calls; slow delays range from 0.5 to 1.5 s. | Behavior when slow responses become more frequent. |",
              "| Short S9 outage (`outage_svc9`) | Both S9 replicas take 2 s during the middle 30% of the workload. | Breaker, fallback and recovery during a temporary problem. |",
              "| Longer S9 outage (`outage_long_svc9`) | The same problem lasts for 65% of the workload. | Behavior as cached data ages. The workload must last long enough to exceed the 5 s cache TTL. |",
              "| S3 degradation (`drift_svc3`) | S3's typical latency becomes 2.5 times larger during 40% of the workload. | Whether adaptive thresholds respond to a slower service without a complete outage. |", "",
              "The lab requires a baseline/proposal comparison; it does not require all five scenarios. "
              "The other scenarios add resilience evidence. Unit tests check code correctness and are different from these performance scenarios.", "",
              "PoC1 uses fixed thresholds and unbounded-age cache; PoC2 adds adaptive thresholds and freshness controls; "
              "PoC3 keeps PoC2's policy and corrects error handling and measurement. "
              "Historical PoC1/2 runs use different workloads, so this presentation does not rank the versions.", "",
              "Decision: GO WITH CHANGES. The saved usual-case comparison supports tail reduction; "
              "remaining noisy scenarios do not support firm performance conclusions."]
    (out / "lab-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "lab-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out

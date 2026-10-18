"""Small, paired diagnostic charts with response quality and eligibility visible."""
import json
from pathlib import Path

from experiment import metric
from mechanism_study import VARIANTS, LABELS, phase


def paired_trials(result, scenario, variant):
    full = {t["seed"]: t for t in result["trials"] if t["scenario"] == scenario and t["variant"] == "full"}
    pairs = [(full[t["seed"]], t) for t in result["trials"]
             if t["scenario"] == scenario and t["variant"] == variant]
    valid = [(a, b) for a, b in pairs if a["measurement_valid"] and b["measurement_valid"]]
    return valid or pairs, len(valid), len(pairs)


def create_mechanism_plots(here):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    base = here / "results/mechanisms"
    source = base / json.loads((base / "latest.json").read_text(encoding="utf-8"))["results"]
    result = json.loads(source.read_text(encoding="utf-8"))
    if result["status"] != "complete":
        raise ValueError("Diagnostic run is incomplete")
    output = source.parent / "presentation"
    output.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    colors = ("#16877b", "#cf8747")
    def save(fig, name):
        for ext in ("png", "svg"):
            fig.savefig(output / f"{name}.{ext}", dpi=160, facecolor="white")
        plt.close(fig)

    comparisons = []
    fig, ax = plt.subplots(figsize=(11, 7))
    for index, variant in enumerate(VARIANTS[1:]):
        pairs, clean, total = paired_trials(result, "random_two", variant)
        row = {"variant": variant, "clean_pairs": clean, "pairs": total,
               "seeds_used": [a["seed"] for a, _ in pairs], "latency": []}
        for side in (0, 1):
            records = [r for pair in pairs for r in pair[side]["records"]]
            m = metric([r["latency_ms"] for r in records])
            row["latency"].append(m)
            bars = ax.barh(index + (side - .5) * .32, m["p95_ms"], height=.32,
                           color=colors[side], hatch=None if clean else "//",
                           label=("PoC3 completo" if side == 0 else "Mecanismo desactivado") if index == 0 else None)
            ax.bar_label(bars, labels=[f"{m['p95_ms']:.1f}"], padding=4, fontsize=10)
        comparisons.append(row)
    ax.set_yticks(range(len(comparisons)),
                  [f"{LABELS[r['variant']]} ({r['clean_pairs']}/{r['pairs']} validas)" for r in comparisons])
    ax.invert_yaxis()
    ax.set_xlabel("Latencia p95 de la API (ms) - menor es mejor")
    ax.set_title("Efecto de cada mecanismo: desactivar uno a la vez", fontweight="bold", pad=16)
    ax.set_xlim(0, max(p.get_width() for p in ax.patches) * 1.2)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="x", alpha=.15)
    ax.set_axisbelow(True)
    fig.text(.5, .025, "Dos servicios aleatorios lentos por solicitud; 3 precargados. Cada fila usa las mismas semillas en ambas barras.\n"
             "p95 incluye todos los resultados de las parejas seleccionadas; interpretar junto con fallos y cache.\n"
             "Estudio pequeno de mecanismos, separado del benchmark de 61 000 solicitudes; no prueba significancia estadistica.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=[.01, .12, .99, 1])
    save(fig, "component_latency")

    fig, ax = plt.subplots(figsize=(10, 6))
    quality = []
    for index, variant in enumerate(VARIANTS):
        records = [r for t in result["trials"] if t["scenario"] == "random_two" and t["variant"] == variant
                   for r in t["records"]]
        counts = {label: sum(r["outcome"] == label for r in records) for label in ("ok", "degraded", "failed")}
        quality.append({"variant": variant, "executed": len(records), "outcomes": counts})
        left = 0
        for label, color, title in (("ok", "#16877b", "Dato del servicio"),
                                    ("degraded", "#d6aa45", "Dato de cache"), ("failed", "#c35b60", "Sin respuesta valida")):
            value = 100 * counts[label] / len(records)
            ax.barh(index, value, left=left, color=color, label=title if index == 0 else None)
            if value >= 4:
                ax.text(left + value / 2, index, f"{value:.1f}%", ha="center", va="center", fontsize=10)
            left += value
    ax.set_yticks(range(len(VARIANTS)), [LABELS[v] for v in VARIANTS])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Porcentaje de solicitudes de la API")
    ax.set_title("Una respuesta rapida tambien debe ser util", fontweight="bold", pad=16)
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.12), ncol=3, frameon=False, fontsize=9)
    fig.text(.5, .02, f"Todas las ejecuciones, incluidas las ruidosas: {quality[0]['executed']} solicitudes por variante. "
             "Cache no se cuenta como dato nuevo del servicio.", ha="center", fontsize=9)
    fig.tight_layout(rect=[.01, .06, .99, 1])
    save(fig, "component_quality")

    pairs, clean, total = paired_trials(result, "persistent_two", "no_breaker")
    fig, ax = plt.subplots(figsize=(9, 5.6))
    phases = ("healthy", "persistent_delay", "recovery")
    phase_data = []
    for side in (0, 1):
        values = []
        for name in phases:
            records = [r for pair in pairs for r in pair[side]["records"] if phase(r["request"]) == name]
            values.append(metric([r["latency_ms"] for r in records])["p95_ms"])
        phase_data.append(values)
        bars = ax.bar([i + (side - .5) * .34 for i in range(3)], values, width=.34, color=colors[side],
                      hatch=None if clean else "//", label="Con circuit breaker" if side == 0 else "Sin circuit breaker")
        ax.bar_label(bars, labels=[f"{v:.1f}" for v in values], padding=4)
    ax.set_xticks(range(3), ["Antes de la demora", "Demora persistente", "Recuperacion"])
    ax.set_ylabel("Latencia p95 de la API (ms)")
    ax.set_title("Circuit breaker: efecto durante una demora persistente", fontweight="bold", pad=18)
    ax.set_ylim(0, max(max(v) for v in phase_data) * 1.3)
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=.15)
    ax.set_axisbelow(True)
    skipped = sum(a["counters"]["breaker_short_circuits"] for a, _ in pairs)
    fig.text(.5, .025, f"Diagnostico separado: los mismos 2 servicios y ambas replicas demoran durante la fase central.\n"
             f"{clean}/{total} parejas validas; {skipped} consultas a servicios omitidas por el circuito. Cache vigente disponible.\n"
             "La API sigue esperando a los otros 8 servicios; circuito abierto no significa latencia total cero.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=[.01, .16, .99, 1])
    save(fig, "circuit_breaker_latency")

    # Compare matching service calls that the enabled breaker rejected at entry.
    service_pairs = []
    for enabled, disabled in pairs:
        first = {}
        for e in enabled["events"]:
            if e["event"] == "breaker_decision":
                first.setdefault((e["req"], e["svc"]), e)
        a = {(r["request"], r["svc"]): r for r in enabled["service_records"]}
        b = {(r["request"], r["svc"]): r for r in disabled["service_records"]}
        for key, e in first.items():
            if not e["allowed"] and e["state"] == "open" and phase(key[0]) == "persistent_delay":
                service_pairs.append({"seed": enabled["seed"], "request": key[0], "svc": key[1],
                                      "with_breaker": a[key], "without_breaker": b[key]})
    service_metrics = {key: metric([p[key]["latency_ms"] for p in service_pairs])
                       for key in ("with_breaker", "without_breaker")}
    phase_summary = {"clean_pairs": clean, "pairs": total, "phase_p95_ms": phase_data,
                     "skipped_calls": skipped, "matching_open_service_calls": len(service_pairs),
                     "matching_service_latency": service_metrics}
    data = {"api_p95_comparisons": comparisons, "quality_all_runs": quality,
            "circuit_breaker": phase_summary}
    representative = pairs[0][0]
    svc = representative["fault_services"][0]
    events = [e for e in representative["events"] if e.get("svc") == svc]
    opened = next(e for e in events if e["event"] == "breaker_failure" and e["before"] == "closed" and e["state"] == "open")
    probe = next(e for e in events if e["event"] == "breaker_decision" and e["state"] == "half_open" and e["allowed"])
    recovered = next(e for e in events if e["event"] == "breaker_success" and e["before"] == "half_open" and e["state"] == "closed")
    omitted = sum(e["event"] == "breaker_decision" and not e["allowed"] for e in events)
    lifecycle = f'''flowchart LR
    C["Cerrado: permite consultar"]
    A["Abierto: responde con cache vigente"]
    H["Semiabierto: permite una prueba"]
    C -->|"5 intentos fallidos: t={opened['ms']/1000:.2f} s"| A
    A -->|"Espera minima 1 s: prueba t={probe['ms']/1000:.2f} s"| H
    H -->|"Si sigue fallando, abre otro segundo"| A
    H -->|"Respuesta valida: cierra t={recovered['ms']/1000:.2f} s"| C
'''
    (output / "circuit_breaker_states.mmd").write_text(lifecycle, encoding="utf-8")
    data["lifecycle_example"] = {"seed": representative["seed"], "svc": svc,
                                 "opened_ms": opened["ms"], "probe_ms": probe["ms"],
                                 "recovered_ms": recovered["ms"], "omitted_calls": omitted}
    (output / "chart-data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    lines = ["# Mechanism measurements", "",
             f"Separate diagnostic study: {result['requests_executed']} API requests; three seeds, {result['rps']} requests/s. "
             "The official 61000-request results are unchanged. This small study does not establish statistical significance.", "",
             "Each disabled component is compared with the full policy using identical primary samples and the same eligible seeds. "
             "If no clean pairs exist, values are noisy observations. Response outcomes retain every run.", "",
             "| Mechanism disabled | Full p95 ms | Disabled p95 ms | Clean pairs |",
             "|---|---:|---:|---:|"]
    for row in comparisons:
        lines.append(f"| {row['variant']} | {row['latency'][0]['p95_ms']:.2f} | {row['latency'][1]['p95_ms']:.2f} | {row['clean_pairs']}/{row['pairs']} |")
    lines += ["", "| Variant | Requests (all runs) | Service response | Cached response | Failed |",
              "|---|---:|---:|---:|---:|"]
    for row in quality:
        c = row["outcomes"]
        lines.append(f"| {row['variant']} | {row['executed']} | {c['ok']} | {c['degraded']} | {c['failed']} |")
    random_full = [t for t in result["trials"] if t["scenario"] == "random_two" and t["variant"] == "full"]
    normal_skips = sum(t["counters"]["breaker_short_circuits"] for t in random_full)
    persistent_full = [t for t in result["trials"] if t["scenario"] == "persistent_two" and t["variant"] == "full"]
    normal_events = [e for t in random_full for e in t["events"]]
    attempts = [e for e in normal_events if e["event"] == "attempt_start"]
    hits = [e for e in normal_events if e["event"] == "cache_hit"]
    recovery = [e for t in persistent_full for e in t["events"]
                if e["event"] == "breaker_success" and e["before"] == "half_open" and e["state"] == "closed"]
    lines += ["", f"Circuit breaker: {normal_skips} skipped service calls in the full ordinary workload; "
              "when it does not activate, latency differences against its disabled variant are execution variation, not demonstrated savings. "
              f"The separate persistent-delay scenario skipped {skipped} service calls in eligible pairs and recorded "
              f"{len(recovery)} successful half-open-to-closed transitions across all seeds.", "",
              f"The state diagram uses a single measured example (seed {representative['seed']}, service {svc}): "
              f"first opening at {opened['ms']/1000:.2f} s, first recovery probe at {probe['ms']/1000:.2f} s, "
              f"successful closing at {recovered['ms']/1000:.2f} s; {omitted} calls omitted. "
              "The grouping of services in sequence diagrams is visual: each service still has its own breaker.", "",
              f"Persistent-delay API p95: {phase_data[0][1]:.2f} ms with breaker versus {phase_data[1][1]:.2f} ms without. "
              f"For {len(service_pairs)} matching service calls rejected at entry, median service latency was "
              f"{service_metrics['with_breaker']['p50_ms']:.3f} versus {service_metrics['without_breaker']['p50_ms']:.3f} ms. "
              "These are conditional service timings, not whole-API timings or a guarantee for every outage.", "",
              "| Mechanism | Observation and interpretation |", "|---|---|",
              "| Hedging / replicas | Compare no_hedging with full AND the cache percentage: low latency can come from cached fallback rather than fresh service responses. |",
              "| Cache / TTL | Compare no_cache; every cache hit records age and fresh/stale tier. Expired data is not served. |",
              "| Three-service preload | Compare no_preload: only initial cached entries are removed; successful calls can still populate caches. The effect is mainly startup-dependent. |",
              "| Retries / backoff / budget | Compare no_retries as a combined retry policy. Attempt events record elapsed times and budget decisions; this does not isolate backoff or budget individually. |",
              "| Adaptive alpha/beta | Compare fixed_thresholds with full; 200 requests per repetition are a short learning window, not proof that fixed values are better in general. |",
              "| Parallel fan-out / cancellation | The diagram groups two slow services and eight others. API latency follows the last required result, and pending work is cancelled; timings are not added across parallel calls. |", "",
              f"Observed full-policy thresholds in the ordinary workload: alpha {min(e['alpha_ms'] for e in attempts):.2f}–"
              f"{max(e['alpha_ms'] for e in attempts):.2f} ms; beta {min(e['beta_ms'] for e in attempts):.2f}–"
              f"{max(e['beta_ms'] for e in attempts):.2f} ms. Maximum cache age served: "
              f"{max((e['age_s'] for e in hits), default=0):.3f} s.", "",
              "Raw per-request/per-service records, circuit decisions, cache ages, retries and cancellation events are retained in results.json.", "",
              "![Component latency](component_latency.png)", "", "![Response quality](component_quality.png)", "",
              "![Circuit breaker](circuit_breaker_latency.png)", "", "![Circuit states](circuit_breaker_states.png)"]
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(create_mechanism_plots(Path(__file__).resolve().parent))

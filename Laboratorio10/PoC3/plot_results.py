"""Read-only visualization of saved experiments; never merge incompatible runs."""
import hashlib
import json
from pathlib import Path

SCENARIOS = {
    "tails": "Nominal",
    "tails_heavy": "Estrés",
    "outage_svc9": "Caída de S9 (30%)",
    "outage_long_svc9": "Caída de S9 (65%)",
    "drift_svc3": "Degradación de S3",
}
COLORS = {"PoC1": "#3b6b9a", "PoC2": "#d98b25", "PoC3": "#17877d"}
FILES = ("01_historical_comparison", "02_poc3_paired_evidence", "03_outcomes_and_freshness")


def read_sources(here):
    paths = {"PoC1": here.parent / "poc1_diagrama/results/results.json",
             "PoC2": here.parent / "poc2_mejorada/results/results.json",
             "PoC3": here / "results/results.json",
             "PoC3-long": here / "results/long-outage-validation.json"}
    data, provenance = {}, {}
    for name, path in paths.items():
        if not path.exists():
            if name == "PoC3":
                raise FileNotFoundError("Run an experiment before plotting: results/results.json is missing")
            continue
        raw = path.read_bytes()
        data[name] = json.loads(raw.decode("utf-8"))
        provenance[name] = {"path": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest()}
    return data, provenance


def historical_points(sources, scenario):
    points = []
    for name, key in (("PoC1", "poc1"), ("PoC2", "poc2")):
        source = sources.get(name)
        if not source or scenario not in source["scenarios"]:
            continue
        entries = source["scenarios"][scenario]
        trial = entries[key]
        # Apply the same pair rule retrospectively; old files did not flag it.
        clean = all(entries[k]["loop_lag_max_ms"] <= 20 for k in ("baseline", key))
        points.append({"poc": name, "valid_pair": clean, "seed": source["params"]["seed"],
                       "repeat": 0, "metrics": {f"p{p}_ms": trial[f"p{p}_ms"] for p in (50, 95, 99)}})
    entry = sources["PoC3"]["scenarios"].get(scenario)
    if entry:
        for pair in entry["pairs"]:
            points.append({"poc": "PoC3", "valid_pair": pair["paired_valid"],
                           "seed": pair["seed"], "repeat": pair["repeat"],
                           "metrics": pair["trials"]["poc3"]["metrics"]["all"]})
    return points


def accepted_records(source, scenario, kind):
    return [record for pair in source["scenarios"].get(scenario, {}).get("pairs", [])
            if pair["paired_valid"] for record in pair["trials"][kind]["records"]]


def outcome_rows(sources):
    rows = []
    scenario = "outage_long_svc9"
    for name, key in (("PoC1", "poc1"), ("PoC2", "poc2")):
        source = sources.get(name)
        if not source or scenario not in source["scenarios"]:
            continue
        trial = source["scenarios"][scenario][key]
        n = trial["requests"]
        rows.append({"name": name, "n": n,
                     "duration_s": source["params"]["n"] / source["params"]["rps"],
                     "ok": 100 * (n - trial["degraded_requests"] - trial["failed_requests"]) / n,
                     "degraded": 100 * trial["degraded_requests"] / n,
                     "failed": 100 * trial["failed_requests"] / n,
                     "age": trial["cache_age_max_s"]})
    for key, label in (("PoC3", "PoC3 · principal"), ("PoC3-long", "PoC3 · extendida")):
        source = sources.get(key)
        if not source or scenario not in source["scenarios"]:
            continue
        trials = [p["trials"]["poc3"] for p in source["scenarios"][scenario]["pairs"]]
        n = sum(t["n"] for t in trials)
        ages = [t["cache_age_max_s"] for t in trials if t["cache_age_max_s"] is not None]
        rows.append({"name": label, "n": n, "duration_s": source["n"] / source["rps"],
                     **{status: 100 * sum(t["metrics"][status]["count"] for t in trials) / n
                        for status in ("ok", "degraded", "failed")},
                     "age": max(ages) if ages else None})
    return rows


def create_plots(here):
    # Keep simulation and tests standard-library only; plotting is optional.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import ScalarFormatter

    sources, provenance = read_sources(here)
    result = sources["PoC3"]
    out = here / "results/plots"
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "figure.facecolor": "white"})

    def save(fig, name):
        fig.savefig(out / f"{name}.png", dpi=160, facecolor="white")
        fig.savefig(out / f"{name}.svg", facecolor="white")
        plt.close(fig)

    names = [s for s in SCENARIOS if historical_points(sources, s)]
    fig, axes = plt.subplots(1, 3, figsize=(14, 6), sharey=True)
    offsets = {"PoC1": -0.24, "PoC2": 0, "PoC3": 0.24}
    markers = {"PoC1": "s", "PoC2": "D", "PoC3": "o"}
    for ax, p in zip(axes, (50, 95, 99)):
        for y, scenario in enumerate(names):
            points = historical_points(sources, scenario)
            for i, point in enumerate(points):
                name = point["poc"]
                jitter = (i - 3) * 0.035 if name == "PoC3" else 0
                ax.scatter(point["metrics"][f"p{p}_ms"], y + offsets[name] + jitter,
                           s=55, marker=markers[name], edgecolor=COLORS[name],
                           facecolor=COLORS[name] if point["valid_pair"] else "none", linewidth=1.6)
        ax.set_title(f"p{p} · todas las respuestas")
        ax.set_xlabel("Latencia registrada (ms)")
        ax.set_xlim(left=0)
        ax.grid(axis="x", alpha=0.18)
        ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(names)), [SCENARIOS[s] for s in names])
    axes[0].invert_yaxis()
    handles = [Line2D([], [], marker=markers[k], color=COLORS[k], linestyle="none", label=k)
               for k in COLORS]
    handles += [Line2D([], [], marker="o", color="#444", linestyle="none", label="Par dentro del límite de ruido"),
                Line2D([], [], marker="o", color="#444", markerfacecolor="none", linestyle="none", label="Par con ruido: descriptivo")]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.56, 0.04))
    fig.suptitle("Comparación histórica: condiciones distintas, sin ranking de velocidad", fontsize=15, x=0.54, y=0.98)
    old_configs = []
    for name in ("PoC1", "PoC2"):
        if name in sources:
            p = sources[name]["params"]
            old_configs.append(f"{name}: N={p['n']}, {p['rps']} rps")
    fig.text(0.54, 0.91, "; ".join(old_configs) +
             f" | PoC3: N={result['n']}, {result['rps']:g} rps por corrida", ha="center", fontsize=10)
    fig.text(0.54, 0.01, "Cada punto es una corrida. PoC3 exige validez de ambos miembros del par; no se mezclan sus muestras.",
             ha="center", fontsize=9, color="#555")
    fig.subplots_adjust(left=0.16, right=0.98, top=0.83, bottom=0.24, wspace=0.12)
    save(fig, FILES[0])

    fig, (left, right) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1, 1.15]})
    for kind, label, color in (("baseline", "Baseline", "#a33b4a"), ("poc3", "PoC3", COLORS["PoC3"])):
        values = sorted(r["latency_ms"] for r in accepted_records(result, "tails", kind))
        if values:
            left.step(values, [(i + 1) / len(values) * 100 for i in range(len(values))],
                      where="post", color=color, label=f"{label} · {len(values)} respuestas", linewidth=2)
    if left.lines:
        left.set_xscale("log")
        left.xaxis.set_major_formatter(ScalarFormatter())
        left.legend(loc="lower right", fontsize=9)
    else:
        left.text(0.5, 0.5, "Sin pares válidos en el escenario nominal", ha="center", transform=left.transAxes)
    left.set_ylim(85, 100.5)
    left.axhline(99, color="#aaa", linestyle=":")
    left.set_title("Nominal: distribución acumulada de la cola")
    left.set_xlabel("Latencia (ms, escala logarítmica)")
    left.set_ylabel("Respuestas acumuladas (%)")
    left.grid(alpha=0.15)
    entries = [s for s in SCENARIOS if s in result["scenarios"]]
    for i, scenario in enumerate(entries):
        summary = result["scenarios"][scenario]["summary"]
        spread = summary["paired_p99_delta_ms"]["all"]
        if spread:
            mean = spread["mean"]
            right.errorbar(mean, i, xerr=[[mean - spread["min"]], [spread["max"] - mean]],
                           fmt="o", color=COLORS["PoC3"], capsize=5)
            right.annotate(f"{mean:.0f} ms · {summary['pairs_valid']}/{summary['pairs_total']} pares",
                           (mean, i), xytext=(12, 12), textcoords="offset points", ha="left", fontsize=9)
        else:
            right.text(0.97, i, f"0/{summary['pairs_total']} pares válidos",
                       transform=right.get_yaxis_transform(), ha="right", va="center", color="#777")
    right.set_yticks(range(len(entries)), [SCENARIOS[s] for s in entries])
    right.set_ylim(len(entries) - 0.45, -0.6)
    right.axvline(0, color="#aaa", linestyle=":")
    right.set_title("Cambio de p99 frente a su propio baseline", pad=18)
    right.set_xlabel("PoC3 − baseline (ms); negativo = menor latencia")
    right.grid(axis="x", alpha=0.15)
    fig.suptitle("Evidencia pareada de PoC3: solo pares válidos", fontsize=15)
    fig.text(0.5, 0.025, "Izquierda: ECDF de respuestas agrupadas. Derecha: media y rango de medias por semilla; no es intervalo de confianza.\n"
             "Las latencias incluyen todos los desenlaces; el gráfico 3 separa su calidad.", ha="center", fontsize=9)
    fig.tight_layout(rect=[0.01, 0.11, 0.99, 0.92], w_pad=3)
    save(fig, FILES[1])

    rows = outcome_rows(sources)
    fig, (left, right) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1.65, 1]})
    labels = [f"{r['name']}\n{r['duration_s']:g} s por corrida" for r in rows]
    bottom = [0.0] * len(rows)
    for status, label, color in (("ok", "Éxito fresco", "#17877d"),
                                 ("degraded", "Dato de caché", "#e6ad42"),
                                 ("failed", "Fallo sin dato", "#bb4654")):
        vals = [r[status] for r in rows]
        left.bar(range(len(rows)), vals, bottom=bottom, color=color, label=label, width=0.65)
        for i, value in enumerate(vals):
            if value >= 5:
                left.text(i, bottom[i] + value / 2, f"{value:.1f}%", ha="center", va="center", fontsize=10)
            bottom[i] += value
    left.set_xticks(range(len(rows)), labels)
    left.set_ylim(0, 105)
    left.set_ylabel("Solicitudes observadas (%)")
    left.set_title("Desenlace durante la caída prolongada")
    left.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.27), fontsize=9, frameon=False)
    right.bar(range(len(rows)), [r["age"] or 0 for r in rows], color=[COLORS.get(r["name"], COLORS["PoC3"]) for r in rows], width=0.6)
    for i, row in enumerate(rows):
        if row["age"] is not None:
            right.text(i, row["age"] + 0.2, f"{row['age']:.2f} s", ha="center", fontsize=10)
    short_names = {"PoC3 · principal": "PoC3\nprincipal", "PoC3 · extendida": "PoC3\nextendida"}
    short_labels = [f"{short_names.get(r['name'], r['name'])}\n{r['duration_s']:g} s" for r in rows]
    right.set_xticks(range(len(rows)), short_labels)
    right.axhline(5, color="#777", linestyle="--", linewidth=1)
    right.text(0.98, 0.95, "Línea discontinua: TTL de 5 s", transform=right.transAxes,
               ha="right", va="top", fontsize=9)
    right.set_ylim(0, max([r["age"] or 0 for r in rows] + [5]) * 1.2 + 0.5)
    right.set_ylabel("Antigüedad máxima servida (s)")
    right.set_title("Frescura del dato de caché")
    fig.suptitle("Disponibilidad frente a frescura: rapidez no equivale a éxito", fontsize=15)
    principal = next((row for row in rows if row["name"] == "PoC3 · principal"), None)
    duration_note = ("La prueba principal de PoC3 dura menos que el TTL; la extendida permite observar su vencimiento."
                     if principal and principal["duration_s"] < 5 else
                     "Considere la duración de la caída y el límite de caché antes de comparar las tasas de fallo.")
    if not rows:
        for ax in (left, right):
            ax.text(0.5, 0.5, "No hay resultados de caída prolongada", transform=ax.transAxes, ha="center")
    fig.text(0.5, 0.025, "Conteos de todas las corridas, incluidas las ruidosas. Duraciones y cargas distintas: no demuestra superioridad.\n"
             + duration_note, ha="center", fontsize=9)
    fig.subplots_adjust(left=0.06, right=0.98, top=0.84, bottom=0.25, wspace=0.3)
    save(fig, FILES[2])

    nominal = result["scenarios"].get("tails", {}).get("summary")
    lines = ["# Saved-result comparison", "", "Historical comparison; not a controlled ranking between versions.", "",
             "| Version | Role |", "|---|---|",
             "| PoC1 | Fixed calibrated thresholds; cache without a maximum age. |",
             "| PoC2 | Adaptive thresholds, bounded-age cache, guarded recovery and retry controls. |",
             "| PoC3 | PoC2 policy with corrected failures, paired samples, transparent calibration and measurement quality. |", "",
             "## 1. Historical latencies", "", f"![Historical comparison](plots/{FILES[0]}.png)", "",
             "Each point is a saved run. Hollow markers identify noisy pairs; PoC3 requires both members to be valid. "
             + "; ".join(f"{name}: N={sources[name]['params']['n']}, {sources[name]['params']['rps']} rps"
                          for name in ("PoC1", "PoC2") if name in sources)
             + f". PoC3: N={result['n']}, {result['rps']:g} rps per run. "
             "Different workloads, seeds and measurement methods prevent attributing cross-version differences to the policy alone.", "",
             "## 2. PoC3 against its own baseline", "", f"![Paired evidence](plots/{FILES[1]}.png)", ""]
    nominal_values = [f"{name}: {sources[name]['scenarios']['tails'][key]['p99_ms']:.1f} ms"
                      for name, key in (("PoC1", "poc1"), ("PoC2", "poc2"))
                      if name in sources and "tails" in sources[name]["scenarios"]]
    if nominal_values:
        insertion = lines.index("## 2. PoC3 against its own baseline")
        lines[insertion:insertion] = ["Saved nominal p99: " + "; ".join(nominal_values)
                                      + ". Single historical runs do not establish a winner.", ""]
    if nominal and nominal["paired_p99_delta_ms"]["all"]:
        base = nominal["outcomes"]["baseline"]["all"]["p99_ms"]["mean"]
        poc = nominal["outcomes"]["poc3"]["all"]["p99_ms"]["mean"]
        lines += [f"Nominal valid pairs: {nominal['pairs_valid']}/{nominal['pairs_total']}. "
                  f"Mean of seed-level p99 values: baseline {base:.1f} ms; PoC3 {poc:.1f} ms. "
                  "This supports a reduction against its own baseline, not superiority to PoC2.", ""]
    else:
        lines += ["There are no clean nominal pairs; no nominal performance conclusion is supported.", ""]
    lines += ["The ECDF pools only accepted records. The difference chart uses seed means and their observed range, not confidence intervals. "
              "Scenarios without clean pairs have no performance estimate.", "",
              "## 3. Outcomes and freshness", "", f"![Outcomes and freshness](plots/{FILES[2]}.png)", "",
              "PoC1 keeps responding with older cache. PoC2/3 stop serving cache after 5 seconds and can fail instead. "
              "Failure rates also depend on the duration of the outage, not only on the architecture.", ""]
    if principal and principal["duration_s"] < 5 and principal["failed"] == 0:
        lines += ["Zero failures in PoC3's short run do not prove higher availability: that run does not exhaust the TTL.", ""]
    extended = next((row for row in rows if row["name"] == "PoC3 · extendida"), None)
    if extended:
        lines += [f"In PoC3's extended validation, {extended['failed']:.2f}% failed and the oldest served cache was "
                  f"{extended['age']:.2f} s. These counts include noisy runs; compare the policy trade-off, not a causal improvement percentage.", ""]
    lines += ["PoC3's demonstrated contribution is correctness and more trustworthy evaluation. "
              "It preserves PoC2's adaptive policy; lower latency than PoC2 has not been demonstrated.", "",
              "Regenerate: `python -B run.py plot` (matplotlib required). Sources and SHA-256 hashes: `plots/sources.json`."]
    (here / "results/comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "sources.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return out

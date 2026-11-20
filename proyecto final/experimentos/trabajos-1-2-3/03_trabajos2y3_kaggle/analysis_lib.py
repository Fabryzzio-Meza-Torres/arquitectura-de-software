"""Analysis helpers for the MINION latency notebooks (figures K1-K9 and tables)."""
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROUTES = ["reranked", "fused_baseline", "fused_fallback", "lex", "sem", "error"]
ROUTE_COLORS = {"reranked": "#CC79A7", "fused_baseline": "#009E73", "fused_fallback": "#009E73",
                "lex": "#0072B2", "sem": "#E69F00", "error": "#D55E00"}
STAGES = ["lex", "sem", "fusion", "rerank"]
LOAD_CONDS = ["L25", "L50", "L75", "L100"]
CONDS = ["L25", "L50", "L75", "L100", "NORERANK", "NOHEDGE", "F1", "F2", "F3H", "F3NH", "F4", "F5", "F6"]
EXPECTED = {"L25": "reranked", "L50": "reranked", "L75": "reranked", "L100": "reranked",
            "NORERANK": "fused_baseline", "NOHEDGE": "reranked", "F1": "fused_fallback", "F2": "fused_fallback",
            "F3H": "reranked", "F3NH": "reranked", "F4": "lex", "F5": "sem", "F6": "error"}
TABLE1_BUDGET_MS = {"lex": 10, "sem": 1000, "fusion": 5, "rerank": 1000}
SLO_MS = 2500


def p_ceil(values, q):
    v = np.sort(np.asarray(values, dtype=float))
    return float(v[max(1, math.ceil(q * len(v))) - 1]) if len(v) else float("nan")


def ecdf(values):
    v = np.sort(np.asarray(values, dtype=float))
    return v, np.arange(1, len(v) + 1) / len(v)


class Run:
    def __init__(self, dataset, root="results", figs="figs"):
        self.ds = dataset
        self.dir = Path(root) / dataset
        self.figs = Path(figs)
        self.figs.mkdir(parents=True, exist_ok=True)
        self.meta = json.loads((self.dir / "run_meta.json").read_text(encoding="utf-8"))
        self.cal = json.loads((self.dir / "calibration.json").read_text(encoding="utf-8"))
        self.sum = pd.read_csv(self.dir / "summary.csv")
        self.warm = self.meta["settings"]["warmup_seconds"]
        self.reps = sorted(self.sum["rep"].unique())
        self._cache = {}

    def _path(self, tag):
        return self.dir / f"requests_{self.ds}_{tag}.jsonl"

    def _load(self, tag):
        if tag not in self._cache:
            df = pd.read_json(self._path(tag), lines=True, dtype={"qid": str})
            for s in STAGES:
                df[f"st_{s}"] = df["stage_ms"].map(lambda d: d.get(s))
            self._cache[tag] = df
        return self._cache[tag]

    def req(self, rep, cond):
        return self._load(f"rep{rep}_{cond}")

    def post(self, rep, cond):
        df = self.req(rep, cond)
        return df[df["t_sched"] >= self.warm]

    def valid(self, rep, cond):
        df = self.post(rep, cond)
        return df[df["n_results"] == 3]

    def pooled(self, cond, valid=True):
        fn = self.valid if valid else self.post
        return pd.concat([fn(r, cond) for r in self.reps], ignore_index=True)

    def row(self, rep, cond):
        return self.sum[(self.sum.rep == rep) & (self.sum.condition == cond)].iloc[0]

    def agg(self, cond, col):
        v = self.sum[self.sum.condition == cond][col].astype(float).dropna()
        return (float(v.median()), float(v.min()), float(v.max())) if len(v) else (np.nan, np.nan, np.nan)

    def save(self, fig, name):
        fig.savefig(self.figs / f"{name}_{self.ds}.png", dpi=200, bbox_inches="tight")
        plt.show()

    @property
    def C(self):
        return self.cal["C_qps"]

    # ------------------------------------------------------------------ tables
    def hardware(self):
        m = self.meta
        smi = [l for l in (m.get("nvidia_smi") or "").splitlines() if "NVIDIA-SMI" in l or "MiB" in l]
        lscpu = {l.split(":", 1)[0].strip(): l.split(":", 1)[1].strip() for l in (m.get("lscpu") or "").splitlines()
                 if ":" in l}
        return {"gpu": m.get("gpu"), "device": m["device"], "nvidia-smi": smi, "cpu_model": lscpu.get("Model name"),
                "cpus": lscpu.get("CPU(s)"), "node": m["node"], "python": m["python"].split()[0],
                "libraries": m["libraries"], "script_sha256": m["script_sha256"],
                "corpus_size": m.get("corpus_size"), "n_test_queries": m.get("n_test_queries"),
                "n_calibration_queries": m.get("n_calibration_queries"), "pilot": m["pilot"],
                "phase0_seconds": round(m.get("phase0_seconds", float("nan")), 1)}

    def stage_table(self):
        rows = []
        for s in STAGES + ["e2e"]:
            st = self.cal["stages_1qps"][s]
            rows.append({"stage": s, "n": st["n"], "p50_ms": st["p50_ms"], "p95_ms": st["p95_ms"],
                         "p99_ms": st["p99_ms"], "table1_budget_p99_ms": TABLE1_BUDGET_MS.get(s, 2000),
                         "table1_timeout_ms": {"lex": 50, "sem": 1200, "fusion": 50, "rerank": 1200}.get(s, SLO_MS)})
        return pd.DataFrame(rows).round(2)

    def ramp_table(self):
        return pd.DataFrame(self.cal["ramp"]).round(3)

    def percentile_table(self):
        rows = []
        for c in CONDS:
            r = {"condition": c, "load_pct": int(self.sum[self.sum.condition == c]["load_pct"].iloc[0]),
                 "qps_offered": round(float(self.sum[self.sum.condition == c]["qps_offered"].iloc[0]), 3)}
            for p in ["p50_ms", "p95_ms", "p99_ms"]:
                med, lo, hi = self.agg(c, p)
                r[p] = "n/a" if np.isnan(med) else f"{med:.1f} [{lo:.1f}-{hi:.1f}]"
            rows.append(r)
        return pd.DataFrame(rows)

    def routes_table(self):
        rows = []
        for c in CONDS:
            pct = {r: self.agg(c, f"route_pct_{r}")[0] for r in ROUTES}
            obs = max(pct, key=pct.get)
            rows.append({"condition": c, "expected_route": EXPECTED[c], "observed_route": obs,
                         "observed_pct": round(pct[obs], 2), "match": obs == EXPECTED[c] and pct[obs] >= 99.9,
                         "others_pct": round(100 - pct[obs], 2)})
        return pd.DataFrame(rows)

    def hedging_table(self):
        out = {}
        for c in ["F3H", "F3NH"]:
            rr = [p_ceil(self.valid(r, c)["st_rerank"].dropna(), 0.99) for r in self.reps]
            e2e = [self.row(r, c)["p99_ms"] for r in self.reps]
            dup = [self.row(r, c)["dup_pct"] for r in self.reps]
            out[c] = {"rerank_p99_ms": np.median(rr), "e2e_p99_ms": float(np.median(e2e)),
                      "dup_pct": float(np.nanmedian(dup)) if not np.all(np.isnan(dup)) else 0.0,
                      "rerank_p99_per_rep": [round(x, 1) for x in rr], "e2e_p99_per_rep": [round(x, 1) for x in e2e]}
        d = pd.DataFrame(out).T
        diff = {"rerank_p99_ms": out["F3NH"]["rerank_p99_ms"] - out["F3H"]["rerank_p99_ms"],
                "e2e_p99_ms": out["F3NH"]["e2e_p99_ms"] - out["F3H"]["e2e_p99_ms"]}
        return d, diff

    def fitness(self):
        """Per repetition values and pass flags for fitness (i), (iii), (iv); (ii) is evaluated in Trabajo 1."""
        rows = []
        for r in self.reps:
            p99 = max(self.row(r, c)["p99_ms"] for c in LOAD_CONDS)
            cont = min(self.row(r, c)["continuity_pct"] for c in ["F1", "F2"])
            dup = max(float(np.nan_to_num(self.row(r, c)["dup_pct"])) for c in LOAD_CONDS + ["F3H"])
            rows.append({"rep": r, "i_p99_ms": p99, "i_ok": p99 <= SLO_MS, "iii_cont_pct": cont,
                         "iii_ok": cont >= 99.0, "iv_dup_pct": dup, "iv_ok": dup <= 10.0})
        return pd.DataFrame(rows)

    def fitness_table(self):
        f = self.fitness()
        rows = [
            {"fitness": "(i) p99 <= 2500 ms, L25-L100", "worst_value": f"{f.i_p99_ms.max():.1f} ms",
             "threshold": f"{SLO_MS} ms", "meets": bool(f.i_ok.all()),
             "margin": f"{SLO_MS - f.i_p99_ms.max():.1f} ms"},
            {"fitness": "(ii) P@3 with reranker >= without", "worst_value": "see Trabajo 1", "threshold": "-",
             "meets": None, "margin": "-"},
            {"fitness": "(iii) continuity >= 99% in F1 and F2", "worst_value": f"{f.iii_cont_pct.min():.2f} %",
             "threshold": "99 %", "meets": bool(f.iii_ok.all()), "margin": f"{f.iii_cont_pct.min() - 99:.2f} pp"},
            {"fitness": "(iv) duplicates <= 10% in L25-L100 and F3H", "worst_value": f"{f.iv_dup_pct.max():.2f} %",
             "threshold": "10 %", "meets": bool(f.iv_ok.all()), "margin": f"{10 - f.iv_dup_pct.max():.2f} pp"},
        ]
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------ figures
    def k1(self):
        steps = self.cal["ramp"]
        off = [s.get("qps_offered_measured", s["rate"]) for s in steps]
        ach = [s["qps_achieved"] for s in steps]
        p99 = [s["p99_ms"] for s in steps]
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        ax[0].plot(off, ach, "o-", color="#CC79A7", label="achieved (reranked, 3 results, <= SLO)")
        lim = max(off) * 1.05
        ax[0].plot([0, lim], [0, lim], "k--", lw=1, label="ideal (achieved = offered)")
        ax[1].plot(off, p99, "o-", color="#0072B2", label="p99 end-to-end")
        ax[1].axhline(SLO_MS, color="k", ls="--", lw=1, label="SLO 2,500 ms")
        for a in ax:
            if self.C:
                a.axvline(self.C, color="#D55E00", ls=":", label=f"C = {self.C:g} QPS")
            a.set_xscale("log")
            a.set_xlabel("offered load (QPS)")
            a.grid(alpha=.3)
            a.legend(fontsize=8)
        ax[0].set_ylabel("achieved throughput (QPS)")
        ax[0].set_yscale("log")
        ax[1].set_ylabel("p99 latency (ms)")
        ax[1].set_yscale("log")
        fig.suptitle(f"K1 - Calibration ramp ({self.ds})")
        fig.tight_layout()
        self.save(fig, "K1_rampa")

    def k2(self):
        df = self._load("calib_1qps")
        data = [df["st_lex"].dropna(), df["st_sem"].dropna(), df["st_fusion"].dropna(), df["st_rerank"].dropna(),
                df["latency_ms"]]
        labels = ["lex", "sem", "fusion", "rerank", "end-to-end"]
        timeouts = [50, 1200, 50, 1200, SLO_MS]
        budget = [10, 1000, 5, 1000, 2000]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.boxplot(data, tick_labels=labels, showfliers=True, flierprops={"markersize": 3})
        for i, (t, b) in enumerate(zip(timeouts, budget), start=1):
            ax.plot([i - .3, i + .3], [t, t], color="#D55E00", lw=2)
            ax.plot(i, b, "D", color="k", ms=5)
        ax.legend(handles=[Line2D([], [], color="#D55E00", lw=2, label="timeout (Table 1)"),
                           Line2D([], [], marker="D", color="k", ls="", label="p99 budget (Table 1)")], fontsize=8)
        ax.set_yscale("log")
        ax.set_ylabel("latency (ms)")
        ax.set_title(f"K2 - Latency per stage at 1 QPS ({self.ds})")
        ax.grid(alpha=.3, axis="y")
        fig.tight_layout()
        self.save(fig, "K2_etapas")

    def k3(self):
        cols = plt.cm.viridis(np.linspace(0.1, 0.9, len(LOAD_CONDS)))
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for c, col in zip(LOAD_CONDS, cols):
            x, y = ecdf(self.pooled(c)["latency_ms"])
            ax.step(x, y, where="post", color=col, label=c)
        ax.axvline(SLO_MS, color="k", ls="--", lw=1, label="SLO 2,500 ms")
        ax.set_xscale("log")
        ax.set_xlabel("end-to-end latency (ms)")
        ax.set_ylabel("ECDF")
        ax.set_title(f"K3 - ECDF of latency by load level ({self.ds})")
        ax.grid(alpha=.3)
        ax.legend()
        fig.tight_layout()
        self.save(fig, "K3_ecdf_carga")

    def k4(self):
        loads = [25, 50, 75, 100]
        cols = {"p50_ms": "#0072B2", "p95_ms": "#E69F00", "p99_ms": "#D55E00"}
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for p, col in cols.items():
            m = [self.agg(c, p) for c in LOAD_CONDS]
            med = np.array([x[0] for x in m])
            err = np.array([[x[0] - x[1] for x in m], [x[2] - x[0] for x in m]])
            ax.errorbar(loads, med, yerr=err, marker="o", color=col, capsize=3, label=p.replace("_ms", ""))
            for c, mk in [("NORERANK", "s"), ("NOHEDGE", "^")]:
                v = self.agg(c, p)
                ax.errorbar([100], [v[0]], yerr=[[v[0] - v[1]], [v[2] - v[0]]], marker=mk, color=col, mfc="white",
                            capsize=3, ls="")
        ax.axhline(SLO_MS, color="k", ls="--", lw=1)
        ax.legend(handles=[Line2D([], [], color=c, marker="o", label=p.replace("_ms", "")) for p, c in cols.items()] +
                          [Line2D([], [], color="gray", marker="s", mfc="white", ls="", label="NORERANK (100%)"),
                           Line2D([], [], color="gray", marker="^", mfc="white", ls="", label="NOHEDGE (100%)"),
                           Line2D([], [], color="k", ls="--", label="SLO 2,500 ms")], fontsize=8)
        ax.set_yscale("log")
        ax.set_xlabel("load (% of C)")
        ax.set_ylabel("latency (ms)")
        ax.set_title(f"K4 - Percentiles vs load, median and range of repetitions ({self.ds})")
        ax.set_xticks(loads)
        ax.grid(alpha=.3)
        fig.tight_layout()
        self.save(fig, "K4_percentiles_carga")

    def k5(self):
        rep = self.reps[0]
        fig, ax = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
        for a, c in zip(ax, ["L100", "F2"]):
            d = self.req(rep, c)
            a.scatter(d["t_sched"], d["latency_ms"], s=6, color="#CC79A7" if c == "L100" else "#009E73")
            a.axvspan(0, self.warm, color="gray", alpha=.25, label="warm-up (discarded)")
            a.axhline(SLO_MS, color="k", ls="--", lw=1, label="SLO 2,500 ms")
            a.set_yscale("log")
            a.set_xlabel("scheduled time (s)")
            a.set_title(f"{c} (rep {rep})")
            a.grid(alpha=.3)
            a.legend(fontsize=8)
        ax[0].set_ylabel("latency (ms)")
        fig.suptitle(f"K5 - Latency over time ({self.ds})")
        fig.tight_layout()
        self.save(fig, "K5_serie_tiempo")

    def k6(self):
        m = np.array([[self.agg(c, f"route_pct_{r}")[0] for r in ROUTES] for c in CONDS])
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(m, cmap="Blues", vmin=0, vmax=100, aspect="auto")
        ax.set_xticks(range(len(ROUTES)), ROUTES, rotation=30, ha="right")
        ax.set_yticks(range(len(CONDS)), CONDS)
        for i in range(len(CONDS)):
            for j in range(len(ROUTES)):
                ax.text(j, i, f"{m[i, j]:.1f}", ha="center", va="center",
                        color="white" if m[i, j] > 55 else "black", fontsize=8)
        fig.colorbar(im, label="% of requests")
        ax.set_xlabel("route used")
        ax.set_ylabel("condition")
        ax.set_title(f"K6 - Route matrix, median of repetitions ({self.ds})")
        fig.tight_layout()
        self.save(fig, "K6_matriz_rutas")

    def k7(self):
        conds = ["NORERANK", "F1", "F2", "F4", "F5", "F6"]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for i, c in enumerate(conds):
            med, lo, hi = self.agg(c, "continuity_pct")
            route = EXPECTED[c]
            ax.bar(i, med, color=ROUTE_COLORS[route], hatch="///" if route == "fused_fallback" else None,
                   edgecolor="white" if route == "fused_fallback" else None, yerr=[[med - lo], [hi - med]],
                   capsize=3)
            ax.text(i, med + 1.5, f"{med:.2f}", ha="center", fontsize=8)
        ax.axhline(99, color="k", ls="--", lw=1)
        ax.set_xticks(range(len(conds)), conds)
        ax.set_ylim(0, 110)
        ax.set_ylabel("continuity (% with 3 results in <= 2,500 ms)")
        ax.legend(handles=[Line2D([], [], color="k", ls="--", label="99% target")] +
                          [Patch(facecolor=ROUTE_COLORS[r], label=r, hatch="///" if r == "fused_fallback" else None)
                           for r in ["fused_baseline", "fused_fallback", "lex", "sem", "error"]], fontsize=8)
        ax.set_title(f"K7 - Service continuity under failures ({self.ds})")
        ax.grid(alpha=.3, axis="y")
        fig.tight_layout()
        self.save(fig, "K7_continuidad")

    def k8(self):
        fig, ax = plt.subplots(1, 3, figsize=(15, 4))
        cols = {"F3H": "#CC79A7", "F3NH": "#0072B2"}
        for a, col, xl in [(ax[0], "st_rerank", "rerank stage latency (ms)"), (ax[1], "latency_ms", "end-to-end latency (ms)")]:
            for c, color in cols.items():
                v = self.pooled(c)[col].dropna()
                x, y = ecdf(v)
                a.step(x, y, where="post", color=color, label=f"{c} (p99 = {p_ceil(v, .99):.0f} ms)")
                a.axvline(p_ceil(v, .99), color=color, ls=":")
            a.set_xscale("log")
            a.set_xlabel(xl)
            a.set_ylabel("ECDF")
            a.grid(alpha=.3)
            a.legend(fontsize=8)
        d = self.sum[self.sum.condition == "F3H"]["dup_pct"].astype(float)
        ax[2].bar(["F3H"], [d.median()], color="#CC79A7", yerr=[[d.median() - d.min()], [d.max() - d.median()]],
                  capsize=4)
        ax[2].axhline(10, color="k", ls="--", lw=1, label="10% limit")
        ax[2].set_ylabel("duplicated requests (% of originals)")
        ax[2].set_ylim(0, max(12, d.max() * 1.2))
        ax[2].legend(fontsize=8)
        fig.suptitle(f"K8 - Hedging: F3H vs F3NH, identical arrivals and delays ({self.ds})")
        fig.tight_layout()
        self.save(fig, "K8_hedging")

    def k9(self):
        f = self.fitness()
        labels = ["(i) p99 <= 2,500 ms\n(worst of L25-L100)", "(ii) P@3 reranker >= baseline",
                  "(iii) continuity >= 99%\n(worst of F1, F2)", "(iv) duplicates <= 10%\n(L25-L100, F3H)"]
        fig, ax = plt.subplots(figsize=(1.8 * len(f) + 4, 4))
        for j, (_, r) in enumerate(f.iterrows()):
            cells = [(r.i_ok, f"{r.i_p99_ms:.0f} ms"), (None, "see Trabajo 1"),
                     (r.iii_ok, f"{r.iii_cont_pct:.2f} %"), (r.iv_ok, f"{r.iv_dup_pct:.2f} %")]
            for i, (ok, txt) in enumerate(cells):
                color = "#BBBBBB" if ok is None else ("#009E73" if ok else "#D55E00")
                ax.add_patch(plt.Rectangle((j, len(cells) - 1 - i), 1, 1, color=color, ec="white", lw=2))
                ax.text(j + .5, len(cells) - 1 - i + .5, txt, ha="center", va="center", color="white", fontsize=9,
                        fontweight="bold")
        ax.set_xlim(0, len(f))
        ax.set_ylim(0, 4)
        ax.set_xticks(np.arange(len(f)) + .5, [f"rep {int(r)}" for r in f.rep])
        ax.set_yticks(np.arange(4) + .5, labels[::-1])
        ax.xaxis.tick_top()
        ax.set_title(f"K9 - Fitness functions by repetition ({self.ds})", pad=28)
        for s in ax.spines.values():
            s.set_visible(False)
        fig.tight_layout()
        self.save(fig, "K9_fitness")

    # ------------------------------------------------------------------ conclusions
    def conclusions(self):
        t, _ = self.hedging_table()
        f = self.fitness()
        _, diff = self.hedging_table()
        l100 = self.agg("L100", "p99_ms")
        nr = self.agg("NORERANK", "p99_ms")
        rt = self.routes_table()
        cont = {c: self.agg(c, "continuity_pct")[0] for c in ["F1", "F2", "F4", "F5", "F6"]}
        b = []
        b.append(f"Measured capacity C = {self.C} QPS; hedging threshold = {self.cal['hedge_threshold_ms']:.1f} ms "
                 f"(p95 of the reranker at 1 QPS).")
        b.append(f"At 100% of C the end-to-end p99 is {l100[0]:.1f} ms (range {l100[1]:.1f}-{l100[2]:.1f}) against the "
                 f"{SLO_MS} ms SLO; fitness (i) {'is met' if f.i_ok.all() else 'is NOT met'} in "
                 f"{int(f.i_ok.sum())}/{len(f)} repetitions.")
        b.append(f"Skipping the reranker (NORERANK) gives p99 = {nr[0]:.1f} ms, so the reranker adds about "
                 f"{l100[0] - nr[0]:.1f} ms at the 99th percentile.")
        b.append(f"Continuity with the reranker failing (F1) or slow (F2): {cont['F1']:.2f}% and {cont['F2']:.2f}%; "
                 f"fitness (iii) {'is met' if f.iii_ok.all() else 'is NOT met'}.")
        b.append(f"Search failures: continuity is {cont['F4']:.2f}% without the semantic search (F4) and "
                 f"{cont['F5']:.2f}% without the lexical search (F5); with both failing (F6) it is {cont['F6']:.2f}%, "
                 f"the controlled error expected by Table 2.")
        b.append(f"{int(rt['match'].sum())}/{len(rt)} conditions used exactly the route predicted by Table 2.")
        b.append(f"Hedging changes the p99 of the reranking stage by {diff['rerank_p99_ms']:.1f} ms and the "
                 f"end-to-end p99 by {diff['e2e_p99_ms']:.1f} ms (F3NH minus F3H), with "
                 f"{t.loc['F3H', 'dup_pct']:.2f}% duplicated requests; fitness (iv) "
                 f"{'is met' if f.iv_ok.all() else 'is NOT met'}.")
        b.append("Fitness (ii), the relevance of the reranked top 3, is evaluated in Trabajo 1 and is not measured "
                 "here.")
        return b

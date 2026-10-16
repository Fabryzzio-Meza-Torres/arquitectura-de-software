import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
sys.path.insert(0, HERE)
import simcore as sc
from diagram_api import DiagramAPI

RES = os.path.join(HERE, "results")
KINDS = ["baseline", "poc1"]


def make_factory(alpha, beta):
    def factory(cfg):
        be = sc.Backend(cfg)
        return DiagramAPI(be, alpha, beta), be
    return factory


def baseline_factory(cfg):
    be = sc.Backend(cfg)
    return sc.BaselineAPI(be), be


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("train")
    e = sub.add_parser("experiment")
    e.add_argument("--scenario", default="all", choices=["all", *sc.SCENARIO_TITLES])
    e.add_argument("--n", type=int, default=4000)
    e.add_argument("--rps", type=float, default=250)
    e.add_argument("--seed", type=int, default=42)
    sub.add_parser("report")
    a = ap.parse_args()
    os.makedirs(RES, exist_ok=True)
    trained_path, results_path = f"{RES}/trained.json", f"{RES}/results.json"

    if a.cmd == "train":
        print("== entrenando PoC 1 (objetivo CVaR_0.99; carga extra <= 5%; timeouts <= 0.5%/llamada; beta = beta* x 1.5)")
        t = sc.train_params(make_factory, safety=1.5)
        json.dump(t, open(trained_path, "w"), indent=1)

    elif a.cmd == "experiment":
        t = json.load(open(trained_path))
        variants = {"baseline": ("Baseline", baseline_factory),
                    "poc1": ("PoC 1: diagrama", make_factory(t["alpha_ms"], t["beta_ms"]))}
        sc.run_experiment(variants, a.scenario, a.n, a.rps, a.seed, results_path,
                          {"alpha_ms": t["alpha_ms"], "beta_ms": t["beta_ms"]})

    elif a.cmd == "report":
        R = json.load(open(results_path))
        t = json.load(open(trained_path))
        p = R["params"]
        sc.plot_results(R, KINDS, f"{RES}/resultados.png",
                        f"PoC 1 (diagrama) vs baseline - N={p['n']}, {p['rps']:.0f} rps, alpha={p['alpha_ms']} ms, beta={p['beta_ms']} ms")
        md = [f"**Parametros entrenados** (objetivo CVaR99, bisecccion; seed de entrenamiento 7, evaluacion {p['seed']}): "
              f"alpha = {t['alpha_ms']} ms, beta* = {t['beta_star_ms']} ms (minimo factible), beta usado = {t['beta_ms']} ms (beta* x {t['safety']}).",
              f"Carga: {p['n']} requests por corrida a {p['rps']:.0f} rps (open-loop).\n"]
        for s in sc.SCENARIO_TITLES:
            if s in R["scenarios"]:
                md += [f"#### {sc.SCENARIO_TITLES[s]}\n", sc.table_md(R, KINDS, s), ""]
        md.append("![resultados](results/resultados.png)")
        text = "\n".join(md)
        open(f"{RES}/tabla.md", "w").write(text + "\n")
        readme = os.path.join(HERE, "README.md")
        if os.path.exists(readme):
            sc.update_readme(readme, text)
        print(text)


if __name__ == "__main__":
    main()

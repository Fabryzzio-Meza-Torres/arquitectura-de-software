import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "common"))
sys.path.insert(0, HERE)
import simcore as sc
from improved_api import ImprovedAPI

RES = os.path.join(HERE, "results")
KINDS = ["baseline", "poc2", "B"]


def make_factory(alpha, beta, mode="C"):
    def factory(cfg):
        be = sc.Backend(cfg)
        return ImprovedAPI(be, alpha, beta, mode=mode), be
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
        print("== entrenando PoC 2 (CVaR_0.99; carga <= 5%; timeouts <= 0.5%/llamada en nominal Y con cola sana pesada)")
        stress = [sc.SimConfig(seed=7, base_sigma=0.55)]
        t = sc.train_params(make_factory, stress_cfgs=stress, beta_lo_margin_ms=1.5 * 10.0 + 1.0)
        json.dump(t, open(trained_path, "w"), indent=1)

    elif a.cmd == "experiment":
        t = json.load(open(trained_path))
        al, be = t["alpha_ms"], t["beta_ms"]
        variants = {"baseline": ("Baseline", baseline_factory),
                    "poc2": ("PoC 2: mejorada", make_factory(al, be, "C")),
                    "B": ("B: retry primero (ablacion)", make_factory(al, be, "B"))}
        sc.run_experiment(variants, a.scenario, a.n, a.rps, a.seed, results_path, {"alpha_ms": al, "beta_ms": be})

    elif a.cmd == "report":
        R = json.load(open(results_path))
        t = json.load(open(trained_path))
        p = R["params"]
        sc.plot_results(R, KINDS, f"{RES}/resultados.png",
                        f"PoC 2 (mejorada) vs baseline vs B - N={p['n']}, {p['rps']:.0f} rps, alpha={p['alpha_ms']} ms, beta={p['beta_ms']} ms")
        md = [f"**Parametros entrenados** (objetivo CVaR99, biseccion, beta robusto; seed de entrenamiento 7, evaluacion {p['seed']}): "
              f"alpha = {t['alpha_ms']} ms, beta* = {t['beta_star_ms']} ms (minimo factible en nominal y con cola sana pesada), beta usado = {t['beta_ms']} ms.",
              f"Carga: {p['n']} requests por corrida a {p['rps']:.0f} rps (open-loop). TTL fresco 1 s, TTL maximo 5 s.\n"]
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

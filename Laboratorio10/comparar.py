import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "common"))
import simcore as sc

R1 = json.load(open(os.path.join(HERE, "poc1_diagrama/results/results.json")))
R2 = json.load(open(os.path.join(HERE, "poc2_mejorada/results/results.json")))

R = {"params": R2["params"], "labels": {"baseline": "Baseline", "poc1": "PoC 1: diagrama", "poc2": "PoC 2: mejorada"},
     "scenarios": {}}
for s in sc.SCENARIO_TITLES:
    R["scenarios"][s] = {"baseline": R1["scenarios"][s]["baseline"], "poc1": R1["scenarios"][s]["poc1"],
                         "poc2": R2["scenarios"][s]["poc2"]}

kinds = ["baseline", "poc1", "poc2"]
sc.plot_results(R, kinds, os.path.join(HERE, "comparativo.png"), "Baseline vs PoC 1 (diagrama) vs PoC 2 (mejorada)")
out = []
for s in sc.SCENARIO_TITLES:
    out += [f"#### {sc.SCENARIO_TITLES[s]}\n", sc.table_md(R, kinds, s), ""]
text = "\n".join(out) + "\n![comparativo](comparativo.png)"
open(os.path.join(HERE, "comparativo.md"), "w").write(text)
readme = os.path.join(HERE, "README.md")
if os.path.exists(readme):
    sc.update_readme(readme, text, "COMPARATIVO")
print("\n".join(out))

import json
import math
from pathlib import Path

base = Path("results/recuperacion_referencia/candidates_scores.jsonl")
resume = Path("results/recuperacion_interrumpida/candidates_scores.jsonl")

def load(path):
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    ids = [str(r["query_id"]) for r in rows]
    assert len(ids) == len(set(ids)), f"Duplicados en {path}"

    return {str(r["query_id"]): r for r in rows}

a = load(base)
b = load(resume)

assert len(a) == 20
assert len(b) == 20
assert set(a) == set(b), "Consultas diferentes"

max_difference = 0.0
differences = 0

for qid in sorted(a):
    x = a[qid]
    y = b[qid]

    assert x["ranking_A"] == y["ranking_A"], qid
    assert x["ranking_B"] == y["ranking_B"], qid

    cx = {str(c["doc_id"]): c for c in x["candidates"]}
    cy = {str(c["doc_id"]): c for c in y["candidates"]}

    assert set(cx) == set(cy), qid

    for doc_id in cx:
        for field in ("fusion", "llm_score"):
            v1 = float(cx[doc_id][field])
            v2 = float(cy[doc_id][field])

            assert math.isfinite(v1) and math.isfinite(v2)

            delta = abs(v1 - v2)
            max_difference = max(max_difference, delta)

            if delta > 1e-9:
                differences += 1

print("Consultas verificadas:", len(a))
print("Candidatos y rankings: consistentes")
print("Diferencia maxima de scores:", max_difference)
print("Scores con diferencia mayor a 1e-9:", differences)

assert max_difference <= 0.001, (
    "Los scores superaron la tolerancia de 0.001"
)

print("RECUPERACION VALIDADA")

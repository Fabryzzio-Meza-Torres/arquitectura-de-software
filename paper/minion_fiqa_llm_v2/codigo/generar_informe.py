import json
from pathlib import Path
from datetime import date

BASE = Path("results")

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

quality = load(BASE / "calidad/summary.json")
batching = load(BASE / "batching/batch_summary.json")

lines = [
    "# MINION — Experimento FiQA con LLM",
    "",
    f"Fecha de consolidacion: {date.today()}",
    "",
    "## 1. Configuracion",
    "",
    "- Dataset: FiQA-2018",
    "- Corpus experimental: 10 000 documentos",
    "- Recuperacion: BM25 top 10 + BGE top 10",
    "- Candidatos: hasta 20 documentos unicos",
    "- Ranking A: fusion convexa, alpha = 0.85",
    "- Ranking B: Qwen2.5-3B-Instruct",
    "- Metricas principales: P@3, nDCG@3, MRR@10",
    "- Metricas adicionales: P@5, nDCG@5",
    "",
    "## 2. Calidad",
    "",
    f"Consultas: {quality['queries']}",
    "",
    "| Metrica | Fusion A | Qwen B | Delta B-A | IC 95% |",
    "|---|---:|---:|---:|---|",
]

for name, r in quality["metrics"].items():
    ci = r["CI95"]
    lines.append(
        f"| {name} | {r['A']:.4f} | {r['B']:.4f} | "
        f"{r['delta']:+.4f} | "
        f"[{ci[0]:+.4f}, {ci[1]:+.4f}] |"
    )

lines += [
    "",
    "## 3. Batching",
    "",
    "| Batch | Repeticiones validas | Tiempo medio (s) | Diferencia maxima |",
    "|---|---:|---:|---:|",
]

for n in (1, 4, 8):
    rows = [
        r for r in batching
        if r["batch"] == n and r["error"] is None
    ]

    if not rows:
        lines.append(f"| {n} | 0 | N/A | N/A |")
        continue

    avg = sum(r["seconds"] for r in rows) / len(rows)
    dif = max(r["max_abs_diff"] for r in rows)

    lines.append(
        f"| {n} | {len(rows)} | {avg:.3f} | {dif:.5f} |"
    )

lines += [
    "",
    "Batch seleccionado: 1, segun tolerancia predefinida de 0.001.",
    "",
    "## 4. Concurrencia",
    "",
    "| Concurrencia | Solicitudes | OK | Throughput | p99 ms |",
    "|---|---:|---:|---:|---:|",
]

for path in sorted((BASE / "concurrencia").glob("*_summary.json")):
    r = load(path)
    lines.append(
        f"| {r['concurrency']} | {r['requests']} | "
        f"{r['success']} | "
        f"{r['throughput_requests_per_s']:.3f} | "
        f"{r['p99_ms']:.2f} |"
    )

lines += [
    "",
    "## 5. Latencia",
    "",
    "| Ranking | Solicitudes | OK | p50 ms | p95 ms | p99 ms | Continuidad |",
    "|---|---:|---:|---:|---:|---:|---:|",
]

for path in sorted((BASE / "latencia").glob("*_summary.json")):
    r = load(path)
    lines.append(
        f"| {r['arm']} | {r['requests']} | "
        f"{r['success']} | {r['p50_ms']:.2f} | "
        f"{r['p95_ms']:.2f} | {r['p99_ms']:.2f} | "
        f"{100*r['continuity_within_2500_ms']:.2f}% |"
    )

lines += [
    "",
    "## 6. Recuperacion",
    "",
    "Registrar si se interrumpio efectivamente el job,",
    "el numero de consultas guardadas antes de interrumpir,",
    "el resultado de la reanudacion y la comparacion",
    "contra la referencia.",
    "",
    "## 7. Limitaciones",
    "",
    "- Corpus reducido de 10 000 documentos.",
    "- Juicios de relevancia incompletos.",
    "- FiQA tiene relevancia principalmente binaria.",
    "- p99 con 50 solicitudes es exploratorio.",
    "- La concurrencia usa una cola conservadora para la GPU.",
    "- El texto enviado al LLM se limita a 384 tokens.",
    "- TREC-COVID tiene otra distribucion de consultas y etiquetas.",
    "",
]

output = Path("results/informe_fiqa.md")
output.write_text("\n".join(lines), encoding="utf-8")

print("Informe generado:", output)

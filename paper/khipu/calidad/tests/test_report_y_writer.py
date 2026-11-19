"""Pruebas de report.py, result_writer.py y subsample_corpus.py."""
import csv
import json
import subprocess
import sys
import threading
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from io_formats import load_latency, load_run  # noqa: E402
from report import Entry, build_main_table, load_entries, pareto  # noqa: E402
from result_writer import ResultWriter  # noqa: E402
from subsample_corpus import make_subsamples  # noqa: E402
from test_baseline_y_flujo import make_mini  # noqa: E402

METRICS = ["P@3", "nDCG@3", "nDCG@10", "MRR@10", "R@20", "Rcap@20", "Suf3@20", "OracleP3@20"]


def fake_system(tmp: Path, name: str, group: str, p3: float, p99: float, size=None, not_ok=0.0, n=60, seed=0):
    rng = np.random.default_rng(seed)
    base = {"P@3": p3, "nDCG@3": p3 + 0.02, "nDCG@10": p3 - 0.03, "MRR@10": min(p3 + 0.15, 1), "R@20": 0.4, "Rcap@20": 0.7, "Suf3@20": 0.9, "OracleP3@20": 0.95}
    pq = {f"q{i}": {m: float(np.clip(v + rng.normal(0, 0.1), 0, 1)) for m, v in base.items()} for i in range(n)}
    prefix = tmp / name.replace(" ", "_")
    with open(f"{prefix}.per_query.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["qid"] + METRICS)
        for q, vals in pq.items():
            w.writerow([q] + [vals[m] for m in METRICS])
    summary = {"n_queries_evaluated": n, "metrics": {m: float(np.mean([q[m] for q in pq.values()])) for m in METRICS},
               "latency": {"p50_ms": p99 / 4, "p95_ms": p99 / 1.6, "p99_ms": p99, "frac_ok": 1 - not_ok},
               "meta": {"system": name, "group": group, **({"corpus_size": str(size)} if size else {})}}
    Path(f"{prefix}.summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return f"{prefix}.summary.json"


@pytest.fixture
def systems(tmp_path):
    specs = [("BM25", "Retrieval", 0.30, 8), ("Denso", "Retrieval", 0.34, 45), ("Híbrido RRF", "Retrieval", 0.38, 52),
             ("Cross-encoder", "Reranker", 0.46, 180), ("LLM listwise", "Reranker", 0.52, 1400), ("FIRST", "Reranker", 0.49, 420),
             ("Cascada", "Cascada", 0.50, 260)]
    return [fake_system(tmp_path, n, g, p, l, seed=i, not_ok=0.02 if n == "LLM listwise" else 0) for i, (n, g, p, l) in enumerate(specs)]


def test_pareto():
    assert pareto([(10, 0.3), (50, 0.5), (60, 0.4), (200, 0.6)]) == [0, 1, 3]


def test_tabla_marca_el_mejor_y_flechas(systems):
    entries = load_entries(systems, None, None)
    table, raw = build_main_table(entries)
    assert "P@3 ↑ (IC 95%)" in table and "p99 ms ↓" in table
    assert "**0.5" in table  # el mejor P@3 en negrita
    assert "**8.0**" in table  # el menor p99 en negrita
    assert len(raw) == 7


def test_report_cli_crea_todo(systems, tmp_path):
    out = tmp_path / "rep"
    p = subprocess.run([sys.executable, str(ROOT / "src" / "report.py"), "--summaries", *systems, "--out-dir", str(out)],
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stdout + p.stderr
    for f in ["tabla_principal.md", "tabla_principal.csv", "fig1_calidad_vs_latencia.png", "fig2_metricas.png",
              "fig3_latencia.png", "fig5_candidatos.png", "figuras.md"]:
        assert (out / f).exists() and (out / f).stat().st_size > 0, f
    assert not (out / "fig4_escalabilidad.png").exists()  # sin corpus_size no hay gráfico de escalabilidad
    assert "Mayor P@3: **LLM listwise**" in (out / "figuras.md").read_text(encoding="utf-8")


def test_escalabilidad_con_corpus_size(tmp_path):
    paths = []
    for i, size in enumerate([3633, 20000, 171332]):
        paths.append(fake_system(tmp_path, f"Cascada_{size}", "Cascada", 0.5, 100 + 60 * i, size=size, seed=i))
        paths[-1] = paths[-1]
    # mismo sistema en tres tamaños: se renombra el system para agruparlos
    for p in paths:
        s = json.loads(Path(p).read_text(encoding="utf-8"))
        s["meta"]["system"] = "Cascada"
        Path(p).write_text(json.dumps(s), encoding="utf-8")
    out = tmp_path / "rep"
    subprocess.run([sys.executable, str(ROOT / "src" / "report.py"), "--summaries", *paths, "--out-dir", str(out)], check=True, capture_output=True)
    assert (out / "fig4_escalabilidad.png").exists()


def test_mas_de_tres_grupos_da_error(tmp_path):
    ps = [fake_system(tmp_path, f"S{i}", f"G{i}", 0.3 + i / 10, 10 + i) for i in range(4)]
    with pytest.raises(SystemExit):
        load_entries(ps, None, None)


def test_result_writer_estados_y_errores(tmp_path):
    with ResultWriter(str(tmp_path / "exp")) as rw:
        with rw.request("q1") as r:
            r.set_results({"d1": 0.9, "d2": 0.5})
        with rw.request("q2") as r:
            r.set_results({"d3": 0.7})
            r.mark_degraded()
        with rw.request("q3") as r:
            r.set_results({"d4": 1.0})
            r.mark_timeout()
        with rw.request("q4") as r:
            raise RuntimeError("falló el modelo")  # se registra y el experimento sigue
    run = load_run(tmp_path / "exp.run")
    assert set(run) == {"q1", "q2"}  # timeout y error no guardan resultados
    status = {q: s for q, _, s in load_latency(tmp_path / "exp.latency.tsv")}
    assert status == {"q1": "ok", "q2": "degraded", "q3": "timeout", "q4": "error"}


def test_result_writer_con_hilos(tmp_path):
    rw = ResultWriter(str(tmp_path / "carga"), top_k=2)

    def work(i):
        with rw.request(f"q{i}") as r:
            r.set_results({"a": 1.0, "b": 0.5, "c": 0.1})

    ts = [threading.Thread(target=work, args=(i,)) for i in range(50)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    rw.close()
    run = load_run(tmp_path / "carga.run")
    assert len(run) == 50 and all(set(v) == {"a", "b"} for v in run.values())  # top_k=2
    assert len(load_latency(tmp_path / "carga.latency.tsv")) == 50


def test_submuestras_anidadas_conservan_relevantes(tmp_path):
    src = make_mini(tmp_path / "data")
    outs = make_subsamples(src, [16, 18], seed=7, keep="relevant", out_root=tmp_path / "data")
    ids = {o.name: {json.loads(l)["_id"] for l in open(o / "corpus.jsonl", encoding="utf-8")} for o in outs}
    small, big = ids["mini-16"], ids["mini-18"]
    relevant = {f"q{i}_d{j}" for i in range(5) for j in range(3)}
    assert relevant <= small and small < big and len(small) == 16 and len(big) == 18
    again = make_subsamples(src, [16], seed=7, keep="relevant", out_root=tmp_path / "otra")
    assert {json.loads(l)["_id"] for l in open(again[0] / "corpus.jsonl", encoding="utf-8")} == small  # misma semilla, mismo resultado
    meta = json.loads((outs[0] / "SUBSAMPLE.json").read_text(encoding="utf-8"))
    assert meta["kept_documents"] == 15 and meta["seed"] == 7
    with pytest.raises(ValueError):
        make_subsamples(src, [10], seed=7, keep="relevant", out_root=tmp_path / "x")  # menor que los relevantes a conservar

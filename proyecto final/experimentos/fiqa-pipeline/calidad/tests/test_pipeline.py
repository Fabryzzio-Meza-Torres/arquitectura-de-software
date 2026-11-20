"""Pruebas con casos de resultado conocido (calculados a mano)."""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import metrics as M  # noqa: E402
from io_formats import load_qrels, load_run, merge_qrels, write_run  # noqa: E402
from latency import percentile_nearest_rank, summarize_latency  # noqa: E402
from significance import compare, holm, paired_randomization_p  # noqa: E402

# 3 relevantes (d1 grado 2, d3 y d4 grado 1), d2 juzgado no relevante
QREL = {"d1": 2, "d2": 0, "d3": 1, "d4": 1}
RANKED = ["d2", "d1", "d5", "d3", "d6"]


def test_precision_recall_mrr():
    assert M.precision_at_k(RANKED, QREL, 3) == pytest.approx(1 / 3)
    assert M.recall_at_k(RANKED, QREL, 20) == pytest.approx(2 / 3)
    assert M.capped_recall_at_k(RANKED, QREL, 3) == pytest.approx(1 / 3)  # min(3 rel, 3) = 3
    assert M.reciprocal_rank_at_k(RANKED, QREL, 10) == pytest.approx(0.5)


def test_precision_lista_corta_divide_por_k():
    assert M.precision_at_k(["d1"], QREL, 3) == pytest.approx(1 / 3)


def test_ndcg_lineal():
    dcg = 2 / math.log2(3)  # d1 (grado 2) en rango 2
    idcg = 2 / math.log2(2) + 1 / math.log2(3) + 1 / math.log2(4)
    assert M.ndcg_at_k(RANKED, QREL, 3) == pytest.approx(dcg / idcg)


def test_ranking_perfecto():
    perfect = ["d1", "d3", "d4"]
    assert M.ndcg_at_k(perfect, QREL, 3) == pytest.approx(1.0)
    assert M.precision_at_k(perfect, QREL, 3) == pytest.approx(1.0)


def test_diagnosticos_de_candidatos():
    assert M.hole_at_k(RANKED, QREL, 10) == pytest.approx(2 / 5)  # d5 y d6 sin juicio
    assert M.sufficiency_at_k(RANKED, QREL, 20, 3) == 0.0  # solo 2 de 3 relevantes
    assert M.oracle_precision(RANKED, QREL, 3, 20) == pytest.approx(2 / 3)
    assert M.sufficiency_at_k(["d1", "d3", "d4"], QREL, 20, 3) == 1.0


def test_desempate_determinista():
    assert M.ranked_list({"b": 1.0, "a": 1.0, "c": 2.0}) == ["c", "a", "b"]


def test_latencia_nearest_rank():
    vals = list(range(1, 101))
    assert percentile_nearest_rank(vals, 50) == 50
    assert percentile_nearest_rank(vals, 95) == 95
    assert percentile_nearest_rank(vals, 99) == 99
    rows = [(str(i), float(i), "ok" if i < 100 else "timeout") for i in vals]
    s = summarize_latency(rows)
    assert s["p99_ms"] == 99 and s["frac_timeout"] == pytest.approx(0.01)


def test_significancia_detecta_mejora_y_no_inventa_diferencias():
    rng = np.random.default_rng(0)
    base = rng.uniform(0.2, 0.6, 200)
    a = {f"q{i}": {"P@3": float(v)} for i, v in enumerate(base)}
    b_same = {k: dict(v) for k, v in a.items()}
    b_better = {f"q{i}": {"P@3": float(min(v + 0.1, 1.0))} for i, v in enumerate(base)}
    same = compare(a, b_same, ["P@3"], n_resamples=2000)[0]
    better = compare(a, b_better, ["P@3"], n_resamples=2000)[0]
    assert same["diff"] == 0 and same["p_raw"] > 0.9
    assert better["diff"] > 0.05 and better["p_raw"] < 0.01 and better["ci95_low"] > 0


def test_holm_monotono_y_acotado():
    adj = holm([0.01, 0.04, 0.03])
    assert adj == pytest.approx([0.03, 0.06, 0.06])
    assert all(0 <= p <= 1 for p in adj)


def test_comparar_exige_mismas_queries():
    with pytest.raises(ValueError):
        compare({"q1": {"P@3": 1.0}}, {"q2": {"P@3": 1.0}}, ["P@3"])


def test_formatos_io(tmp_path):
    q = tmp_path / "qrels.tsv"
    q.write_text("query-id\tcorpus-id\tscore\nq1\td1\t2\nq1\td2\t0\n", encoding="utf-8")
    assert load_qrels(q) == {"q1": {"d1": 2, "d2": 0}}
    extra = {"q1": {"d2": 1, "d9": 1}}
    assert merge_qrels(load_qrels(q), extra)["q1"] == {"d1": 2, "d2": 1, "d9": 1}  # el juicio manual gana
    r = tmp_path / "x.run"
    write_run(r, {"q1": {"d1": 0.9, "d2": 0.5}}, "t")
    assert load_run(r) == {"q1": {"d1": 0.9, "d2": 0.5}}
    r.write_text("q1 Q0 d1 1 0.9 t\nq1 Q0 d1 2 0.8 t\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_run(r)


def test_evaluate_cli_extremo_a_extremo(tmp_path):
    qrels = tmp_path / "qrels.tsv"
    qrels.write_text("q1\td1\t1\nq1\td2\t1\nq1\td3\t1\nq2\td4\t2\nq3\td9\t0\n", encoding="utf-8")  # q3 sin relevantes: no cuenta
    write_run(tmp_path / "run", {"q1": {"d1": 3, "d2": 2, "d3": 1}}, "t")  # q2 sin resultados: puntúa 0
    (tmp_path / "lat.tsv").write_text("q1\t10\tok\nq2\t500\ttimeout\n", encoding="utf-8")
    out = tmp_path / "res" / "r"
    p = subprocess.run([sys.executable, str(ROOT / "src" / "evaluate.py"), "--qrels", str(qrels), "--run",
                        str(tmp_path / "run"), "--latency", str(tmp_path / "lat.tsv"), "--out", str(out)],
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stderr
    import json
    s = json.loads(Path(f"{out}.summary.json").read_text(encoding="utf-8"))
    assert s["n_queries_evaluated"] == 2 and s["n_queries_missing_in_run"] == 1
    assert s["metrics"]["P@3"] == pytest.approx((1.0 + 0.0) / 2)  # q1 perfecto, q2 vacío
    assert s["latency"]["p99_ms"] == 500 and s["latency"]["frac_timeout"] == 0.5
    assert Path(f"{out}.per_query.csv").exists()


def test_review_sample_y_merge(tmp_path):
    import json
    (tmp_path / "qrels.tsv").write_text("q1\td1\t1\n", encoding="utf-8")
    (tmp_path / "queries.jsonl").write_text(json.dumps({"_id": "q1", "text": "hola"}) + "\n", encoding="utf-8")
    (tmp_path / "corpus.jsonl").write_text("\n".join(json.dumps({"_id": d, "title": d, "text": "texto " + d}) for d in ["d1", "d2", "d3"]) + "\n", encoding="utf-8")
    write_run(tmp_path / "r.run", {"q1": {"d1": 3, "d2": 2, "d3": 1}}, "t")
    csv_path = tmp_path / "review.csv"
    subprocess.run([sys.executable, str(ROOT / "src" / "review_sample.py"), "sample", "--qrels", str(tmp_path / "qrels.tsv"),
                    "--queries", str(tmp_path / "queries.jsonl"), "--corpus", str(tmp_path / "corpus.jsonl"),
                    "--runs", str(tmp_path / "r.run"), "--out", str(csv_path)], check=True, capture_output=True)
    text = csv_path.read_text(encoding="utf-8")
    assert "d2" in text and "d3" in text and ",d1," not in text  # d1 ya tiene juicio
    import csv as _csv
    rows = list(_csv.DictReader(open(csv_path, encoding="utf-8")))
    rows[0]["label"] = "2"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    subprocess.run([sys.executable, str(ROOT / "src" / "review_sample.py"), "merge", "--csv", str(csv_path),
                    "--out", str(tmp_path / "extra.tsv")], check=True, capture_output=True)
    assert (tmp_path / "extra.tsv").read_text(encoding="utf-8").strip() == f"q1\t{rows[0]['docid']}\t2"

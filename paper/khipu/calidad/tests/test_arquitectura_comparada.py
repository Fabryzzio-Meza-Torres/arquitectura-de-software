"""Pruebas de lo agregado para comparar la arquitectura base con la propuesta."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from compare_rankings import alpha_sweep, auc, compare, fuse, spearman  # noqa: E402
from io_formats import load_latency, load_run, load_stages, write_run  # noqa: E402
from latency import summarize_latency, summarize_stages  # noqa: E402
from onepagers import build, coverage, load_onepagers  # noqa: E402
from result_writer import ResultWriter  # noqa: E402


# ------------------------------------------------------------------ latencia
def test_p99_con_y_sin_respuestas_vacias():
    rows = [(f"q{i}", 100.0, "ok") for i in range(98)] + [("q98", 2500.0, "timeout"), ("q99", 2500.0, "timeout")]
    s = summarize_latency(rows)
    assert s["p99_ms"] == 2500.0               # todas las solicitudes: la cola se ve
    assert s["p99_with_results_ms"] == 100.0   # solo las que entregan resultados: la cola se esconde
    assert s["n_with_results"] == 98


def test_solicitudes_adicionales_en_porcentaje():
    rows = [(f"q{i}", 10.0, "ok") for i in range(50)]
    s = summarize_latency(rows, extra_requests=4)
    assert s["extra_requests_pct"] == pytest.approx(8.0)
    assert "extra_requests_pct" not in summarize_latency(rows)  # sin dato no se inventa un 0 %


def test_writer_guarda_extra_y_etapas(tmp_path):
    with ResultWriter(str(tmp_path / "exp")) as rw:
        with rw.request("q1") as r:
            with r.stage("llm"):
                pass
            with r.stage("llm"):
                pass
            r.add_extra()
            r.set_results({"d1": 1.0})
        with rw.request("q2") as r:
            r.set_results({"d2": 1.0})
    rows, extra = load_latency(tmp_path / "exp.latency.tsv", with_extra=True)
    assert len(rows) == 2 and extra == 1
    stages = load_stages(tmp_path / "exp.stages.tsv")
    assert [s[1] for s in stages] == ["llm", "llm"]
    assert summarize_stages(stages)["llm"]["n"] == 2


def test_writer_sin_extra_mantiene_tres_columnas(tmp_path):
    with ResultWriter(str(tmp_path / "exp")) as rw:
        with rw.request("q1") as r:
            r.set_results({"d1": 1.0})
    assert len((tmp_path / "exp.latency.tsv").read_text(encoding="utf-8").strip().split("\t")) == 3
    assert not (tmp_path / "exp.stages.tsv").exists()


# ------------------------------------------------------------------ one-pagers
def _mini_corpus(root: Path, n=4):
    root.mkdir(parents=True)
    (root / "qrels").mkdir()
    with open(root / "corpus.jsonl", "w", encoding="utf-8") as f:
        for i in range(n):
            f.write(json.dumps({"_id": f"d{i}", "title": f"t{i}", "text": "texto largo " * 50}) + "\n")
    (root / "queries.jsonl").write_text(json.dumps({"_id": "q1", "text": "hola"}) + "\n", encoding="utf-8")
    (root / "qrels" / "test.tsv").write_text("query-id\tcorpus-id\tscore\nq1\td0\t1\n", encoding="utf-8")


def _write_ops(path: Path, ids, text="resumen corto"):
    with open(path, "w", encoding="utf-8") as f:
        for i in ids:
            f.write(json.dumps({"_id": i, "text": f"{text} {i}", "model": "m", "prompt_sha": "abc12345"}, ensure_ascii=False) + "\n")


def test_onepagers_cobertura_y_build(tmp_path):
    data = tmp_path / "fiqa-8000"
    _mini_corpus(data)
    _write_ops(tmp_path / "op.jsonl", ["d0", "d1"])
    ops = load_onepagers(tmp_path / "op.jsonl")
    cov = coverage({"d0", "d1", "d2", "d3"}, ops)
    assert cov["missing"] == ["d2", "d3"] and cov["coverage"] == 0.5
    with pytest.raises(ValueError, match="Faltan 2"):
        build(data, ops)
    _write_ops(tmp_path / "op2.jsonl", ["d0", "d1", "d2", "d3"])
    out = build(data, load_onepagers(tmp_path / "op2.jsonl"))
    assert out.name == "fiqa-8000-onepager"
    first = json.loads((out / "corpus.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert first["text"] == "resumen corto d0" and first["title"] == "t0"
    assert (out / "qrels" / "test.tsv").exists() and (out / "ONEPAGERS.json").exists()


def test_onepagers_rechaza_vacios_y_repetidos(tmp_path):
    p = tmp_path / "op.jsonl"
    p.write_text(json.dumps({"_id": "d0", "text": "  "}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="vacío"):
        load_onepagers(p)
    p.write_text(json.dumps({"_id": "d0", "text": "a"}) + "\n" + json.dumps({"_id": "d0", "text": "b"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="repetido"):
        load_onepagers(p)


# ------------------------------------------------------------------ comparación
def test_auc_y_spearman_valores_conocidos():
    assert auc(np.array([0.9, 0.8, 0.2, 0.1]), np.array([True, True, False, False])) == 1.0
    assert auc(np.array([0.1, 0.2, 0.8, 0.9]), np.array([True, True, False, False])) == 0.0
    assert auc(np.array([0.5, 0.5]), np.array([True, False])) == 0.5          # empate
    assert np.isnan(auc(np.array([0.5, 0.6]), np.array([True, True])))         # sin negativos no se define
    assert spearman(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0])) == pytest.approx(1.0)


def _runs_para_comparar(tmp_path):
    qrels = tmp_path / "qrels.tsv"
    # q1: d1,d2,d3 relevantes; q2: d4 relevante; d9 y d8 juzgados no relevantes
    qrels.write_text("q1\td1\t1\nq1\td2\t1\nq1\td3\t1\nq1\td9\t0\nq2\td4\t1\nq2\td8\t0\n", encoding="utf-8")
    lex = {"q1": {"d9": 1.0, "d5": 0.9, "d6": 0.8, "d1": 0.1}, "q2": {"d4": 1.0, "d5": 0.5, "d6": 0.2, "d8": 0.1}}
    base = {"q1": {"d1": 1.0, "d2": 0.9, "d5": 0.8, "d9": 0.1}, "q2": {"d8": 1.0, "d4": 0.9, "d5": 0.5, "d6": 0.1}}
    prop = {"q1": {"d1": 1.0, "d2": 0.9, "d3": 0.8, "d9": 0.1}, "q2": {"d4": 1.0, "d8": 0.9, "d5": 0.5, "d6": 0.1}}
    paths = {}
    for name, run in (("lexical", lex), ("base", base), ("proposed", prop)):
        paths[name] = str(tmp_path / f"{name}.run")
        write_run(paths[name], run, name)
    return str(qrels), paths


def test_compare_cuenta_consultas_donde_gana_el_lexico(tmp_path):
    qrels, paths = _runs_para_comparar(tmp_path)
    s = compare(qrels, paths, str(tmp_path / "cmp"))
    assert s["n_queries"] == 2
    # q2: el léxico pone d4 primero (P@3 = 1/3) y la base lo pone segundo (también 1/3): empate;
    # q1: el léxico no tiene relevantes en el top 3 salvo ninguno (d1 está 4.º): pierde contra la base
    w = s["pairwise_wins"]["lexical vs base"]["P@3"]
    assert w["a_gana"] == 0 and w["b_gana"] == 1 and w["empate"] == 1
    assert s["means"]["proposed"]["P@3"] > s["means"]["lexical"]["P@3"]
    assert (tmp_path / "cmp.join.csv").exists() and (tmp_path / "cmp.comparison.md").exists()
    # el join trae una fila por (consulta, documento) y deja vacío lo que no está en un run
    lines = (tmp_path / "cmp.join.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("qid,docid,grade,lexical_rank")
    d3 = [l for l in lines if l.startswith("q1,d3,")][0].split(",")
    assert d3[3] == "" and d3[7] != ""   # d3 no está en léxico, sí en propuesta


def test_pointwise_excluye_sin_juicio_por_defecto(tmp_path):
    qrels, paths = _runs_para_comparar(tmp_path)
    s = compare(qrels, paths, str(tmp_path / "cmp"))
    n_default = s["pointwise"]["lexical"]["n_pairs"]
    s2 = compare(qrels, paths, str(tmp_path / "cmp2"), unjudged_as_negative=True)
    assert s2["pointwise"]["lexical"]["n_pairs"] > n_default   # d5, d6 sin juicio solo entran como negativos
    assert s["pointwise"]["proposed"]["auc_pooled"] >= s["pointwise"]["lexical"]["auc_pooled"]


def test_alpha_0_es_lexico_y_alpha_1_es_semantico(tmp_path):
    qrels = tmp_path / "qrels.tsv"
    qrels.write_text("q1\tdA\t1\nq1\tdB\t0\nq1\tdC\t0\n", encoding="utf-8")
    lex = {"q1": {"dA": 0.1, "dB": 0.9, "dC": 0.5}}    # el léxico pone dA al final
    sem = {"q1": {"dA": 0.9, "dB": 0.1, "dC": 0.5}}    # el semántico pone dA primero
    write_run(str(tmp_path / "lex.run"), lex, "lex")
    write_run(str(tmp_path / "sem.run"), sem, "sem")
    table = alpha_sweep(str(qrels), str(tmp_path / "lex.run"), str(tmp_path / "sem.run"), str(tmp_path / "a"))
    by = {round(r["alpha"], 1): r for r in table}
    assert by[0.0]["P@3"] == pytest.approx(1 / 3) and by[1.0]["P@3"] == pytest.approx(1 / 3)
    assert by[1.0]["nDCG@3"] == pytest.approx(1.0) and by[0.0]["nDCG@3"] < 1.0
    assert (tmp_path / "a.alpha.csv").exists()


def test_fuse_normaliza_y_une_candidatos():
    f = fuse({"a": 10.0, "b": 0.0}, {"b": 5.0, "c": 1.0}, 0.5)
    assert f["a"] == pytest.approx(0.5) and f["b"] == pytest.approx(0.5) and f["c"] == pytest.approx(0.0)

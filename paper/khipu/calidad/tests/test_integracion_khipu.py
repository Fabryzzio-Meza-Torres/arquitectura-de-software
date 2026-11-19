"""Pruebas de la integración con paper/khipu: candidatos, LLM (modos), armado de rankings y consistencia con el sistema."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import armar_runs  # noqa: E402
import candidatos  # noqa: E402
import compare_rankings as cr  # noqa: E402
import llm_semantico as llm  # noqa: E402
from io_formats import load_run  # noqa: E402


def _toy():
    ids = [f"d{i:02d}" for i in range(30)]
    rng = np.random.default_rng(0)
    emb = rng.normal(size=(30, 8)).astype(np.float32)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    lex_table = {"q uno": rng.random(30), "q dos": rng.random(30)}
    q_emb = {"q uno": emb[3] + 0.05, "q dos": emb[20] - 0.05}
    return ids, emb, lex_table, q_emb


def test_candidatos_son_la_union_de_los_dos_top10():
    ids, emb, lex_table, q_emb = _toy()
    rows = candidatos.construir(ids, emb, [("1", "q uno")], lambda q: lex_table[q], lambda q: q_emb[q])
    lex = lex_table["q uno"]
    sem = emb @ q_emb["q uno"]
    esperado = set(np.argsort(-lex)[:10]) | set(np.argsort(-sem)[:10])
    assert {d["id"] for d in rows[0]["docs"]} == {ids[i] for i in esperado}
    assert rows[0]["query"] == "q uno"
    assert 10 <= len(rows[0]["docs"]) <= 20


def test_base_coincide_con_la_fusion_del_sistema():
    """Réplica de Engine.fuse (minion_bench.py): min-max por consulta sobre candidatos, alfa=0.85, desempate por id."""
    ids, emb, lex_table, q_emb = _toy()
    rows = candidatos.construir(ids, emb, [("1", "q uno")], lambda q: lex_table[q], lambda q: q_emb[q])
    cands = {r["qid"]: {d["id"]: d for d in r["docs"]} for r in rows}
    base = armar_runs.armar(cands, None, 0.85, 0.85)["base"]["1"]
    docs = rows[0]["docs"]
    mm = lambda x: np.ones_like(x) if x.max() == x.min() else (x - x.min()) / (x.max() - x.min())  # noqa: E731
    lex_n = mm(np.array([d["lex"] for d in docs], dtype=np.float64))
    sem_n = mm(np.array([d["sem"] for d in docs], dtype=np.float64))
    fused = 0.15 * lex_n + 0.85 * sem_n
    esperado = [docs[i]["id"] for i in sorted(range(len(docs)), key=lambda i: (-fused[i], docs[i]["id"]))]
    obtenido = [d for d, _ in sorted(base.items(), key=lambda kv: (-kv[1], kv[0]))]
    assert obtenido == esperado


def test_minmax_constante_vale_uno_como_el_sistema():
    assert cr._minmax({"a": 2.0, "b": 2.0}) == {"a": 1.0, "b": 1.0}


def test_lectura_de_scores_del_llm():
    assert llm.leer_numero("0,85") == 0.85
    assert llm.leer_numero("Score: 7") == 1.0  # se recorta a [0, 1]
    assert llm.leer_numero("no sé") is None
    assert llm.leer_lista("Claro: [0.1, 0.9, 0.5]", 3) == [0.1, 0.9, 0.5]
    assert llm.leer_lista("[0.1]", 3) == [0.1, None, None]
    assert llm.leer_lista("basura", 2) == [None, None]


def _backend_falso(prompt: str) -> str:
    """Puntúa por el largo del documento; así uno-por-uno y por lotes deben dar lo mismo."""
    if "documentos numerados" in prompt:
        partes = [p for p in prompt.split("\n\n") if p.startswith("[") and "]" in p[:4]]
        return json.dumps([round(len(p.split("] ", 1)[1]) / 100, 3) for p in partes])
    doc = prompt.split("Documento:\n", 1)[1].rsplit("\n\nScore:", 1)[0]
    return str(round(len(doc) / 100, 3))


def test_los_dos_modos_dan_los_mismos_scores():
    docs = [(f"d{i}", "x" * (10 + 7 * i)) for i in range(23)]
    a, malos_a = llm.puntuar_consulta("q", docs, _backend_falso, "paralelo4")
    b, malos_b = llm.puntuar_consulta("q", docs, _backend_falso, "lote10")
    assert a == b and malos_a == malos_b == 0
    assert len(a) == 23


def test_score_ilegible_vale_cero_y_se_cuenta():
    docs = [("d1", "texto"), ("d2", "texto")]
    scores, malos = llm.puntuar_consulta("q", docs, lambda p: "no sé", "paralelo4")
    assert scores == {"d1": 0.0, "d2": 0.0} and malos == 2


def test_armar_exige_los_mismos_candidatos():
    cands = {"1": {"a": {"id": "a", "lex": 1.0, "sem": 0.5}, "b": {"id": "b", "lex": 0.2, "sem": 0.9}}}
    with pytest.raises(SystemExit):
        armar_runs.armar(cands, {"1": {"a": 0.4}}, 0.85, 0.5)


def test_flujo_completo_hasta_la_comparacion(tmp_path):
    ids, emb, lex_table, q_emb = _toy()
    consultas = [("1", "q uno"), ("2", "q dos")]
    rows = candidatos.construir(ids, emb, consultas, lambda q: lex_table[q], lambda q: q_emb[q])
    cand_file = tmp_path / "c.jsonl"
    cand_file.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    scores_file = tmp_path / "l.jsonl"
    with open(scores_file, "w", encoding="utf-8") as f:
        for r in rows:
            for d in r["docs"]:
                f.write(json.dumps({"qid": r["qid"], "id": d["id"], "score": (int(d["id"][1:]) % 7) / 7}) + "\n")
    runs = armar_runs.armar(armar_runs.cargar_candidatos(str(cand_file)), armar_runs.cargar_llm(str(scores_file)),
                            0.85, 0.5)
    from io_formats import write_run
    paths = {}
    for n in ("lexical", "base", "proposed"):
        write_run(tmp_path / f"{n}.run", runs[n], tag=n)
        paths[n] = str(tmp_path / f"{n}.run")
    qrels = tmp_path / "qrels.tsv"
    qrels.write_text("query-id\tcorpus-id\tscore\n" + "".join(
        f"{r['qid']}\t{r['docs'][0]['id']}\t1\n" for r in rows), encoding="utf-8")
    out = cr.compare(str(qrels), paths, str(tmp_path / "cmp"), unjudged_as_negative=True)
    assert (tmp_path / "cmp.comparison.md").exists()
    assert set(load_run(paths["proposed"])["1"]) == set(load_run(paths["base"])["1"])
    assert out is not None


def test_calidad_por_ruta(tmp_path):
    import calidad_por_ruta as cpr
    qrels = tmp_path / "q.tsv"
    qrels.write_text("query-id\tcorpus-id\tscore\n1\ta\t1\n1\tb\t1\n2\tc\t1\n", encoding="utf-8")
    reg = [
        {"condition": "L100", "qid": "1", "t_sched": 40.0, "route": "reranked", "doc_ids": ["a", "b", "x"]},
        {"condition": "L100", "qid": "2", "t_sched": 41.0, "route": "reranked", "doc_ids": ["x", "y", "z"]},
        {"condition": "L100", "qid": "1", "t_sched": 5.0, "route": "reranked", "doc_ids": ["x", "y", "z"]},  # calentamiento
        {"condition": "F6", "qid": "1", "t_sched": 50.0, "route": "error", "doc_ids": []},
    ]
    d = tmp_path / "res"
    d.mkdir()
    (d / "requests_fiqa_rep1_L100.jsonl").write_text("\n".join(json.dumps(r) for r in reg[:3]), encoding="utf-8")
    (d / "requests_fiqa_rep1_F6.jsonl").write_text(json.dumps(reg[3]), encoding="utf-8")
    rows = {(r["condition"], r["route"]): r for r in cpr.calcular(str(d), str(qrels))}
    assert rows[("L100", "reranked")]["n"] == 2
    assert rows[("L100", "reranked")]["P@3"] == pytest.approx((2 / 3 + 0) / 2)
    assert rows[("F6", "error")]["P@3"] == 0.0  # sin resultados cuenta como 0


# ------------------------------------------------------------------ RG-S, batches y one-pagers
class _ScorerFalso:
    """Reparte probabilidad entre las etiquetas 0-4 según el largo del prompt; guarda el tamaño de cada pasada."""

    def __init__(self):
        self.pasadas = []

    def probs(self, prompts):
        self.pasadas.append(len(prompts))
        out = []
        for p in prompts:
            k = (len(p) // 7) % 5
            pr = [0.02] * 5
            pr[k] = 0.92
            out.append((pr, 0.9))
        return out


def test_esperanza_es_continua_y_en_0_1():
    assert llm.esperanza([1, 0, 0, 0, 0]) == 0.0
    assert llm.esperanza([0, 0, 0, 0, 1]) == 1.0
    assert llm.esperanza([0.2, 0.2, 0.2, 0.2, 0.2]) == pytest.approx(0.5)
    assert 0 < llm.esperanza([0.1, 0.1, 0.6, 0.1, 0.1]) < 1
    assert llm.esperanza([0, 0, 0, 0, 0]) == 0.0


def test_batch_de_4_y_de_10_dan_los_mismos_scores_y_las_pasadas_esperadas():
    docs = [(f"d{i:02d}", "palabra " * (5 + 3 * i)) for i in range(20)]
    s4, s10 = _ScorerFalso(), _ScorerFalso()
    a, malos_a = llm.puntuar_consulta_rgs("q", docs, s4, "lote4")
    b, malos_b = llm.puntuar_consulta_rgs("q", docs, s10, "lote10")
    c, _ = llm.puntuar_consulta_rgs("q", docs, _ScorerFalso(), "paralelo4")
    assert a == b == c and malos_a == malos_b == 0
    assert s4.pasadas == [4] * 5 and s10.pasadas == [10] * 2  # 20 candidatos: 5 pasadas de 4 o 2 de 10
    assert len(set(a.values())) > 3  # no binario: varios valores distintos


def test_modo_invalido_y_masa_baja():
    class Malo:
        def probs(self, prompts):
            return [([0.2] * 5, 0.1) for _ in prompts]
    scores, malos = llm.puntuar_consulta_rgs("q", [("a", "x"), ("b", "y")], Malo(), "lote4")
    assert malos == 2 and set(scores) == {"a", "b"}
    with pytest.raises(ValueError):
        llm.puntuar_consulta_rgs("q", [("a", "x")], Malo(), "raro")


def test_helpers_de_onepagers():
    import generar_onepagers as go
    assert go.pendientes(["a", "b", "c"], {"b": {}}) == ["a", "c"]
    assert go.limpiar("  Digest:  hola\n mundo ") == "hola mundo"
    p = go.prompt_para({"title": "T", "text": "x" * 10000}, 90)
    assert "Title: T" in p and "90 words" in p and len(p) < 7000
    assert len(go.prompt_sha_onepager()) == 8


def test_submuestra_conserva_solo_relevantes_de_dev_y_test(tmp_path):
    import subsample_corpus as sc
    d = tmp_path / "fiqa"
    (d / "qrels").mkdir(parents=True)
    (d / "corpus.jsonl").write_text("\n".join(json.dumps({"_id": f"d{i}", "title": "", "text": "t"}) for i in range(50)),
                                    encoding="utf-8")
    (d / "queries.jsonl").write_text(json.dumps({"_id": "1", "text": "q"}), encoding="utf-8")
    for split, doc in (("train", "d1"), ("dev", "d2"), ("test", "d3")):
        (d / "qrels" / f"{split}.tsv").write_text(f"query-id\tcorpus-id\tscore\n1\t{doc}\t1\n", encoding="utf-8")
    assert sc.kept_ids(d, "relevant") == {"d1", "d2", "d3"}
    assert sc.kept_ids(d, "relevant", ["dev", "test"]) == {"d2", "d3"}
    sc.make_subsamples(d, [10], 42, "relevant", tmp_path, ["dev", "test"])
    ids = {json.loads(l)["_id"] for l in open(tmp_path / "fiqa-10" / "corpus.jsonl", encoding="utf-8")}
    assert {"d2", "d3"} <= ids and len(ids) == 10


def test_respaldo_de_onepager_y_modulos_nuevos_importan():
    import generar_onepagers as go
    import pipeline  # noqa: F401
    import verificar_modelo  # noqa: F401
    r = go.respaldo({"title": "Titulo", "text": "una dos tres cuatro cinco seis siete"}, 5)
    assert r == "Titulo. una dos tres cuatro" and len(r.split()) == 5


def test_pipeline_parametros_por_defecto():
    import pipeline
    a = pipeline.parse(["--work-dir", "/tmp/x"])
    assert a.size == 8000 and a.batches_latencia == ["lote4", "lote10"] and not a.smoke
    assert pipeline.parse(["--work-dir", "/tmp/x", "--size", "10000"]).size == 10000


def test_shards_reparten_sin_repetir_ni_perder():
    import generar_onepagers as go
    ids = [f"d{i}" for i in range(10)]
    partes = [go.en_shard(ids, i, 3) for i in (1, 2, 3)]
    assert sorted(sum(partes, [])) == sorted(ids) and len({d for p in partes for d in p}) == 10
    with pytest.raises(ValueError):
        go.en_shard(ids, 4, 3)


def test_merge_de_onepagers(tmp_path):
    import onepagers as op

    def w(name, recs):
        p = tmp_path / name
        p.write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
        return str(p)
    a = w("a.jsonl", [{"_id": "1", "text": "uno", "model": "m", "prompt_sha": "x"}])
    b = w("b.jsonl", [{"_id": "2", "text": "dos", "model": "m", "prompt_sha": "x"}])
    assert op.merge([a, b], tmp_path / "m.jsonl") == 2
    c = w("c.jsonl", [{"_id": "3", "text": "tres", "model": "otro", "prompt_sha": "x"}])
    with pytest.raises(ValueError):
        op.merge([a, c], tmp_path / "m2.jsonl")  # modelos distintos
    d = w("d.jsonl", [{"_id": "1", "text": "distinto", "model": "m", "prompt_sha": "x"}])
    with pytest.raises(ValueError):
        op.merge([a, d], tmp_path / "m3.jsonl")  # mismo doc, texto distinto


def test_nan_no_rompe_el_score():
    nan = float("nan")
    assert llm.esperanza([nan, 0.1, 0.1, 0.1, 0.1]) == 0.0
    class Malo:
        def probs(self, prompts):
            return [([nan] * 5, nan) for _ in prompts]
    scores, malos = llm.puntuar_consulta_rgs("q", [("a", "x")], Malo(), "lote4")
    assert scores == {"a": 0.0} and malos == 1


def test_reporte_final_genera_md_y_graficos(tmp_path):
    import reporte_final as rf
    from io_formats import write_run
    rng = np.random.default_rng(1)
    tag = "Modelo-1.5B"
    out = tmp_path / "calidad_out"
    (out / f"test_{tag}").mkdir(parents=True)
    qids = [str(i) for i in range(30)]
    qrels = tmp_path / "test.tsv"
    qrels.write_text("query-id\tcorpus-id\tscore\n" + "".join(f"{q}\td{int(q) % 7}\t1\n" for q in qids), encoding="utf-8")
    for n in ("lexical", "base", "proposed"):
        write_run(out / f"test_{tag}" / f"{n}.run", {q: {f"d{k}": float(rng.random()) for k in range(8)} for q in qids}, tag=n)
    (out / f"comparacion_{tag}.comparison.json").write_text("{}", encoding="utf-8")
    (out / f"alpha_{tag}.alpha.csv").write_text("alpha,P@3,nDCG@3\n0.0,0.2,0.3\n0.5,0.3,0.4\n1.0,0.25,0.35\n", encoding="utf-8")
    for modo, ms in (("lote4", 900.0), ("lote10", 600.0)):
        (out / f"fiqa.test.{tag}.{modo}.tiempos.tsv").write_text("".join(f"{q}\t{ms + int(q)}\tok\n" for q in qids), encoding="utf-8")
        (out / f"fiqa.test.{tag}.{modo}.scores.jsonl").write_text("".join(
            json.dumps({"qid": q, "id": f"d{k}", "score": round(float(rng.random()), 3) if modo == "lote4" else 0.5})
            + "\n" for q in qids for k in range(8)), encoding="utf-8")
    (out / "entorno.json").write_text(json.dumps({"gpu": "T4", "plataforma": "x", "smoke": True}), encoding="utf-8")
    md = rf.generar(str(out), str(qrels))
    texto = md.read_text(encoding="utf-8")
    assert "prueba corta" in texto and "Propuesta menos base" in texto and "batch" in texto.lower()
    for fig in ("fig1_calidad", "fig2_alfa", "fig3_latencia_llm", "fig4_scores_llm"):
        assert (md.parent / f"{fig}_{tag}.png").exists()
    assert (md.parent / "resumen.json").exists()

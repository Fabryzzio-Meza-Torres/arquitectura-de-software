"""Pruebas del BM25, las estadísticas, la descarga local y el flujo completo, con un dataset de juguete."""
import json
import math
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bm25_baseline import BM25, tokenize  # noqa: E402
from dataset_stats import compute_stats  # noqa: E402
from download_data import download, update_manifest  # noqa: E402
from make_table import build_table  # noqa: E402


def make_mini(root: Path, name: str = "mini") -> Path:
    """5 queries (qa..qe); cada una tiene 3 documentos relevantes que comparten una palabra única."""
    d = root / name
    (d / "qrels").mkdir(parents=True)
    words = ["alfa", "bravo", "charlie", "delta", "eco"]
    docs, qrels_dev, qrels_test, queries = [], [], [], []
    for qi, w in enumerate(words):
        qid = f"q{qi}"
        queries.append({"_id": qid, "text": f"{w} pregunta"})
        for j in range(3):
            did = f"{qid}_d{j}"
            docs.append({"_id": did, "title": f"Titulo {w}", "text": f"{w} contenido numero {j} sobre {w}"})
            (qrels_dev if qi < 2 else qrels_test).append(f"{qid}\t{did}\t{1 + (j == 0)}")
        qrels_test_target = qrels_dev if qi < 2 else qrels_test
        qrels_test_target.append(f"{qid}\truido{qi}\t0")
    docs += [{"_id": f"ruido{i}", "title": "Otro", "text": "texto generico sin relacion"} for i in range(5)]
    (d / "corpus.jsonl").write_text("\n".join(json.dumps(x) for x in docs) + "\n", encoding="utf-8")
    (d / "queries.jsonl").write_text("\n".join(json.dumps(x) for x in queries) + "\n", encoding="utf-8")
    header = "query-id\tcorpus-id\tscore\n"
    (d / "qrels" / "dev.tsv").write_text(header + "\n".join(qrels_dev) + "\n", encoding="utf-8")
    (d / "qrels" / "test.tsv").write_text(header + "\n".join(qrels_test) + "\n", encoding="utf-8")
    return d


def test_bm25_coincide_con_la_formula_a_mano():
    docs = [("a", "gato gato perro"), ("b", "perro"), ("c", "pez")]
    bm = BM25(k1=1.2, b=0.75).fit(docs)
    n, avgdl = 3, (3 + 1 + 1) / 3
    idf = math.log(1 + (n - 1 + 0.5) / (1 + 0.5))  # "gato" aparece en 1 documento
    expected_a = idf * 2 * 2.2 / (2 + 1.2 * (1 - 0.75 + 0.75 * 3 / avgdl))
    res = bm.search("gato", 10)
    assert [d for d, _ in res] == ["a"]
    assert res[0][1] == pytest.approx(expected_a)
    assert bm.search("inexistente", 10) == []


def test_bm25_orden_y_top_k():
    bm = BM25().fit([("x", "uno dos tres"), ("y", "uno"), ("z", "otra cosa")])
    res = bm.search("uno", 1)
    assert len(res) == 1 and res[0][0] == "y"  # documento más corto puntúa más
    assert "the" not in tokenize("the cat")


def test_stats_del_dataset_de_juguete(tmp_path):
    d = make_mini(tmp_path)
    s = compute_stats(d)
    assert s["n_docs"] == 20 and s["n_queries"] == 5
    assert s["splits"]["dev"]["n_queries_with_relevant"] == 2
    assert s["splits"]["test"]["n_queries_with_relevant"] == 3
    assert s["splits"]["test"]["relevant_per_query"]["mean"] == 3
    assert s["splits"]["test"]["pct_queries_with_3plus_relevant"] == 100.0
    assert s["splits"]["test"]["judged_docs_missing_from_corpus"] == 0
    assert s["examples"]["relevant_doc"]["grade"] == 2 and s["examples"]["not_relevant_doc"]["grade"] == 0


def test_descarga_local_y_manifiesto(tmp_path):
    src = make_mini(tmp_path / "origen", "mini")
    zpath = tmp_path / "fuente" / "mini.zip"
    zpath.parent.mkdir()
    with zipfile.ZipFile(zpath, "w") as z:
        for f in src.rglob("*"):
            if f.is_file():
                z.write(f, f"mini/{f.relative_to(src).as_posix()}")
    root = tmp_path / "data"
    entry = download("mini", root, base_url=zpath.parent.as_uri() + "/{name}.zip")
    update_manifest(root, [entry])
    assert (root / "mini" / "corpus.jsonl").exists()
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    assert len(manifest["mini"]["md5"]) == 32 and len(manifest["mini"]["sha256"]) == 64
    assert download("mini", root, base_url="file:///no-existe/{name}.zip")["status"] == "ya_existia"


def test_zip_inseguro_se_rechaza(tmp_path):
    bad = tmp_path / "fuente" / "malo.zip"
    bad.parent.mkdir()
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("../fuera.txt", "x")
    with pytest.raises(ValueError):
        download("malo", tmp_path / "data", base_url=bad.parent.as_uri() + "/{name}.zip")


def test_run_all_extremo_a_extremo(tmp_path):
    make_mini(tmp_path / "data")
    p = subprocess.run([sys.executable, str(ROOT / "src" / "run_all.py"), "--datasets", "mini", "--skip-download",
                        "--data-root", str(tmp_path / "data"), "--results-root", str(tmp_path / "res")],
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stdout + p.stderr
    s = json.loads((tmp_path / "res" / "mini" / "bm25_test.summary.json").read_text(encoding="utf-8"))
    assert s["metrics"]["P@3"] == pytest.approx(1.0)  # cada query tiene 3 relevantes y BM25 los encuentra
    assert s["metrics"]["nDCG@3"] > 0.9 and s["latency"]["frac_ok"] == 1.0
    assert (tmp_path / "res" / "baseline_bm25.md").exists()


def test_run_all_avisa_si_faltan_datos(tmp_path):
    p = subprocess.run([sys.executable, str(ROOT / "src" / "run_all.py"), "--datasets", "no_existe", "--skip-download",
                        "--data-root", str(tmp_path / "data"), "--results-root", str(tmp_path / "res")],
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 1 and "FALLÓ no_existe" in p.stdout


def test_tabla():
    s = {"n_queries_evaluated": 3, "metrics": {"P@3": 0.5, "nDCG@3": 0.4, "nDCG@10": 0.3, "MRR@10": 0.6, "R@20": 0.7},
         "latency": {"p50_ms": 1.0, "p95_ms": 2.0, "p99_ms": 3.0, "frac_ok": 0.9}}
    t = build_table([("BM25", s)])
    assert "| BM25 | 3 | 0.500" in t and "10.0%" in t

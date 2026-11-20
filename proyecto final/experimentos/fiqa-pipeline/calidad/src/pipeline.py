"""Pipeline completo de la comparación base contra propuesta, igual en Kaggle, Khipu o una PC con GPU.

Pasos: verificar modelos -> bajar FiQA -> submuestra con los relevantes de dev y test -> one-pagers -> dataset de
one-pagers -> candidatos (dev y test) -> score del sLLM (RG-S) con batch 4 y 10 -> α de la propuesta con dev ->
rankings y comparación en test -> reporte final (reporte/reporte.md y gráficos). Cada paso se salta si su salida ya existe, así que se puede reiniciar.

  python calidad/src/pipeline.py --work-dir /ruta/trabajo --smoke          # prueba de que todo encadena (números sin valor)
  python calidad/src/pipeline.py --work-dir /ruta/trabajo --size 8000      # corrida completa
  DRY=1 python calidad/src/pipeline.py --work-dir /tmp/x                   # solo imprime los comandos

One-pagers compartidos (para que todos midan sobre los MISMOS textos): si existe calidad/data/onepagers_fiqa_<size>.jsonl
en el repo, se usa y no se genera nada. Para crearlo entre varias personas, cada una corre su parte:
  python calidad/src/pipeline.py --work-dir <carpeta> --shard 1/3     (otra persona 2/3, otra 3/3)
y luego quien sea los une con `onepagers.py merge` y sube el archivo unido a calidad/data/. También sirve --onepagers <archivo>.
Escribe en <work-dir>/calidad_out/: pasos.json (tiempo de cada paso), entorno.json (GPU y versiones; los tiempos del
sLLM solo son comparables entre corridas con la misma GPU), modelos_ok.json y todos los resultados.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent
KHIPU = SRC.parents[1]  # paper/khipu (en Kaggle el runner arma el mismo árbol)
DRY = bool(os.environ.get("DRY"))
PASOS: list = []


def REPO_ONEPAGERS(size: int) -> Path:
    """Dónde vive en el repo el archivo de one-pagers que usan todos."""
    return KHIPU / "calidad" / "data" / f"onepagers_fiqa_{size}.jsonl"


def py(script: str, *args) -> list:
    return [sys.executable, "-u", str(SRC / script), *map(str, args)]


class Corrida:
    def __init__(self, a):
        self.a = a
        self.out = Path(a.work_dir) / "calidad_out"
        self.data = Path(a.work_dir) / "data"
        self.data1p = Path(a.work_dir) / "data1p"
        self.out.mkdir(parents=True, exist_ok=True)

    def sh(self, cmd, nombre, salida: Path | None = None):
        if salida is not None and Path(salida).exists():
            print(f"\n=== {nombre}: ya existe {salida}, se salta", flush=True)
            return
        t0 = time.perf_counter()
        print(f"\n=== {nombre}\n$ {' '.join(map(str, cmd))}", flush=True)
        if not DRY:
            subprocess.run([str(c) for c in cmd], check=True, cwd=str(KHIPU))
        PASOS.append({"paso": nombre, "segundos": round(time.perf_counter() - t0, 1)})
        (self.out / "pasos.json").write_text(json.dumps(PASOS, indent=1), encoding="utf-8")

    def entorno(self):
        info = {"plataforma": platform.platform(), "python": sys.version.split()[0], "smoke": self.a.smoke}
        try:
            import torch
            info.update({"torch": torch.__version__, "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None})
        except Exception:  # noqa: BLE001
            pass
        (self.out / "entorno.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
        print("entorno:", info, flush=True)

    def modelos(self) -> tuple:
        """Verifica los modelos y devuelve (modelo de one-pagers, modelos que puntúan). Falla ya, no tras horas."""
        a = self.a
        todos = list(dict.fromkeys(a.modelo_onepager + a.modelos_score))
        ok_file = self.out / "modelos_ok.json"
        self.sh(py("verificar_modelo.py", "--modelos", *todos, "--out", ok_file, "--device", a.device),
                "verificar modelos", ok_file)
        ok = json.loads(ok_file.read_text(encoding="utf-8"))["ok"] if not DRY else todos
        op = next((m for m in a.modelo_onepager if m in ok), None)
        score = [m for m in a.modelos_score if m in ok]
        if op is None or not score:
            raise SystemExit(f"Ningún modelo útil pasó la verificación (ver {ok_file}). One-pagers: {op}, sLLM: {score}.")
        print(f"modelo de one-pagers: {op} | sLLM que puntúan: {score}", flush=True)
        return op, score

    def run(self):
        a, o = self.a, self.out
        self.entorno()
        op_model, score_models = self.modelos()
        nq = ["--max-queries", "20"] if a.smoke else []
        size = a.size
        sub = self.data / f"fiqa-{size}"
        self.sh([sys.executable, "-c", f"import sys; sys.path.insert(0,r'{KHIPU}'); import minion_bench as m; "
                 f"m.load_dataset('fiqa', r'{self.data}')"], "descargar FiQA", self.data / "fiqa" / "corpus.jsonl")
        self.sh(py("subsample_corpus.py", "--data-dir", self.data / "fiqa", "--sizes", size, "--keep-splits", "dev",
                   "test", "--out-root", self.data), f"submuestra {size}", sub / "corpus.jsonl")
        # one-pagers: se reutiliza el archivo del repo (o el de --onepagers) para que todos midan sobre los MISMOS textos;
        # si no existe, se generan (retoma si se cortó).
        op = o / f"onepagers_{size}.jsonl"
        compartido = Path(a.onepagers) if a.onepagers else REPO_ONEPAGERS(size)
        if a.shard:  # solo la parte i/N de los one-pagers; luego se unen con `onepagers.py merge`
            i, n = a.shard.split("/")
            parte = o / f"onepagers_{size}.shard{i}de{n}.jsonl"
            self.sh(py("generar_onepagers.py", "--data-dir", sub, "--modelo", op_model, "--out", parte, "--shard", a.shard,
                       "--batch", a.onepager_batch, *(["--max-docs", 64] if a.smoke else [])), f"one-pagers parte {a.shard}")
            print(f"\nListo. Sube {parte} al repo (calidad/data/). Cuando estén todas las partes: "
                  f"python calidad/src/onepagers.py merge --inputs <partes> --out {REPO_ONEPAGERS(size)}", flush=True)
            return
        if compartido.exists() and not op.exists() and not DRY:
            print(f"usando los one-pagers compartidos: {compartido}", flush=True)
            shutil.copy(compartido, op)
        completo = (not DRY and op.exists() and not a.smoke and
                    sum(1 for _ in open(op, encoding="utf-8")) >= sum(1 for _ in open(sub / "corpus.jsonl", encoding="utf-8")))
        self.sh(py("generar_onepagers.py", "--data-dir", sub, "--modelo", op_model, "--out", op,
                   "--batch", a.onepager_batch, *(["--max-docs", 64] if a.smoke else [])), "one-pagers",
                op if completo else None)
        if a.smoke and not DRY:  # en smoke solo hay 64 one-pagers: se recorta la submuestra a esos documentos
            ids = {json.loads(l)["_id"] for l in open(op, encoding="utf-8")}
            keep = [l for l in open(sub / "corpus.jsonl", encoding="utf-8") if json.loads(l)["_id"] in ids]
            open(sub / "corpus.jsonl", "w", encoding="utf-8").writelines(keep)
        self.sh(py("onepagers.py", "check", "--data-dir", sub, "--onepagers", op), "one-pagers: cobertura")
        self.sh(py("onepagers.py", "build", "--data-dir", sub, "--onepagers", op), "dataset de one-pagers")
        if not DRY:
            shutil.rmtree(self.data1p, ignore_errors=True)
            self.data1p.mkdir(parents=True)
            shutil.copytree(self.data / f"fiqa-{size}-onepager", self.data1p / "fiqa")
        for split in ("dev", "test"):
            self.sh(py("candidatos.py", "--dataset", "fiqa", "--data-dir", self.data1p, "--split", split,
                       "--out", o / "fiqa", "--device", a.device, "--encode-batch", 128, *nq),
                    f"candidatos {split}", o / f"fiqa.{split}.candidatos.jsonl")
        for model in score_models:
            tag = model.split("/")[-1]
            q = a.batch_calidad
            for split in ("dev", "test"):
                self.sh(py("llm_semantico.py", "--candidatos", o / f"fiqa.{split}.candidatos.jsonl", "--data-dir",
                           self.data1p, "--dataset", "fiqa", "--modelo", model, "--modo", q, "--device", a.device,
                           "--out", o / f"fiqa.{split}.{tag}.{q}"), f"sLLM {tag} {split} {q}",
                        o / f"fiqa.{split}.{tag}.{q}.scores.jsonl")
            for b in a.batches_latencia:
                if b != q:
                    self.sh(py("llm_semantico.py", "--candidatos", o / "fiqa.test.candidatos.jsonl", "--data-dir",
                               self.data1p, "--dataset", "fiqa", "--modelo", model, "--modo", b, "--device", a.device,
                               "--out", o / f"fiqa.test.{tag}.{b}"), f"sLLM {tag} test {b} (latencia)",
                            o / f"fiqa.test.{tag}.{b}.scores.jsonl")
            dev_run, test_run = o / f"dev_{tag}", o / f"test_{tag}"
            self.sh(py("armar_runs.py", "--candidatos", o / "fiqa.dev.candidatos.jsonl", "--llm",
                       o / f"fiqa.dev.{tag}.{q}.scores.jsonl", "--out", dev_run), f"runs dev {tag}")
            self.sh(py("compare_rankings.py", "alpha", "--qrels", self.data1p / "fiqa" / "qrels" / "dev.tsv",
                       "--lexical", dev_run / "lexical.run", "--semantic", dev_run / "llm.run",
                       "--out", o / f"alpha_{tag}"), f"alfa en dev {tag}")
            alpha = 0.85
            if not DRY:
                rows = list(csv.DictReader(open(o / f"alpha_{tag}.alpha.csv", encoding="utf-8")))
                alpha = float(max(rows, key=lambda r: (float(r["P@3"]), float(r["nDCG@3"])))["alpha"])
            self.sh(py("armar_runs.py", "--candidatos", o / "fiqa.test.candidatos.jsonl", "--llm",
                       o / f"fiqa.test.{tag}.{q}.scores.jsonl", "--alpha-llm", alpha, "--out", test_run),
                    f"runs test {tag} (alfa {alpha})")
            self.sh(py("compare_rankings.py", "compare", "--qrels", self.data1p / "fiqa" / "qrels" / "test.tsv",
                       "--lexical", test_run / "lexical.run", "--base", test_run / "base.run",
                       "--proposed", test_run / "proposed.run", "--out", o / f"comparacion_{tag}"),
                    f"comparación {tag}")
        # reporte final (tabla, IC de la diferencia, latencia por batch y gráficos): cada quien lo genera solo
        self.sh(py("reporte_final.py", "--out-dir", o, "--qrels", self.data1p / "fiqa" / "qrels" / "test.tsv"),
                "reporte final")


def parse(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--size", type=int, default=8000, help="documentos de la submuestra (8000 por defecto; 10000 también sirve)")
    ap.add_argument("--smoke", action="store_true", help="64 one-pagers y 20 consultas: solo prueba el encadenado")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--onepagers", help="archivo de one-pagers ya generado (por defecto: el del repo, si existe)")
    ap.add_argument("--shard", help="i/N: solo genera la parte i de N de los one-pagers y termina (se reparte entre personas)")
    ap.add_argument("--modelo-onepager", nargs="+", default=["Qwen/Qwen2.5-3B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"],
                    help="en orden de preferencia; se usa el primero que pase la verificación")
    ap.add_argument("--modelos-score", nargs="+", default=["Qwen/Qwen2.5-3B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"])
    ap.add_argument("--batch-calidad", default="lote10", help="batch con el que se puntúa dev y test")
    ap.add_argument("--batches-latencia", nargs="+", default=["lote4", "lote10"])
    ap.add_argument("--onepager-batch", type=int, default=16)
    return ap.parse_args(argv)


def main(argv=None):
    a = parse(argv)
    c = Corrida(a)
    try:
        c.run()
    finally:
        if not DRY:
            subprocess.run(["tar", "-czf", str(Path(a.work_dir) / "calidad_results.tar.gz"), "-C", a.work_dir, "calidad_out"])


if __name__ == "__main__":
    main()

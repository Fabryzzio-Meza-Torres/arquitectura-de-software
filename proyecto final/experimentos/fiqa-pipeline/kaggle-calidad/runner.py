"""Kaggle: instala dependencias, arma el árbol de paper/khipu con los datasets adjuntos y lanza calidad/src/pipeline.py.

ANTES de la corrida completa: SMOKE = True (minutos; los números no valen). Luego SMOKE = False.
Resultados: /kaggle/working/calidad_results.tar.gz (se genera aunque algo falle).
"""
import glob, shutil, subprocess, sys
from pathlib import Path

SMOKE = True
SIZE = 8000          # 10000 también sirve; con más documentos tardan más los one-pagers
ONEPAGERS = None     # ruta a un onepagers_*.jsonl ya generado; si no, se busca en los datasets adjuntos
SHARD = None         # "1/3": solo genera la parte 1 de 3 de los one-pagers y termina (se reparte entre personas)

W, K = Path("/kaggle/working"), Path("/kaggle/working/khipu")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bm25s==0.3.16", "PyStemmer==3.1.0"], check=True)
(K / "calidad" / "src").mkdir(parents=True, exist_ok=True)
shutil.copy(glob.glob("/kaggle/input/**/minion_bench.py", recursive=True)[0], K / "minion_bench.py")
shutil.copy(glob.glob("/kaggle/input/**/alpha.json", recursive=True)[0], K / "alpha.json")
for f in glob.glob("/kaggle/input/**/calidad_src/*.py", recursive=True):
    shutil.copy(f, K / "calidad" / "src")
if ONEPAGERS is None:  # si alguien adjuntó un dataset con los one-pagers, se usa
    hallados = glob.glob("/kaggle/input/**/onepagers_*.jsonl", recursive=True)
    ONEPAGERS = hallados[0] if hallados else None
sys.path.insert(0, str(K / "calidad" / "src"))
import pipeline  # noqa: E402

pipeline.main(["--work-dir", str(W), "--size", str(SIZE), *(["--smoke"] if SMOKE else []),
               *(["--onepagers", ONEPAGERS] if ONEPAGERS else []), *(["--shard", SHARD] if SHARD else [])])

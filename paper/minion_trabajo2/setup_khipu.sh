#!/usr/bin/env bash
# Ejecutar en el nodo de acceso; solo preparación/descargas, no benchmark.
set -euo pipefail
PROJ="$HOME/minion_trabajo2"
ENV="$HOME/venvs/minion"
mkdir -p "$PROJ"/{data,logs,results,results_pilot} "$HOME/venvs"
cd "$PROJ"

if [ ! -f "$ENV/bin/activate" ]; then
  python3 -m venv "$ENV"
fi
source "$ENV/bin/activate"
python -m pip install --upgrade pip
python -m pip install torch sentence-transformers transformers faiss-cpu bm25s PyStemmer numpy huggingface_hub pandas matplotlib
python -m pip freeze > requirements_installed.txt

# Modelos en caché persistente del usuario
python - <<'PYMODELS'
from huggingface_hub import snapshot_download
snapshot_download('BAAI/bge-base-en-v1.5', revision='a5beb1e3e68b9ab74eb54cfd186867f64f240e1a')
snapshot_download('cross-encoder/ms-marco-MiniLM-L-6-v2')
PYMODELS

# Si ya subiste los 5 archivos, no se descargan de nuevo.
if [ ! -f data/fiqa/corpus.jsonl ] || [ ! -f data/fiqa/queries.jsonl ] || [ ! -f data/fiqa/qrels/train.tsv ] || [ ! -f data/fiqa/qrels/test.tsv ]; then
  cd data
  if [ ! -f fiqa.zip ]; then
    wget -c https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/fiqa.zip -O fiqa.zip
  fi
  unzip -oq fiqa.zip
  cd ..
fi
python - <<'PYVERIFY'
from pathlib import Path
p = Path('data/fiqa')
for f in ('corpus.jsonl','queries.jsonl','qrels/train.tsv','qrels/dev.tsv','qrels/test.tsv'):
    assert (p/f).is_file(), f'Falta {p/f}'
print('OK: datos FiQA y dependencias preparados')
PYVERIFY

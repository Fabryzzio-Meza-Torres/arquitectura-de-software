#!/usr/bin/env bash
# Khipu, paso 1 (en el nodo de acceso, que tiene internet): entorno, FiQA y modelos. Los nodos de cómputo pueden no tener
# internet, así que todo lo que se descarga se hace aquí. No probado en una sesión real de Khipu: revisar rutas y módulos.
# Uso, desde paper/khipu:   bash calidad/khipu_preparar.sh [DIR_TRABAJO]
set -euo pipefail
W="${1:-$HOME/minion_calidad}"
mkdir -p "$W"
python3 -m venv "$W/venv" && source "$W/venv/bin/activate"
pip install -q numpy bm25s==0.3.16 PyStemmer==3.1.0 sentence-transformers transformers accelerate certifi
export HF_HOME="$W/hf"                      # los modelos quedan aquí; el job usa el mismo HF_HOME
python - <<PY
import sys; sys.path.insert(0, "."); import minion_bench as m
m.load_dataset("fiqa", "$W/data")
from huggingface_hub import snapshot_download
for r in ["Qwen/Qwen2.5-3B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct", "BAAI/bge-base-en-v1.5"]:
    snapshot_download(r)
PY
echo "Listo en $W. Ahora: sbatch calidad/khipu_correr.sbatch   (editar partición y GPU antes: sinfo / myaccount)"

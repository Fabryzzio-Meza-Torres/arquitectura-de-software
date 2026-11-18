#!/bin/bash
#SBATCH --job-name=check-minion311
#SBATCH --account=tesis
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:05:00
#SBATCH --output=logs/check-minion311-%j.out

set -euo pipefail

module load python3/3.11.11
source "$HOME/venvs/minion311/bin/activate"

srun --ntasks=1 "$HOME/venvs/minion311/bin/python" -c '
import sys
import torch
import transformers
import sentence_transformers
import faiss
import bm25s

print("Python:", sys.version)
print("Ejecutable:", sys.executable)
print("PyTorch:", torch.__version__)
print("CUDA:", torch.cuda.is_available())
print("Dependencias OK")
'

#!/bin/bash
#SBATCH --job-name=ciencia-preflight
#SBATCH --partition=gpu
#SBATCH --nodelist=ag001
#SBATCH --gres=gpu:a100_3g.20gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=20G
#SBATCH --time=00:10:00
#SBATCH --output=logs/preflight-%j.log
#SBATCH --error=logs/preflight-%j.log
set -euo pipefail
cd "${MINION_EXPERIMENT_ROOT:?Set MINION_EXPERIMENT_ROOT}"
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
date -Is
nvidia-smi
srun "${MINION_PYTHON:?Set MINION_PYTHON}" -u preflight.py
date -Is

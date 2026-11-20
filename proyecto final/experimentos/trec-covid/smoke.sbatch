#!/bin/bash
#SBATCH --job-name=ciencia-smoke
#SBATCH --partition=gpu
#SBATCH --nodelist=ag001
#SBATCH --gres=gpu:a100_3g.20gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=00:20:00
#SBATCH --output=logs/smoke-%j.log
#SBATCH --error=logs/smoke-%j.log
set -euo pipefail
cd "${MINION_EXPERIMENT_ROOT:?Set MINION_EXPERIMENT_ROOT}/smoke_validation"
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg EXPERIMENT_SMOKE=1
srun "${MINION_PYTHON:?Set MINION_PYTHON}" -u run.py quality
srun "${MINION_PYTHON:?Set MINION_PYTHON}" -u run.py performance
srun "${MINION_PYTHON:?Set MINION_PYTHON}" -u report.py
echo SMOKE_COMPLETE

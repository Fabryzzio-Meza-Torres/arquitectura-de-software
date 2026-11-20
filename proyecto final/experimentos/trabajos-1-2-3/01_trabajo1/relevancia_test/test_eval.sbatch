#!/bin/bash
#SBATCH --job-name=minion-test
#SBATCH --account=investigacion2
#SBATCH --partition=gpu
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:a100_2g.10gb:1
#SBATCH --output=logs/test-%j.log
#SBATCH --error=logs/test-%j.log
set -euo pipefail
cd /home/usuario/projects/minion_fiqa_alpha
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8 MPLBACKEND=Agg
date -Is
hostname
nvidia-smi
srun .venv/bin/python -u minion_test.py "$@"
date -Is
if [[ "$*" != *--pilot* ]]; then
  srun .venv/bin/python -u build_report.py
fi

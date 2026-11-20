#!/bin/bash
#SBATCH --job-name=trec-v4-analysis
#SBATCH --account=investigacion2
#SBATCH --partition=standard
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/trec-v4-analysis-%j.log
#SBATCH --error=logs/trec-v4-analysis-%j.log
set -euo pipefail
cd /home/usuario/projects/minion_trec_khipu_v4_20261118
export MPLBACKEND=Agg OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1
export CUDA_VISIBLE_DEVICES=''
srun /home/usuario/projects/minion_fiqa_alpha/.venv/bin/python -u build_v4_notebook.py

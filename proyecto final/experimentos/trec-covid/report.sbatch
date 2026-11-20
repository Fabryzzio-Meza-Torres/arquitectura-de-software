#!/bin/bash
#SBATCH --job-name=ciencia-report
#SBATCH --partition=standard
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/report-%j.log
#SBATCH --error=logs/report-%j.log
set -euo pipefail
cd "${MINION_EXPERIMENT_ROOT:?Set MINION_EXPERIMENT_ROOT}"
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
date -Is
srun "${MINION_PYTHON:?Set MINION_PYTHON}" -u report.py
tar -czf resultados_completos.tar.gz resultados entrada_comun logs provenance *.py *.sbatch *.json *.txt *.md *.ipynb
sha256sum resultados_completos.tar.gz > resultados_completos.tar.gz.sha256
date -Is

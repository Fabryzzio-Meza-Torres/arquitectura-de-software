#!/bin/bash
#SBATCH --job-name=minion-complementarios
#SBATCH --account=investigacion2
#SBATCH --partition=standard
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/home/usuario/projects/minion_fiqa_alpha/complementarios_20261118/logs/complementarios-%j.log
#SBATCH --error=/home/usuario/projects/minion_fiqa_alpha/complementarios_20261118/logs/complementarios-%j.log
set -euo pipefail
cd /home/usuario/projects/minion_fiqa_alpha/complementarios_20261118
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=4 MPLBACKEND=Agg
export CUDA_VISIBLE_DEVICES=''
date -Is
hostname
srun ../.venv/bin/python -u complementarios.py
date -Is

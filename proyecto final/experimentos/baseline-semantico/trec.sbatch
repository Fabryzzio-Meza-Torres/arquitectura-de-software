#!/bin/bash
#SBATCH --job-name=semantic-only-trec
#SBATCH --account=investigacion2
#SBATCH --partition=gpu
#SBATCH --nodelist=ag001
#SBATCH --gres=gpu:a100_3g.20gb:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:15:00
#SBATCH --output=logs/trec-%j.log
#SBATCH --error=logs/trec-%j.log
set -euo pipefail
cd /home/usuario/projects/minion_semantic_baselines_20261119
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
date -Is
nvidia-smi
srun /home/usuario/projects/minion_fiqa_alpha/.venv/bin/python -u semantic_baseline.py --dataset trec --smoke
srun /home/usuario/projects/minion_fiqa_alpha/.venv/bin/python -u semantic_baseline.py --dataset trec
date -Is

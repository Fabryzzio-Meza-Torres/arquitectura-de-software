#!/bin/bash
#SBATCH --job-name=semantic-only-fiqa
#SBATCH --account=investigacion2
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:20:00
#SBATCH --output=logs/fiqa-%j.log
#SBATCH --error=logs/fiqa-%j.log
set -euo pipefail
cd /home/usuario/projects/minion_semantic_baselines_20261119
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
date -Is
nvidia-smi
srun /home/usuario/projects/minion_fiqa_alpha/.venv/bin/python -u semantic_baseline.py --dataset fiqa --smoke
srun /home/usuario/projects/minion_fiqa_alpha/.venv/bin/python -u semantic_baseline.py --dataset fiqa
date -Is

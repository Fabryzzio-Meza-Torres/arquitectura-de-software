#!/bin/bash
#SBATCH --job-name=fiqa-qwen-quality
#SBATCH --account=tesis
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=logs/calidad-%j.out
set -euo pipefail
module load python3/3.11.11
source ~/venvs/minion311/bin/activate
cd ~/minion_fiqa_llm_v2
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4
python codigo/minion_v2.py quality --dataset fiqa --data data/fiqa --cache data/cache --out results/calidad --batch 4 --topk 3

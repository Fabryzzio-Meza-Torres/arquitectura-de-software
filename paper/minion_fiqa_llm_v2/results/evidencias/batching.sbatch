#!/bin/bash
#SBATCH --job-name=fiqa-qwen-batch
#SBATCH --account=tesis
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=logs/batch-%j.out
set -euo pipefail
module load python3/3.11.11
source ~/venvs/minion311/bin/activate
cd ~/minion_fiqa_llm_v2
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4
python codigo/minion_v2.py batch --dataset fiqa --data data/fiqa --cache data/cache --out results/batching --batch 4 --topk 3

#!/bin/bash
#SBATCH --job-name=fiqa-qwen-perf
#SBATCH --account=tesis
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=logs/perf-%j.out
set -euo pipefail
module load python3/3.11.11
source ~/venvs/minion311/bin/activate
cd ~/minion_fiqa_llm_v2
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4
# Pilot limited size before increasing request count.
python codigo/minion_v2.py concurrency --dataset fiqa --data data/fiqa --cache data/cache --out results/concurrencia --batch 1 --topk 3 --requests 50 --arm B
python codigo/minion_v2.py latency --dataset fiqa --data data/fiqa --cache data/cache --out results/latencia --batch 1 --topk 3 --requests 50 --arm A
python codigo/minion_v2.py latency --dataset fiqa --data data/fiqa --cache data/cache --out results/latencia --batch 1 --topk 3 --requests 50 --arm B

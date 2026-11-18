#!/bin/bash
#SBATCH --job-name=fiqa-completo-v4
#SBATCH --account=tesis
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=05:00:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail

cd "$HOME/minion_trabajo2"

module load python3/3.11.11
source "$HOME/venvs/minion311/bin/activate"

export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4

echo "=== FIQA COMPLETO V4 ==="
hostname
python --version
nvidia-smi

python -m py_compile minion_bench.py

srun --ntasks=1 python minion_bench.py \
  --dataset fiqa \
  --phase all \
  --reps 3 \
  --calib-queries 500 \
  --ramp-seconds 120 \
  --ramp-rates 1,2,4,8,16,32,64 \
  --cond-seconds 180 \
  --warmup-seconds 30 \
  --conditions all \
  --threads 4 \
  --data-dir data \
  --alpha-json alpha.json \
  --out results_fiqa_completo_v4/

echo "=== EXPERIMENTO FINALIZADO ==="

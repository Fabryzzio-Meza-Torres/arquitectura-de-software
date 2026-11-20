#!/bin/bash
#SBATCH --job-name=minion-pilot-v4b
#SBATCH --account=tesis
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:45:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail

cd "$HOME/minion_trabajo2"

module load python3/3.11.11
source "$HOME/venvs/minion311/bin/activate"

export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4

echo "=== PILOTO MINION V4 ==="
hostname
python --version
nvidia-smi

srun --ntasks=1 python minion_bench.py \
  --dataset fiqa \
  --subset 2000 \
  --phase all \
  --reps 1 \
  --calib-queries 100 \
  --ramp-seconds 60 \
  --ramp-rates 1,2,4,8,16 \
  --cond-seconds 60 \
  --warmup-seconds 10 \
  --conditions all \
  --threads 4 \
  --data-dir data \
  --alpha-json alpha.json \
  --out results_pilot_v4_nuevo/

echo "=== PILOTO FINALIZADO ==="

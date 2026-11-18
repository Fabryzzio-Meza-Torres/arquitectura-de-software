#!/bin/bash
#SBATCH --job-name=minion-calib-diag
#SBATCH --account=tesis
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail

cd "$HOME/minion_trabajo2"

module load python3/3.11.11
source "$HOME/venvs/minion311/bin/activate"

export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

srun --ntasks=1 "$HOME/venvs/minion311/bin/python" minion_bench.py \
  --dataset fiqa \
  --subset 2000 \
  --phase calib \
  --calib-queries 100 \
  --ramp-seconds 60 \
  --ramp-rates 1,2,4,8,16 \
  --threads 4 \
  --data-dir data \
  --alpha-json alpha.json \
  --out results_calib_diagnostico/

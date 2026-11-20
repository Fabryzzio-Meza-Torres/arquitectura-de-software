#!/usr/bin/env bash
#SBATCH --job-name=minion-fiqa
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
nvidia-smi
# Repeticiones finales: lee calibration.json ya confirmado.
test -s results/calibration.json || { echo 'Falta results/calibration.json'; exit 1; }
srun python minion_bench.py --dataset fiqa --phase runs --reps 3 \
    --threads 4 --data-dir data --alpha-json alpha.json --out results/

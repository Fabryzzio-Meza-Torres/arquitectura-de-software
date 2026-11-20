#!/bin/bash
#SBATCH --job-name=trec-fixed-load-v4
#SBATCH --account=investigacion2
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=05:00:00
#SBATCH --output=logs/trec-fixed-load-v4-%j.log
#SBATCH --error=logs/trec-fixed-load-v4-%j.log
set -euo pipefail
cd /home/usuario/projects/minion_trec_khipu_v4_20261118
module load python3/3.11.11
source .venv311_exact/bin/activate
export HF_HOME="$PWD/hf_home"
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
date -Is
hostname
python --version
nvidia-smi
python comparability_check.py
python prepare_fixed_load.py
cat fixed_load_plan.json
srun --ntasks=1 python -u minion_bench.py \
 --dataset trec-covid --phase runs --reps 3 --calib-queries 500 \
 --ramp-seconds 120 --ramp-rates 1,2,4,8,16,32,64 \
 --cond-seconds 180 --warmup-seconds 30 --conditions all --threads 4 \
 --data-dir data --alpha-json alpha.json --out results_trec_covid_carga_fija_v4/
nvidia-smi
date -Is

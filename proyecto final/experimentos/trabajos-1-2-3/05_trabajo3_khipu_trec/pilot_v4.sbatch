#!/bin/bash
#SBATCH --job-name=trec-pilot-v4
#SBATCH --account=investigacion2
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --output=logs/trec-pilot-v4-%j.log
#SBATCH --error=logs/trec-pilot-v4-%j.log
set -euo pipefail
cd /home/usuario/projects/minion_trec_khipu_v4_20261118
module load python3/3.11.11
source .venv311_exact/bin/activate
export HF_HOME="$PWD/hf_home"
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4
date -Is
hostname
nvidia-smi
python comparability_check.py
mkdir -p pilot
python -c 'import json; json.dump({"C_qps":1.0,"hedge_threshold_ms":200.0,"purpose":"PILOT ONLY synthetic scheduling values; final job recalibrates"},open("pilot/calibration.json","w"))'
srun --ntasks=1 python -u minion_bench.py --dataset trec-covid --subset 2000 \
 --phase runs --reps 1 --cond-seconds 20 --warmup-seconds 5 \
 --conditions L100,F1,F2,F3H,F3NH,F4,F5,F6 --threads 4 \
 --data-dir data --alpha-json alpha.json --out pilot/
python pilot_validate.py
date -Is

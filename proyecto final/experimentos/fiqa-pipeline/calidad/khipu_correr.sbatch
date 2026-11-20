#!/usr/bin/env bash
#SBATCH --job-name=minion-calidad
#SBATCH --partition=gpu            # VERIFICAR con `sinfo` y `myaccount` (puede ser otra partición)
#SBATCH --gres=gpu:1               # VERIFICAR la sintaxis (shard/MIG/GPU completa) en la guía de Khipu
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=minion_calidad_%j.log
# Khipu, paso 2. Se lanza desde paper/khipu:  sbatch calidad/khipu_correr.sbatch
# Cambiar SMOKE=1 por SMOKE=0 para la corrida completa. No probado en una sesión real de Khipu.
set -euo pipefail
W="${W:-$HOME/minion_calidad}"
source "$W/venv/bin/activate"
export HF_HOME="$W/hf" HF_HUB_OFFLINE=1      # los modelos ya se descargaron en el nodo de acceso
SMOKE="${SMOKE:-1}"
nvidia-smi || true
python calidad/src/pipeline.py --work-dir "$W/run" $([ "$SMOKE" = 1 ] && echo --smoke) ${SIZE:+--size $SIZE} \
    ${ONEPAGERS:+--onepagers $ONEPAGERS}
echo "Resultados: $W/run/calidad_results.tar.gz  (copiarlos fuera de Khipu: no hay backup)"

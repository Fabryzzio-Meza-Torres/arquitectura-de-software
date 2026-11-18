#!/bin/bash
#SBATCH --job-name=verificar-python
#SBATCH --account=tesis
#SBATCH --partition=data-science
#SBATCH --nodelist=ds001
#SBATCH --gres=shard:1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:03:00
#SBATCH --output=logs/verificar-python-%j.out

set -euo pipefail

module load python3/3.11.11

echo "Python del módulo:"
python3 --version
which python3

echo "Python del entorno virtual:"
"$HOME/venvs/minion/bin/python" --version

echo "Comprobación de annotations:"
python3 -c "from __future__ import annotations; print('OK')"

echo "Verificación completada"

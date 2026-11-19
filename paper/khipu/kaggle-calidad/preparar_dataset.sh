#!/usr/bin/env bash
# Arma kaggle-calidad/dataset/ con los scripts de calidad/src (carpeta calidad_src) para subirlos como dataset.
# Desde paper/khipu:  bash kaggle-calidad/preparar_dataset.sh
set -euo pipefail
rm -rf kaggle-calidad/dataset && mkdir -p kaggle-calidad/dataset/calidad_src
cp calidad/src/*.py kaggle-calidad/dataset/calidad_src/
cp kaggle-calidad/dataset-metadata.json kaggle-calidad/dataset/
echo "Listo. Subir con: kaggle datasets create -p kaggle-calidad/dataset --dir-mode zip   (o 'version' si ya existe)"
echo "Luego:           kaggle kernels push -p kaggle-calidad"

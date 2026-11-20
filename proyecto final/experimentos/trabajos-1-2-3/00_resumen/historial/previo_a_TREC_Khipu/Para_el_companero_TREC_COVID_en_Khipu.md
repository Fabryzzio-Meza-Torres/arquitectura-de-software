# Corrida pendiente para comparar FiQA y TREC-COVID en Khipu

Debes correr **el Trabajo 3 de latencia y fallas con TREC-COVID**. El Trabajo 1 de relevancia ya está completo para los dos datasets.

Usa el mismo código v4 de la rama `paper/trabajo2`, commit `650c992c4dd6aabd73b06ed9a218eb763ce80fba`, que produjo FiQA en el job `63828`.

## Montaje que debes mantener

- Nodo `ds001`, GPU NVIDIA RTX A6000, partición `data-science` si tu cuenta tiene acceso.
- La misma solicitud de GPU compartida: `--gres=shard:1`.
- 4 CPU, `--threads 4`, 32 GB de RAM; pedir 5 horas como en el job de FiQA.
- Tu propia cuenta autorizada y el mismo entorno o versiones registradas en la corrida de FiQA.
- α = 0,85, cargado del `alpha.json` validado. No volver a ajustarlo.
- Corpus completo: 171.332 documentos. Consultas de test: 50.
- 3 repeticiones, las 13 condiciones, 180 segundos por condición y descarte inicial de 30 segundos.
- Calibración nueva para TREC-COVID: 500 consultas a 1 QPS y rampa 1,2,4,8,16,32,64 de 120 segundos por escalón.
- Mantener la regla v4 de C de ruta completa y el limitador de duplicadas. **No copiar C=8 ni el umbral de hedging de FiQA.**

El `minion_bench.py` de esta rama coincide con el ejecutado al normalizar CRLF a LF. La huella SHA-256 del script con LF debe ser:

`bb027763a577074373d5c1909467fbac67f8b5484d37696b29e1f697f02f22b7`

## Comando del programa dentro del job Slurm

Adapta la cuenta y las rutas a tu entorno autorizado. Conserva el mismo montaje del archivo `job_fiqa_completo_v4.sbatch` y cambia el dataset y el nombre de salida:

```bash
srun --ntasks=1 python minion_bench.py \
  --dataset trec-covid \
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
  --out results_trec_covid_completo_v4/
```

## Evidencia que debes devolver

`calibration.json`, `run_meta.json`, `summary.csv` con 39 filas, los 39 archivos `requests_trec-covid_rep*`, el log de Slurm, el código exacto y las versiones del entorno. Genera después el notebook y las figuras de resultados.

Registra `nvidia-smi` antes y después, procesos concurrentes y uso de GPU. En la corrida de FiQA había otro proceso usando la misma A6000: usar el mismo nodo no garantiza la misma contención ni permite atribuir diferencias solo al dataset.

Esta corrida sigue **pendiente** en la consolidación. El TREC-COVID ya disponible en la otra rama se ejecutó en Kaggle/T4 y se conserva como una serie distinta.

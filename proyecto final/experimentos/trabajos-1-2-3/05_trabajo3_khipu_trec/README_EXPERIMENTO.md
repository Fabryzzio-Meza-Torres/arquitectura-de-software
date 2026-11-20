# TREC-COVID en Khipu: intento de capacidad y ensayo a carga fija

Referencia: FiQA job 63828, `paper/trabajo2`, ds001 / RTX A6000 compartida.

| Registro | Job | Propósito |
|---|---|---|
| Piloto real | 63909 | Validar datos/modelos y ocho rutas con corpus reducido; su calibración diagnóstica no es final |
| Intento original v4 | 63911 | Calibración con corpus completo; falló el criterio de capacidad desde el primer escalón |
| Complementario a carga fija | 63919 | Medir 13 condiciones × 3 repeticiones a los mismos QPS absolutos de FiQA |
| Análisis CPU | 63913 | Verificar solicitudes, generar tablas/nueve figuras y ejecutar el notebook |

`minion_bench.py` es idéntico al código v4 de la referencia, SHA-256 `bb027763a577074373d5c1909467fbac67f8b5484d37696b29e1f697f02f22b7`. Se conservaron α=0,85, versiones, recursos, tiempos de espera, políticas y ventanas. La carga externa se adapta mediante un archivo de entrada, sin editar el benchmark.

## Leer los resultados correctamente

- `results_trec_covid_completo_v4/`: intento original. Contiene las 500 solicitudes iniciales y los metadatos. No contiene una capacidad válida: el programa original abortó conforme a su regla. La rampa solo quedó redondeada en el log.
- `results_trec_covid_carga_fija_v4/`: ensayo complementario. **El campo `C_qps=8` es una escala externa de carga, no capacidad validada de TREC.** El archivo lo marca mediante `capacity_validated=false`, `trec_capacity_qps=null`, `C_role` y `protocol`.
- `fixed_load_plan.json`: procedencia de la referencia 8 QPS de FiQA, cargas 2/4/6/8 QPS y umbral de hedging propio de TREC calculado con los registros iniciales. Las condiciones de falla usan 6 QPS, como FiQA.
- `comparability_final.json`: distingue controles verificados y límites. La regla de capacidad no pudo completarse para el ensayo final; la comparación es a iguales QPS absolutos.
- `tabla_paper_trec-covid.csv`, `fitness_por_repeticion.csv`, `hedging_pareado.csv`: resultados del ensayo a carga fija, sin agrupar con Kaggle ni atribuirlos a una C de TREC.

No se aumentó el plazo léxico de 50 ms, no se rebajó el requisito del 99 % y no se descartó el intento fallido. El fallo no demuestra capacidad cero ni identifica qué tasa menor a 1 QPS podría sostener el criterio.

## Qué respalda la comparación

Se comprobaron código, α, configuración, Python, versiones de librerías, nodo, GPU, recursos Slurm, condiciones, tres repeticiones, 180 s por ventana, 30 s de descarte y QPS absolutos. Los percentiles, continuidad y copias se reconstruyeron desde los 39 archivos. F3H/F3NH comparten consultas, llegadas y asignación determinista de demoras. Las banderas de demora efectivamente aplicada pueden diferir cuando una consulta activa respaldo antes del reranker. `hedging_exposicion_por_solicitud.csv` conserva ese contraste; no se fuerza igualdad ni se eliminan consultas para mejorar el resultado.

La GPU es compartida y las condiciones se ejecutan en orden fijo; no se controla la misma contención que en FiQA. La revisión física de MiniLM usada por la referencia no se registró; aquí se conserva la revisión preparada, sin afirmar verificación retrospectiva. La relevancia procede del Trabajo 1 y no se midió por solicitud bajo carga.

## Reproducción y archivos

El proyecto remoto es `/home/usuario/projects/minion_trec_khipu_v4_20261118`. Los scripts `.sbatch` muestran los comandos usados. El notebook ya está ejecutado y el análisis no vuelve a invocar modelos. Para repetir inferencias hacen falta el corpus y los modelos referenciados en `data_hashes.json` y `prepared_models.json`, además del entorno y las rutas registradas; esos insumos pesados no se incluyen en esta copia de resultados.

`export_manifest.json` registra las huellas de la exportación remota; `MANIFEST_SHA256.json` en la raíz integrada registra el paquete final. Los logs y `slurm_accounting.txt` respaldan estados, nodos y tiempos reales.

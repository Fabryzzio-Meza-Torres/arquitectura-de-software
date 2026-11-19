# Scripts

Todo está en `src/`. Para correrlos paso a paso, ver `00-guia-de-uso.md`.

## Qué hace cada uno

| Script | Para qué existe | Qué hace |
| --- | --- | --- |
| `run_all.py` | Dejar todo listo con un comando. | Descarga los datos, los verifica, calcula estadísticas, corre un BM25 y arma la tabla. |
| `download_data.py` | Tener los mismos datos todos. | Descarga NFCorpus, TREC-COVID y FiQA-2018, comprueba su integridad y guarda sus huellas en `data/MANIFEST.json`. |
| `dataset_stats.py` | Documentar los datos con números reales. | Cuenta documentos, queries, juicios y relevantes por query, y extrae un ejemplo real. |
| `bm25_baseline.py` | Tener una línea base y validar la evaluación. | Busca con BM25 y guarda los resultados (`.run`) y las latencias. |
| `evaluate.py` | Medir cualquier sistema con las mismas reglas. | Calcula todas las métricas por query y en promedio, y resume la latencia. |
| `significance.py` | Saber si una mejora es real. | Compara dos sistemas query a query: diferencia, intervalo y p-valor. |
| `report.py` | Tablas y gráficos del paper, fáciles de leer. | Junta varias corridas en una tabla (mejor valor en negrita) y cinco gráficos: calidad contra latencia, métricas, latencia, escalabilidad y candidatos. |
| `make_table.py` | Tabla simple para `run_all.py`. | Versión mínima de la tabla; para el paper se usa `report.py`. |
| `result_writer.py` | Que cada compañero guarde sus resultados sin errores. | Mide la latencia de cada consulta, registra el estado y escribe el `.run` y el `.latency.tsv`. Puede medir etapas aparte (`r.stage`) y contar solicitudes duplicadas (`r.add_extra`). Ver `05-formatos-para-el-equipo.md`. |
| `subsample_corpus.py` | Probar la escalabilidad (E6). | Crea submuestras anidadas de un corpus con semilla fija, conservando los relevantes. |
| `onepagers.py` | Que base y propuesta lean el mismo texto. | Comprueba que cada documento de la submuestra tenga su one-pager y crea el dataset `-onepager` con el mismo formato BEIR. |
| `compare_rankings.py` | Comparar base, propuesta y solo léxico. | Une los rankings por (consulta, documento), cuenta en cuántas consultas gana cada uno, calcula AUC y Spearman por documento, y barre el peso α de la unión. Ver `07-comparacion-arquitecturas.md`. |
| `review_sample.py` | Medir el efecto de los juicios incompletos. | Exporta documentos sin juicio para etiquetarlos y luego los convierte en juicios extra. |
| `metrics.py`, `io_formats.py`, `latency.py` | Compartir código base. | Definen las métricas, los formatos de archivo y los percentiles. No se corren: los usan los demás. |

## Cómo se conectan

```
download_data → dataset_stats
              → bm25_baseline → evaluate → significance
                                         → report
                                  review_sample ↗
subsample_corpus → (one-pagers generados por el equipo) → onepagers build
                 → corridas de base, propuesta y solo léxico → compare_rankings
```

`run_all.py` encadena la primera fila de ese flujo. Los demás scripts los usa cada compañero con sus propios resultados.

## Formatos que todos respetamos

- **Resultados (`.run`):** una línea por documento, `id_query Q0 id_documento posición puntaje nombre`. Se genera con `write_run()`.
- **Latencia (`.latency.tsv`):** una línea por consulta, `id_query`, milisegundos y estado (`ok`, `degraded`, `timeout`, `error`). Incluye también las consultas fallidas. Una 4.ª columna opcional cuenta las solicitudes duplicadas de esa consulta.
- **Etapas (`.stages.tsv`, opcional):** `id_query`, etapa y milisegundos, por ejemplo cada ronda del LLM.
- **One-pagers (`.jsonl`):** `_id`, `text`, `model`, `prompt_sha` y `seed` por documento.

## Pruebas

`python -m pytest tests -q` ejecuta 40 pruebas con casos calculados a mano y un dataset de juguete. Cubren las métricas, el BM25, la descarga, la comparación estadística, el guardado de resultados, las submuestras, los gráficos, el flujo completo, los one-pagers y la comparación de arquitecturas.

## Pendiente

Correr `report.py` con los resultados reales de E1 a E6 cuando existan; los gráficos están probados solo con datos de ejemplo.

# Comparación de fusión convexa y puntuación LLM

Análisis exploratorio de TREC-COVID sobre un corpus aleatorio de 10.000 documentos. Solo cambia la etapa final de ranking.

**Calidad completa:** True. Una tabla parcial no equivale a una evaluación final.

quality: job 64078, nodo ag001, GPU NVIDIA A100-PCIE-40GB MIG 3g.20gb, precisión LLM float32.

performance: job 64079, nodo ag001, GPU NVIDIA A100-PCIE-40GB MIG 3g.20gb, precisión LLM float32.

## Relevancia

| method   |       P3 |    nDCG3 |    MRR10 |
|:---------|---------:|---------:|---------:|
| BM25     | 0.546667 | 0.46     | 0.696722 |
| LLM      | 0.666667 | 0.617952 | 0.844556 |
| fusion   | 0.686667 | 0.640187 | 0.885667 |
| semantic | 0.613333 | 0.592775 | 0.874333 |

| metric   |   queries |   difference_LLM_minus_fusion |   ci95_low |   ci95_high |   wins |   ties |   losses |   bootstrap_replicates |   seed |
|:---------|----------:|------------------------------:|-----------:|------------:|-------:|-------:|---------:|-----------------------:|-------:|
| P3       |        50 |                    -0.02      |  -0.113333 |   0.0733333 |     14 |     22 |       14 |                  10000 |     42 |
| nDCG3    |        50 |                    -0.0222351 |  -0.110876 |   0.062423  |     15 |     16 |       19 |                  10000 |     42 |
| MRR10    |        50 |                    -0.0411111 |  -0.131111 |   0.0516667 |      7 |     33 |       10 |                  10000 |     42 |

Consultas con al menos un positivo juzgado en la muestra: 50/50. Las métricas principales conservan todas las consultas.

Diagnóstico de puntuación: `{"pairs": 893, "invalid_scores": 0, "degraded_label_mass_fraction": 0.004479283314669653, "truncation_fraction": 0.004479283314669653, "score_zero_or_one_fraction": 0.0}`. Una masa baja en las etiquetas limita la interpretación del score condicional.

## Batch y estabilidad

|   batch |   median_pairs_per_second |   median_seconds |   successful_repeats |
|--------:|--------------------------:|-----------------:|---------------------:|
|       1 |                   2.42364 |          73.0306 |                    3 |
|       4 |                   1.91424 |          92.4648 |                    3 |
|       8 |                   1.6749  |         105.678  |                    3 |

|   batch | complete   |   max_absolute_score_difference | identical_top3   | accepted   |
|--------:|:-----------|--------------------------------:|:-----------------|:-----------|
|       1 | True       |                     0           | True             | True       |
|       4 | True       |                     4.95017e-05 | True             | True       |
|       8 | True       |                     4.41968e-05 | True             | True       |

## Concurrencia

|   concurrency |   requests |   errors |   seconds |   successful_requests_per_second |
|--------------:|-----------:|---------:|----------:|---------------------------------:|
|             4 |         50 |        0 |   364.935 |                         0.137011 |
|             2 |         50 |        0 |   364.936 |                         0.13701  |
|             1 |         50 |        0 |   364.989 |                         0.13699  |

Carga cerrada con una instancia de modelo y acceso GPU serializado; incluye espera interna. No demuestra capacidad con llegadas abiertas ni un óptimo universal.

## Latencia completa

| method   |   requests |   successful |   errors |   p50_seconds |   p95_seconds |   p99_seconds |   mean_seconds | p99_exploratory   |
|:---------|-----------:|-------------:|---------:|--------------:|--------------:|--------------:|---------------:|:------------------|
| LLM      |       1000 |         1000 |        0 |      7.23091  |     8.80183   |     9.47962   |      7.29616   | False             |
| fusion   |       1000 |         1000 |        0 |      0.022296 |     0.0230266 |     0.0236634 |      0.0223509 | False             |

Los percentiles corresponden a solicitudes correctas; los errores se informan por separado. Consultas repetidas, modelos calientes y sin caché de respuestas. p99 es especialmente incierto con pocas observaciones.

Coste adicional medio en 1000 solicitudes pareadas: 7.2738 s.

## Recuperación

`{
  "passed": true,
  "interrupted_process_exit": 77,
  "committed_before_stop": 3,
  "expected": 40,
  "actual": 40,
  "duplicate_rows": 0,
  "missing_rows": 0,
  "scope": "real abrupt subprocess exit, committed score checkpoint and replay; stored reference scores, no model re-inference or machine failure"
}`

## Límites e interpretación

Los juicios son independientes del LLM y están incompletos. El score no es una probabilidad calibrada ni una verificación de verdad científica. El corpus es una muestra de 10.000 documentos, no el benchmark completo. TREC-COVID ya fue observado en trabajos anteriores: no se afirma una prueba ciega.

Los dos métodos comparten búsquedas y candidatos; el estudio atribuye diferencias a la puntuación final bajo esta configuración. No se agregan aquí los experimentos complementarios de los compañeros, que deberán identificarse por separado.

La conclusión de valor debe combinar la diferencia de relevancia y su incertidumbre con el coste de latencia. Una mejora de calidad no se presupone; no se cambia el prompt ni se descartan consultas para obtenerla.

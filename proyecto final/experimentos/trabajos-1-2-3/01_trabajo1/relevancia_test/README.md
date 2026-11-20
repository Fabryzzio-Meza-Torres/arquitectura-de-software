# Trabajo 1 — MINION: evaluación final en Khipu

α = **0,85**, leído del `alpha.json` validado en FiQA-dev. No se volvió a ajustar.
Todo el cómputo, las figuras y la ejecución del notebook se realizaron en Khipu mediante Slurm.
La corrida completa es el job **63769** en **ag001**, con una GPU A100 MIG 2g.10gb, 8 CPU y 48 GiB de RAM solicitados.
La contabilidad exacta del job está en `slurm_accounting.csv`; el log es `test-63769.log`.

## Resultados de prueba

| Dataset | P@3 fused | P@3 reranked | ΔP@3 | IC pareado 95 % |
|---|---:|---:|---:|---|
| fiqa | 0.251543 | 0.230967 | -0.020576 | [-0.035494, -0.005658] |
| trec-covid | 0.913333 | 0.886667 | -0.026667 | [-0.093333, +0.033333] |

Los IC usan 10.000 remuestreos pareados de consultas, percentiles 2,5 y 97,5 y `default_rng(42)` reiniciado por dataset.
Se evaluaron 648 consultas FiQA-test sobre 57.638 documentos y 50 consultas TREC-COVID sobre 171.332 documentos.
Los qrels se conservaron íntegros y se usaron solo para evaluar. No se cambiaron los hiperparámetros ni el valor de α.

## Entregable principal

Abrir `trabajo1_relevancia.ipynb`: está ejecutado, contiene las 15 figuras PNG inline, sus interpretaciones, ejemplos R9 y conclusiones.
Su fuente editable en formato percent es `trabajo1_relevancia.py`. Los módulos y scripts de ejecución se incluyen al lado.

## Archivos de resultados

- `metrics.csv`: P@3, nDCG@3, MRR@10; Recall@20 solo para fused y consultas con relevantes. MRR de lex/sem es complementario para R1.
- `paper_table.csv`: tabla consolidada para el paper y rutas de respaldo.
- `bootstrap.csv`: ΔP@3 e IC pareado de cada dataset.
- `bootstrap_samples_*.csv`: las 10.000 diferencias remuestreadas por dataset.
- `metric_ci.csv`: IC marginales de las barras R1.
- `judged.csv`, `condensed.csv`: cobertura de juicios y métricas tras condensar.
- `per_query_metrics.csv`: resultados por consulta para permitir auditoría y análisis pareado.
- `cands_*_test.parquet`: mismos candidatos para fused/reranked; ambos puntajes crudos, normalizados, puntaje de fusión, puntaje del cross-encoder y rangos de cada ruta.
- `runs/`: ocho runs TREC. Sus puntajes decrecen con el rango para preservar exactamente los desempates; los puntajes originales están en parquet.
- `figs/`: R1–R8, 15 PNG a 200 dpi. R3 usa la curva de desarrollo validada, sin recalcularla.
- `R9_ejemplos.md`: mejora y caída con consulta, top 3, grado y extracto de documento.
- `alpha_usado.json`: copia idéntica al α validado, con su configuración y procedencia.
- `counts.json`, `run_summary.json`, `prepared_test.json`, `environment.json`, `final_verification.json`, `manifest.json`: auditoría, estado y reproducibilidad.

## Interpretación y límites

El reranker recibe exactamente la unión top 10 BM25/top 10 BGE y solo reordena sus documentos, con un lote por consulta.
BM25, prefijo BGE, revisión del modelo, forward fp16, CLS, L2 float32, longitud 512 y desempates coinciden con la fase de desarrollo.
El cross-encoder oficial usa float32, longitud 512 y logits; los empates mantienen el orden fusionado.
El alias de modelo del enunciado redirige al repositorio oficial `cross-encoder/ms-marco-MiniLM-L6-v2`, cuya revisión está registrada.

Judged@10 y condensación usan la presencia del par consulta-documento en qrels, incluido el grado 0, tal como pide la especificación.
TREC-COVID contiene dos entradas −1 (sin juicio según NIST); se conservaron y se auditó si aparecen en candidatos.
Véase `final_verification.json` para comprobar si las definiciones de presencia y grado no negativo coinciden en las listas recuperadas.
FiQA solo contiene juicios positivos: con los mismos candidatos, la P@3 condensada necesariamente empata. Ese cero no demuestra ausencia de sesgo.
Las métricas oficiales se calcularon con `ir_measures` y coincidieron con un cálculo independiente por consulta.
Los IC describen variabilidad entre consultas del benchmark; no corrigen juicios incompletos ni garantizan relevancia fuera de estos datos.
No se midió latencia ni se validó un SLO. Este trabajo no demuestra rendimiento bajo un presupuesto de tiempo.

## Reejecución

El proyecto remoto es `/home/usuario/projects/minion_fiqa_alpha`; los resultados están en `test_results/`.
Se conservan allí los corpus, modelos, índices y embeddings. `prepare_test.py` prepara los insumos que faltan y `test_eval.sbatch` ejecuta la evaluación y el informe.
La evaluación reutiliza puntajes y embeddings compatibles al reejecutar. Para ejecutar este notebook en Khipu se necesita el proyecto remoto y el mismo entorno; las salidas ya están embebidas para leerlo sin ejecutar.

El primer piloto (63766) se detuvo al detectar los dos grados −1; el diagnóstico 63767 confirmó su significado y no modificó las etiquetas.
El piloto corregido 63768 terminó correctamente. El job CPU 63770 comprobó las figuras y el kernel del notebook mientras corría la evaluación completa.
Los artefactos del piloto no se mezclaron con los resultados finales.

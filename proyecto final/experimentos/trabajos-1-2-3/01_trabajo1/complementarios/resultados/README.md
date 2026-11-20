# MINION — análisis complementarios

Estos experimentos complementarios reutilizan los artefactos del Trabajo 1; no sustituyen sus resultados principales.
α permanece en 0,85; RRF usa k=60, fijado antes de evaluar. No se ejecutan modelos.

## Experimento 1: combinación convexa frente a RRF

Se toman los rangos originales de top 10 léxico y semántico de los runs TREC. Una ausencia aporta cero.
RRF suma 1/(60+rango), con rangos desde 1; los empates se resuelven por ID ascendente.
Se comprueba igualdad de candidatos por consulta con la combinación convexa guardada.
Se guardan P@3, nDCG@3, métricas por consulta y diferencias RRF menos convexa con IC pareados de 10.000 remuestreos.

## Experimento 2: reranking selectivo

Se invoca el reranker cuando hay al menos cuatro candidatos y el margen fusionado puesto 3 menos puesto 4 es menor o igual al umbral.
Los umbrales se fijaron exclusivamente con los márgenes de las 500 consultas de FiQA-dev durante la prueba previa.
Se usan cuantiles lineales para metas de 25 %, 50 % y 75 %; meta 50 % es la comparación principal.
Los empates en el umbral invocan todos los márgenes iguales: se reportan las tasas reales, sin ajustarlas en test.
Cuando hay menos de cuatro candidatos, se devuelve la fusión; el control aleatorio respeta la misma elegibilidad.

Se simulan las decisiones usando los rankings fused/reranked guardados. Cada control aleatorio tiene exactamente el mismo
número de invocaciones por dataset que su política selectiva y se promedia sobre 100 selecciones sin reemplazo.
Las semillas y las decisiones individuales de cada selección se guardan. Las diferencias contra fusión y el promedio aleatorio
son pareadas por consulta. Sus IC adicionales usan el promedio por consulta de esas 100 selecciones como control fijo;
no son un bootstrap jerárquico de la incertidumbre Monte Carlo.

## Archivos

- `rrf_metrics_*`, `rrf_per_query_*`, `rrf_paired_differences_*`, `rrf_scores_*`: comparación de fusión y sus rangos/puntajes.
- `selective_metrics_*`, `selective_per_query_*`, `selective_paired_differences_*`: relevancia, invocaciones y comparaciones pareadas.
- `selective_decisions_*`: márgenes y decisiones de cada umbral por consulta.
- `random_draw_metrics_*`, `random_decisions_*`, `random_seeds_*`: 100 selecciones, métricas y semillas auditables.
- `thresholds_fixed.json`, `dev_margins.csv`: umbrales de desarrollo congelados y sus márgenes de origen.
- `inputs_manifest.json`, `run_summary.json`, `verification_*`: rutas, huellas, versiones, semillas y validación.
- `experimento_1_fusiones.png`, `experimento_2_selectivo.png`: una figura a 200 dpi por experimento.

La relevancia se calcula con ir_measures y se contrasta con un cálculo explícito de P@3 y nDCG@3 por consulta.
Las entradas de relevancia -1 se conservan y reciben la semántica de sin juicio del evaluador.
Los logs de Slurm están en la carpeta hermana `logs/`. El entorno usado es `.venv` del proyecto del Trabajo 1.

Este análisis evalúa relevancia y número de invocaciones simuladas. No mide latencia ni permite convertir una reducción
de invocaciones en una mejora temporal. Las latencias de estas variantes requieren una prueba aparte.

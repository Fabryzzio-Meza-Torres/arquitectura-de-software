# Plan experimental comparable con FiQA v4

## Preguntas

1. ¿Qué relevancia producen BM25, BGE, la fusión y el reranking? La responde el Trabajo 1 con qrels y consultas test, después de fijar α en desarrollo.
2. ¿Qué ocurre con la cola de latencia al aumentar la carga? La responden los Trabajos 2 y 3 con un generador Poisson open-loop y latencia desde el instante programado.
3. ¿Se entregan tres documentos dentro de 2,5 segundos cuando fallan componentes? Se responde con continuidad y distribución de rutas.
4. ¿El hedging reduce la cola bajo demoras inyectadas con un presupuesto de copias? Se contrasta F3H contra F3NH con las mismas consultas, llegadas y asignación determinista de demoras. La exposición efectiva puede diferir por respaldos previos al reranker, y se audita por solicitud.

## Qué se mantiene fijo

La referencia es el Trabajo 2 de FiQA, job 63828, nodo ds001, RTX A6000 compartida, script v4 con SHA-256 `bb027763a577074373d5c1909467fbac67f8b5484d37696b29e1f697f02f22b7`.

Se conservan el código, α=0,85 y su configuración, Python 3.11.11, las versiones registradas de las librerías, nodo y modelo de GPU, un shard, 4 CPU/hilos, 32 GB de RAM, tres repeticiones, las 13 condiciones, duración de 180 segundos por condición, descarte de 30 segundos, tiempos de espera, política de respaldo y limitador v4 de duplicadas.

Antes de la corrida, `comparability_check.py` verifica automáticamente la huella del código, el contenido de alpha.json, la configuración congelada, Python, las versiones y el modelo de GPU.

## Qué cambia intencionalmente

El corpus y las consultas cambian a TREC-COVID: 171.332 documentos y 50 consultas test. Se conserva texto título + espacio + contenido y el mismo pipeline.

Cada dataset se calibra de nuevo: 500 consultas a 1 QPS, umbral de hedging igual al p95 del reranker, y rampa 1, 2, 4, 8, 16, 32, 64 QPS con 120 segundos por escalón. La fuente de consultas de calibración sigue el código v4: train en FiQA y títulos aleatorios del corpus en TREC-COVID, semilla 42.

La C principal exige al menos 99 % de respuestas reranked y p99 estable, y se limita por el primer escalón fallido. El diagnóstico de capacidad que admite otras rutas se registra por separado. C y el umbral de FiQA no se copian a TREC-COVID.

Los niveles L25–L100 son porcentajes de la C de cada dataset. No necesariamente representan los mismos QPS absolutos. Deben mostrarse ambas cifras al comparar.

## Condiciones y significado

| Condición | Intervención | Qué permite observar |
|---|---|---|
| L25, L50, L75, L100 | 25, 50, 75 y 100 % de C | Latencia bajo carga y uso de respaldos |
| NORERANK | No invoca el reranker | Referencia temporal de fusión sola |
| NOHEDGE | Reranker sin copias | Costo del sistema completo sin hedging |
| F1 | Ambas réplicas del reranker fallan | Respaldo fusionado por error |
| F2 | Ambas réplicas se demoran 1500 ms | Respaldo por vencimiento de plazo |
| F3H | Demora de 800 ms en 5 % de solicitudes, con hedging | Política de duplicación |
| F3NH | Misma asignación de demoras y llegadas, sin hedging | Control pareado de F3H |
| F4 | Falla semántica | Respaldo léxico |
| F5 | Falla léxica | Respaldo semántico |
| F6 | Fallan ambas rutas de recuperación | Error controlado; no se esperan tres resultados |

## Qué se mide y cómo se resume

Se guardan todas las solicitudes. Para estadísticas finales se excluyen las programadas antes de 30 segundos. p50, p95 y p99 se calculan sobre respuestas con tres documentos, con el método de rango ceil(q × N). La continuidad usa como denominador todas las solicitudes medidas y exige tres documentos y latencia menor o igual a 2500 ms.

Se muestran los tres valores por condición, su mediana y rango. Con tres repeticiones, ese rango es descriptivo y no debe llamarse intervalo de confianza. Los IC del Trabajo 1 y de los complementarios provienen de 10.000 remuestreos de consultas; responden otra pregunta.

El porcentaje de duplicadas es copias enviadas dividido entre invocaciones originales del reranker, usando el mismo descarte de calentamiento. Se muestran los porcentajes de cada ruta: continuidad de 100 % no significa que todas las consultas hayan completado reranking.

## Límites de comparabilidad que deben mantenerse visibles

ds001 es compartido. La corrida FiQA tenía otros procesos usando la A6000; las condiciones actuales de contención pueden diferir. Se registran nvidia-smi, metadatos y recursos Slurm. Compartir nodo y GPU no equivale a aislamiento ni convierte toda diferencia en un efecto causal del dataset.

La revisión de BGE está fijada. La referencia FiQA registró el nombre de MiniLM pero no su revisión exacta de caché; la nueva corrida conserva la revisión preparada. La comparación de pesos del reranker con el archivo físico usado por la referencia no puede demostrarse solo con sus metadatos.

Las réplicas comparten GPU y máquina y no simulan aislamiento de fallas físicas. Las fallas son inyectadas en el proceso. Relevancia y latencia se estudian en corridas distintas; no debe presentarse una curva de calidad bajo carga como si hubiera sido medida.

## Evidencia que se actualizará

La carpeta consolidada incorporará una serie TREC-COVID/Khipu nueva, sin reemplazar TREC-COVID/Kaggle. Se actualizarán las tablas de latencia y fitness, la comparación FiQA/TREC en ds001, las figuras, un notebook ejecutado, la procedencia, las huellas SHA-256 y el resumen explicativo. Piloto y corridas finales permanecerán separados.

## Incidencia de calibración y análisis complementario a carga fija

El job 63911 conserva el intento exacto del protocolo anterior. En el primer escalón no se alcanzó el 99 % de ruta completa; el programa original se detiene sin fijar C. No se aumenta el plazo léxico, no se reduce el 99 % y no se presenta la continuidad por respaldo como capacidad de reranking.

Para completar el contraste operativo se ejecuta el job 63919 como **análisis complementario a carga absoluta fija**. La referencia se toma de FiQA job 63828, cuyo C ya registrado era 8 QPS. Se aplican a TREC las mismas cargas absolutas 2/4/6/8 QPS, conservando código, recursos, 13 condiciones, tres repeticiones y plazos. La fase `runs` del código original lee un adaptador de entrada: su campo `C_qps=8` es únicamente una escala externa de carga y NO es una capacidad validada de TREC. `capacity_validated=false` y `trec_capacity_qps=null` quedan registrados.

El umbral de hedge de TREC se calcula con los 500 registros de su intento de calibración: p95 de rerank de las solicitudes que completaron esa ruta, siguiendo el mismo cálculo original. `prepare_fixed_load.py` documenta la adaptación y preserva el intento fallido. Los valores de rampa solo quedaron redondeados en stdout porque la fuente original aborta antes de guardar calibration.json. Las 500 solicitudes iniciales sí se guardan completas.

Este contraste responde qué pasa **a los mismos QPS absolutos** en el mismo montaje nominal. No permite comparar L100 como 100 % de la capacidad propia de cada dataset ni afirmar que TREC sostuvo 8 QPS con ≥99 % de reranking. La falla de calibración y las rutas de respaldo forman parte del resultado, y la contención compartida permanece sin controlar.

## Auditoría de exposición a demoras

El código asigna la demora de F3 por semilla 42, repetición e índice de solicitud. La bandera delay_injected solo se activa si se alcanza el reranker. Las consultas y horarios de F3H/F3NH coinciden, pero un timeout léxico puede llevar una de las dos a respaldo antes de aplicar la demora. Se conservan las banderas observadas, se verifica que toda demora aplicada estuviera asignada y se reportan las diferencias por repetición. No se sustituyen esas banderas por las asignadas ni se eliminan consultas; la diferencia de p99 describe las ventanas completas y no aísla causalmente solo el hedge.

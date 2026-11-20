# Resumen integrado de los tres trabajos MINION

18 de noviembre de 2026 · Relevancia offline, latencia y tolerancia a fallas

La evidencia respalda la continuidad del servicio dentro del presupuesto de 2,5 segundos en las condiciones medidas, pero no demuestra una mejora de relevancia al añadir el cross-encoder. FiQA pierde P@3 con un intervalo pareado negativo; en TREC-COVID el efecto sigue siendo incierto. El beneficio del hedging depende del montaje y no se reproduce de forma consistente en Khipu.

## Qué aporta cada trabajo

| Trabajo | Contenido verificado | Montaje |
|---|---|---|
| 1 | α definitivo y relevancia en FiQA-test y TREC-COVID | Khipu ag001 · A100 MIG 10 GB |
| 2 | Latencia y fallas de FiQA · 3 repeticiones × 13 condiciones | Khipu ds001 · RTX A6000 compartida |
| 3 | TREC-COVID: intento v4 y ensayo complementario a carga fija | Khipu ds001 · RTX A6000 compartida |
| Series adicionales | FiQA y TREC-COVID · dos series completas | Kaggle · Tesla T4 |

La nueva ejecución de TREC en ds001 conserva el código y entorno de FiQA. El intento de capacidad v4 falla en el primer escalón; se conserva como resultado. Un ensayo complementario mide las mismas cargas absolutas de FiQA, sin declarar una capacidad propia de TREC. Las series Kaggle permanecen separadas.

## Conclusiones principales

| Pregunta | Resultado e interpretación |
|---|---|
| ¿Mejora el reranking la relevancia? | FiQA: ΔP@3 = −2,06 puntos porcentuales; IC 95 % [−3,55; −0,57]. TREC-COVID: −2,67 pp; IC [−9,33; +3,33]. |
| ¿Se cumple p99 ≤ 2500 ms? | FiQA/Khipu y las series Kaggle cumplen en 3/3; TREC/Khipu a carga fija en 3/3. No se validó C de TREC. |
| ¿Funcionan las rutas de respaldo? | Las series previas alcanzan 100 % en F1/F2; el mínimo de TREC/Khipu es 100,00 %. F6 devuelve error controlado. |
| ¿Se respeta el 10 % de duplicadas? | FiQA/Khipu cumple en 3/3; TREC/Khipu a carga fija en 3/3. TREC/Kaggle supera 10 % en dos repeticiones L25. |

## Cómo leer las estadísticas

Relevancia: promedios macro por consulta e intervalos percentiles del 95 % con 10.000 remuestreos pareados. Latencia: mediana del p99 de las tres repeticiones y rango mínimo–máximo. Ese rango no es un intervalo de confianza. Los percentiles se reconstruyeron como el elemento ordenado en la posición ceil(0,99 × N), descartando los primeros 30 segundos.

Las tablas completas y los archivos originales están reunidos en este paquete. El resumen utiliza las corridas finales; los pilotos y diagnósticos se conservan como historial.

# Diseño experimental y lectura de las estadísticas

El proyecto estudia relevancia, latencia y continuidad. La fusión es f=(1−α)×BM25 normalizado + α×semántico normalizado; α=0,85 da 85 % al puntaje semántico. Los trabajos comparten pipeline, pero responden preguntas distintas: una respuesta rápida o continua no demuestra que contenga mejores documentos. Los complementarios exploran decisiones nuevas de fusión e invocación sin medir sus latencias.

| Pregunta | Diseño y unidad de análisis | Resultado |
|---|---|---|
| ¿Qué documentos devuelve? | Trabajo 1 · consultas test con qrels; α se fija solo en dev | P@3, nDCG@3, MRR@10 y Recall@20 |
| ¿Qué pasa al aumentar carga? | Trabajos 2 y 3 · Poisson open-loop, latencia desde instante programado | p50/p95/p99, continuidad y rutas |
| ¿Qué ocurre ante fallas? | Errores y demoras inyectados en 13 condiciones | Tres resultados dentro de 2500 ms |
| ¿Ayuda duplicar solicitudes? | F3H/F3NH con consultas, llegadas y asignación de demoras iguales | Diferencia de p99 y costo de copias |
| ¿Conviene otra decisión? | Complementarios · candidatos y rankings guardados | Relevancia e invocaciones simuladas |

## Controles compartidos en Khipu

FiQA job 63828 y TREC job 63919 usan el mismo script v4, α = 0,85, Python 3.11.11, las versiones registradas de las siete librerías principales, ds001/A6000, un shard, 4 CPU/hilos y 32 GB. Se mantienen las 13 condiciones, tres repeticiones, 180 segundos por condición, descarte de 30 segundos, plazos y limitador de copias. El código y esos controles se verifican automáticamente.

## Cambios intencionales y protocolo que no pudo completarse

Cambian corpus y consultas: FiQA 57.638 documentos/648 consultas test; TREC 171.332/50. Se intentó la misma calibración: 500 solicitudes a 1 QPS, p95 de rerank como umbral y rampa 1–64 QPS en escalones de 120 s. La fuente de calibración v4 es train de FiQA y títulos de TREC con semilla 42. El intento TREC no sostuvo ≥99 % de ruta completa en el primer escalón; por la regla original no tiene C validada en esta grilla.

El ensayo posterior es complementario a carga fija: usa los 2/4/6/8 QPS ya definidos por FiQA, con el umbral propio de TREC. Las etiquetas L25–L100 son porcentajes de la referencia externa de 8 QPS; en TREC no equivalen a porcentajes de una capacidad validada. Así se contrasta la operación a iguales QPS absolutos sin modificar el criterio original.

## Denominadores, incertidumbre y límites

p99 se calcula sobre respuestas de tres documentos. Continuidad divide respuestas válidas en ≤2500 ms entre todas las solicitudes medidas. Copias divide duplicadas por invocaciones originales del reranker. Una continuidad alta puede coexistir con respaldos. La mediana y rango de tres repeticiones son descriptivos, no IC; los IC de relevancia remuestrean consultas de forma pareada.

La GPU compartida puede tener distinta contención: mismo nodo no elimina ese factor. Las réplicas comparten máquina y GPU; las fallas son inyectadas. La revisión física de MiniLM de la referencia no quedó registrada y no puede comprobarse retrospectivamente. Las condiciones se ejecutan en orden fijo; el pareamiento de entradas no elimina cambios de contención entre ventanas. Tampoco se midió relevancia por solicitud bajo carga.

# Trabajo 1 Relevancia y valor definitivo de alfa

Se fijó α = 0,85 en 500 consultas de FiQA-dev, sobre 57.638 documentos. Entre 21 valores, fue el máximo único de P@3: 0,251333, con nDCG@3 de 0,402684. Los tests no se usaron para ajustar α.

## Resultados de prueba

| Dataset | Lista | P@3 | nDCG@3 | MRR@10 |
|---|---|---|---|---|
| fiqa | fused | 0,25154 | 0,37692 | 0,50035 |
| fiqa | reranked | 0,23097 | 0,34007 | 0,44818 |
| trec-covid | fused | 0,91333 | 0,85888 | 0,94000 |
| trec-covid | reranked | 0,88667 | 0,82469 | 0,91400 |

FiQA-test contiene 648 consultas y TREC-COVID 50, sobre sus corpus completos de 57.638 y 171.332 documentos. En ambas listas se conserva exactamente la unión de top 10 BM25 y top 10 semántico, con ambos puntajes calculados para todos los candidatos. Solo cambia su orden al aplicar el cross-encoder.

| Dataset | ΔP@3 en pp | IC pareado 95 % en pp | Lectura |
|---|---|---|---|
| fiqa | -2,06 | [-3,55; -0,57] | Negativo |
| trec-covid | -2,67 | [-9,33; 3,33] | Incluye cero |

La fitness de que el reranker no reduzca P@3 no se cumple en la estimación puntual de ninguno de los tests. FiQA presenta evidencia de caída según sus qrels; el intervalo de TREC-COVID no permite afirmar una mejora ni una caída concluyente. Esto no prueba que todo cross-encoder sea peor: el resultado corresponde al modelo MiniLM y a la configuración congelada.

## Cobertura de juicios y límites

Recall@20 de fused: 0,53050 en FiQA y 0,03392 en TREC-COVID; solo se promedian consultas con relevantes. El reranker no puede recuperar documentos ausentes de la unión de candidatos.

| Dataset | Judged@10 fused | Judged@10 reranked | ΔP@3 condensada |
|---|---|---|---|
| FiQA | 11,59 % | 10,63 % | 0,00000 |
| TREC-COVID | 93,80 % | 96,80 % | −0,02667 |

FiQA solo contiene juicios positivos. Al quitar los documentos no juzgados, la P@3 condensada de dos ordenaciones de los mismos candidatos necesariamente empata; ese cero es estructural y no demuestra ausencia de sesgo. TREC-COVID conserva el signo negativo al condensar. Sus dos entradas −1 se mantuvieron y no aparecieron entre los candidatos recuperados.

## Evidencia de ejecución

Ajuste dev: job 63761, ag001, 6 min 10 s. Evaluación test y notebook: job 63769, ag001, 19 min 45 s. El notebook contiene 29 celdas de código ejecutadas, 15 figuras embebidas y cero errores. La copia local y los artefactos se verificaron mediante SHA-256.

Fuentes: 01_trabajo1/ajuste_dev/alpha.json y alpha_curve.csv; 01_trabajo1/relevancia_test/metrics.csv, bootstrap.csv, judged.csv, condensed.csv y final_verification.json.

# Trabajo 2 Latencia y fallas de FiQA en Khipu

La corrida final v4 es el job 63828, en ds001 con RTX A6000 compartida, 4 CPU/hilos y 32 GB de RAM solicitados. Se midieron 13 condiciones durante 180 segundos, con descarte de 30 segundos, en tres repeticiones. Hay 39 archivos de solicitudes y 39 filas de resumen.

## Capacidad y tiempos observados

La calibración fija C = 8 QPS para la ruta completa reranked, con umbral de hedging de 140,397 ms. Un diagnóstico separado alcanza 64 QPS aceptando otras rutas. Esos 64 QPS no son la capacidad de la ruta completa. En v4, C queda limitado por el primer escalón fallido; esta definición debe mantenerse al repetir TREC-COVID.

| Condición | Carga o falla | p99 mediana [rango] ms | Continuidad mínima |
|---|---|---|---|
| L25 | 25 % de C · 2 QPS | 313,3 [306,5; 323,3] | 100,0 % |
| L50 | 50 % · 4 QPS | 492,6 [431,6; 542,6] | 100,0 % |
| L75 | 75 % · 6 QPS | 969,6 [648,9; 1162,2] | 100,0 % |
| L100 | 100 % · 8 QPS | 1483,0 [1417,6; 1504,0] | 100,0 % |
| NORERANK | Sin reranking · 8 QPS | 88,3 [84,5; 89,9] | 100,0 % |
| F1 | Reranker falla · 6 QPS | 82,4 [80,1; 83,0] | 100,0 % |
| F2 | Reranker lento · 6 QPS | 1281,8 [1281,6; 1289,7] | 100,0 % |

L100 reduce el presupuesto disponible de reranking: 4,47 %, 5,38 % y 8,79 % de las solicitudes terminan en fused_fallback, aunque todas entregan tres resultados antes de 2,5 s. El 6,21 % es el promedio de esos porcentajes. La continuidad del 100 % no implica que el 100 % haya recibido el reranker.

## Hedging bajo demoras inyectadas

| Repetición | p99 con hedge ms | p99 sin hedge ms | Reducción por hedge ms |
|---|---|---|---|
| 1 | 1091,1 | 1061,1 | -30,0 |
| 2 | 1070,4 | 983,1 | -87,4 |
| 3 | 1211,8 | 1262,8 | 51,0 |

El hedge mejora el p99 en una de las tres repeticiones y lo empeora en dos. Las medianas son 1091,1 ms con hedge y 1061,1 ms sin él. No hay evidencia consistente de beneficio en este montaje. Las llegadas, consultas y banderas de demora coinciden exactamente entre F3H y F3NH en cada repetición.

Fitness (i), (iii) y (iv): cumplen en las tres repeticiones. La mayor proporción de duplicadas en las condiciones de fitness es 9,883 %. F4 vuelve a léxico y F5 a semántico; F6 devuelve error. La GPU tenía otro proceso activo, por lo que no se puede atribuir la diferencia frente a Kaggle solo al modelo de GPU.

Fuente: 02_trabajo2_khipu_fiqa/results_fiqa_completo_v4/ y logs/fiqa-completo-v4-63828.out. Los percentiles se recalcularon desde las solicitudes; el script coincide con la huella registrada al normalizar CRLF a LF.

# Trabajo 3 TREC COVID en ds001: dos resultados distintos

El piloto 63909 pasó en 3 min 51 s con modelos reales y ocho condiciones de rutas. Su corpus reducido y calibración diagnóstica solo validan el funcionamiento. El intento de capacidad 63911 usa corpus completo y protocolo v4; el ensayo 63919 conserva ese pipeline y mide cargas absolutas fijas. Su tiempo real fue 01:59:35. Los tres registros se mantienen separados.

## 1. Intento v4: no se pudo fijar capacidad

En las 500 solicitudes iniciales, 462 (92,4 %) completan reranking y 38 vencen el plazo léxico de 50 ms. El umbral propio de hedging es 154,424 ms. En la rampa, el primer escalón entrega aproximadamente 97 % por la ruta completa, por debajo de 99 %. El programa se detiene según su regla, sin emitir una C válida. Esto no demuestra que la capacidad sea cero ni identifica una tasa sostenible menor que 1 QPS.

Los 500 registros se conservan completos. El código original aborta antes de guardar calibration.json y las solicitudes de la rampa; sus resultados solo están disponibles redondeados en el log. No se cambia el plazo, no se rebaja el 99 % y no se sustituye capacidad por continuidad mediante respaldo.

## 2. Ensayo complementario a iguales QPS que FiQA

| Condición | QPS nominales | p99 mediana [rango] ms | Continuidad mínima |
|---|---|---|---|
| L25 | 2,0 | 560,4 [556,0; 721,8] | 100,00 % |
| L50 | 4,0 | 974,8 [743,6; 992,8] | 100,00 % |
| L75 | 6,0 | 1527,1 [1125,5; 1617,3] | 100,00 % |
| L100 | 8,0 | 1745,8 [1728,9; 2067,9] | 99,92 % |
| NORERANK | 8,0 | 297,2 [251,2; 315,8] | 100,00 % |
| F1 | 6,0 | 233,9 [223,1; 283,6] | 100,00 % |
| F2 | 6,0 | 1438,3 [1426,8; 1439,9] | 100,00 % |

A 8 QPS, FiQA tiene p99 mediano de 1483,0 ms y TREC 1745,8 ms. Es un contraste a igual tasa absoluta y montaje nominal, no a iguales porcentajes de capacidad propia ni una atribución causal exclusiva al dataset. El campo C_qps=8 del adaptador solo escala la carga; capacity_validated=false y trec_capacity_qps=null lo aclaran.

La reducción p99 sin hedge menos con hedge es -87,0, -166,0, 73,6 ms por repetición. Consultas, llegadas y asignación de demoras coinciden, pero las demoras efectivas difieren en 2, 1, 1 solicitudes poscalentamiento por repetición al activarse respaldo antes del reranker. La diferencia de p99 no aísla solo el hedge. Fitness temporales bajo estas cargas: (i) 3/3; (iii) 3/3; (iv) 3/3. No certifican la capacidad v4 que no pudo calibrarse.

Fuentes: 05_trabajo3_khipu_trec/, intento original, fixed_load_plan.json, los 39 archivos del ensayo, notebook ejecutado, nueve figuras, verificación y logs Slurm. La contención compartida limita todas las inferencias entre corridas.

# Series de Kaggle como evidencia complementaria

La rama feat/khipu-kaggle-results contiene dos series completas en Tesla T4: FiQA y TREC-COVID, cada una con 39 condiciones, tres repeticiones y un notebook ejecutado sin errores. Ambas usan C = 2 QPS. Los umbrales de hedging son 168,069 ms en FiQA y 162,169 ms en TREC-COVID.

## Resultados operativos por montaje

| Serie | Condición | p99 mediana [rango] ms | Continuidad mínima |
|---|---|---|---|
| FiQA · Kaggle | L100 | 325,3 [314,7; 379,4] | 100,0 % |
| FiQA · Kaggle | NORERANK | 43,3 [42,2; 45,3] | 100,0 % |
| FiQA · Kaggle | F3H | 389,5 [312,0; 449,9] | 100,0 % |
| FiQA · Kaggle | F3NH | 947,6 [930,7; 988,9] | 100,0 % |
| FiQA · Kaggle | F2 | 1368,0 [1364,5; 1379,8] | 100,0 % |
| TREC · Kaggle | L100 | 407,6 [388,8; 453,5] | 100,0 % |
| TREC · Kaggle | NORERANK | 111,2 [99,7; 112,0] | 100,0 % |
| TREC · Kaggle | F3H | 433,5 [428,5; 634,5] | 100,0 % |
| TREC · Kaggle | F3NH | 984,4 [977,3; 1046,2] | 100,0 % |
| TREC · Kaggle | F2 | 1517,2 [1472,4; 1518,7] | 100,0 % |

El hedging reduce la mediana de p99 de F3NH a F3H en 558,1 ms para FiQA y 551,0 ms para TREC-COVID, aproximadamente 58,9 % y 56,0 %, respectivamente. La reducción aparece en las tres repeticiones de cada dataset. Estos resultados describen Kaggle/T4 a 75 % de su C; no se trasladan a ds001, donde la carga absoluta y el comportamiento del hedge son diferentes.

## Duplicación y fitness

En TREC-COVID, L25 registra 8/89 = 8,989 % de duplicadas en la primera repetición y 9/89 = 10,112 % en las otras dos. Por ello la fitness (iv) falla en 2 de 3 repeticiones. Las fitness (i) y (iii) cumplen en las tres; F1/F2 mantienen 100 % de continuidad. FiQA/Kaggle cumple (i), (iii) y (iv) en las tres.

El código de Kaggle comprueba la razón de copias antes de añadir la siguiente; con conteos discretos puede admitir una copia que lleve la razón por encima del límite. También el porcentaje global después del calentamiento difiere de una razón móvil de 60 segundos. El código v4 de Khipu comprueba el efecto de añadir la copia y controla además el denominador poscalentamiento. No son implementaciones idénticas del limitador.

## Cómo se relaciona con el ensayo nuevo de Khipu

La ejecución nueva en ds001 permite contrastar TREC con FiQA a iguales QPS absolutos. Su intento de capacidad falla y se documenta por separado. Kaggle conserva dos series propias completas; sigue siendo incorrecto mezclar sus latencias con Khipu como si solo cambiara el dataset.

Fuentes: 03_trabajos2y3_kaggle/results/fiqa/ y results/trec-covid/, tabla_paper_*.csv y los dos notebooks. El documento HANDOFF corresponde a un estado anterior; prevalecen las corridas y metadatos finales que sí están guardados.

# Experimentos complementarios de fusión y selección

El job CPU 63778 terminó correctamente en n005 en 8 segundos. Reutilizó los puntajes y rankings guardados, sin ejecutar modelos. Estos análisis complementan el Trabajo 1 y no sustituyen sus resultados principales ni miden latencia.

## Combinación convexa frente a RRF

RRF usa k = 60 y las posiciones originales desde 1 de los top 10 léxico y semántico. Una ausencia aporta cero. Se verificó la misma unión de candidatos por consulta; los empates se resuelven por ID ascendente.

| Dataset | Métrica | Δ RRF menos convexa | IC pareado 95 % |
|---|---|---|---|
| fiqa | P@3 | -0,03755 | [-0,05041; -0,02521] |
| fiqa | nDCG@3 | -0,05353 | [-0,06990; -0,03711] |
| trec-covid | P@3 | -0,11333 | [-0,17333; -0,05333] |
| trec-covid | nDCG@3 | -0,10592 | [-0,16073; -0,05207] |

RRF resulta inferior en P@3 y nDCG@3 en ambos datasets; los cuatro intervalos excluyen cero. Esta conclusión se limita a k = 60, dos listas top 10 y la configuración α = 0,85 ya fijada. No demuestra que RRF sea inferior en otros tamaños de listas o colecciones.

## Reranking selectivo con meta principal del 50 por ciento

La política invoca el reranker cuando el margen fusionado entre los puestos 3 y 4 es pequeño; con menos de cuatro candidatos devuelve la fusión. Los umbrales 0,01090972, 0,02539713 y 0,05134022 se congelaron en FiQA-dev para metas de 25 %, 50 % y 75 %. No se ajustaron en test.

| Dataset | Política | P@3 | nDCG@3 | Invocaciones |
|---|---|---|---|---|
| fiqa | Fusión | 0,25154 | 0,37692 | 0,0 % |
| fiqa | Completo | 0,23097 | 0,34007 | 100,0 % |
| fiqa | Selectivo meta 50 % | 0,24691 | 0,36607 | 51,9 % |
| fiqa | Aleatorio media 100 | 0,24144 | 0,35845 | 51,9 % |
| trec-covid | Fusión | 0,91333 | 0,85888 | 0,0 % |
| trec-covid | Completo | 0,88667 | 0,82469 | 100,0 % |
| trec-covid | Selectivo meta 50 % | 0,90000 | 0,85877 | 72,0 % |
| trec-covid | Aleatorio media 100 | 0,89540 | 0,83551 | 72,0 % |

La meta 50 % se convierte en 51,85 % de invocaciones en FiQA y 72 % en TREC-COVID: hay cambio de distribución de márgenes. Frente a fusión sola, ΔP@3 es −0,00463 en FiQA, IC [−0,01543; +0,00669], y −0,01333 en TREC, IC [−0,06667; +0,04000]. Los intervalos incluyen cero; esto no prueba equivalencia ni no inferioridad.

Frente al control aleatorio con exactamente las mismas invocaciones y 100 semillas, las ventajas medias de P@3 son +0,00548 y +0,00460, con IC que también incluyen cero. Esos IC son condicionales al promedio de 100 selecciones, no un bootstrap jerárquico. Reducir invocaciones no permite cuantificar un ahorro de latencia: esa variante requiere una prueba temporal aparte.

# Auditoría y trazabilidad de la comparación

## Ramas y fuentes preservadas

| Rama y commit | Contenido relevante |
|---|---|
| main · f749842d9437 | Base común del repositorio; sin los resultados del paper añadidos en las otras ramas. |
| paper/trabajo2 · 650c992c4dd6 | FiQA/Khipu v4 final, calibración, scripts, 39 condiciones y logs; conserva pilotos previos. |
| feat/khipu-kaggle-results · 45e4db4e0cdf | FiQA y TREC-COVID en Kaggle, calibraciones, 78 condiciones, 18 figuras K1–K9 y dos notebooks. |

Repositorio: github.com/Fabryzzio-Meza-Torres/arquitectura-de-software. Las copias se tomaron de esos commits; las ramas originales no fueron modificadas. procedencia.json y MANIFEST_SHA256.json permiten identificar origen y contenido de la consolidación.

## Comprobaciones realizadas

Se revisaron 156 filas de resumen frente a los logs poscalentamiento: p50, p95, p99 y continuidad coinciden dentro del redondeo publicado. Para duplicadas, Khipu usa 0 cuando no se invoca el reranker; la tabla integrada muestra no aplicable en ese caso. Los doce pares F3H/F3NH tienen idénticas consultas y llegadas. Las banderas de demora de las nueve parejas originales coinciden; en TREC/Khipu se registran diferencias de exposición por respaldos previos al reranker. Las huellas del código coinciden con metadatos, admitiendo la conversión de finales de línea CRLF/LF en la copia de Khipu.

Se conservaron los datos originales y se añadieron tablas normalizadas. No se combinaron latencias de GPUs diferentes, no se reentrenaron modelos y no se reinterpretaron pilotos como corridas finales. La ejecución de los dos notebooks de Kaggle y del notebook del Trabajo 1 se comprobó por sus contadores y salidas, sin volver a correr inferencias.

## Ejecución nueva, trazabilidad y límites

El intento 63911 conserva el protocolo de capacidad y su fallo. El job 63919 ejecuta un ensayo complementario a las cargas absolutas de FiQA, con código idéntico. Los 39 resúmenes se contrastan con las solicitudes y el notebook contiene 17 celdas ejecutadas, nueve figuras y cero errores.

comparability_final.json distingue controles verificados y límites: código, α, entorno, recursos, condiciones y cargas coinciden; la capacidad de TREC no fue validada. No se certifica idéntica contención ni revisión física de MiniLM de la referencia. Los scripts de análisis se separan del benchmark congelado y todos los artefactos se inventarían con SHA-256.

## Decisión que sostiene la evidencia

La fusión α = 0,85 sigue siendo la referencia de relevancia más sólida entre las variantes evaluadas. Los respaldos protegen continuidad y se deben leer junto con las proporciones de ruta. El intento fallido de calibración revela un límite operativo del protocolo en TREC, mientras el ensayo fijo describe su comportamiento a las cargas de FiQA. La selección por margen aún necesita una prueba temporal propia.

Archivos de auditoría: 04_tablas_y_auditoria/latencia_por_repeticion.csv, latencia_mediana_y_rango.csv, fitness_por_repeticion.csv, pareamiento_hedging.csv, verificacion_summaries.csv e inventario_series.json. El paquete incluye los códigos originales y el código de consolidación para reproducir estas tablas.

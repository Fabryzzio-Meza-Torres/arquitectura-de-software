# Guía para explicar la experimentación de MINION

## Hilo de la exposición

“Primero elegimos qué documentos devolver; después medimos qué ocurre al servirlos bajo carga y fallas. Finalmente probamos dos variantes complementarias sin volver a ejecutar los modelos.”

### 1. Fijar la decisión antes del test

El Trabajo 1 usa el corpus completo de FiQA y solo sus consultas dev para probar 21 valores de α. Cada consulta comparte la misma unión del top 10 BM25 y top 10 BGE. Ambos puntajes se completan para cada candidato y se normalizan min-max por consulta. Elegimos α=0,85 por P@3, con nDCG@3 y menor α como desempates. La fórmula es f=(1−α)×BM25 normalizado + α×semántico normalizado: α=0,85 asigna 85 % al puntaje semántico y 15 % al léxico. α queda congelado antes de FiQA-test y TREC-COVID.

P@3 es la fracción de los tres primeros documentos que son relevantes. nDCG@3 tiene en cuenta el orden y los grados de relevancia de los juicios disponibles. Comparamos fusión y cross-encoder sobre los mismos candidatos para que el cambio sea la ordenación. El reranker no puede recuperar documentos ausentes de esa unión.

Resultado que debemos decir: en FiQA, el reranker reduce P@3 en 2,06 puntos porcentuales, IC pareado 95 % [−3,55; −0,57]. En TREC, la diferencia es −2,67 pp, IC [−9,33; +3,33], por lo que ese test no establece una mejora ni una caída concluyente. Estos resultados corresponden a este modelo y a estos qrels.

### 2. Medir el servicio y sus respaldos

Los Trabajos 2 y 3 generan llegadas Poisson sin esperar que termine la consulta anterior. La latencia incluye espera desde el instante programado. Cada condición dura 180 s; se excluyen los primeros 30 s y se repite tres veces. Se guardan las solicitudes, no solo el promedio.

Tres cifras responden preguntas diferentes:

- p99: tiempo que alcanza el 99 % de las respuestas válidas de tres documentos.
- Continuidad: fracción de todas las solicitudes que entregan tres documentos en ≤2500 ms.
- Ruta: cuántas reciben reranking, fusión de respaldo, recuperación léxica/semántica o error.

Una continuidad del 100 % puede incluir respuestas de respaldo. Por eso no significa que el reranker haya terminado siempre. Las barras mínimo–máximo de tres p99 son un rango descriptivo, no un intervalo de confianza.

Las condiciones L25–L100 aumentan carga. NORERANK y NOHEDGE eliminan una política. F1/F2 fuerzan error/lentitud del reranker. F3H/F3NH repiten las mismas consultas, llegadas y asignación de demoras con y sin hedging. En TREC/Khipu las demoras efectivas pueden diferir porque algunas consultas activan respaldo antes del reranker; esa exposición se conserva por solicitud. La diferencia de p99 no aísla perfectamente el efecto del hedge. F4/F5 eliminan una ruta de recuperación y F6 elimina ambas: en F6 se espera error controlado.

### 3. Qué hicimos para comparar con nuestra compañera

Se reutilizó su código v4 exacto y se igualaron α, Python, versiones, ds001/RTX A6000, un shard, 4 CPU/hilos, 32 GB, plazos, repeticiones y ventanas. Se conserva su resultado de FiQA sin reescribirlo. La GPU es compartida y las condiciones son secuenciales, por lo que no se controla idéntica contención.

Hay dos resultados nuevos que deben contarse por separado:

- **Intento original 63911:** no cumple la regla de capacidad ≥99 % de reranking completo desde el primer escalón. No se pudo validar C en la grilla 1–64 QPS. No demuestra una capacidad de cero ni permite inferir una tasa menor que 1 QPS. Se conserva el fallo sin aumentar plazos ni rebajar el 99 %.
- **Complementario 63919:** usa las cargas absolutas ya registradas en FiQA: 2/4/6/8 QPS, con el umbral propio de TREC. El adaptador utiliza C_qps=8 solo para escalar cargas; no es una capacidad validada de TREC. Así se compara a iguales QPS absolutos, sin afirmar una comparación a igual porcentaje de capacidad propia.

A 8 QPS, los p99 medianos [rango de tres repeticiones] son:

| Dataset / ds001 | p99 ms | Qué representa 8 QPS |
|---|---|---|
| FiQA | 1483.0 [1417.6; 1504.0] | C validada por su calibración |
| TREC-COVID | 1745.8 [1728.9; 2067.9] | Referencia externa de carga fija |

La C de FiQA se estimó con consultas train y no garantiza idéntica proporción de reranking al servir test. Los títulos de calibración de TREC tampoco son sus preguntas test. La diferencia describe operación observada con esos corpus, consultas y contención. No prueba que el dataset sea la única causa. Las series Kaggle/T4 se muestran como evidencia de otro montaje; sus tiempos no se mezclan con Khipu.

### 4. Qué añaden los complementarios offline

RRF se fija con k=60 antes de evaluar y suma contribuciones de las posiciones originales. La unión de candidatos es la misma que en la fusión convexa. En ambas colecciones, RRF pierde P@3 con IC negativos en estas corridas.

El reranking selectivo usa el margen entre puestos 3 y 4. Los umbrales se fijan solo en FiQA-dev y se aplican sin reajuste a ambos tests. La comparación principal apunta al 50 % en dev, pero invoca 51,85 % en FiQA-test y 72 % en TREC: una tasa objetivo no se transfiere automáticamente entre colecciones. El control aleatorio usa el mismo número de invocaciones y promedia 100 selecciones con semillas guardadas.

La selectividad no demuestra una mejora de P@3 con esos intervalos. Menos invocaciones tampoco demuestra menor latencia: esa variante requiere otra prueba temporal.

## Evidencia para responder preguntas

El PDF integrado contiene resultados e interpretación. La carpeta 04 conserva las tablas verificadas. La carpeta 05 incluye el plan, la comparación automática, los dos intentos nuevos, el notebook ejecutado, nueve figuras y los logs. Los originales de las ramas se conservan en 02 y 03; procedencia.json fija sus commits y MANIFEST_SHA256.json permite verificar los archivos.

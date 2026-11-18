# Informe de resultados — Trabajos 2 y 3 (Latencia y fallas)

Paper: **MINION: Parallel Hybrid Retrieval and Reranking under a Latency Budget**.
Datasets: **FiQA-2018** (Trabajo 2, Persona 2) y **TREC-COVID** (Trabajo 3, Persona 3).

Este informe explica, en lenguaje simple, qué se hizo, qué números salieron y qué se puede (y qué no se puede) concluir. Todos los números salen de `results/<dataset>/summary.csv`, `calibration.json` y de los notebooks ejecutados `trabajo2_latencia_fiqa.ipynb` y `trabajo3_latencia_trec-covid.ipynb`.

---

## 1. La idea en una página

**Qué es MINION.** Es un buscador que, ante una pregunta, hace dos búsquedas a la vez:

- una **léxica** (BM25: busca por palabras parecidas),
- una **semántica** (un modelo de lenguaje que busca por significado).

Mezcla los dos resultados (fusión) y luego un tercer modelo, el **reranker**, reordena los mejores candidatos y se queda con los **3 mejores**. El reranker es lo más lento, pero mejora la calidad de la respuesta.

**Qué preguntamos en estos trabajos.** No medimos si las respuestas son buenas (eso es el Trabajo 1). Medimos **tiempo y continuidad**:

1. ¿Responde el sistema dentro de **2,5 segundos** (el límite, llamado SLO) aunque haya mucha gente consultando?
2. Si algo se rompe (el reranker, la búsqueda semántica, la léxica), ¿el sistema **sigue dando 3 resultados** a tiempo, aunque sean de menor calidad?
3. Para evitar que unas pocas consultas lentas arruinen la experiencia, el sistema usa **hedging**: si el reranker tarda demasiado, manda la misma consulta a una segunda copia del reranker y se queda con la que responda primero. ¿Funciona sin gastar demasiado trabajo extra?

**Respuesta corta.**

| Pregunta | FiQA | TREC-COVID |
|---|---|---|
| ¿p99 dentro de 2,5 s con carga normal? | **Sí** (peor caso 379 ms) | **Sí** (peor caso 463 ms) |
| ¿Sigue respondiendo si falla el reranker? | **Sí**, 100 % de continuidad | **Sí**, 100 % de continuidad |
| ¿El hedging ayuda? | **Sí**: baja el p99 de 948 a 389 ms | **Sí**: baja el p99 de 984 a 433 ms |
| ¿Duplicadas ≤ 10 %? | **Sí** (máx. 7,79 %) | **No, por poco** (máx. 10,11 %) |

Hay dos matices que importan y están explicados más abajo: el caso de las duplicadas en TREC-COVID (sección 7) y que la capacidad C = 2 QPS es apretada (sección 4).

---

## 2. Qué se hizo, paso a paso

### 2.1 Cambio de hardware

La especificación pedía correr en **Khipu** (GPU RTX A6000). No hubo cuenta, así que todo corrió en **Kaggle con una GPU Tesla T4**, más pequeña. Esto se declara como limitación: los milisegundos exactos no son comparables con los de un A6000, aunque la forma de los resultados (qué es más lento que qué, cómo reaccionan las fallas) sí debería mantenerse.

### 2.2 Orden de ejecución

1. **Piloto.** Una prueba chica (2.000 documentos, escalones de 20 s, 1 repetición de 60 s) en FiQA, para comprobar que el script funciona y que cada condición usa la ruta esperada. Sus resultados **no son entregables** (están en `pilot-out/`, fuera del repositorio).
2. **Calibración.** Con el corpus completo (57.638 documentos en FiQA, 171.332 en TREC-COVID) se mide el sistema "en reposo" y luego bajo carga creciente para fijar dos números que quedan **congelados** (`"frozen": true`):
   - **C**: la capacidad del sistema, en consultas por segundo (QPS).
   - **Umbral de hedging**: a partir de cuántos milisegundos se manda la copia al segundo reranker.
3. **Corrida final.** Las **13 condiciones × 3 repeticiones** (39 corridas por dataset), cada una de 3 minutos (los primeros 30 s se descartan como calentamiento).

### 2.3 Cómo se genera la carga

Las consultas llegan como en la vida real: de forma **aleatoria** (proceso de Poisson), sin esperar a que terminen las anteriores ("open-loop"). La latencia se mide **desde la hora en que la consulta debió llegar**, no desde que el sistema empezó a atenderla. Así, si el sistema se atasca, el retraso aparece en las cifras y no se esconde.

### 2.4 Las 13 condiciones

La "carga" se expresa como porcentaje de C. Como C = 2 QPS, el 100 % son 2 QPS, el 75 % son 1,5 QPS, etc.

| Condición | Qué se prueba | Ruta esperada |
|---|---|---|
| **L25, L50, L75, L100** | Sistema completo, sin fallas, con 25/50/75/100 % de la carga | `reranked` (top 3 del reranker) |
| **NORERANK** | Línea base: el reranker **ni se usa**. Solo búsqueda híbrida | `fused_baseline` |
| **NOHEDGE** | Sistema completo a 100 % pero **sin hedging** | `reranked` |
| **F1** | El reranker **falla** (error inmediato en las dos copias) | `fused_fallback` |
| **F2** | El reranker **se cuelga** (demora 1,5 s, más que su plazo de 1,2 s) | `fused_fallback` |
| **F3H** | El reranker A es lento el 5 % de las veces (0,8 s), **con** hedging | `reranked` |
| **F3NH** | **Exactamente lo mismo** que F3H, pero **sin** hedging | `reranked` |
| **F4** | Falla la búsqueda semántica | `lex` (top 3 de BM25) |
| **F5** | Falla la búsqueda léxica | `sem` (top 3 semántico) |
| **F6** | Fallan las dos búsquedas | `error` (error controlado) |

Dos detalles de diseño que dan validez a la comparación:

- **F3H y F3NH reciben las mismas llegadas y las mismas demoras** (misma semilla). La única diferencia es si se duplica o no. Por eso la diferencia entre ambas se puede atribuir al hedging y a nada más.
- **NORERANK ≠ F1/F2.** NORERANK es el sistema "sin reranker por diseño". F1 y F2 son el sistema *con* reranker pero roto: prueban que la ruta de respaldo funciona.

### 2.5 Qué significa cada medida

- **p50 / p95 / p99**: el tiempo en que responde el 50 %, 95 % y 99 % de las consultas. El p99 es el "caso malo pero real": 1 de cada 100 consultas tarda eso o más.
- **Continuidad**: porcentaje de consultas que reciben **3 resultados en ≤ 2.500 ms**, sobre *todas* las enviadas.
- **% de duplicadas**: copias extra enviadas por hedging, sobre las solicitudes originales. El paper pide que no pase de **10 %**.
- **Ruta**: qué camino siguió cada consulta (reranker, respaldo, solo léxica, etc.).

---

## 3. Calibración: cómo se comporta el sistema en reposo

A 1 QPS (sin hedging), tiempo por etapa, en milisegundos:

| Etapa | FiQA p50 / p95 / p99 | TREC-COVID p50 / p95 / p99 |
|---|---|---|
| Búsqueda léxica (BM25) | 4,7 / 6,3 / 7,4 | 6,3 / 13,7 / 19,4 |
| Búsqueda semántica | 28,3 / 99,7 / 155,5 | 62,2 / 152,7 / 261,2 |
| Fusión | 0,5 / 0,6 / 1,0 | 0,5 / 0,9 / 1,4 |
| Reranker | 115,4 / 168,1 / 177,0 | 114,6 / 162,2 / 181,3 |
| **Total (extremo a extremo)** | **149,1 / 228,2 / 305,4** | **184,3 / 284,4 / 383,0** |

Lo que se ve:

- **El reranker domina el tiempo**: unos 115 ms de los ~150–185 ms totales. Por eso quitarlo (NORERANK) baja tanto la latencia.
- **La búsqueda semántica es la más irregular**: su mediana es baja, pero su p99 es 5 a 6 veces mayor. Es la etapa con "cola larga".
- BM25 y la fusión son casi gratis.
- TREC-COVID es más lento que FiQA en la parte semántica (corpus de 171 mil documentos contra 57 mil).

**Umbral de hedging** = p95 del reranker medido aquí: **168,069 ms (FiQA)** y **162,169 ms (TREC-COVID)**. La lógica es: si el reranker A no ha respondido en el tiempo en que el 95 % de las veces ya habría respondido, probablemente se atascó, y se manda la copia a B.

---

## 4. Capacidad C = 2 QPS (con una advertencia)

Se subió la carga en escalones de 2 minutos (1, 2, 4 y 8 QPS) y se buscó la mayor tasa en que el sistema (a) atiende al menos el 99 % de lo que le llega y (b) mantiene el p99 estable (la segunda mitad del escalón no puede ser más de 1,2 veces peor que la primera).

| Escalón | FiQA | TREC-COVID |
|---|---|---|
| 1 QPS | pasa | pasa |
| **2 QPS** | **pasa** → **C = 2** | **pasa** → **C = 2** |
| 4 QPS | falla *solo* por estabilidad del p99 (razón 1,42; throughput 100 %) | falla *solo* por estabilidad del p99 (razón 1,26; throughput 100 %) |
| 8 QPS | falla por throughput (93,3 %) | falla por throughput (88,8 %) |

Cómo leerlo en simple: **a 4 QPS el sistema todavía atendía todo, pero su p99 empeoraba durante el escalón**, señal de que empezaba a acumular cola. A 8 QPS ya no daba abasto. Por eso C = 2 es razonable, pero **es un valor apretado**: el escalón de 4 QPS falló por un margen chico y la regla es sensible al ruido. Es una limitación que conviene decir en el paper. Además, el ritmo de 16 QPS en adelante no se ejecutó (la rampa se corta tras dos escalones seguidos fallidos).

---

## 5. Resultados bajo carga normal (L25 a L100)

p99 (ms), mediana de las 3 repeticiones; entre corchetes, mínimo y máximo.

| Condición | FiQA | TREC-COVID |
|---|---|---|
| L25 (0,5 QPS) | 242 [236–263] | 256 [247–287] |
| L50 (1,0 QPS) | 252 [234–279] | 324 [315–327] |
| L75 (1,5 QPS) | 309 [297–313] | 432 [399–463] |
| L100 (2,0 QPS) | 325 [315–379] | 408 [389–454] |
| NOHEDGE (2,0 QPS) | 307 [296–315] | 400 [397–412] |
| **NORERANK (2,0 QPS)** | **43 [42–45]** | **111 [100–112]** |

Qué se demuestra:

1. **El límite de 2,5 s se cumple con enorme holgura.** El peor p99 de todas las corridas con carga normal es 379 ms (FiQA) y 463 ms (TREC-COVID), es decir, unas **5 a 7 veces por debajo del SLO**. Fitness (i) cumple.
2. **La latencia sube suavemente con la carga**, sin saltos bruscos: el sistema no se satura hasta C.
3. **El costo del reranker es real**: a la misma carga, el p99 con reranker (325 y 408 ms) es entre 3,7 y 7,5 veces el de NORERANK (43 y 111 ms). Esto cuesta tiempo; si vale la pena en calidad lo dice el Trabajo 1, **no este trabajo**.
4. **Con o sin hedging a carga normal casi no hay diferencia** (L100 contra NOHEDGE). Es lo esperable: si no hay fallas, el hedging casi no se dispara.

---

## 6. Resultados con fallas

### 6.1 La ruta correcta se activa siempre

En las **78 corridas** (13 condiciones × 3 repeticiones × 2 datasets), la ruta dominante fue la que dice la Tabla 2 del paper, al 100 %. Por ejemplo: F4 siempre dio `lex`, F5 siempre `sem`, F1/F2 siempre `fused_fallback`, F6 siempre `error`, y NORERANK siempre `fused_baseline`. **Las rutas no se mezclan** (la matriz K6 lo muestra).

### 6.2 Continuidad y tiempo bajo fallas

| Condición | Qué pasó | p99 FiQA (ms) | p99 TREC-COVID (ms) | Continuidad |
|---|---|---|---|---|
| F1 | Reranker falla → respaldo | 45 | 120 | 100 % |
| F2 | Reranker colgado → espera su plazo y luego respaldo | 1.368 | 1.517 | 100 % |
| F4 | Sin semántica → solo BM25 | 5,9 | 10,0 | 100 % |
| F5 | Sin léxica → solo semántica | 42 | 105 | 100 % |
| F6 | Fallan las dos búsquedas | n/a | n/a | **0 %** (esperado) |

En simple:

- **F1 (error inmediato)**: el sistema se da cuenta enseguida y entrega el top 3 de la fusión en ~30 ms de mediana. Incluso es *más rápido* que el sistema normal, porque se salta el reranker.
- **F2 (reranker colgado)**: es el peor caso de tiempo, porque el sistema **espera el plazo de 1,2 s del reranker antes de rendirse**. Aun así queda en ~1,4–1,5 s, **dentro del SLO de 2,5 s**. Continuidad 100 %. Fitness (iii) cumple.
- **F4 y F5**: perder una de las dos búsquedas es casi imperceptible en tiempo. F4 es aún más rápida porque BM25 es rapidísima.
- **F6 da 0 % de continuidad a propósito**: si fallan *las dos* búsquedas no hay nada que devolver. Lo importante es que el sistema responde un **error controlado** y no se cae. F6 no entra en las fitness (iii), que solo evalúa F1 y F2.

---

## 7. Hedging: la comparación F3H contra F3NH

Ambas condiciones usan las mismas llegadas y demoran exactamente las mismas solicitudes (el 5 % se frena 0,8 s). La única diferencia es que F3H tiene hedging.

| Medida | FiQA F3H | FiQA F3NH | TREC-COVID F3H | TREC-COVID F3NH |
|---|---|---|---|---|
| p99 del reranker (ms) | 306 | 917 | 310 | 918 |
| p99 extremo a extremo (ms) | 389 | 948 | 433 | 984 |
| Mejora en p99 total | **−558 ms** | | **−551 ms** | |
| % de duplicadas | 6,9 % | 0 % | 7,8 % | 0 % |

Qué se demuestra:

- **El hedging corta la cola**: sin él, las solicitudes frenadas esperan casi los 0,8 s completos y el p99 llega a ~950–980 ms. Con él, la copia en la réplica B responde a tiempo y el p99 baja a ~390–430 ms, **menos de la mitad**.
- **Cuesta poco**: solo 7–8 % de consultas extra, por debajo del tope de 10 %.
- **No es una mejora del caso típico**: la mediana (p50) casi no cambia (≈ 137 ms contra 143 ms). Lo que se beneficia es el **final de la distribución**, que es justo lo que importa para un SLO.

Esto es una evidencia fuerte porque la comparación está controlada (misma semilla).

### Sobre el límite de duplicadas (fitness iv)

La fitness (iv) pide ≤ 10 % de duplicadas en **L25–L100 y F3H**.

- **FiQA: cumple** (peor caso 7,79 %).
- **TREC-COVID: no cumple por 0,11 puntos**: en L25 las repeticiones 2 y 3 dieron 10,11 % (9 duplicadas sobre 89 originales). El notebook lo marca en rojo.

Por qué es un resultado delicado y no un fallo grave:

- **Pocas muestras**: L25 tiene solo 89 solicitudes. Una sola duplicada más o menos mueve el porcentaje en más de un punto. En FiQA, L25 dio ~1 %.
- **El umbral de hedging parece quedar justo para este dataset**: TREC-COVID dispara más hedges que FiQA a carga baja (≈ 9 % contra ≈ 1 %). Es una hipótesis razonable pero **no la verifiqué**; haría falta comparar los tiempos del reranker en calibración contra los de L25.
- **El tope se controla por ventana de 60 s, no sobre el total**: así que el porcentaje acumulado de la corrida puede quedar apenas por encima de 10 % sin que haya un error de implementación. Pasa también en **F1 y F2 (10,39 % = 24 de 231)**. Eso **no afecta la fitness (iv)**, porque F1 y F2 no entran en ella, pero explica por qué el número se pasa de 10 un poco.

Conclusión honesta: en TREC-COVID el hedging **casi** cumple el tope, y habría que decirlo como está, sin redondear.

---

## 8. Las fitness functions en una tabla

| Fitness | Qué exige | FiQA | TREC-COVID |
|---|---|---|---|
| (i) | p99 ≤ 2.500 ms en L25–L100 | **Cumple** (peor 379 ms; margen 2.121 ms) | **Cumple** (peor 463 ms; margen 2.037 ms) |
| (ii) | P@3 con reranker ≥ sin reranker | Se mide en el **Trabajo 1** | Se mide en el **Trabajo 1** |
| (iii) | Continuidad ≥ 99 % en F1 y F2 | **Cumple** (100 %) | **Cumple** (100 %) |
| (iv) | Duplicadas ≤ 10 % en L25–L100 y F3H | **Cumple** (peor 7,79 %) | **No cumple** (peor 10,11 %) |

---

## 9. Qué se demuestra y qué no

### Se demuestra (con evidencia directa)

1. **Con carga normal el sistema es mucho más rápido que el límite**: p99 de 0,25–0,46 s contra un SLO de 2,5 s.
2. **El sistema degrada con elegancia**: cada falla activa la ruta de respaldo prevista, sin mezclar caminos, y la continuidad se mantiene en 100 % salvo cuando es imposible (F6).
3. **El peor escenario de fallas (reranker colgado) sigue dentro del SLO** (~1,4–1,5 s).
4. **El hedging reduce el p99 más de la mitad** frente a no usarlo, con un costo de 7–8 % de solicitudes extra, y la comparación está controlada por semilla.
5. **Los resultados son consistentes entre dos datasets distintos** y entre las 3 repeticiones (los rangos son estrechos, salvo donde se indica).

### No se demuestra / hay que tener cuidado

1. **La calidad de las respuestas**: aquí solo se mide tiempo. Que el reranker valga su costo (3,7 a 7,5 veces más p99) depende del Trabajo 1.
2. **Que esto sea el rendimiento real de Khipu**: la GPU fue una T4 de Kaggle, no un A6000.
3. **Escalabilidad a más carga**: C = 2 QPS es una carga baja en términos absolutos, y el valor de C es sensible al ruido (el escalón de 4 QPS falló por poco).
4. **Que el hedging cumpla el tope en cualquier dataset**: en TREC-COVID quedó 0,11 puntos arriba en L25.

### Limitaciones declaradas

- GPU **Tesla T4** de Kaggle en lugar de un A6000.
- Las **dos réplicas del reranker comparten la misma GPU** (no son máquinas independientes), así que el hedging es optimista en un aspecto: en producción las réplicas podrían estar en hardware distinto.
- Todo corre en **un proceso y una sola máquina**.
- **p99 sobre pocas muestras** en cargas bajas (L25 tiene 89 solicitudes por corrida).
- TREC-COVID usa solo **50 consultas de prueba** (recorridas de forma cíclica); FiQA usa 648.
- La rampa de calibración solo llegó a 8 QPS.

---

## 10. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Especificación del trabajo | `TRABAJO_2y3_latencia_khipu.md` |
| Script de medición | `minion_bench.py` |
| Notebooks ejecutados | `trabajo2_latencia_fiqa.ipynb`, `trabajo3_latencia_trec-covid.ipynb` |
| Figuras K1–K9 (18 PNG) | `figs/` |
| Resumen por repetición y condición | `results/<dataset>/summary.csv` |
| Calibración (C y umbral) | `results/<dataset>/calibration.json` |
| Entorno de la corrida | `results/<dataset>/run_meta.json` |
| Registro de cada solicitud | `results/<dataset>/requests_*.jsonl` (39 por dataset + calibración) |
| Tablas para el paper | `tabla_paper_fiqa.csv`, `tabla_paper_trec-covid.csv` |

### Qué muestra cada figura

| Figura | Qué muestra |
|---|---|
| K1 | Calibración: capacidad lograda contra ofrecida, y p99 contra carga. Marca C |
| K2 | Tiempo por etapa (léxica, semántica, fusión, reranker, total) a 1 QPS |
| K3 | Distribución acumulada (ECDF) de la latencia en L25–L100 |
| K4 | p50, p95 y p99 contra % de carga, con NORERANK y NOHEDGE aparte |
| K5 | Latencia de cada solicitud en el tiempo (L100 y F2) |
| K6 | Matriz: qué ruta usó cada una de las 13 condiciones |
| K7 | Continuidad en F1, F2, F4–F6 |
| K8 | F3H contra F3NH: latencia del reranker y total, y % de duplicadas |
| K9 | Semáforo de las fitness (i), (iii) y (iv) por repetición |

> **Nota de verificación.** Los números de este informe se leyeron de `summary.csv`, `calibration.json` y las salidas guardadas de los notebooks. Las figuras existen y sus notebooks se ejecutaron sin errores, pero **no se revisaron visualmente una por una** (títulos, leyendas y colores) en esta sesión.

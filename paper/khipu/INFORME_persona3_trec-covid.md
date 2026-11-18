# Informe de resultados — Trabajo 3 (Persona 3) · TREC-COVID

Paper: **MINION: Parallel Hybrid Retrieval and Reranking under a Latency Budget**.
Dataset: **TREC-COVID** (171.332 documentos, 50 consultas de prueba).

Este informe explica, en lenguaje simple, qué se hizo en el Trabajo 3, qué números salieron y qué se puede (y qué no) concluir. Los números salen de `results/trec-covid/summary.csv`, `results/trec-covid/calibration.json`, `tabla_paper_trec-covid.csv` y del notebook ejecutado `trabajo3_latencia_trec-covid.ipynb`.

---

## 1. La idea en una página

**Qué es MINION.** Ante una pregunta, el sistema hace dos búsquedas a la vez:

- una **léxica** (BM25: busca por palabras parecidas),
- una **semántica** (un modelo de lenguaje que busca por significado).

Mezcla los dos resultados (fusión) y un tercer modelo, el **reranker**, reordena los mejores candidatos y se queda con los **3 mejores**. El reranker es lo más lento, pero mejora la calidad.

**Qué se midió.** Solo **tiempo y continuidad** (la calidad de las respuestas es del Trabajo 1):

1. ¿Responde dentro de **2,5 segundos** (el SLO) aunque haya carga?
2. Si algo falla (reranker, búsqueda semántica o léxica), ¿sigue dando **3 resultados** a tiempo?
3. ¿El **hedging** (mandar una copia a un segundo reranker cuando el primero tarda demasiado) reduce los casos lentos sin gastar demasiado trabajo extra?

**Respuesta corta para TREC-COVID**

| Pregunta | Resultado |
|---|---|
| ¿p99 dentro de 2,5 s con carga normal? | **Sí.** Peor caso: 463 ms |
| ¿Sigue respondiendo si falla el reranker? | **Sí.** Continuidad 100 % en F1 y F2 |
| ¿El hedging ayuda? | **Sí.** Baja el p99 de 984 ms a 433 ms |
| ¿Duplicadas ≤ 10 %? | **No, por poco.** Máximo 10,11 % (L25) |

---

## 2. Qué se hizo

### 2.1 Hardware

La especificación pedía Khipu (RTX A6000), pero no hubo cuenta. Todo corrió en **Kaggle con GPU Tesla T4**. Es una limitación declarada: los milisegundos exactos no son comparables con los de un A6000, aunque la forma de los resultados sí debería mantenerse.

### 2.2 Orden de ejecución

1. **Piloto** (hecho en FiQA, con 2.000 documentos): sirvió para validar el script y las rutas. No es entregable.
2. **Calibración** con el corpus completo de TREC-COVID: se mide el sistema en reposo y bajo carga creciente para fijar dos valores **congelados**: la capacidad **C** y el **umbral de hedging**.
3. **Corrida final:** 13 condiciones × 3 repeticiones = 39 corridas de 3 minutos (los primeros 30 s se descartan como calentamiento).

### 2.3 Cómo se genera la carga

Las consultas llegan de forma aleatoria (proceso de Poisson) **sin esperar a las anteriores** ("open-loop"). La latencia se mide **desde la hora en que la consulta debió llegar**, así que si el sistema se atasca, el retraso se ve en las cifras.

### 2.4 Las 13 condiciones

La carga se expresa como % de C. Como C = 2 QPS, el 100 % son 2 QPS y el 75 % son 1,5 QPS.

| Condición | Qué se prueba | Ruta esperada |
|---|---|---|
| **L25, L50, L75, L100** | Sistema completo, sin fallas, con 25/50/75/100 % de la carga | `reranked` |
| **NORERANK** | Línea base: el reranker no se usa | `fused_baseline` |
| **NOHEDGE** | Sistema completo a 100 %, sin hedging | `reranked` |
| **F1** | El reranker **falla** (error inmediato en las dos copias) | `fused_fallback` |
| **F2** | El reranker **se cuelga** (demora 1,5 s, más que su plazo de 1,2 s) | `fused_fallback` |
| **F3H** | El reranker A es lento el 5 % de las veces (0,8 s), **con** hedging | `reranked` |
| **F3NH** | **Las mismas** llegadas y demoras que F3H, **sin** hedging | `reranked` |
| **F4** | Falla la búsqueda semántica | `lex` |
| **F5** | Falla la búsqueda léxica | `sem` |
| **F6** | Fallan las dos búsquedas | `error` |

F3H y F3NH usan la misma semilla, así que la única diferencia entre ellas es el hedging. NORERANK (sin reranker por diseño) no es lo mismo que F1/F2 (reranker roto).

### 2.5 Medidas

- **p50 / p95 / p99:** tiempo en que responde el 50 %, 95 % y 99 % de las consultas.
- **Continuidad:** % de consultas con 3 resultados en ≤ 2.500 ms, sobre todas las enviadas.
- **% de duplicadas:** copias extra por hedging sobre las solicitudes originales (tope del paper: 10 %).

---

## 3. Calibración (1 QPS, sin hedging)

| Etapa | p50 | p95 | p99 |
|---|---|---|---|
| Búsqueda léxica | 6,3 ms | 13,7 ms | 19,4 ms |
| Búsqueda semántica | 62,2 ms | 152,7 ms | 261,2 ms |
| Fusión | 0,5 ms | 0,9 ms | 1,4 ms |
| Reranker | 114,6 ms | 162,2 ms | 181,3 ms |
| **Total** | **184,3 ms** | **284,4 ms** | **383,0 ms** |

- **El reranker domina** (~115 ms de ~184 ms).
- **La semántica tiene cola larga:** su p99 es unas 4 veces su mediana. Con 171 mil documentos es más lenta que en FiQA (p50 62 ms contra 28 ms).
- BM25 y la fusión casi no cuestan.

**Umbral de hedging = 162,169 ms** (el p95 del reranker). Si el reranker A no ha respondido en el tiempo en que el 95 % de las veces ya lo habría hecho, se manda la copia a B.

---

## 4. Capacidad C = 2 QPS (con advertencia)

| Escalón | Resultado |
|---|---|
| 1 QPS | pasa |
| **2 QPS** | **pasa** → **C = 2** |
| 4 QPS | falla **solo** por estabilidad del p99 (2ª mitad = 812 ms contra 644 ms de la 1ª; razón 1,26 > 1,2). Throughput 100 % |
| 8 QPS | falla por throughput (88,8 %) |

A 4 QPS el sistema todavía atendía todo, pero el p99 empeoraba durante el escalón (señal de cola que crece). A 8 QPS ya no daba abasto. C = 2 es razonable, pero **es apretado**: el escalón de 4 QPS falló por un margen chico y la regla es sensible al ruido. Además, 16 QPS en adelante no se ejecutó (la rampa se corta tras dos escalones seguidos fallidos).

---

## 5. Carga normal

Mediana de 3 repeticiones y [mín–máx]:

| Condición | p50 (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|
| L25 (0,5 QPS) | 194,4 | 231,0 | 255,8 [246,9–286,5] |
| L50 (1,0 QPS) | 172,8 | 263,9 | 324,2 [314,6–326,7] |
| L75 (1,5 QPS) | 170,3 | 296,6 | 431,6 [398,9–463,0] |
| L100 (2,0 QPS) | 168,5 | 286,3 | 407,6 [388,8–453,5] |
| NOHEDGE (2,0 QPS) | 170,4 | 293,0 | 400,1 [397,4–412,4] |
| **NORERANK (2,0 QPS)** | **58,9** | **83,8** | **111,2 [99,7–112,0]** |

- **El SLO de 2,5 s se cumple con mucha holgura:** el peor p99 es 463 ms (unas 5 veces por debajo). **Fitness (i) cumple.**
- **La latencia sube suave** con la carga, sin saltos hasta C.
- **El reranker cuesta:** a 2 QPS, el p99 con reranker (408 ms) es unas 3,7 veces el de NORERANK (111 ms). Si ese costo vale la pena en calidad lo dice el Trabajo 1, no este trabajo.
- **Con o sin hedging a carga normal casi no hay diferencia** (L100 contra NOHEDGE): sin fallas, el hedging casi no se dispara.

---

## 6. Fallas

### 6.1 Rutas

En las **39 corridas** de TREC-COVID, la ruta dominante fue la de la Tabla 2 del paper al 100 %. Las rutas no se mezclan.

### 6.2 Continuidad y tiempo

| Condición | Qué pasó | p99 (ms) | Continuidad |
|---|---|---|---|
| F1 | Reranker falla → respaldo | 119,8 | 100 % |
| F2 | Reranker colgado → espera 1,2 s y usa respaldo | 1.517 | 100 % |
| F4 | Sin semántica → solo BM25 | 10,0 | 100 % |
| F5 | Sin léxica → solo semántica | 105,2 | 100 % |
| F6 | Fallan las dos búsquedas | n/a | **0 %** (esperado) |

- **F1:** el sistema se da cuenta enseguida y responde con el top 3 de la fusión (~60 ms de mediana), incluso más rápido que el sistema normal.
- **F2:** es el peor caso de tiempo, porque se espera el plazo de 1,2 s del reranker antes de rendirse. Aun así queda en ~1,5 s, **dentro del SLO**. **Fitness (iii) cumple.**
- **F4 y F5:** perder una búsqueda casi no se nota en tiempo.
- **F6 da 0 % a propósito:** si fallan las dos búsquedas no hay nada que devolver; lo importante es que responde un **error controlado**. F6 no entra en la fitness (iii).

---

## 7. Hedging: F3H contra F3NH

| Medida | F3H (con hedging) | F3NH (sin hedging) |
|---|---|---|
| p99 del reranker | 310 ms | 918 ms |
| p99 extremo a extremo | 433 ms | 984 ms |
| Mejora en p99 total | **−551 ms** | |
| % de duplicadas | 7,8 % | 0 % |

- **Corta la cola:** sin hedging, las solicitudes frenadas esperan casi los 0,8 s completos (p99 ~984 ms). Con hedging, la copia en la réplica B responde a tiempo y el p99 baja a ~433 ms, **menos de la mitad**.
- **Cuesta poco:** 7,8 % de consultas extra, por debajo del 10 %.
- **No mejora el caso típico:** la mediana casi no cambia (173 ms contra 174 ms). Lo que mejora es el **final de la distribución**, que es lo que importa para un SLO.
- La comparación está controlada (misma semilla), así que la diferencia se atribuye al hedging.

### Duplicadas: lo que no cumple (fitness iv)

La fitness (iv) pide ≤ 10 % de duplicadas en **L25–L100 y F3H**. En TREC-COVID, **L25 dio 10,11 %** en las repeticiones 2 y 3 (9 duplicadas sobre 89 originales): se pasa por **0,11 puntos**. El notebook lo marca en rojo.

Por qué conviene explicarlo así y no maquillarlo:

- **Pocas muestras:** L25 tiene solo 89 solicitudes; una duplicada más o menos mueve el % más de un punto.
- **Hipótesis (no verificada):** el umbral de hedging (162 ms) queda justo para este dataset. En L25, TREC-COVID dispara ≈ 9–10 % de hedges, mientras FiQA dispara ≈ 1 %. Habría que comparar los tiempos del reranker en calibración contra los de L25 para confirmarlo.
- **El tope se controla por ventana de 60 s**, no sobre el total de la corrida; por eso el % acumulado puede quedar apenas sobre 10 %. F1 y F2 dan 10,39 % (24 de 231) por lo mismo, pero **no cuentan** para la fitness (iv).

---

## 8. Fitness functions

| Fitness | Exige | TREC-COVID |
|---|---|---|
| (i) | p99 ≤ 2.500 ms en L25–L100 | **Cumple** (peor 463,0 ms; margen 2.037 ms) |
| (ii) | P@3 con reranker ≥ sin reranker | Se mide en el **Trabajo 1** |
| (iii) | Continuidad ≥ 99 % en F1 y F2 | **Cumple** (100 %) |
| (iv) | Duplicadas ≤ 10 % en L25–L100 y F3H | **No cumple** (peor 10,11 %; −0,11 pp) |

---

## 9. Qué se demuestra y qué no

### Se demuestra

1. Con carga normal el sistema es **mucho más rápido que el límite**: p99 de 0,26–0,46 s contra 2,5 s.
2. **Degrada con elegancia:** cada falla activa la ruta de respaldo prevista y la continuidad se mantiene en 100 % salvo cuando es imposible (F6).
3. El peor escenario (reranker colgado) **sigue dentro del SLO** (~1,5 s).
4. El **hedging reduce el p99 más de la mitad** (984 → 433 ms) con 7,8 % de solicitudes extra, en una comparación controlada.

### No se demuestra / hay que tener cuidado

1. **La calidad de las respuestas** (Trabajo 1).
2. **El rendimiento real en Khipu:** la GPU fue una T4 de Kaggle.
3. **Escalabilidad:** C = 2 QPS es carga baja y el valor de C es sensible al ruido.
4. **Que el hedging cumpla el tope de 10 %** en este dataset: en L25 quedó 0,11 puntos por encima.

### Limitaciones declaradas

- GPU Tesla T4 de Kaggle en lugar de A6000.
- Las **dos réplicas del reranker comparten la misma GPU**; en producción podrían estar en hardware distinto.
- Un solo proceso y una sola máquina.
- p99 sobre **pocas muestras** en cargas bajas (L25: 89 solicitudes por corrida).
- Solo **50 consultas de prueba** (recorridas de forma cíclica).
- La rampa de calibración solo llegó a 8 QPS.

---

## 10. Archivos del Trabajo 3

| Qué | Dónde |
|---|---|
| Notebook ejecutado | `trabajo3_latencia_trec-covid.ipynb` |
| Figuras K1–K9 | `figs/K*_trec-covid.png` |
| Resumen por repetición y condición | `results/trec-covid/summary.csv` |
| Calibración (C y umbral) | `results/trec-covid/calibration.json` |
| Entorno de la corrida | `results/trec-covid/run_meta.json` |
| Registro de cada solicitud | `results/trec-covid/requests_*.jsonl` |
| Tabla para el paper | `tabla_paper_trec-covid.csv` |

| Figura | Qué muestra |
|---|---|
| K1 | Calibración: capacidad lograda contra ofrecida, y p99 contra carga; marca C |
| K2 | Tiempo por etapa a 1 QPS |
| K3 | ECDF de la latencia en L25–L100 |
| K4 | p50, p95 y p99 contra % de carga, con NORERANK y NOHEDGE aparte |
| K5 | Latencia de cada solicitud en el tiempo (L100 y F2) |
| K6 | Matriz de rutas de las 13 condiciones |
| K7 | Continuidad en F1, F2, F4–F6 |
| K8 | F3H contra F3NH y % de duplicadas |
| K9 | Semáforo de las fitness (i), (iii) y (iv) por repetición |

> **Nota de verificación.** Los números se leyeron de `summary.csv`, `calibration.json` y las salidas guardadas del notebook. Las figuras existen y el notebook se ejecutó sin errores, pero **no se revisaron visualmente una por una**.

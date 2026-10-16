**Parametros entrenados** (objetivo CVaR99, biseccion, beta robusto; seed de entrenamiento 7, evaluacion 42): alpha = 17.0 ms, beta* = 34.1 ms (minimo factible en nominal y con cola sana pesada), beta usado = 34.1 ms.
Carga: 4000 requests por corrida a 250 rps (open-loop). TTL fresco 1 s, TTL maximo 5 s.

#### 1. Colas (modelo del profe: 10 servicios al 1%)

| Metrica | Baseline | PoC 2: mejorada | B: retry primero (ablacion) |
|---|---:|---:|---:|
| p50 (ms) | 19.5 | 19.8 | 19.6 |
| p95 (ms) | 1003.3 | 33.9 | 33.8 |
| p99 (ms) | 1081.4 | 39.4 | 43.7 |
| CVaR99 (ms) | 1092.1 | 46.0 | 54.9 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 41804 | 41933 |
| Carga extra | 0.0% | 4.51% | 4.83% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 9 (0.22%) | 0 (0.0%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 1792 / 12 / 21 | 1911 / 22 / 22 |
| Antiguedad max. del dato de cache (s) | - | 0.01 | 0 |
| Lag p99 del event loop (ms) | 2.5 | 2.28 | 2.04 |

#### 2. Estres: servicios 8-10 al 10%, colas de 0.5-1.5 s

| Metrica | Baseline | PoC 2: mejorada | B: retry primero (ablacion) |
|---|---:|---:|---:|
| p50 (ms) | 21.8 | 22.5 | 22.3 |
| p95 (ms) | 1367.9 | 42.1 | 47.4 |
| p99 (ms) | 1479.6 | 46.2 | 64.1 |
| CVaR99 (ms) | 1489.8 | 49.9 | 76.5 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 42829 | 43061 |
| Carga extra | 0.0% | 7.07% | 7.65% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 168 (4.2%) | 0 (0.0%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 2817 / 12 / 181 | 2871 / 190 / 190 |
| Antiguedad max. del dato de cache (s) | - | 0.01 | 0 |
| Lag p99 del event loop (ms) | 2.26 | 1.77 | 2.21 |

#### 3. Service 9 caido (30% central)

| Metrica | Baseline | PoC 2: mejorada | B: retry primero (ablacion) |
|---|---:|---:|---:|
| p50 (ms) | 22.5 | 20.1 | 19.7 |
| p95 (ms) | 2002.9 | 35.7 | 37.5 |
| p99 (ms) | 2003.8 | 52.6 | 95.2 |
| CVaR99 (ms) | 2005.7 | 64.3 | 141.4 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 40503 | 40795 |
| Carga extra | 0.0% | 1.26% | 1.99% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 1256 (31.4%) | 1253 (31.32%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 69 (1.73%) | 64 (1.6%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 1793 / 13 / 39 | 2064 / 30 / 48 |
| Antiguedad max. del dato de cache (s) | - | 5.0 | 5.0 |
| Lag p99 del event loop (ms) | 1.56 | 4.96 | 3.92 |

#### 4. Service 9 caido, prolongado (65%)

| Metrica | Baseline | PoC 2: mejorada | B: retry primero (ablacion) |
|---|---:|---:|---:|
| p50 (ms) | 2001.8 | 19.3 | 19.7 |
| p95 (ms) | 2003.5 | 33.8 | 33.9 |
| p99 (ms) | 2007.7 | 40.3 | 40.0 |
| CVaR99 (ms) | 2013.7 | 49.1 | 52.0 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 39222 | 39128 |
| Carga extra | 0.0% | -1.94% | -2.18% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 1256 (31.4%) | 1251 (31.27%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 1363 (34.08%) | 1366 (34.15%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 1798 / 15 / 47 | 1700 / 22 / 45 |
| Antiguedad max. del dato de cache (s) | - | 5.0 | 5.0 |
| Lag p99 del event loop (ms) | 2.03 | 1.76 | 2.5 |

#### 5. Service 3 degradado x2.5 (40% central)

| Metrica | Baseline | PoC 2: mejorada | B: retry primero (ablacion) |
|---|---:|---:|---:|
| p50 (ms) | 22.9 | 22.9 | 23.3 |
| p95 (ms) | 1002.4 | 43.1 | 44.8 |
| p99 (ms) | 1082.6 | 59.4 | 61.6 |
| CVaR99 (ms) | 1092.5 | 72.8 | 71.7 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 41896 | 41821 |
| Carga extra | 0.0% | 4.74% | 4.55% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 10 (0.25%) | 0 (0.0%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 1880 / 16 / 26 | 1799 / 22 / 22 |
| Antiguedad max. del dato de cache (s) | - | 0.01 | 0 |
| Lag p99 del event loop (ms) | 7.1 | 5.51 | 7.32 |

![resultados](results/resultados.png)

#### 1. Colas (modelo del profe: 10 servicios al 1%)

| Metrica | Baseline | PoC 1: diagrama | PoC 2: mejorada |
|---|---:|---:|---:|
| p50 (ms) | 19.7 | 19.9 | 19.8 |
| p95 (ms) | 1003.2 | 33.6 | 33.9 |
| p99 (ms) | 1082.1 | 39.2 | 39.4 |
| CVaR99 (ms) | 1092.7 | 44.3 | 46.0 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 42059 | 41804 |
| Carga extra | 0.0% | 5.15% | 4.51% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 3 (0.07%) | 9 (0.22%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 2055 / 4 / 7 | 1792 / 12 / 21 |
| Antiguedad max. del dato de cache (s) | - | 0.0 | 0.01 |
| Lag p99 del event loop (ms) | 3.48 | 2.32 | 2.28 |

#### 2. Estres: servicios 8-10 al 10%, colas de 0.5-1.5 s

| Metrica | Baseline | PoC 1: diagrama | PoC 2: mejorada |
|---|---:|---:|---:|
| p50 (ms) | 22.2 | 22.5 | 22.5 |
| p95 (ms) | 1367.4 | 42.0 | 42.1 |
| p99 (ms) | 1479.7 | 48.0 | 46.2 |
| CVaR99 (ms) | 1490.8 | 50.6 | 49.9 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 43148 | 42829 |
| Carga extra | 0.0% | 7.87% | 7.07% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 134 (3.35%) | 168 (4.2%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 3144 / 4 / 138 | 2817 / 12 / 181 |
| Antiguedad max. del dato de cache (s) | - | 0.01 | 0.01 |
| Lag p99 del event loop (ms) | 3.62 | 2.73 | 1.77 |

#### 3. Service 9 caido (30% central)

| Metrica | Baseline | PoC 1: diagrama | PoC 2: mejorada |
|---|---:|---:|---:|
| p50 (ms) | 22.8 | 19.9 | 20.1 |
| p95 (ms) | 2003.1 | 37.7 | 35.7 |
| p99 (ms) | 2006.2 | 73.8 | 52.6 |
| CVaR99 (ms) | 2009.6 | 96.1 | 64.3 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 40978 | 40503 |
| Carga extra | 0.0% | 2.45% | 1.26% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 1370 (34.25%) | 1256 (31.4%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 69 (1.73%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 2277 / 6 / 74 | 1793 / 13 / 39 |
| Antiguedad max. del dato de cache (s) | - | 5.47 | 5.0 |
| Lag p99 del event loop (ms) | 4.13 | 3.87 | 4.96 |

#### 4. Service 9 caido, prolongado (65%)

| Metrica | Baseline | PoC 1: diagrama | PoC 2: mejorada |
|---|---:|---:|---:|
| p50 (ms) | 2001.6 | 19.9 | 19.3 |
| p95 (ms) | 2003.7 | 46.8 | 33.8 |
| p99 (ms) | 2009.8 | 88.0 | 40.3 |
| CVaR99 (ms) | 2015.6 | 123.7 | 49.1 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 39751 | 39222 |
| Carga extra | 0.0% | -0.62% | -1.94% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 2739 (68.47%) | 1256 (31.4%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 1363 (34.08%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 2355 / 5 / 138 | 1798 / 15 / 47 |
| Antiguedad max. del dato de cache (s) | - | 10.95 | 5.0 |
| Lag p99 del event loop (ms) | 3.39 | 4.64 | 1.76 |

#### 5. Service 3 degradado x2.5 (40% central)

| Metrica | Baseline | PoC 1: diagrama | PoC 2: mejorada |
|---|---:|---:|---:|
| p50 (ms) | 22.2 | 22.7 | 22.9 |
| p95 (ms) | 1002.3 | 41.6 | 43.1 |
| p99 (ms) | 1081.9 | 69.8 | 59.4 |
| CVaR99 (ms) | 1092.4 | 77.4 | 72.8 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 43384 | 41896 |
| Carga extra | 0.0% | 8.46% | 4.74% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 3 (0.07%) | 10 (0.25%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 3320 / 64 / 67 | 1880 / 16 / 26 |
| Antiguedad max. del dato de cache (s) | - | 0.01 | 0.01 |
| Lag p99 del event loop (ms) | 2.47 | 2.83 | 5.51 |

![comparativo](comparativo.png)
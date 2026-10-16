**Parametros entrenados** (objetivo CVaR99, bisecccion; seed de entrenamiento 7, evaluacion 42): alpha = 22.2 ms, beta* = 39.7 ms (minimo factible), beta usado = 59.6 ms (beta* x 1.5).
Carga: 4000 requests por corrida a 250 rps (open-loop).

#### 1. Colas independientes

| Metrica | Baseline | PoC 1: diagrama |
|---|---:|---:|
| p50 (ms) | 21.9 | 22.5 |
| p95 (ms) | 1366.5 | 46.1 |
| p99 (ms) | 1480.2 | 63.5 |
| CVaR99 (ms) | 1489.9 | 71.4 |
| Requests ejecutadas | 4000 | 4000 |
| Llamadas a backend | 40000 | 42137 |
| Carga extra | 0.0% | 5.34% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 128 (3.2%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 2135 / 2 / 130 |
| Antiguedad max. del dato de cache (s) | - | 0.01 |
| Lag p99 del event loop (ms) | 3.17 | 3.46 |

#### 2. Service 9 caido (30% central)

| Metrica | Baseline | PoC 1: diagrama |
|---|---:|---:|
| p50 (ms) | 674.4 | 21.5 |
| p95 (ms) | 2003.2 | 51.9 |
| p99 (ms) | 2014.0 | 62.5 |
| CVaR99 (ms) | 2026.1 | 64.4 |
| Requests ejecutadas | 4000 | 4000 |
| Llamadas a backend | 40000 | 40700 |
| Carga extra | 0.0% | 1.75% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 1485 (37.12%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 2024 / 2 / 195 |
| Antiguedad max. del dato de cache (s) | - | 5.62 |
| Lag p99 del event loop (ms) | 5.46 | 1.52 |

#### 3. Service 9 caido, prolongado (65%)

| Metrica | Baseline | PoC 1: diagrama |
|---|---:|---:|
| p50 (ms) | 2001.5 | 21.6 |
| p95 (ms) | 2003.4 | 61.4 |
| p99 (ms) | 2035.3 | 62.9 |
| CVaR99 (ms) | 2052.3 | 64.3 |
| Requests ejecutadas | 4000 | 4000 |
| Llamadas a backend | 40000 | 39293 |
| Carga extra | 0.0% | -1.77% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 2845 (71.12%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 1940 / 2 / 261 |
| Antiguedad max. del dato de cache (s) | - | 11.22 |
| Lag p99 del event loop (ms) | 2.04 | 1.79 |

#### 4. Service 3 degradado x2.5 (40% central)

| Metrica | Baseline | PoC 1: diagrama |
|---|---:|---:|
| p50 (ms) | 26.7 | 27.6 |
| p95 (ms) | 1367.2 | 50.3 |
| p99 (ms) | 1480.1 | 63.0 |
| CVaR99 (ms) | 1490.1 | 69.9 |
| Requests ejecutadas | 4000 | 4000 |
| Llamadas a backend | 40000 | 43175 |
| Carga extra | 0.0% | 7.94% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 128 (3.2%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 3167 / 8 / 136 |
| Antiguedad max. del dato de cache (s) | - | 0.01 |
| Lag p99 del event loop (ms) | 1.88 | 2.93 |

![resultados](results/resultados.png)

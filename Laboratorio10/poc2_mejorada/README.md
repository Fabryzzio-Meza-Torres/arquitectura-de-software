# PoC 2 - El diagrama con mejoras

Parte de la misma arquitectura del diagrama, con los cambios que salieron de comparar la PoC 1 contra una iteración intermedia (la variante B de este README, que reintenta antes de usar la caché). Diagrama: `arquitectura-poc2.png`.

![arquitectura](arquitectura-poc2.png)

## Puntos débiles encontrados y qué se cambió

| Punto débil | Dónde se vio | Cambio en la PoC 2 |
|---|---|---|
| Con un servicio degradado (no caído), α fijo hedgea de más y se pasa del presupuesto de carga | PoC 1 en el escenario 5: 8.46% de carga extra (la PoC 2 usa 4.74%) | α y β se adaptan por servicio con la mediana móvil de latencia, sin pasar de 100 ms y manteniendo β - α ≥ 1.5 veces la mediana |
| La caché no tiene límite de antigüedad ni marca | PoC 1 en el escenario 4: sirvió datos de hasta 10.95 s (la PoC 2 se queda en 5.0 s) | Caché de dos niveles: fresca (≤ 1 s) y vieja (≤ 5 s, solo con el breaker abierto o tras agotar reintentos). Pasado el TTL la llamada falla (GG) en vez de servir un dato más viejo. Todo dato de caché se marca como degradado |
| Reintentar antes de usar la caché cuesta latencia | Variante B contra PoC 2, p99: 43.7 contra 39.4 ms (escenario 1), 64.1 contra 46.2 (2) y 95.2 contra 52.6 (3) | Al vencer β, si la caché es fresca se responde de inmediato. Solo se reintenta cuando no hay dato fresco |
| Reintentos sin control | PoC 1 reintenta hasta 3 veces sin límite global | Backoff exponencial con jitter y presupuesto de reintentos (≤ 10% de las llamadas) |
| Al terminar el cooldown, el breaker deja pasar todas las llamadas | PoC 1 | Half-open con una sola sonda; el resto se cortocircuita mientras la sonda está en vuelo |
| β = β* × 1.5 era un margen puesto a ojo | PoC 1 | β se entrena exigiendo los timeouts también bajo una cola sana más pesada (σ 0.55 en vez de 0.35), sin factor manual |

Lo que no cambia: warm up de los 3 servicios problemáticos, hedged request a la réplica, breaker + fallback, retry máximo 3 y GG, y la caché solo para los servicios con warm up.

## Parámetros

Mismo método de entrenamiento que la PoC 1 (CVaR99 con búsqueda binaria, carga ≤ 5%, timeouts ≤ 0.5% por llamada) pero con β robusto: α = 17.0 ms, β* = 34.1 ms, β usado = 34.1 ms (β quedó en el piso β - α ≥ 1.5 veces la mediana). Como β salió menor que en la PoC 1 (44.6 ms), parte de la diferencia de p99 viene de ahí y no solo de la política de caché. Para separar los dos efectos se corre también la variante B con los mismos α y β.

## Cómo correrla

```bash
cd poc2_mejorada
python3 run.py train
python3 run.py experiment --scenario all     # o tails | tails_heavy | outage_svc9 | outage_long_svc9 | drift_svc3
python3 run.py report
```

`mode="B"` en `ImprovedAPI` es la variante que reintenta antes de usar la caché; se deja solo para comparar.

# Resultados del experimento - PoC 2

Baseline = fan-out a los 10 servicios esperando al más lento. B = misma PoC 2 pero reintentando antes de usar la caché (mismos α y β). Misma simulación y mismas latencias que en la PoC 1.

<!-- RESULTS:START -->
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
<!-- RESULTS:END -->

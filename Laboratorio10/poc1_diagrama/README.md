# PoC 1 - Arquitectura tal cual el diagrama

Implementa el diagrama `arquitectura-poc1.png` sin cambios, para medir si la arquitectura propuesta por el equipo reduce la tail latency.

![arquitectura](arquitectura-poc1.png)

## Qué hace

Por cada llamada a uno de los 10 servicios (el fan-out es paralelo):

1. Al arrancar se hace warm up de los 3 servicios más problemáticos (Service 8, 9 y 10, las APIs externas) y se precarga su caché.
2. Si el servicio no responde en α ms, se envía la misma llamada a una réplica (hedged request). Gana la primera respuesta y se cancela la otra.
3. Si no hay respuesta en β ms entra el circuit breaker con fallback. Si el servicio tiene caché se responde con ese dato. Si no tiene, se reintenta (máximo 3 intentos, vuelve al paso 2).
4. Pasados los 3 intentos se notifica (GG) y la llamada se da por fallida.

El breaker abre tras 5 fallos seguidos y se prueba de nuevo al segundo. La caché solo existe para los servicios con warm up, como dice el diagrama.

## Cómo se entrenaron α y β

Las consideraciones del diagrama piden entrenar α y β con búsqueda binaria, y la foto de la justificación da la función objetivo: CVaR_q(T) = min sobre τ de [ τ + E[(T-τ)+] / (1-q) ] (Rockafellar y Uryasev). Con q = 0.99 es el promedio del 1% peor de las latencias. El mínimo se alcanza en τ = VaR (el p99) y la derivada de esa función es monótona, por eso τ también se calcula por bisección. Se comprobó que el CVaR calculado así coincide con el promedio directo de la cola en todas las corridas.

Para fijar los parámetros se minimiza el CVaR99 con dos restricciones: carga extra de a lo más 5% y timeouts de a lo más 0.5% por llamada (con α y β acotados a 100 ms, la cota del diagrama). Como cada restricción es monótona en su parámetro, se usan dos búsquedas binarias anidadas: primero el menor α que cumple la carga, luego el menor β que cumple los timeouts, y a ese β se le multiplica por 1.5 como margen. El entrenamiento usa una semilla distinta a la de la evaluación.

Resultado: α = 22.2 ms, β* = 39.7 ms, β usado = 59.6 ms.

## Cómo correrla

```bash
cd poc1_diagrama
python3 run.py train
python3 run.py experiment --scenario all     # o tails | outage_svc9 | outage_long_svc9 | drift_svc3
python3 run.py report
```

Solo usa la librería estándar de Python para la simulación (matplotlib para el gráfico). El simulador y las métricas están en `../common/simcore.py`.

# Resultados del experimento - PoC 1

Baseline = fan-out a los 10 servicios esperando al más lento. Las dos variantes ven exactamente las mismas latencias simuladas (comparación pareada).

<!-- RESULTS:START -->
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
<!-- RESULTS:END -->

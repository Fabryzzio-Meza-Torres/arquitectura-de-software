# Lab 10 - A tale of tails (Performance / Scalability)

Arquitectura de Software 2026-II. Reducir la tail latency de un sistema que consulta 10 servicios en paralelo.

## Contenido

| Carpeta | Qué es |
|---|---|
| `poc1_diagrama/` | PoC 1: la arquitectura tal cual el diagrama del equipo. Tiene su propio README con sus resultados |
| `poc2_mejorada/` | PoC 2: el diagrama con mejoras a partir de los puntos débiles medidos. Tiene su propio README con sus resultados |
| `common/simcore.py` | Simulador de los 10 servicios, generador de carga, métricas (percentiles y CVaR) y entrenamiento de α y β |
| `comparar.py` | Junta los resultados de las dos PoC en `comparativo.md` y `comparativo.png` |

## Qué pedía el enunciado y cómo se resolvió

| Entregable | Cómo se resolvió |
|---|---|
| Diagrama de arquitectura (10 pts) | `poc1_diagrama/arquitectura-poc1.png` (el diagrama del equipo) y `poc2_mejorada/arquitectura-poc2.png` (con mejoras) |
| PoC (5 pts) | Simulación en Python con `asyncio`: 10 servicios con 2 réplicas, latencia normal de ~10 ms y, como describió el profe, la misma probabilidad (1%) en cada uno de los 10 servicios de que una llamada tarde ~1000 ms (rango 900 a 1100 ms); a lo más 3 servicios lentos en una request sale solo del azar. Carga open-loop de 250 rps con 4000 requests por corrida |
| Resultados del experimento (5 pts) | Tabla con p50, p95, p99, CVaR99 y requests ejecutadas, baseline contra cada PoC, en 5 escenarios. Están en el README de cada PoC y en la sección de abajo |
| Decisión (GO / GO WITH CHANGES / NO-GO) | Al final de este README |

Cómo se midió: las dos PoC y el baseline reciben las mismas latencias simuladas, y la latencia se mide desde el instante en que la request estaba agendada (así no se esconden las demoras). Se monitorea el lag del event loop de Python para saber si la medición se contamina; se repitieron las corridas que tuvieron picos de lag.

Escenarios:

1. Colas (modelo del profe): los 10 servicios con 1% de llamadas lentas de ~1000 ms. Con 10 servicios, el 9.6% de las requests toca al menos una llamada lenta, por eso sufren el p95 y el p99 y no el p50.
2. Estrés: servicios 8 a 10 con 10% de llamadas lentas de 0.5 a 1.5 s (el modelo que usamos antes, más duro que el del profe).
3. Caída de Service 9 durante el 30% central de la prueba (todas sus réplicas responden en 2 s).
4. Caída de Service 9 prolongada (65% de la prueba), para ver qué pasa cuando la caché envejece.
5. Service 3 degradado (2.5 veces más lento, no caído) durante el 40% central.

## Cómo correr todo

```bash
cd poc1_diagrama && python3 run.py train && python3 run.py experiment --scenario all && python3 run.py report
cd ../poc2_mejorada && python3 run.py train && python3 run.py experiment --scenario all && python3 run.py report
cd .. && python3 comparar.py
```

Cada escenario tarda 1 a 2 minutos por PoC; conviene correrlos de a uno (`--scenario tails`, `tails_heavy`, `outage_svc9`, `outage_long_svc9`, `drift_svc3`). Si el event loop tiene un pico de lag mayor a 20 ms, la corrida se repite sola (hasta 3 veces).

# Resultados del experimento - comparativo

Cada PoC con sus resultados detallados está en su propio README; esta tabla pone las dos lado a lado.

<!-- COMPARATIVO:START -->
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
<!-- COMPARATIVO:END -->

## Decisión: GO WITH CHANGES

- La arquitectura del diagrama funciona. En el modelo del profe (escenario 1) el p99 baja de 1082 ms a 39 ms y el p95 de 1003 ms a 34 ms, con el p50 sin cambios (19.7 a 19.9 ms) y 5.15% más llamadas a backend. En ese escenario el hedging hace casi todo el trabajo: el warm up y la caché casi no se usan (0.07% de requests degradadas). Se ven recién en el estrés (3.35%) y en las caídas.
- En el escenario 1 la PoC 2 y la PoC 1 son equivalentes (p99 39.4 contra 39.2 ms, CVaR99 46.0 contra 44.3 ms); la diferencia está dentro del ruido. La PoC 2 se justifica en los otros escenarios: con Service 9 caído su p99 es 52.6 ms contra 73.8 ms de la PoC 1 (CVaR99 64.3 contra 96.1), y con Service 3 degradado la carga extra baja de 8.46% a 4.74% (CVaR99 72.8 contra 77.4). Frente a reintentar primero (variante B) el p99 baja de 43.7 a 39.4 ms en el escenario 1 y de 64.1 a 46.2 ms en el estrés.
- El TTL máximo es una decisión de negocio. En la caída prolongada (escenario 4) la PoC 2 acota la antigüedad del dato servido a 5.0 s, pero para eso falla la llamada a Service 9 (GG) en el 34.08% de las requests; la PoC 1 sirve todas con datos de hasta 10.95 s. Esa latencia baja de la PoC 2 (p99 40.3 ms) incluye requests que terminaron en GG sin dato. Si el negocio prefiere disponibilidad sobre frescura, se sube el TTL.
- Es un cambio a vigilar: en el escenario 3 la PoC 2 también falla el 1.73% de las requests (la PoC 1, 0%), probablemente por datos que superan el TTL máximo de 5 s mientras Service 9 sigue caído (no se verificó la causa exacta por request).

## Limitaciones

- Es una simulación en un solo proceso: latencias sintéticas, réplicas independientes y sin efecto de la carga extra sobre los servicios. Antes de producción hay que validar con servicios reales y una prueba de carga.
- Una semilla por escenario. Las diferencias de unos pocos ms entre PoC 1 y PoC 2 (por ejemplo en el escenario 1) están dentro del ruido de la medición.
- Parte de la diferencia entre PoC 1 y PoC 2 viene de que β es menor en la PoC 2 (34.1 ms contra 44.6 ms). Un β tan cercano a α es sensible a la distribución real de latencias; la variante B (mismos α y β) sirve para separar ese efecto del de la política de caché.
- El modelo del profe se tomó de lo que contaron los compañeros (1% de llamadas lentas de ~1000 ms en cada servicio); conviene confirmarlo con el enunciado o con el profe.
- No se simula la idempotencia de las operaciones: el hedging y los reintentos solo son válidos para lecturas o escrituras idempotentes.

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
| PoC (5 pts) | Simulación en Python con `asyncio`: 10 servicios con 2 réplicas, latencia sana de ~10 ms y llamadas lentas de 0.5 a 1.5 s (1% en los servicios 1 a 7 y 10% en los servicios 8 a 10). Carga open-loop de 250 rps con 4000 requests por corrida |
| Resultados del experimento (5 pts) | Tabla con p50, p95, p99, CVaR99 y requests ejecutadas, baseline contra cada PoC, en 4 escenarios. Están en el README de cada PoC y en la sección de abajo |
| Decisión (GO / GO WITH CHANGES / NO-GO) | Al final de este README |

Cómo se midió: las dos PoC y el baseline reciben las mismas latencias simuladas, y la latencia se mide desde el instante en que la request estaba agendada (así no se esconden las demoras). Se monitorea el lag del event loop de Python para saber si la medición se contamina; se repitieron las corridas que tuvieron picos de lag.

Escenarios:

1. Colas independientes: el caso del enunciado.
2. Caída de Service 9 durante el 30% central de la prueba (todas sus réplicas responden en 2 s).
3. Caída de Service 9 prolongada (65% de la prueba), para ver qué pasa cuando la caché envejece.
4. Service 3 degradado (2.5 veces más lento, no caído) durante el 40% central.

## Cómo correr todo

```bash
cd poc1_diagrama && python3 run.py train && python3 run.py experiment --scenario all && python3 run.py report
cd ../poc2_mejorada && python3 run.py train && python3 run.py experiment --scenario all && python3 run.py report
cd .. && python3 comparar.py
```

Cada `experiment --scenario all` tarda entre 3 y 4 minutos; también se puede correr un escenario por vez.

# Resultados del experimento - comparativo

Cada PoC con sus resultados detallados está en su propio README; esta tabla pone las dos lado a lado.

<!-- COMPARATIVO:START -->
#### 1. Colas independientes

| Metrica | Baseline | PoC 1: diagrama | PoC 2: mejorada |
|---|---:|---:|---:|
| p50 (ms) | 21.9 | 22.5 | 22.2 |
| p95 (ms) | 1366.5 | 46.1 | 46.9 |
| p99 (ms) | 1480.2 | 63.5 | 57.4 |
| CVaR99 (ms) | 1489.9 | 71.4 | 59.2 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 42137 | 41902 |
| Carga extra | 0.0% | 5.34% | 4.75% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 128 (3.2%) | 131 (3.28%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 2135 / 2 / 130 | 1899 / 3 / 134 |
| Antiguedad max. del dato de cache (s) | - | 0.01 | 0.01 |
| Lag p99 del event loop (ms) | 3.17 | 3.46 | 1.65 |

#### 2. Service 9 caido (30% central)

| Metrica | Baseline | PoC 1: diagrama | PoC 2: mejorada |
|---|---:|---:|---:|
| p50 (ms) | 674.4 | 21.5 | 22.2 |
| p95 (ms) | 2003.2 | 51.9 | 46.4 |
| p99 (ms) | 2014.0 | 62.5 | 58.0 |
| CVaR99 (ms) | 2026.1 | 64.4 | 60.3 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 40700 | 40474 |
| Carga extra | 0.0% | 1.75% | 1.18% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 1485 (37.12%) | 1332 (33.3%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 94 (2.35%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 2024 / 2 / 195 | 1794 / 4 / 139 |
| Antiguedad max. del dato de cache (s) | - | 5.62 | 5.0 |
| Lag p99 del event loop (ms) | 5.46 | 1.52 | 1.75 |

#### 3. Service 9 caido, prolongado (65%)

| Metrica | Baseline | PoC 1: diagrama | PoC 2: mejorada |
|---|---:|---:|---:|
| p50 (ms) | 2001.5 | 21.6 | 21.9 |
| p95 (ms) | 2003.4 | 61.4 | 45.7 |
| p99 (ms) | 2035.3 | 62.9 | 57.4 |
| CVaR99 (ms) | 2052.3 | 64.3 | 59.7 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 39293 | 39045 |
| Carga extra | 0.0% | -1.77% | -2.39% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 2845 (71.12%) | 1295 (32.38%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 1397 (34.92%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 1940 / 2 / 261 | 1670 / 3 / 127 |
| Antiguedad max. del dato de cache (s) | - | 11.22 | 5.0 |
| Lag p99 del event loop (ms) | 2.04 | 1.79 | 2.06 |

#### 4. Service 3 degradado x2.5 (40% central)

| Metrica | Baseline | PoC 1: diagrama | PoC 2: mejorada |
|---|---:|---:|---:|
| p50 (ms) | 26.7 | 27.6 | 27.5 |
| p95 (ms) | 1367.2 | 50.3 | 51.6 |
| p99 (ms) | 1480.1 | 63.0 | 60.4 |
| CVaR99 (ms) | 1490.1 | 69.9 | 77.1 |
| Requests ejecutadas | 4000 | 4000 | 4000 |
| Llamadas a backend | 40000 | 43175 | 41955 |
| Carga extra | 0.0% | 7.94% | 4.89% |
| Requests degradadas (dato de cache) | 0 (0.0%) | 128 (3.2%) | 131 (3.28%) |
| Requests con llamada fallida (GG) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| Hedges / retries / timeouts | 0 / 0 / 0 | 3167 / 8 / 136 | 1949 / 6 / 137 |
| Antiguedad max. del dato de cache (s) | - | 0.01 | 0.01 |
| Lag p99 del event loop (ms) | 1.88 | 2.93 | 2.01 |

![comparativo](comparativo.png)
<!-- COMPARATIVO:END -->

## Decisión: GO WITH CHANGES

- La arquitectura del diagrama funciona: el p99 baja de unos 1480 ms a 63.5 ms y el p50 no cambia, con 5.34% más de llamadas a backend.
- Los cambios de la PoC 2 son los que se recomiendan hacer antes de implementar. Con servicio degradado la carga extra baja de 7.94% a 4.89%, y en una caída larga la antigüedad del dato servido queda acotada (5.0 s contra 11.22 s). Frente a reintentar primero (variante B), el p99 baja de 74.9 a 57.4 ms.
- El TTL máximo es una decisión de negocio. Con 5 s, en la caída prolongada la PoC 2 falla la llamada a Service 9 en el 34.92% de las requests en lugar de servir datos viejos; la PoC 1 las sirve todas (con datos de hasta 11.22 s). Si el negocio prefiere disponibilidad sobre frescura, se sube el TTL.
- En el escenario 4 el CVaR99 de la PoC 2 (77.1 ms) quedó peor que el de la PoC 1 (69.9 ms), aunque su p99 es menor. Es un punto a revisar.

## Limitaciones

- Es una simulación en un solo proceso: latencias sintéticas, réplicas independientes y sin efecto de la carga extra sobre los servicios. Antes de producción hay que validar con servicios reales y una prueba de carga.
- Una semilla por escenario. Las diferencias de unos pocos ms entre PoC 1 y PoC 2 están dentro del ruido de la medición.
- La mejora de p99 de la PoC 2 sobre la PoC 1 se debe en parte a un β menor (44.4 ms contra 59.6 ms). Un β tan cercano a α es sensible a la distribución real de latencias.
- No se simula la idempotencia de las operaciones: el hedging y los reintentos solo son válidos para lecturas o escrituras idempotentes.

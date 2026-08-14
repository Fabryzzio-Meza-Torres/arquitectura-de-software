# Evaluación de requisitos — Iteración 02

Fecha: 2026-08-13  
Fuentes: `Agents/Eval-Spec.md`, `README.md`, los requisitos de iteración 02 y las cuatro personas de `Personas/`.  
Comparación: `reportes/reporte-iteracion-01.md`.

## 1. Detalle por persona

### Mapeo de relevancia

- **Shakira:** Alta: RF-01, RF-06, RF-07, RF-11, RNF-03, RNF-04, RNF-08, RNF-09. Media: RF-02, RF-03, RF-04, RF-08, RNF-01, RNF-02, RNF-06, RNF-07. No aplica: RF-05, RF-09, RF-10, RNF-05, RNF-10.
- **Rensso:** Alta: RF-01, RF-02, RF-03, RF-06, RF-07, RF-11, RNF-01, RNF-02, RNF-03, RNF-04, RNF-08, RNF-09. Media: RF-04, RF-05, RF-08, RNF-06, RNF-07. No aplica: RF-09, RF-10, RNF-05, RNF-10.
- **Mariel:** Alta: RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-09, RF-10, RNF-01, RNF-02, RNF-03, RNF-04, RNF-05, RNF-08, RNF-09, RNF-10. Media: RF-08, RF-11, RNF-06, RNF-07. No aplica: ninguno.
- **Carlos:** Alta: RF-01, RF-03, RF-04, RF-06, RF-07, RF-11, RNF-03, RNF-04, RNF-08, RNF-09. Media: RF-02, RF-05, RF-08, RNF-01, RNF-02, RNF-06, RNF-07. No aplica: RF-09, RF-10, RNF-05, RNF-10.

Solo se puntúan los requisitos de relevancia Alta o Media. El criterio de Bloque B “sin cruces” integra el máximo únicamente de RF-04 y RF-05; los demás requisitos tienen máximo B de 6. La viabilidad por escala obtiene puntos solo cuando el propio requisito exige pruebas en 1K/100K/10M.

| Persona | Requerimiento (ID) | Relevancia | Score (A+B+C / máx) | Justificación |
| --- | --- | --- | --- | --- |
| Shakira Carol G Frisancho | RF-01 | Alta | 5+2+2 / 26 | RF-01 — A (5/9): identifica y confirma la información vigente, sin fallback de edición; B (2/6): campos/estados verificables, sin escala o rendimiento; C (2/11): confirma persistencia del diagnóstico. |
| Shakira Carol G Frisancho | RF-02 | Media | 1+2+2 / 26 | RF-02 — A (1/9): la trazabilidad reduce ambigüedad, pero no es su flujo principal; B (2/6): eventos obligatorios verificables; C (2/11): conserva de forma inmutable cambios clínicos. |
| Shakira Carol G Frisancho | RF-03 | Media | 1+2+3 / 26 | RF-03 — A (1/9): aporta continuidad, aunque la interna no controla el relevo; B (2/6): estados, campos y límite de turno verificables; C (3/11): garantiza información al entrante y alerta el faltante. |
| Shakira Carol G Frisancho | RF-04 | Media | 1+4+0 / 28 | RF-04 — A (1/9): ayuda a identificar cobertura, pero no es un flujo propio; B (4/8): validación verificable y cruces/duplicados bloqueados; C (0/11): no contacta ni distribuye diagnósticos. |
| Shakira Carol G Frisancho | RF-06 | Alta | 9+2+8 / 26 | RF-06 — A (9/9): alerta simple, destinatarios visibles y fallback si no hay responsable; B (2/6): máximo de tres acciones y contenido verificable; C (8/11): contacto nocturno, fallback, push multirrol y diagnóstico persistido. |
| Shakira Carol G Frisancho | RF-07 | Alta | 9+4+6 / 26 | RF-07 — A (9/9): flujo completo hasta acuse con fallback; B (4/6): umbrales verificables y de respuesta; C (6/11): contacto/escalamiento nocturno y distribución a varios niveles. |
| Shakira Carol G Frisancho | RF-08 | Media | 5+2+0 / 26 | RF-08 — A (5/9): cubre parcialmente acceso seguro y elevación excepcional; B (2/6): reglas y auditoría comprobables; C (0/11): no resuelve por sí mismo los problemas críticos. |
| Shakira Carol G Frisancho | RF-11 | Alta | 9+2+4 / 26 | RF-11 — A (9/9): flujo visible offline, conflicto y canal alternativo; B (2/6): estados y comportamiento verificables; C (4/11): fallback de contacto y persistencia durante desconexión. |
| Shakira Carol G Frisancho | RNF-01 | Media | 1+6+0 / 26 | RNF-01 — A (1/9): disponibilidad útil sin flujo de usuario; B (6/6): escala, 99.9 % y meta de disponibilidad explícitas; C (0/11): disponibilidad no define relevo, routing o persistencia. |
| Shakira Carol G Frisancho | RNF-02 | Media | 1+4+2 / 26 | RNF-02 — A (1/9): reduce interrupción, pero no guía al usuario durante ella; B (4/6): RTO/RPO medibles y de rendimiento; C (2/11): garantiza cero pérdida de diagnósticos confirmados. |
| Shakira Carol G Frisancho | RNF-03 | Alta | 5+6+0 / 26 | RNF-03 — A (5/9): satisface acceso inmediato, sin caso borde; B (6/6): escala y tres umbrales de latencia verificables; C (0/11): no garantiza entrega, contacto o persistencia. |
| Shakira Carol G Frisancho | RNF-04 | Alta | 9+4+8 / 26 | RNF-04 — A (9/9): entrega rápida con reintento para desconectados; B (4/6): máximos de 2 y 5 segundos; C (8/11): contacto rápido, fallback, push múltiple y persistencia previa. |
| Shakira Carol G Frisancho | RNF-06 | Media | 5+2+0 / 26 | RNF-06 — A (5/9): acceso por rol con denegación/fallback temporal; B (2/6): cobertura del 100 % verificable; C (0/11): no atiende los tres problemas críticos. |
| Shakira Carol G Frisancho | RNF-07 | Media | 1+2+0 / 26 | RNF-07 — A (1/9): protege sus datos, sin resolver claridad o contacto; B (2/6): protocolos/algoritmos verificables; C (0/11): cifrado no equivale a persistencia disponible. |
| Shakira Carol G Frisancho | RNF-08 | Alta | 9+2+0 / 26 | RNF-08 — A (9/9): tareas cortas, aprendizaje medido y alternativa al color; B (2/6): acciones, tiempo y éxito cuantificados; C (0/11): no define routing, relevo o persistencia. |
| Shakira Carol G Frisancho | RNF-09 | Alta | 9+2+2 / 26 | RNF-09 — A (9/9): estados, sincronización y manejo de conflicto forman un flujo completo; B (2/6): porcentajes verificables; C (2/11): garantiza durabilidad del diagnóstico ante fallos parciales. |
| Rensso Victor Hugo Mora Choque | RF-01 | Alta | 5+2+2 / 26 | RF-01 — A (5/9): cubre registro y diagnóstico vigente, sin un fallback propio; B (2/6): reglas verificables; C (2/11): confirma persistencia del diagnóstico. |
| Rensso Victor Hugo Mora Choque | RF-02 | Alta | 5+2+2 / 26 | RF-02 — A (5/9): historial completo e inmutable, sin flujo alternativo; B (2/6): eventos definidos; C (2/11): conserva cambios clínicos. |
| Rensso Victor Hugo Mora Choque | RF-03 | Alta | 9+2+3 / 26 | RF-03 — A (9/9): relevo completo, acuse y manejo del incompleto; B (2/6): contenido/estados verificables; C (3/11): diagnóstico disponible antes/durante el cambio. |
| Rensso Victor Hugo Mora Choque | RF-04 | Media | 1+4+0 / 28 | RF-04 — A (1/9): mejora su asignación, pero no su flujo clínico; B (4/8): validación concreta y sin cruces; C (0/11): no contacta al responsable. |
| Rensso Victor Hugo Mora Choque | RF-05 | Media | 5+4+0 / 28 | RF-05 — A (5/9): cubre parcialmente cambios con fallback si falta reemplazo; B (4/8): revalida y evita cruces; C (0/11): no gestiona emergencias clínicas. |
| Rensso Victor Hugo Mora Choque | RF-06 | Alta | 9+2+8 / 26 | RF-06 — A (9/9): push con contexto y fallback; B (2/6): tres acciones y destinatarios comprobables; C (8/11): resuelve contacto, fallback, push múltiple y persistencia del contexto. |
| Rensso Victor Hugo Mora Choque | RF-07 | Alta | 9+4+6 / 26 | RF-07 — A (9/9): escalamiento completo hasta acuse; B (4/6): 30/60/120 y respuesta verificables; C (6/11): contacto/escalamiento y notificación multinivel. |
| Rensso Victor Hugo Mora Choque | RF-08 | Media | 5+2+0 / 26 | RF-08 — A (5/9): acceso médico y elevación temporal cubren parcialmente su necesidad; B (2/6): reglas verificables; C (0/11): sin cobertura crítica directa. |
| Rensso Victor Hugo Mora Choque | RF-11 | Alta | 9+2+4 / 26 | RF-11 — A (9/9): permite registrar/reportar offline con conflictos y fallback; B (2/6): estados verificables; C (4/11): continuidad persistente y canal alternativo. |
| Rensso Victor Hugo Mora Choque | RNF-01 | Alta | 1+6+0 / 26 | RNF-01 — A (1/9): apoya la guardia sin definir un flujo personal; B (6/6): 99.9 % en las tres escalas; C (0/11): no responde las preguntas críticas por sí solo. |
| Rensso Victor Hugo Mora Choque | RNF-02 | Alta | 1+4+2 / 26 | RNF-02 — A (1/9): protege continuidad, sin interacción/fallback del médico; B (4/6): RTO y RPO medibles; C (2/11): cero pérdida confirmada. |
| Rensso Victor Hugo Mora Choque | RNF-03 | Alta | 5+6+0 / 26 | RNF-03 — A (5/9): acceso al diagnóstico/relevo menor a 1 segundo; B (6/6): umbrales en todas las escalas; C (0/11): rapidez de lectura no garantiza relevo. |
| Rensso Victor Hugo Mora Choque | RNF-04 | Alta | 9+4+8 / 26 | RNF-04 — A (9/9): push rápido y fallback de conectividad; B (4/6): máximos medibles; C (8/11): contacto, fallback, multidestino y persistencia. |
| Rensso Victor Hugo Mora Choque | RNF-06 | Media | 5+2+0 / 26 | RNF-06 — A (5/9): permisos con alternativa autorizada; B (2/6): 100 % de operaciones probado; C (0/11): no resuelve continuidad clínica. |
| Rensso Victor Hugo Mora Choque | RNF-07 | Media | 1+2+0 / 26 | RNF-07 — A (1/9): confidencialidad útil, sin satisfacer sus flujos principales; B (2/6): TLS/AES verificables; C (0/11): no asegura disponibilidad persistente. |
| Rensso Victor Hugo Mora Choque | RNF-08 | Alta | 9+2+0 / 26 | RNF-08 — A (9/9): tareas rápidas, aprendizaje y accesibilidad medidos; B (2/6): métricas concretas; C (0/11): no define los tres flujos críticos. |
| Rensso Victor Hugo Mora Choque | RNF-09 | Alta | 9+2+2 / 26 | RNF-09 — A (9/9): sincronización y conflicto con estados claros; B (2/6): cero pérdida/100 % verificables; C (2/11): persistencia ante fallos. |
| Mariel Carolina Tovar Tolentino | RF-01 | Alta | 5+2+2 / 26 | RF-01 — A (5/9): ofrece dato vigente para supervisión, sin fallback propio; B (2/6): versión/campos verificables; C (2/11): persistencia confirmada. |
| Mariel Carolina Tovar Tolentino | RF-02 | Alta | 5+2+2 / 26 | RF-02 — A (5/9): cubre auditoría clínica y de alertas, sin caso borde de consulta; B (2/6): eventos obligatorios; C (2/11): historial inmutable. |
| Mariel Carolina Tovar Tolentino | RF-03 | Alta | 9+2+3 / 26 | RF-03 — A (9/9): estados, acuse y alerta de relevo incompleto; B (2/6): flujo verificable; C (3/11): garantiza diagnóstico al turno entrante. |
| Mariel Carolina Tovar Tolentino | RF-04 | Alta | 9+4+0 / 28 | RF-04 — A (9/9): administra, bloquea cruces y maneja falta de cobertura; B (4/8): verificable y respeta “sin cruces”; C (0/11): no notifica emergencias clínicas. |
| Mariel Carolina Tovar Tolentino | RF-05 | Alta | 9+4+0 / 28 | RF-05 — A (9/9): flujo completo de cambio y fallback sin reemplazo; B (4/8): validación verificable y sin cruces; C (0/11): no trata alertas clínicas. |
| Mariel Carolina Tovar Tolentino | RF-06 | Alta | 9+2+8 / 26 | RF-06 — A (9/9): routing, estados y fallback visibles; B (2/6): acciones/contenido verificables; C (8/11): contacto, fallback, push multirrol y persistencia. |
| Mariel Carolina Tovar Tolentino | RF-07 | Alta | 9+4+6 / 26 | RF-07 — A (9/9): escala hasta jefatura y cierre documentado; B (4/6): tiempos y rendimiento concretos; C (6/11): medianoche completa y notificación multinivel. |
| Mariel Carolina Tovar Tolentino | RF-08 | Media | 5+2+0 / 26 | RF-08 — A (5/9): acceso supervisor y elevaciones auditadas; B (2/6): reglas comprobables; C (0/11): sin solución crítica autónoma. |
| Mariel Carolina Tovar Tolentino | RF-09 | Alta | 5+2+0 / 26 | RF-09 — A (5/9): satisface dashboard y drill-down, sin fallback del tablero; B (2/6): filtros/estados verificables; C (0/11): visualiza pero no garantiza los flujos críticos. |
| Mariel Carolina Tovar Tolentino | RF-10 | Alta | 5+2+0 / 26 | RF-10 — A (5/9): satisface reportes y auditoría, sin caso borde; B (2/6): campos/exportación verificables; C (0/11): reportar después no resuelve directamente los incidentes. |
| Mariel Carolina Tovar Tolentino | RF-11 | Media | 5+2+4 / 26 | RF-11 — A (5/9): apoya continuidad con flujo/fallback, pero no es su tarea principal; B (2/6): estados verificables; C (4/11): canal alternativo y persistencia offline. |
| Mariel Carolina Tovar Tolentino | RNF-01 | Alta | 5+6+0 / 26 | RNF-01 — A (5/9): cumple disponibilidad de supervisión, sin fallback visible; B (6/6): 99.9 % y escalas; C (0/11): no garantiza por sí solo los flujos críticos. |
| Mariel Carolina Tovar Tolentino | RNF-02 | Alta | 5+4+2 / 26 | RNF-02 — A (5/9): continuidad y cero pérdida satisfacen supervisión, sin flujo alterno; B (4/6): RTO/RPO verificables; C (2/11): persistencia confirmada. |
| Mariel Carolina Tovar Tolentino | RNF-03 | Alta | 5+6+0 / 26 | RNF-03 — A (5/9): dashboard y datos en menos de 1 segundo; B (6/6): escala/latencia verificables; C (0/11): no ejecuta relevo o alerta. |
| Mariel Carolina Tovar Tolentino | RNF-04 | Alta | 9+4+8 / 26 | RNF-04 — A (9/9): entrega y fallback medidos; B (4/6): 2/5 segundos verificables; C (8/11): cubre contacto, fallback, push y persistencia. |
| Mariel Carolina Tovar Tolentino | RNF-05 | Alta | 5+6+0 / 26 | RNF-05 — A (5/9): cubre expansión de Essalud, sin flujo de usuario; B (6/6): fases y conservación de SLA verificables; C (0/11): escala no resuelve incidentes por sí sola. |
| Mariel Carolina Tovar Tolentino | RNF-06 | Media | 5+2+0 / 26 | RNF-06 — A (5/9): acceso supervisor con fallback temporal; B (2/6): 100 % de rutas verificable; C (0/11): sin cobertura crítica directa. |
| Mariel Carolina Tovar Tolentino | RNF-07 | Media | 1+2+0 / 26 | RNF-07 — A (1/9): seguridad necesaria pero no satisface dashboard/reportes; B (2/6): controles concretos; C (0/11): no garantiza persistencia disponible. |
| Mariel Carolina Tovar Tolentino | RNF-08 | Alta | 9+2+0 / 26 | RNF-08 — A (9/9): UX rápida, accesible y probada por rol; B (2/6): métricas concretas; C (0/11): no responde directamente a los problemas críticos. |
| Mariel Carolina Tovar Tolentino | RNF-09 | Alta | 5+2+2 / 26 | RNF-09 — A (5/9): aporta continuidad y flujo de error, aunque indirecto para jefatura; B (2/6): cero pérdida/100 % medibles; C (2/11): durabilidad ante fallos. |
| Mariel Carolina Tovar Tolentino | RNF-10 | Alta | 5+6+0 / 26 | RNF-10 — A (5/9): auditoría completa y rápida, sin fallback; B (6/6): cobertura, escala y latencia verificables; C (0/11): auditar no ejecuta relevo, contacto o push. |
| Carlos Balbuena Palacios | RF-01 | Alta | 5+2+2 / 26 | RF-01 — A (5/9): indicaciones/diagnóstico vigentes y confirmados, sin fallback de consulta; B (2/6): reglas verificables; C (2/11): persistencia confirmada. |
| Carlos Balbuena Palacios | RF-02 | Media | 1+2+2 / 26 | RF-02 — A (1/9): historial ayuda a interpretar cambios, pero no es su tarea principal; B (2/6): eventos definidos; C (2/11): conserva cambios clínicos. |
| Carlos Balbuena Palacios | RF-03 | Alta | 9+2+3 / 26 | RF-03 — A (9/9): entrega, acuse y fallback por incompletitud; B (2/6): estados/campos comprobables; C (3/11): continuidad garantizada al cambio. |
| Carlos Balbuena Palacios | RF-04 | Alta | 9+4+0 / 28 | RF-04 — A (9/9): horario claro, bloqueo y contingencia de cobertura; B (4/8): validación verificable y sin cruces; C (0/11): no contacta en emergencias. |
| Carlos Balbuena Palacios | RF-05 | Media | 9+4+0 / 28 | RF-05 — A (9/9): cambios notificados y fallback sin reemplazo; B (4/8): revalidación completa y sin cruces; C (0/11): no atiende alertas clínicas. |
| Carlos Balbuena Palacios | RF-06 | Alta | 9+2+8 / 26 | RF-06 — A (9/9): alerta simple, routing automático y fallback; B (2/6): máximo de acciones/contenido verificable; C (8/11): contacto, fallback, push multirrol y persistencia. |
| Carlos Balbuena Palacios | RF-07 | Alta | 9+4+6 / 26 | RF-07 — A (9/9): escalamiento claro hasta acuse; B (4/6): 30/60/120 verificables; C (6/11): medianoche y distribución multinivel. |
| Carlos Balbuena Palacios | RF-08 | Media | 5+2+0 / 26 | RF-08 — A (5/9): acceso de enfermería con alternativa autorizada; B (2/6): reglas comprobables; C (0/11): no resuelve problemas críticos. |
| Carlos Balbuena Palacios | RF-11 | Alta | 9+2+4 / 26 | RF-11 — A (9/9): reporte offline, estados, conflictos y canal alternativo; B (2/6): comportamiento verificable; C (4/11): fallback y persistencia offline. |
| Carlos Balbuena Palacios | RNF-01 | Media | 1+6+0 / 26 | RNF-01 — A (1/9): disponibilidad apoya su trabajo sin flujo propio; B (6/6): 99.9 % y escalas; C (0/11): sin respuesta crítica autónoma. |
| Carlos Balbuena Palacios | RNF-02 | Media | 1+4+2 / 26 | RNF-02 — A (1/9): continuidad útil, sin guiar durante la caída; B (4/6): RTO/RPO verificables; C (2/11): cero pérdida confirmada. |
| Carlos Balbuena Palacios | RNF-03 | Alta | 5+6+0 / 26 | RNF-03 — A (5/9): consulta inmediata de diagnóstico/indicaciones; B (6/6): latencia en tres escalas; C (0/11): no garantiza relevo o alerta. |
| Carlos Balbuena Palacios | RNF-04 | Alta | 9+4+8 / 26 | RNF-04 — A (9/9): push rápido y fallback desconectado; B (4/6): máximos medibles; C (8/11): contacto, fallback, push múltiple y persistencia. |
| Carlos Balbuena Palacios | RNF-06 | Media | 5+2+0 / 26 | RNF-06 — A (5/9): permisos y elevación temporal; B (2/6): cobertura del 100 %; C (0/11): sin solución crítica directa. |
| Carlos Balbuena Palacios | RNF-07 | Media | 1+2+0 / 26 | RNF-07 — A (1/9): confidencialidad útil, pero no satisface flujos operativos; B (2/6): controles verificables; C (0/11): no garantiza disponibilidad persistente. |
| Carlos Balbuena Palacios | RNF-08 | Alta | 9+2+0 / 26 | RNF-08 — A (9/9): acciones mínimas, aprendizaje y accesibilidad medidos; B (2/6): criterios cuantificados; C (0/11): no define routing/relevo/persistencia. |
| Carlos Balbuena Palacios | RNF-09 | Alta | 9+2+2 / 26 | RNF-09 — A (9/9): sincronización y conflicto con flujo visible; B (2/6): cero pérdida y 100 % verificables; C (2/11): persistencia durante fallos. |

## 2. Resumen de iteración

| Persona | Cálculo | Score |
| --- | --- | --- |
| Shakira Carol G Frisancho | (165 / 418) × 10 | 3.95/10 |
| Rensso Victor Hugo Mora Choque | (186 / 446) × 10 | 4.17/10 |
| Mariel Carolina Tovar Tolentino | (234 / 550) × 10 | 4.25/10 |
| Carlos Balbuena Palacios | (194 / 446) × 10 | 4.35/10 |
| **PROMEDIO** | **(3.95 + 4.17 + 4.25 + 4.35) / 4** | **4.18/10 - FAILED** |

### Comparación con la iteración 01

| Persona | Iteración 01 | Iteración 02 | Variación |
| --- | ---: | ---: | ---: |
| Shakira Carol G Frisancho | 1.09 | 3.95 | +2.86 |
| Rensso Victor Hugo Mora Choque | 0.94 | 4.17 | +3.23 |
| Mariel Carolina Tovar Tolentino | 1.10 | 4.25 | +3.15 |
| Carlos Balbuena Palacios | 1.04 | 4.35 | +3.31 |
| **PROMEDIO** | **1.04** | **4.18** | **+3.14** |

- **Mejoraron:** RF-01–RF-08 y RNF-01–RNF-08 incorporan criterios verificables. El mayor avance está en RF-03, RF-06, RF-07 y RNF-04, que ahora responden explícitamente rotación, medianoche y tiempo real.
- **Nuevos:** RF-09 (dashboard), RF-10 (reportes), RF-11 (offline/conflictos), RNF-09 (durabilidad/sincronización) y RNF-10 (auditoría íntegra).
- **Siguen penalizados:** requisitos de seguridad, UX, reporting y escala obtienen C=0 cuando no responden por sí solos uno de los tres problemas críticos. La rúbrica mantiene esos 11 puntos dentro del máximo incluso cuando el requisito es útil, por lo que el conjunto mejora sustancialmente pero no alcanza 7/10.

## 3. Gaps críticos

- RF-03 — Rensso, Mariel, Carlos y Shakira — Rotación de doctor — Si el saliente está incapacitado o abandona el turno, el fallback solo alerta y visibiliza el faltante; no designa quién puede completar o validar el relevo en su lugar.
- RF-11 — Rensso, Carlos y Shakira — Medianoche — El “canal alternativo institucional” no está identificado ni tiene tiempo máximo de activación/entrega, por lo que ese último fallback aún es ambiguo.
- RNF-04 / RNF-05 — Todas las personas — Tiempo real/viabilidad — Se exigen 2 segundos y las tres escalas, pero falta definir la carga nominal por hospital (camas, usuarios concurrentes, alertas y actualizaciones por segundo) para reproducir la prueba.
- RF-02 / RNF-10 — Mariel — Auditoría — No se fija un período mínimo de retención; RF-10 admite rangos de fechas, pero no garantiza cuántos años de historia estarán disponibles.
- RNF-08 — Todas las personas — Satisfacción/UX — No define tamaño/muestreo de usuarios representativos ni una clasificación objetiva de “error clínico crítico”, lo que limita la reproducibilidad del 90 %.
- RNF-07 — Todas las personas — Viabilidad/seguridad — “Equivalente aprobado” no identifica quién aprueba ni qué estándar decide equivalencia, dejando una parte del criterio de cifrado abierta.

No se detectaron contradicciones entre RF y RNF. RF-04 bloquea cruces/duplicados sin excepción; la contingencia autorizada se limita a turnos todavía sin cobertura.

## 4. Recomendación

El conjunto cubre funcionalmente los tres problemas críticos, pero necesita otra iteración porque obtiene 4.18/10. Priorizar el relevo sin saliente, el canal alternativo, el perfil de carga 1K/100K/10M, la retención de auditoría y las métricas de UX; mantener la rúbrica y el umbral sin forzar aprobación.

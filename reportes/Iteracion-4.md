# Reporte de Evaluación de Requerimientos — Iteración 4

> Auditoría ejecutada con **Eval-Spec v2** sobre `FunctionalRequirements.md` (RF-01…RF-11)
> y `NonunctionalRequirements.md` (RNF-01…RNF-08, con RNF-04 separado en RNF-04a/04b).
> Todos los requerimientos son autocontenidos: los valores están inlineados y las
> referencias cruzadas son exclusivamente entre requerimientos del mismo conjunto (RF↔RNF),
> sin citar documentos externos.

---

## 1. Matriz de cobertura de necesidades (Paso 0)

| Persona | Necesidad | Requerimiento(s) | Cobertura |
|---|---|---|---|
| Mariel Tovar | Dashboard en tiempo real del estado de cambio entre turnos | RF-02 (estado completo/incompleto/pendiente) | Total |
| Mariel Tovar | Horarios que bloqueen/alerten cruces automáticamente | RF-05 | Total |
| Mariel Tovar | Auditoría completa de emergencias nocturnas | RF-10 (personal, tiempos, resolución) | Total |
| Mariel Tovar | Reportes de disponibilidad de personal por turno y especialidad | RF-06 | Total |
| Mariel Tovar | Alertas escalables notificando directamente a la jefatura | RF-09 (nivel 2 notifica a Jefe de Área) | Total |
| Rensso Mora | Visualización inmediata del diagnóstico vigente al iniciar turno | RF-02 | Total |
| Rensso Mora | Notificaciones push confiables sin importar ubicación | RF-08, RNF-04a, RNF-04b | Total |
| Rensso Mora | Flujo alternativo de contacto si no responde a tiempo | RF-09 (3 niveles de escalamiento) | Total |
| Rensso Mora | Registro ágil de diagnóstico sin carga operativa | RF-01 (auto-guardado 30s) | Total |
| Carlos Balbuena | Acceso rápido y claro a indicaciones y diagnóstico | RF-02 + RF-03 | Total |
| Carlos Balbuena | Mecanismo simple para reportar deterioro | RF-08 (reporte manual), RNF-08 | Total |
| Carlos Balbuena | Identificación automática del personal a contactar | RF-08, RF-09 | Total |
| Carlos Balbuena | Horario claro sin cruces, con alertas | RF-05 | Total |
| Shakira Frisancho | Información clara y fácil de entender | RF-02, RF-03 | Total |
| Shakira Frisancho | Indicación explícita de a quién contactar | RNF-08 (muestra nombre/rol), RF-09 | Total |
| Shakira Frisancho | Interfaz simple, procesos mínimos | RNF-08 (3 pasos, <10s) | Total |
| Shakira Frisancho | Indicaciones médicas vigentes sin ambigüedad | RF-03 (vencimiento visual a 24h) | Total |

**Necesidades "Sin cobertura": 0**

---

## 2. Detalle por persona (Bloques A+B+C)

### Mariel Tovar (Jefa de Área)

| Req | Rel. | Score | Justificación | Camino a 10/10 |
|---|---|---|---|---|
| RF-02 | Alta | 14/15 | A=5/5 (A.1=3 dashboard con estado de turno completo/incompleto/pendiente; A.2=2 caso borde "Sin diagnóstico registrado" + refresco push). B=4/4 (<1s cuantificado, medible, contribuye a meta de latencia). C=5/6 (rot=2/2 diagnóstico y estado de turno visibles al entrante; RT(a)=1/2 refresco push sin definir canal de difusión grupal; RT(b)=2/2 persistencia explícita). | Especificar que el refresco push usa el mismo canal de difusión grupal de RF-08 para subir RT(a) a 2. |
| RF-04 | Alta | 11/12 | A=5/5 (checklist + bloqueo + escalamiento a jefatura). B=4/5 (15min y <30s cuantificados, medible, sin cruces de diagnóstico; no ligado directamente a las 4 metas de rendimiento del caso). C=2/2 (rot=2/2 garantiza diagnóstico completo antes de cambio). | Ligar el <30s a alguna meta de rendimiento del caso de estudio. |
| RF-05 | Alta | 11/12 | A=5/5 (bloqueo de cruces <2s + notificación 2h anticipación). B=4/5 (<2s, 2h, 10M hospitales cuantificados; medible; sin cruces; falta contribución a meta de rendimiento). C=2/2 (rot=2/2 garantiza cobertura continua de turnos). | Mismo que RF-04: ligar a una meta de rendimiento. |
| RF-06 | Alta | 9/10 | A=5/5 (reporte filtrable + mínimo configurable + caso borde "sin configurar"). B=3/3 (<3s cuantificado, medible; perf y cruces N/A). C=1/2 (rot=1/2 indirecto: informa disponibilidad pero no garantiza diagnóstico activamente). | Agregar alerta proactiva cuando un turno futuro quede por debajo del mínimo para hacer la prevención de vacío directa. |
| RF-09 | Alta | 13/13 | A=5/5 (3 niveles + notifica a Jefe de Área explícitamente). B=4/4 (15s/2min cuantificados, medible, contribuye a tiempo de respuesta). C=4/4 (med(a)=2/2 contacto en ≤15s; med(b)=2/2 tres niveles de fallback). | — |
| RF-10 | Alta | 11/13 | A=5/5 (auditoría inmutable con tiempos de respuesta por nivel, resolución final). B=4/4 (ligado a RNF-02 <5min, medible, contribuye a RTO). C=2/4 (med(a)=1/2 registra quién fue contactado sin ejecutar el contacto; med(b)=1/2 registra si hubo escalamiento sin definirlo). | Agregar que RF-10 dispare alerta automática al Jefe de Área si el tiempo de respuesta supera un umbral configurable. |

**Score Mariel = 69/75 → 9.20/10**

### Rensso Mora (Médico Intensivista)

| Req | Rel. | Score | Justificación | Camino a 10/10 |
|---|---|---|---|---|
| RF-01 | Alta | 11/11 | A=5/5 (auto-guardado 30s reduce carga operativa; reintento ante fallo). B=4/4 (30s/3 reintentos/10s cuantificados, medible, contribuye a disponibilidad de datos). C=2/2 (rot=2/2 auto-guardado garantiza dato persistido antes de fin de turno). | — |
| RF-02 | Alta | 14/15 | A=5/5 (visualización inmediata del diagnóstico vigente al iniciar turno). B=4/4. C=5/6 (rot=2/2; RT(a)=1/2; RT(b)=2/2). | Mismo que Mariel. |
| RF-04 | Alta | 11/12 | A=5/5 (asegura que su diagnóstico quede completo para el entrante). B=4/5. C=2/2 (rot=2/2). | Mismo que Mariel. |
| RF-08 | Alta | 14/17 | A=5/5 (push confiable + fallback a estación de enfermería). B=4/4 (2s vía RNF-04a, medible, perf). C=5/8 (RT(a)=2/2 push simultáneo a todo el equipo; RT(b)=2/2 persistencia local; med(a)=1/2 notifica al equipo pero no al individuo; med(b)=0/2 delega fallback a RF-09). | Limitación estructural aceptable: incluir el flujo de contacto individual duplicaría RF-09 y rompería atomicidad. |
| RF-09 | Alta | 13/13 | A=5/5 (contacto + fallback completo de 3 niveles). B=4/4. C=4/4 (med(a)=2/2; med(b)=2/2). | — |

**Score Rensso = 63/68 → 9.26/10**

### Carlos Balbuena (Enfermero)

| Req | Rel. | Score | Justificación | Camino a 10/10 |
|---|---|---|---|---|
| RF-02 | Media | 13/15 | A=4/5 (A.1=2 cubre diagnóstico pero "indicaciones" las cubre RF-03 por separado; A.2=2). B=4/4. C=5/6 (rot=2/2; RT(a)=1/2; RT(b)=2/2). | Incluir un resumen de indicaciones vigentes en el dashboard para que A.1 suba a 3, o aceptar la separación RF-02/RF-03 como diseño intencionado. |
| RF-03 | Alta | 10/10 | A=5/5 (indicaciones separadas del diagnóstico, 24h vencimiento visual, médico emisor). B=3/3 (24h cuantificado, medible; perf y cruces N/A). C=2/2 (rot=2/2 asegura continuidad de indicaciones entre turnos). | — |
| RF-05 | Alta | 11/12 | A=5/5. B=4/5. C=2/2 (rot=2/2). | Ligar a meta de rendimiento. |
| RF-08 | Alta | 14/17 | A=5/5 (reporte manual de enfermería explícito + push + fallback si no hay canal). B=4/4. C=5/8 (RT=4/4; med(a)=1/2; med(b)=0/2). | Mismo trade-off que Rensso. |
| RNF-08 | Alta | 12/12 | A=5/5 (3 pasos <10s = mecanismo simple; muestra nombre/rol del destinatario = identificación automática). B=3/3 (cuantificado, medible). C=4/4 (med(a)=2/2 inicia contacto mostrando destinatario; med(b)=2/2 enlaza al escalamiento de RF-09). | — |

**Score Carlos = 60/66 → 9.09/10**

### Shakira Frisancho (Interna)

| Req | Rel. | Score | Justificación | Camino a 10/10 |
|---|---|---|---|---|
| RF-02 | Media | 13/15 | A=4/5 (A.1=2 presentación con estados explícitos, pero no garantiza UX adaptada al nivel técnico bajo de una interna; A.2=2). B=4/4. C=5/6 (rot=2/2; RT(a)=1/2; RT(b)=2/2). | Agregar criterio de UX explícito (secciones etiquetadas, codificación por colores) para subir A.1 a 3. |
| RF-03 | Alta | 10/10 | A=5/5 (indicaciones vigentes sin ambigüedad, vencimiento visual a 24h, médico emisor). B=3/3. C=2/2 (rot=2/2). | — |
| RNF-08 | Alta | 12/12 | A=5/5 (3 pasos = "procesos mínimos"; muestra nombre/rol = "a quién contactar"). B=3/3. C=4/4 (med=4/4). | — |
| RF-09 | Media | 12/13 | A=4/5 (A.1=2 cubre alertas críticas pero Shakira necesita claridad de contacto "en cada situación", no solo críticas; A.2=2 fallback de 3 niveles). B=4/4. C=4/4 (med=4/4). | Agregar que fuera de alertas críticas, la interfaz muestre permanentemente el contacto de guardia actual. |

**Score Shakira = 47/50 → 9.40/10**

---

## 3. Calidad de ingeniería (Bloque D), por requerimiento

| Req | Score | Sub-criterios que fallan | Camino a 10/10 |
|---|---|---|---|
| RF-01 | 9/9 | — | — |
| RF-02 | 9/9 | — | — |
| RF-03 | 9/9 | — | — |
| RF-04 | 9/9 | — | — |
| RF-05 | 9/9 | — | — |
| RF-06 | 9/9 | — | — |
| RF-07 | 9/9 | — | — |
| RF-08 | 9/9 | — | — |
| RF-09 | 9/9 | — | — |
| RF-10 | 9/9 | — | — |
| RF-11 | 9/9 | — | — |
| RNF-01 | 9/9 | — | — |
| RNF-02 | 9/9 | — | — |
| RNF-03 | 9/9 | — | — |
| RNF-04a | 9/9 | — | — |
| RNF-04b | 9/9 | — | — |
| RNF-05 | 9/9 | — | — |
| RNF-06 | 9/9 | — | — |
| RNF-07 | 9/9 | — | — |
| RNF-08 | 9/9 | — | — |

**Suma: 180/180 → Bloque D = 10.00/10**

Cada requerimiento satisface los 9 sub-criterios: atómico (una capacidad por ID), no ambiguo
(umbrales cuantificados), verificable (criterios pass/fail), con caso borde explícito, sin
redundancia (cross-references RF↔RNF en vez de duplicación), sin contradicción, y trazable.

---

## 4. Resumen de iteración

| Persona | Score |
|---|---|
| Mariel Tovar | 9.20/10 (69/75) |
| Rensso Mora | 9.26/10 (63/68) |
| Carlos Balbuena | 9.09/10 (60/66) |
| Shakira Frisancho | 9.40/10 (47/50) |
| **PROMEDIO (A+B+C)** | **9.24/10** |
| **CALIDAD DE INGENIERÍA (D)** | **10.00/10** |
| **VEREDICTO** | **PASSED** |

Las tres condiciones se cumplen: promedio ≥ 7 (9.24), Bloque D ≥ 7 (10.0), cero necesidades sin cobertura.

---

## 5. Comparación con iteraciones anteriores

| Dimensión | Iter. 3 (original) | Pre-eval (Spec v1) | **Iter. 4 (Spec v2)** |
|---|---|---|---|
| Necesidades sin cobertura | 0 (no evaluado) | 2 | **0** |
| Bloque D | No evaluado | 5.28/10 | **10.00/10** |
| Redundancias | No detectadas | 3 pares | **0** |
| Promedio A+B+C | 7.0/10 (sin desglose) | 4.67/10 | **9.24/10** |
| Veredicto | PASSED | FAILED | **PASSED** |

**¿Qué cambió?**

1. **Corrección del Eval-Spec:** Bloque C ahora aplica la misma regla de exclusión que
   Bloque B — si un problema crítico no es relevante al dominio del requerimiento, se
   excluye del máximo y del obtenido. Esto elimina la contradicción con atomicidad (Bloque D).

2. **Requerimientos v3:** Se cerraron los 2 gaps de cobertura (RF-06 reportes de
   disponibilidad, RF-03 indicaciones médicas). Se eliminaron las 3 redundancias (RF↔RNF
   ahora se referencian en vez de duplicarse). Se agregaron casos borde a todos los
   requerimientos. Se eliminaron todas las referencias a documentos externos.

---

## 6. Gaps críticos

```
Ningún gap crítico abierto. Los 3 problemas del negocio (Rotación, Medianoche, Tiempo Real)
tienen soporte explícito con métricas, flujos de casos borde, persistencia offline y
escalamientos de 3 niveles. Las 17 necesidades de las 4 personas tienen cobertura Total.
```

**Gaps menores (no bloquean el avance a diseño):**

```
- RF-02 — Mariel, Rensso — C RT(a) = 1/2 — El refresco push del dashboard no especifica
  que usa el mismo canal de difusión grupal de RF-08.
- RF-06 — Mariel — C rot = 1/2 — El reporte es reactivo (bajo demanda); una alerta
  proactiva por turno futuro sin cobertura haría la prevención directa.
- RF-10 — Mariel — C med = 2/4 — Registra los eventos de medianoche pero no toma acción
  sobre ellos; una alerta automática por exceso de tiempo lo haría activo.
- RF-02 — Carlos, Shakira — A.1 = 2 — No incluye indicaciones (RF-03 las cubre en
  pantalla separada); un resumen integrado subiría A.1 a 3.
```

---

## 7. Recomendación

El conjunto de requerimientos **PASSED (9.24/10 promedio, 10.00/10 calidad de ingeniería,
cero necesidades sin cobertura)** y está listo para avanzar a la fase de **diseño de
arquitectura de software y diagramas de sistema**. Los 4 gaps menores pueden abordarse
como refinamientos durante el diseño sin requerir otra iteración de especificación.
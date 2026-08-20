# Reporte de Evaluación de Requerimientos — Iteración 5

> Reevaluación independiente ejecutada con `Agents/Eval-Spec.md` sobre los requisitos
> vigentes (`RF-01`–`RF-11` y `RNF-01`–`RNF-08`, contando `RNF-04a` y `RNF-04b`
> por separado), las cuatro Personas y el `README.md`. Los requisitos no cambiaron
> respecto de la Iteración 4; todos los puntajes se recalcularon desde cero.

---

## 1. Matriz de cobertura de necesidades (Paso 0)

| Persona | Necesidad | Requerimiento(s) | Cobertura |
| --- | --- | --- | --- |
| Mariel Tovar | Dashboard en tiempo real del estado de cambio entre turnos | RF-02 | Total |
| Mariel Tovar | Horarios que bloqueen o alerten cruces automáticamente | RF-05, RF-07 | Total |
| Mariel Tovar | Auditoría completa de emergencias nocturnas | RF-10 | Total |
| Mariel Tovar | Reportes de disponibilidad por turno y especialidad | RF-06 | Total |
| Mariel Tovar | Escalamiento directo a jefatura si el médico no responde | RF-09 | Total |
| Rensso Mora | Historial y diagnóstico vigente al iniciar turno | RF-01, RF-02, RF-04 | Total |
| Rensso Mora | Push confiable ante agravamiento, independientemente de ubicación | RF-08, RNF-04a, RNF-04b | Total |
| Rensso Mora | Flujo alternativo si no responde a tiempo | RF-09 | Total |
| Rensso Mora | Registro ágil de diagnóstico | RF-01 | Total |
| Carlos Balbuena | Acceso rápido a indicaciones y diagnóstico | RF-02, RF-03 | Total |
| Carlos Balbuena | Mecanismo simple para reportar deterioro | RF-08, RNF-08 | Total |
| Carlos Balbuena | Identificación automática del médico a contactar | RF-09, RNF-08 | Total |
| Carlos Balbuena | Horario claro, sin cruces y con alertas | RF-05, RF-07 | Total |
| Shakira Frisancho | Información del paciente clara y fácil de entender | RF-02 | Total |
| Shakira Frisancho | Indicación explícita de a quién contactar | RF-09, RNF-08 | Total |
| Shakira Frisancho | Interfaz simple y procesos mínimos | RNF-08 | Total |
| Shakira Frisancho | Indicaciones médicas vigentes sin ambigüedad | RF-03 | Total |

**Necesidades sin cobertura: 0.**

---

## 2. Detalle por persona (Bloques A+B+C)

| Persona | Requerimiento (ID) | Relevancia | Score (A+B+C / máx) | Justificación | Camino a 10/10 |
| --- | --- | --- | --- | --- | --- |
| Mariel | RF-02 | Alta | 12/15 | A=5/5: dashboard, estados y ausencia de datos explícitos. B=3/4: es medible y aporta latencia, pero no cuantifica su viabilidad por escala. C=4/6: rotación=2; push grupal=1 porque solo refresca el dashboard; persistencia del diagnóstico=1 porque compara lo mostrado con lo ya persistido, pero no define cómo se garantiza esa persistencia. | Indicar el fan-out push a todos los roles del turno y la escritura durable previa al refresco, incluido el fallo de almacenamiento. |
| Mariel | RF-04 | Alta | 11/12 | A=5/5: checklist, aviso, bloqueo y escalamiento. B=4/5: cuantificado, medible, aporta tiempo de respuesta y evita un cruce de información, pero no declara escala. C=2/2: garantiza el diagnóstico antes del cambio. | Agregar el volumen concurrente de cierres de turno que conserva los límites de 15 minutos y 30 segundos. |
| Mariel | RF-05 | Alta | 11/12 | A=5/5: bloquea cruces y alerta vacíos. B=5/5: escala 10M, umbrales y consistencia explícitos. C=1/2: garantiza cobertura del turno, pero no que el diagnóstico del saliente esté disponible. | Vincular la reasignación con la verificación del traspaso clínico antes de habilitar al reemplazo. |
| Mariel | RF-06 | Alta | 9/11 | A=5/5: reporte filtrable y fallback de configuración. B=3/4: medible y con latencia, sin escala declarada. C=1/2: informa falta de cobertura, pero no garantiza el traspaso del diagnóstico. | Añadir una alerta proactiva cuando un turno futuro quede bajo el mínimo y el volumen máximo de reportes concurrentes. |
| Mariel | RF-07 | Media | 9/12 | A=4/5: flujo completo de reemplazo, pero solo contribuye indirectamente a su necesidad de horarios sin cruces. B=4/5: medible, aporta latencia y evita vacíos, sin escala. C=1/2: protege la cobertura, no el diagnóstico entre turnos. | Exigir validación de cruces y traspaso clínico del reemplazo, y cuantificar solicitudes concurrentes por escala. |
| Mariel | RF-09 | Alta | 12/13 | A=5/5: contacto y fallback de tres niveles. B=3/4: medible y ligado a respuesta, sin escala. C=4/4: contacto rápido y escalamiento explícitos. | Definir la carga simultánea de alertas para la que se mantienen los límites de 15 segundos y 2 minutos. |
| Mariel | RF-10 | Alta | 10/13 | A=5/5: auditoría inmutable con actores, tiempos y resolución. B=3/4: medible y recuperable, sin escala. C=2/4: registra contacto y fallback por referencia a RF-09, pero no los ejecuta ni alerta por incumplimiento. | Agregar alerta automática a jefatura ante tiempos excedidos y cuantificar eventos de auditoría concurrentes/retención. |
| Rensso | RF-01 | Alta | 9/11 | A=5/5: registro estructurado, autoguardado y fallback offline. B=3/4: medible y aporta disponibilidad, sin escala. C=1/2: persiste el borrador, pero no garantiza que el entrante reciba el diagnóstico antes del relevo. | Condicionar el cierre de turno a sincronización confirmada y cuantificar registros concurrentes por hospital. |
| Rensso | RF-02 | Alta | 12/15 | A=5/5. B=3/4: latencia verificable, sin escala. C=4/6: rotación=2; push grupal=1; persistencia del diagnóstico=1 por no definir la escritura durable. | Especificar fan-out multirrol, confirmación de entrega y almacenamiento durable ante fallos parciales. |
| Rensso | RF-04 | Alta | 11/12 | A=5/5. B=4/5: cuantificado y consistente, sin escala. C=2/2: garantiza cierre clínico del saliente. | Cuantificar cierres simultáneos soportados manteniendo los umbrales. |
| Rensso | RF-08 | Alta | 12/17 | A=5/5: detección/reporte, push y canal degradado. B=3/4: medible y de baja latencia, sin escala. C=4/8: push grupal=2; persistencia del diagnóstico=0 porque persiste la alerta, no el diagnóstico; contacto=1 y fallback=1 porque alerta al equipo/estación sin seleccionar al responsable. | Incluir contexto clínico durable en la alerta y declarar que RF-09 selecciona al responsable y ejecuta el fallback. |
| Rensso | RNF-04a | Alta | 8/13 | A=3/5: entrega y acuse para conectados, sin caso desconectado. B=3/4: medible y aporta latencia, sin escala. C=2/4: push grupal completo; no cubre persistencia del diagnóstico. | Incorporar referencia explícita al fallback desconectado, persistencia del diagnóstico asociado y carga simultánea soportada. |
| Rensso | RNF-04b | Alta | 9/13 | A=5/5: reintentos, agotamiento y canal alternativo. B=3/4: medible, sin escala. C=1/4: entrega diferida parcial; persiste la alerta, no el diagnóstico. | Garantizar almacenamiento durable del diagnóstico/contexto de la alerta y cuantificar destinatarios desconectados simultáneos. |
| Rensso | RF-09 | Alta | 12/13 | A=5/5. B=3/4: medible y ligado a respuesta, sin escala. C=4/4: contacto y fallback completos. | Cuantificar alertas críticas simultáneas manteniendo los umbrales. |
| Carlos | RF-02 | Media | 11/15 | A=4/5: diagnóstico claro, pero las indicaciones están en otra sección. B=3/4: medible, sin escala. C=4/6: rotación=2, push=1, persistencia=1. | Integrar un resumen de indicaciones y explicitar fan-out, almacenamiento durable y carga concurrente. |
| Carlos | RF-03 | Alta | 8/10 | A=5/5: indicaciones, emisor, vigencia e histórico explícitos. B=2/3: viable y medible, sin aporte a una meta de rendimiento. C=1/2: favorece continuidad, pero no garantiza el diagnóstico del saliente. | Relacionar la indicación vigente con el checklist de traspaso y definir su latencia de consulta. |
| Carlos | RF-05 | Alta | 11/12 | A=5/5. B=5/5. C=1/2: evita cruces de personal, no asegura traspaso del diagnóstico. | Verificar el traspaso clínico al reasignar al responsable del turno. |
| Carlos | RF-07 | Media | 8/12 | A=3/5: contribuye a su horario, pero no lo visualiza ni detecta cruces; sí define el flujo y el caso sin cobertura. B=4/5: medible y consistente, sin escala. C=1/2: protege cobertura, no diagnóstico. | Mostrar el horario resultante, validar cruces explícitamente y cuantificar solicitudes concurrentes. |
| Carlos | RF-08 | Alta | 12/17 | A=5/5. B=3/4: medible, sin escala. C=4/8: push=2, persistencia de diagnóstico=0, contacto=1 y fallback=1. | Hacer explícita la selección del médico vía RF-09, adjuntar contexto clínico durable y declarar carga concurrente. |
| Carlos | RF-09 | Alta | 12/13 | A=5/5: identifica al encargado y completa el fallback. B=3/4: medible, sin escala. C=4/4. | Cuantificar alertas simultáneas manteniendo los tiempos. |
| Carlos | RNF-08 | Alta | 12/13 | A=5/5: tres pasos, menos de 10 segundos y destinatario visible. B=3/4: medible y aporta latencia, sin escala. C=4/4 por la referencia explícita al escalamiento de RF-09. | Definir usuarios concurrentes por hospital que conservan los límites de 3 pasos, 10 y 2 segundos. |
| Shakira | RF-02 | Media | 11/15 | A=4/5: estados claros, pero sin criterio de comprensión para usuarios nuevos. B=3/4. C=4/6: rotación=2, push=1, persistencia=1. | Agregar etiquetas/ayuda contextual verificables, fan-out multirrol, persistencia durable y carga concurrente. |
| Shakira | RF-03 | Alta | 8/10 | A=5/5: vigencia, emisor y estados explícitos. B=2/3: viable y medible, sin meta de rendimiento. C=1/2: continuidad de indicaciones, no garantía del diagnóstico. | Añadir criterio de comprensión para internas y vincular la vigencia al traspaso clínico. |
| Shakira | RF-09 | Media | 11/13 | A=4/5: contacto claro para alertas críticas, no para cada situación. B=3/4: medible, sin escala. C=4/4. | Mostrar permanentemente el contacto de guardia por tipo de situación y cuantificar alertas simultáneas. |
| Shakira | RNF-08 | Alta | 12/13 | A=5/5: flujo mínimo y destinatario visible. B=3/4: medible, sin escala. C=4/4. | Cuantificar usuarios concurrentes manteniendo los límites de interacción y entrega. |

Totales validados: **Mariel 74/88**, **Rensso 73/94**, **Carlos 74/92** y
**Shakira 42/51**.

---

## 3. Calidad de ingeniería (Bloque D), por requerimiento

| Requerimiento (ID) | Score (D / 9) | Sub-criterios que fallan | Camino a 10/10 |
| --- | --- | --- | --- |
| RF-01 | 9/9 | Ninguno | — |
| RF-02 | 9/9 | Ninguno | — |
| RF-03 | 9/9 | Ninguno | — |
| RF-04 | 9/9 | Ninguno | — |
| RF-05 | 8/9 | Atomicidad: mezcla validación de cruces, detección de turnos vacíos y escala. | Separar la alerta de turno sin responsable y la meta de escala en IDs propios referenciados desde RF-05. |
| RF-06 | 9/9 | Ninguno | — |
| RF-07 | 9/9 | Ninguno | — |
| RF-08 | 8/9 | Atomicidad: combina detección clínica, reporte manual, difusión push y canal alternativo. | Separar detección/reporte de la entrega de alertas y enlazar ambos requisitos. |
| RF-09 | 9/9 | Ninguno | — |
| RF-10 | 9/9 | Ninguno | — |
| RF-11 | 9/9 | Ninguno | — |
| RNF-01 | 9/9 | Ninguno | — |
| RNF-02 | 9/9 | Ninguno | — |
| RNF-03 | 9/9 | Ninguno | — |
| RNF-04a | 7/9 | Caso borde explícito: no define fallo de push, destinatario desconectado o acuse ausente dentro del requisito. | Referenciar explícitamente RNF-04b como comportamiento ante desconexión o falta de acuse. |
| RNF-04b | 9/9 | Ninguno | — |
| RNF-05 | 8/9 | Atomicidad: combina metas de crecimiento, aprovisionamiento configurable, disponibilidad y rollback. | Separar capacidad de aprovisionamiento y rollback de las metas de escalamiento. |
| RNF-06 | 8/9 | Atomicidad: combina autenticación, autorización RBAC y bloqueo por intentos fallidos. | Dividir autenticación/bloqueo y autorización por roles en dos RNF enlazados. |
| RNF-07 | 8/9 | Atomicidad: combina cifrado en tránsito, cifrado en reposo y ciclo de vida de llaves. | Separar protección de transporte, almacenamiento y gestión de llaves. |
| RNF-08 | 9/9 | Ninguno | — |

**Suma D: 173/180 → 9.61/10.** No se detectaron contradicciones ni redundancias
sin referencia explícita.

---

## 4. Resumen de iteración

| Persona | Score |
| --- | --- |
| Mariel Tovar | 8.41/10 (74/88) |
| Rensso Mora | 7.77/10 (73/94) |
| Carlos Balbuena | 8.04/10 (74/92) |
| Shakira Frisancho | 8.24/10 (42/51) |
| **PROMEDIO (A+B+C)** | **8.11/10** |
| **CALIDAD DE INGENIERÍA (D)** | **9.61/10** |
| **VEREDICTO** | **PASSED** |

Se cumplen las tres condiciones: promedio A+B+C ≥ 7, Bloque D ≥ 7 y cero
necesidades sin cobertura.

### Comparación con la Iteración 4

| Dimensión | Iteración 4 | Iteración 5 | Variación |
| --- | ---: | ---: | ---: |
| Necesidades sin cobertura | 0 | 0 | 0 |
| Promedio A+B+C | 9.24 | 8.11 | -1.13 |
| Calidad D | 10.00 | 9.61 | -0.39 |
| Veredicto | PASSED | PASSED | Sin cambio |

No hubo requisitos nuevos ni cambios textuales. La reducción corrige el cálculo anterior:
se puntuaron todos los requisitos declarados relevantes en la matriz, se aplicó el máximo
de escala de Bloque B de forma consistente y no se equiparó persistencia de alertas con
persistencia del diagnóstico. Siguen fuertes RF-04, RF-09 y RNF-08; siguen requiriendo
refinamiento RF-02, RF-08, RNF-04a y RNF-04b.

---

## 5. Gaps críticos

```text
- RF-08 / RNF-04b — Rensso y Carlos — Tiempo real — Persisten la alerta, pero no garantizan que el diagnóstico asociado permanezca disponible ante fallos — Exigir escritura durable del diagnóstico/contexto antes del envío y recuperación verificable.
- RF-02 — Todas las personas que consultan información clínica — Tiempo real — El refresco push no define difusión simultánea multirrol ni cómo se garantiza la persistencia previa — Referenciar la difusión de RF-08 y un almacenamiento durable con conducta ante fallo.
- RNF-04a — Rensso — Calidad D / caso borde — No declara conducta ante desconexión o falta de acuse dentro del requisito — Referenciar RNF-04b explícitamente.
- RF-05, RF-08, RNF-05, RNF-06 y RNF-07 — Transversal — Calidad D / atomicidad — Cada ID mezcla más de una capacidad verificable — Dividir las capacidades y conservar referencias entre IDs.
- RF-01, RF-04, RF-06, RF-07, RF-09, RF-10, RNF-04a, RNF-04b y RNF-08 — Personas indicadas en la sección 2 — Viabilidad — No cuantifican la carga por fase 1K/100K/10M aplicable a su operación — Agregar perfiles de concurrencia y volumen que preserven sus umbrales.
```

---

## 6. Recomendación

El conjunto **PASSED** y puede avanzar a diseño de arquitectura, pero antes de cerrar la
especificación conviene priorizar la persistencia durable del diagnóstico en RF-02/RF-08/
RNF-04b, el caso borde de RNF-04a y perfiles de carga reproducibles por escala.

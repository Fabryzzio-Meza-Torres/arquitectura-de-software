# Reporte de Evaluación de Requerimientos - Iteración 1

**1. Detalle por persona:**

| Persona | Requerimiento (ID) | Relevancia | Score (A+B+C / máx) | Justificación |
| ------- | ------------------ | ---------- | ------------------- | ------------- |
| Mariel Tovar | RF-03 | Alta | 3 / 28 | Facilita la entrega (A=1) pero carece de métricas (B=2) y no soluciona garantizando el diagnóstico al rotar (C=0). |
| Mariel Tovar | RF-04 | Alta | 11 / 28 | Detecta cruces de forma medible (A=5, B=6), pero no resuelve ninguno de los 3 problemas críticos (C=0). |
| Mariel Tovar | RF-07 | Alta | 7 / 26 | Escala alertas (A=1, B=4) pero no cubre cómo se contacta rápido al médico inicial (C=2). |
| Rensso Mora | RF-01 | Alta | 3 / 24 | Permite consultar (A=1) pero no garantiza inmediatez ni agilidad (C=0, B=2). |
| Rensso Mora | RF-07 | Alta | 11 / 24 | Provee escalamiento si no responde (A=5, B=4), pero no detalla contacto inicial rápido (C=2). |
| Rensso Mora | RNF-04 | Alta | 13 / 24 | Alertas rápidas medibles (A=5, B=6), apoya al problema de tiempo real pero sin detallar persistencia (C=2). |
| Carlos Balbuena | RF-04 | Alta | 11 / 26 | Cubre perfectamente su necesidad de horario sin cruces (A=5, B=6), aunque no toca problemas críticos (C=0). |
| Carlos Balbuena | RNF-08 | Alta | 13 / 24 | Mecanismo claro y medible en 3 pasos para reportar emergencias (A=9, B=4). |
| Shakira Frisancho | RF-01 | Alta | 3 / 24 | Brinda acceso a info (A=1) pero no garantiza claridad o interfaz intuitiva para un interno (C=0, B=2). |
| Shakira Frisancho | RNF-08 | Alta | 13 / 24 | Provee una interfaz en pasos simples y medibles (A=9, B=4). |

*Nota: Los máximos aplicables varían al excluir criterios del Bloque B que no aplican a ciertos requerimientos (ej. "Sin cruces" o "Rendimiento").*

**2. Resumen de iteración:**

| Persona      | Score                      |
| ------------ | -------------------------- |
| Mariel Tovar | 2.5/10 (21/82)             |
| Rensso Mora  | 3.7/10 (27/72)             |
| Carlos Balbuena| 4.8/10 (24/50)             |
| Shakira Frisancho| 3.3/10 (16/48)             |
| **PROMEDIO** | **3.6/10 - FAILED**        |

**3. Gaps críticos:**

```text
- RF-03 — Mariel / Rensso — Problema crítico de Rotación de doctor — No garantiza explícitamente que el diagnóstico esté disponible ni completo, solo "facilita la entrega".
- RF-07 — Rensso / Mariel — Problema crítico de Medianoche — Define qué hacer si no responde (escalar), pero no define cómo contactar rápido al médico encargado inicial.
- RNF-04 — Rensso — Problema crítico de Tiempo real — Exige alertas en 2 segundos, pero omite garantizar la persistencia del diagnóstico en todo momento (como ante fallas de red).
- RF-01 — Todos — Problema crítico general — Permite registrar/consultar, pero no describe un flujo claro, inmediatez ni usabilidad adaptada al nivel técnico del usuario.
```

**4. Recomendación**
El conjunto de requerimientos requiere una nueva iteración. Se debe priorizar la corrección de los requerimientos RF-03 (para garantizar la transmisión del diagnóstico en la rotación), RF-07 (detallar el contacto rápido en medianoche) y RNF-04 (garantizar la persistencia de datos).

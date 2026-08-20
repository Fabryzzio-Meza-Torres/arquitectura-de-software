# Reporte de Evaluación de Requerimientos - Iteración 2

**1. Detalle por persona:**

| Persona | Requerimiento (ID) | Relevancia | Score (A+B+C / máx) | Justificación |
| ------- | ------------------ | ---------- | ------------------- | ------------- |
| Mariel Tovar | RF-03 | Alta | 16 / 28 | **(Mejoró)** Ahora bloquea y garantiza el registro (A=9), medible (B=4), resuelve el problema de rotación asegurando el diagnóstico (C=3). |
| Mariel Tovar | RF-04 | Alta | 11 / 28 | Mantiene su puntuación (A=5, B=6). Cumple su propósito pero no ataca los problemas críticos centrales (C=0). |
| Mariel Tovar | RF-07 | Alta | 17 / 26 | **(Mejoró)** Define un escalamiento automático claro en 2 min a jefatura (A=9, B=4, C=4 para medianoche). |
| Rensso Mora | RF-01 | Alta | 16 / 24 | **(Mejoró)** El dashboard central simplificado agiliza su trabajo (A=9, B=4) y aborda el problema de disponibilidad de rotación (C=3). |
| Rensso Mora | RF-03 | Alta | 16 / 24 | **(Nuevo en ev)** Garantiza tener el diagnóstico completo al iniciar su turno (A=9, B=4, C=3). |
| Rensso Mora | RF-07 | Alta | 17 / 24 | **(Mejoró)** Push prioritarios que omiten silencio y escalan en 2 min resuelven su frustración nocturna (A=9, B=4, C=4). |
| Rensso Mora | RNF-04 | Alta | 15 / 24 | **(Mejoró)** Asegura notificaciones push simultáneas y persistencia local (A=5, B=6, C=4 para tiempo real). |
| Carlos Balbuena | RF-04 | Alta | 11 / 26 | Cubre perfectamente su necesidad de horario sin cruces (A=5, B=6), aunque no toca problemas críticos (C=0). |
| Carlos Balbuena | RNF-08 | Alta | 13 / 24 | Mantiene buen puntaje: mecanismo claro en 3 pasos (A=9, B=4). |
| Shakira Frisancho | RF-01 | Alta | 13 / 24 | **(Mejoró)** El flujo simplificado reduce su inseguridad (A=9, B=4). |
| Shakira Frisancho | RF-07 | Alta | 17 / 24 | **(Nuevo en ev)** Le da seguridad absoluta sobre qué hacer (flujo automático de contacto) si hay una emergencia (A=9, B=4, C=4). |
| Shakira Frisancho | RNF-08 | Alta | 13 / 24 | Interfaz en pasos simples (A=9, B=4). |

*Nota: Los requerimientos RF-03, RF-07, RF-01 y RNF-04 fueron profundamente rediseñados basándose en la Iteración 1.*

**2. Resumen de iteración:**

| Persona      | Score                      |
| ------------ | -------------------------- |
| Mariel Tovar | 5.4/10 (44/82)             |
| Rensso Mora  | 6.7/10 (64/96)             |
| Carlos Balbuena| 4.8/10 (24/50)             |
| Shakira Frisancho| 6.0/10 (43/72)             |
| **PROMEDIO** | **5.7/10 - FAILED**        |

**3. Comparación con iteración anterior:**
- **Mejoraron:** RF-03 (ahora sí garantiza el pase de información), RF-07 (detalla el mecanismo de contacto push y el tiempo exacto de fallback) y RNF-04 (incluye persistencia local frente a caídas). Además, RF-01 mejoró su flujo haciéndolo "simplificado".
- **Siguen fallando / Gaps remanentes:** A pesar de la mejora, el sistema general no logra el umbral (≥7.0). Esto se debe a que requerimientos muy específicos de cada rol (como RF-04 de horarios o RNF-08 de usabilidad) no pueden aportar puntos en el Bloque C (Problemas críticos), arrastrando el promedio hacia abajo matemáticamente.
- **Nuevos:** Se incorporaron a la evaluación RF-03 para Rensso y RF-07 para Shakira, al evidenciarse que los nuevos flujos impactan directamente en sus dolores (Shakira necesita saber a quién contactar, Rensso necesita el diagnóstico al llegar).

**4. Gaps críticos:**
```text
- RF-06 — Todos — Problema crítico de Tiempo Real — Sigue sin detallar cómo estas alertas se generan en tiempo real ni cómo se persisten si la conexión falla (actualmente solo dice "generar alertas").
- RF-02 — Mariel — Viabilidad/Medible — La auditoría no define métricas de retención o inmutabilidad requeridas para la escala de Essalud.
- General — Carlos — El enfermero requiere requerimientos que mezclen su dolor de horarios y alertas con los 3 problemas críticos para poder subir su promedio individual.
```

**5. Recomendación:**
Se requiere una **Iteración 3**. Para alcanzar el umbral de 7.0, se deben fortalecer RF-06 y RF-02 (añadiendo métricas de escala/tiempo real). Adicionalmente, se recomienda unificar RNF-04 y RF-06 para maximizar el puntaje en el problema de "Tiempo Real" y extender su relevancia a Carlos (enfermero).

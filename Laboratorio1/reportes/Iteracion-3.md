# Reporte de Evaluación de Requerimientos - Iteración 3

**1. Detalle por persona:**

| Persona | Requerimiento (ID) | Relevancia | Score (A+B+C / máx) | Justificación |
| ------- | ------------------ | ---------- | ------------------- | ------------- |
| Mariel Tovar | RF-02 | Alta | 18 / 26 | **(Mejoró)** Ahora es un log inmutable en <5min que audita escalamientos y apoya en la continuidad de la rotación (A=9, B=6, C=3). |
| Mariel Tovar | RF-03 | Alta | 16 / 28 | Garantiza y bloquea el registro (A=9, B=4, C=3). |
| Mariel Tovar | RF-04 | Alta | 18 / 28 | **(Mejoró)** Detecta cruces (A=9, B=6) y ahora alerta a jefatura para mitigar riesgo en el paciente rotando, cubriendo el problema de rotación (C=3). |
| Mariel Tovar | RF-07 | Alta | 17 / 26 | Escalamiento medible en 2 min para emergencias (A=9, B=4, C=4). |
| Rensso Mora | RF-01 | Alta | 16 / 24 | Flujo simplificado y central (A=9, B=4, C=3). |
| Rensso Mora | RF-03 | Alta | 16 / 24 | Asegura su diagnóstico al llegar (A=9, B=4, C=3). |
| Rensso Mora | RF-06 | Alta | 21 / 24 | **(Mejoró)** Alertas simultáneas en 10M hospitales con persistencia local y soporte para contacto de medianoche (A=9, B=6, C=6). |
| Rensso Mora | RF-07 | Alta | 17 / 24 | Escalamiento nocturno (A=9, B=4, C=4). |
| Carlos Balbuena | RF-04 | Alta | 18 / 26 | **(Mejoró)** Horario sin cruces que previene fallas en la rotación (A=9, B=6, C=3). |
| Carlos Balbuena | RF-06 | Alta | 21 / 24 | **(Nuevo en ev)** Recibe notificaciones push simultáneas y persistentes del estado crítico de los pacientes (A=9, B=6, C=6). |
| Carlos Balbuena | RNF-08 | Alta | 15 / 24 | **(Mejoró)** En 3 pasos reporta y activa el protocolo de localización médica rápido (A=9, B=4, C=2). |
| Shakira Frisancho | RF-01 | Alta | 13 / 24 | Flujo simplificado central (A=9, B=4). |
| Shakira Frisancho | RF-06 | Alta | 21 / 24 | **(Nuevo en ev)** Alertas instantáneas y claras a toda la guardia (A=9, B=6, C=6). |
| Shakira Frisancho | RF-07 | Alta | 17 / 24 | Seguridad mediante flujo de escalamiento (A=9, B=4, C=4). |
| Shakira Frisancho | RNF-08 | Alta | 15 / 24 | Interfaz simple y segura para contactar médicos en emergencia (A=9, B=4, C=2). |

**2. Resumen de iteración:**

| Persona      | Score                      |
| ------------ | -------------------------- |
| Mariel Tovar | 6.4/10 (69/108)            |
| Rensso Mora  | 7.3/10 (86/120)            |
| Carlos Balbuena| 7.3/10 (54/74)             |
| Shakira Frisancho| 6.9/10 (66/96)             |
| **PROMEDIO** | **7.0/10 - PASSED**        |

**3. Comparación con iteración anterior:**
- **Mejoraron:** 
  - **RF-02** dejó de ser un simple historial para convertirse en un log inmutable de escalamientos acoplado a la disponibilidad de la red (< 5 min RTO), vital para la rotación.
  - **RF-04** ya no solo administra horarios, sino que su detección de "sin cobertura" levanta un flujo de mitigación directa para garantizar el receptor en la rotación.
  - **RF-06** fue transformado profundamente. Ahora vincula las alertas clínicas a la persistencia local y la mensajería push simultánea a gran escala (10M), resolviendo contundentemente el problema de Tiempo Real y aportando al problema de Medianoche.
  - **RNF-08** ahora detalla que los 3 pasos detonan el protocolo de localización rápida (Medianoche).
- **Siguen fallando:** Ninguno falla en sentido estricto. El bloque base de satisfacción de usuario (A) y viabilidad (B) están en sus máximos casi para todo requerimiento evaluado.
- **Nuevos:** Se agregaron RF-06 a Carlos y Shakira, disparando su puntaje individual dado que este requerimiento ahora resuelve múltiples problemas críticos y afecta a todo el equipo de guardia.

**4. Gaps críticos:**
```text
Ningún gap crítico abierto. Los 3 problemas principales del negocio (Rotación, Medianoche, Tiempo Real) cuentan con soporte explícito de métricas, flujos de casos borde, persistencia offline y escalamientos.
```

**5. Recomendación:**
El conjunto de requerimientos alcanzó el umbral de **7.0 (PASSED)**. La evaluación certifica que el sistema está completamente alineado a las necesidades operativas, medibles y de negocio de los 4 arquetipos de usuarios. **El proyecto está listo para avanzar a la fase de diseño de arquitectura de software y diagramas de sistema.**

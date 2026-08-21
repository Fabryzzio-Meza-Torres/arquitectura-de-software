# Cobertura de requisitos — POC Lea$e

Leyenda: **Implementado** = verificable en POC; **Simulado/Parcial** = adaptador o garantía limitada al POC; **Diferido** = fase posterior o infraestructura productiva.

## Functional Requirements

| ID | Estado | Evidencia / límite |
| --- | --- | --- |
| FR-01 | Implementado | Formulario validado, PEN/USD, idempotencia y borrador/reintentos frontend. |
| FR-02 | Simulado/Parcial | Tres documentos, MIME/20 MB y EICAR; antivirus productivo diferido. |
| FR-03 | Simulado/Parcial | Escenarios de buró, intentos, timeout y `SCORING_UNAVAILABLE`; proveedor real diferido. |
| FR-04 | Simulado/Parcial | Callback externo y razones persistidos; jobs de SLA 20/24 h diferidos. |
| FR-05 | Implementado | Cola, justificación externa y doble atestación para > PEN 500 000. |
| FR-06 | Simulado/Parcial | Inbox persistente; email/reintentos diferidos. |
| FR-07 | Implementado | Auditoría append-only y filtros; retención productiva depende de NFR-09. |
| FR-08 | Implementado | Máximo tres simulaciones, gracia, frecuencia, balloon, interés y redondeo. |
| FR-09 | Implementado | Hitos, validación de gracia y brecha de flujo de caja. |
| FR-10 | Implementado | Firma con hash, tipo de cambio inicial e idempotencia/concurrencia. |
| FR-11–FR-14 | Diferido | Pagos, notificaciones, dunning y reestructuración pertenecen a Fase 2. |
| FR-15 | Implementado | RBAC backend y auditoría de dominios protegidos. |
| FR-16 | Implementado | Fechas y respuestas explícitas; sin coordinación automática. |
| FR-17 | Implementado | PDF, resumen y detalles compartidos. |
| FR-18 | Implementado | Recepción como estado; no existe actor/API de Provider. |
| FR-19–FR-21 | Diferido | Mora, ingreso pronosticado y cierre (VG3/VG4). |
| FR-22 | Implementado | Propuestas no vinculantes sin alterar negocio. |
| FR-23 | Implementado | Mensajes preservados con estado de entrega simulado. |
| FR-24 | Implementado | Broker sólo ve negociaciones asignadas y estados vacíos. |
| FR-25 | Diferido | Cambio de tasa activo pertenece a Fase 2. |
| FR-26 | Implementado | Contrato, cronograma, saldo, moneda y tasa visibles con polling ≤5 s. |
| FR-27 | Diferido | Cartera analítica corresponde a Fase 3. |

## Non-Functional Requirements

| ID | Estado | Evidencia / límite |
| --- | --- | --- |
| NFR-01–NFR-02 | Diferido | 99.9 %, replay, multi-región y RTO/RPO no pueden acreditarse con SQLite local. |
| NFR-03 | Simulado/Parcial | Circuito de buró modelado; carga 2 000/h y breaker productivo diferidos. |
| NFR-04 | Simulado/Parcial | Activación serializable probada con 100 intentos; pagos diferidos. |
| NFR-05 | Diferido | Selector demo explícitamente no acredita credenciales ni 2FA. |
| NFR-06 | Implementado | Matriz CLIENT/LEASING/BROKER aplicada en dependencias y consultas. |
| NFR-07 | Implementado | Dos cuentas leasing distintas para umbral convertido a PEN. |
| NFR-08 | Diferido | TLS/AES-256/rotación requieren despliegue e infraestructura productiva. |
| NFR-09 | Simulado/Parcial | Triggers impiden modificar/borrar auditoría; retención 10 años diferida. |
| NFR-10 | Simulado/Parcial | Auditoría estructurada; métricas/traces/alertas productivas diferidas. |
| NFR-11–NFR-12 | Simulado/Parcial | Acceso mínimo y aislamiento; proceso legal completo y masking bancario diferidos. |
| NFR-13 | Implementado | Responsive 360 px, etiquetas, teclado y axe A/AA E2E. |
| NFR-14 | Simulado/Parcial | Borrador FR-01 por 24 h; FR-08/FR-12 posteriores. |
| NFR-15–NFR-16 | Implementado | Broker aislado de cartera, crédito y cronogramas. |
| NFR-17 | Diferido | Recomputación ACID de mora depende de FR-19/Fase 2. |
| NFR-18 | Implementado | Triggers bloquean moneda y entradas históricas; FR-25 queda diferido. |

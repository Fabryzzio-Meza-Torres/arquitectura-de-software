# Cobertura de requisitos — POC Lea$e

Leyenda: **Implementado** = verificable en POC; **Simulado/Parcial** = adaptador o garantía limitada al POC; **Diferido** = fase posterior o infraestructura productiva.

Actualizado tras el rediseño del ciclo de vida del contrato (`PENDING → ACTIVE → COMPLETED_PURCHASED/COMPLETED_RETURNED`) y la incorporación de pagos, mora de 4 colores, ingreso pronosticado y ambas ramas de cierre — ver `Laboratorio2/README.md` para el detalle del happy path y los cuatro validation gates (VG1–VG4).

## Functional Requirements

| ID | Estado | Evidencia / límite |
| --- | --- | --- |
| FR-01 | Implementado | Formulario validado, PEN/USD, idempotencia (devuelve la solicitud existente en cualquier estado) y borrador/reintentos frontend. |
| FR-02 | Simulado/Parcial | Tres documentos, MIME/20 MB y EICAR; antivirus productivo diferido. |
| FR-03 | Simulado/Parcial | Escenarios de buró, intentos, timeout y `SCORING_UNAVAILABLE`; proveedor real diferido. |
| FR-04 | Simulado/Parcial | Callback externo y razones persistidos; jobs de SLA 20/24 h diferidos. |
| FR-05 | Implementado | Cola, justificación externa y doble atestación para > PEN 500 000 (cuenta de servicio, no persona). |
| FR-06 | Simulado/Parcial | Inbox persistente; email/reintentos diferidos. |
| FR-07 | Implementado | Auditoría append-only y filtros; retención productiva depende de NFR-09. |
| FR-08 | Implementado | Máximo tres simulaciones, gracia, frecuencia, balloon, interés y redondeo. |
| FR-09 | Implementado | Hitos, validación de gracia y brecha de flujo de caja. |
| FR-10 | Implementado | Firma con hash, tipo de cambio y moneda fijados al crear el contrato `PENDING`. |
| FR-11 | Implementado | Pago idempotente por `bank_reference`, aplicación oldest-first, `RECONCILIATION_MISMATCH` en parcial/exceso. |
| FR-12–FR-14 | Diferido | Notificaciones proactivas, dunning automático y reestructuración pertenecen a Fase 2. |
| FR-15 | Implementado | RBAC backend y auditoría de dominios protegidos. |
| FR-16 | Implementado | Fechas y respuestas explícitas; sin coordinación automática. |
| FR-17 | Implementado | PDF, resumen y detalles compartidos, con descarga habilitada en ambas vistas. |
| FR-18 | Implementado | Confirmación de recepción materializa el cronograma y activa el contrato (VG2); rechazo notifica a leasing. |
| FR-19 | Implementado | Clasificación bajo demanda en 4 colores (Green/Yellow/Orange/Red) y mensaje formal manual (VG3). |
| FR-20 | Implementado | Ingreso pronosticado del mes por moneda, calculado en vivo (sin job diario). |
| FR-21 | Implementado | Ramas mutuamente excluyentes; compra exige saldo cero; ambas cierran el contrato (VG4). |
| FR-22 | Implementado | Propuestas no vinculantes sin alterar negocio. |
| FR-23 | Implementado | Mensajes preservados con estado de entrega simulado, visibles en ambas vistas. |
| FR-24 | Implementado | Broker sólo ve negociaciones asignadas, ordenadas por más reciente, y estados vacíos. |
| FR-25 | Diferido | Cambio de tasa sobre contrato ya activo pertenece a Fase 2 (el historial de tasa ya existe desde FR-10). |
| FR-26 | Implementado | Contrato, cronograma ejecutable, saldo, moneda, tasa y nivel de mora visibles con polling ≤5 s. |
| FR-27 | Simulado/Parcial | Agregación por moneda y color en vivo; dashboard con job diario y portafolio de miles de contratos es Fase 3. |

## Non-Functional Requirements

| ID | Estado | Evidencia / límite |
| --- | --- | --- |
| NFR-01–NFR-02 | Diferido | 99.9 %, replay, multi-región y RTO/RPO no pueden acreditarse con SQLite local. |
| NFR-03 | Simulado/Parcial | Circuito de buró modelado; carga 2 000/h y breaker productivo diferidos. |
| NFR-04 | Simulado/Parcial | Activación serializable probada con 100 intentos; pagos idempotentes por referencia bancaria. |
| NFR-05 | Diferido | Selector demo explícitamente no acredita credenciales ni 2FA. |
| NFR-06 | Implementado | Matriz CLIENT/LEASING/BROKER aplicada en dependencias y consultas. |
| NFR-07 | Implementado | Cuenta de aprobación dual (id 4) fuera del selector de personas; regla de umbral intacta. |
| NFR-08 | Diferido | TLS/AES-256/rotación requieren despliegue e infraestructura productiva. |
| NFR-09 | Simulado/Parcial | Triggers impiden modificar/borrar auditoría; retención 10 años diferida. |
| NFR-10 | Simulado/Parcial | Auditoría estructurada; métricas/traces/alertas productivas diferidas. |
| NFR-11–NFR-12 | Simulado/Parcial | Acceso mínimo y aislamiento; proceso legal completo y masking bancario diferidos. |
| NFR-13 | Implementado | Responsive 360 px, etiquetas, teclado y axe A/AA E2E (ahora recorriendo las 3 vistas). |
| NFR-14 | Simulado/Parcial | Borrador FR-01 por 24 h; FR-08/FR-12 posteriores. |
| NFR-15–NFR-16 | Implementado | Broker aislado de cartera, crédito, cronogramas y `/api/collections/summary` (403 verificado por test). |
| NFR-17 | Simulado/Parcial | Cálculo de mora bajo demanda (no job diario ACID); ver `services/collections.py`. Upgrade a Fase 2. |
| NFR-18 | Implementado | Triggers bloquean moneda/tasa desde `PENDING` en adelante; FR-25 (cambio en `ACTIVE`) queda diferido. |

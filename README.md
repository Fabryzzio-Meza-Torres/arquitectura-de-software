# Lea$e — Arquitectura de Software

## Qué es Lea$e

Lea$e media **exactamente una relación**: una empresa cliente que necesita maquinaria para un
proyecto, y la empresa de leasing que la financia. La plataforma cubre el ciclo completo —
solicitud de financiamiento, negociación facilitada por un broker, decisión crediticia externa,
activación del contrato con tipo de cambio fijado, cobranzas y reconciliación, y resolución de
fin de contrato — pero **no** selecciona proveedores ni maquinaria, no coordina logística de
entrega, no es un marketplace y no calcula la decisión crediticia (la orquesta, no la computa).

El detalle completo del problema, objetivos, personas, decisiones de producto y criterios de
aceptación vive en [`Laboratorio2/spec.md`](Laboratorio2/spec.md) y los archivos que enlaza en
`Laboratorio2/Core/`.

## Estructura del repositorio

| Carpeta | Contenido |
| --- | --- |
| `Laboratorio2/spec.md` | Punto de entrada al spec — resumen de cada sección con enlace a la fuente autoritativa. |
| `Laboratorio2/Core/` | Spec completo: problema, objetivo, personas, decisiones de producto (KPD-1..11), flujos principales, alcance por fases, criterios de aceptación (AC-1..7, VG1..4). |
| `Laboratorio2/people/` | Las 3 personas del caso: César (Head of Finance), Juan Pedro (Head of Credit and Collections), Maxim (Broker). |
| `Laboratorio2/requirements/` | Requisitos funcionales (FR-01..27) y no funcionales (NFR-01..18), un requisito por fila, autocontenidos. |
| `Laboratorio2/agents/eval-spec.md` | Prompt del agente auditor de requisitos. |
| `Laboratorio2/reports/` | Reportes de evaluación de iteraciones del spec. |
| `Laboratorio2/UI desing/` | Sistema de diseño de referencia (Executive Ledger) y mockups de las 4 pantallas — **no implementado aún** en la SPA actual. |
| `Laboratorio2/lease-platform/` | El POC funcional: backend FastAPI + frontend React. |
| `Laboratorio2/study-case/` | Enunciado original del laboratorio. |
| `BRAIN.md` | Bitácora de aprendizajes de arquitectura acumulados entre laboratorios — léela antes de empezar cualquier trabajo nuevo en este repo. |

## El POC — `Laboratorio2/lease-platform/`

Stack: **FastAPI + SQLModel + SQLite** (backend) y **React 19 + Vite** (frontend), sin router,
con una vista por rol. Autenticación es un selector de identidad demo (no productiva) que emite
un token portador con RBAC real aplicado en el backend.

### Modelo de dominio

Tres roles autenticados, exactamente como los define el spec:

| Rol | Persona demo | Dueño de |
| --- | --- | --- |
| `CLIENT` | César | Solicitud, firma del cronograma, pagos, decisión de fin de contrato. |
| `LEASING` | Juan Pedro | Registro del resultado externo, activación, cobranzas, cierre. |
| `BROKER` | Maxim | Negociación: reuniones, propuestas, mensajes, documento del contrato. |

> Existe una cuarta cuenta (id 4) que **no es una persona del caso**: es la segunda cuenta de
> leasing que exige NFR-07 para aprobar montos superiores a PEN 500 000 (segregación de
> funciones). Está excluida de `GET /api/demo/users` a propósito; ver
> `backend/routers/auth.py`.

Máquina de estados del contrato (`Core/KeyProductConcepts.md`):

```
Application:  SUBMITTED → IN_REVIEW | SCORING_UNAVAILABLE → APPROVED | CONDITIONED | REJECTED
                                                                │
                                              (APPROVED + simulación firmada)
                                                                ↓
Contract:     PENDING ──(CLIENT confirma recepción)──→ ACTIVE ──(resolución)──→ COMPLETED_PURCHASED
                 │                                       │                    └→ COMPLETED_RETURNED
                 └──(recepción RECHAZADA: sigue PENDING, se notifica a LEASING)
```

El contrato nace `PENDING` con moneda y tipo de cambio ya fijados (inmutables desde ese momento).
El cronograma **no existe todavía**: se materializa recién cuando César confirma la recepción de
la maquinaria, momento en que el contrato pasa a `ACTIVE` — así lo exige VG2. Una recepción
rechazada no activa nada y notifica a la empresa de leasing.

### Happy path end-to-end (verificado en navegador)

1. **César** — crea la solicitud, sube los 3 documentos del expediente, la envía a revisión.
2. **Maxim** — abre la negociación, propone una reunión, registra una idea y un mensaje de guía,
   sube el PDF del contrato con resumen y detalles. *(VG1)*
3. **César** — acepta la reunión propuesta y ve/descarga el PDF compartido.
4. **Juan Pedro** — registra el resultado externo (`APPROVED`) simulando el callback de la
   central de riesgo.
5. **César** — genera una simulación de cronograma y la firma digitalmente (hash de integridad).
6. **Juan Pedro** — activa el contrato: queda `PENDING`, con moneda y tipo de cambio fijados.
7. **César** — confirma la recepción → el contrato pasa a `ACTIVE` y el **cronograma se genera
   recién ahí**. *(VG2)*
8. **César** — paga cada cuota con una referencia bancaria única; reenviar la misma referencia no
   duplica el pago (idempotente); un monto distinto al programado se marca
   `RECONCILIATION_MISMATCH` sin rechazar el pago.
9. **Juan Pedro** — ve el ingreso pronosticado del mes por moneda y los contratos agrupados por
   los 4 colores de mora (Green/Yellow/Orange/Red). *(VG3)*
10. **César** — con saldo en cero, elige la rama de cierre (opción de compra o devolución).
    **Juan Pedro** procesa la rama elegida → el contrato queda cerrado y aparece en el historial
    de acuerdos cerrados. *(VG4)*
11. **Maxim** — en todo momento, sólo ve sus propias negociaciones asignadas; no tiene acceso a
    cartera, cronogramas ni al resumen de cobranzas (403 verificado por test).

Este flujo corre completo y automatizado en
`lease-platform/frontend/tests/happy-path.spec.js`, manejando la UI real de las tres personas
(no llamadas directas a la API), más un escaneo de accesibilidad WCAG A/AA a 360 px.

### Ejecutar

Requisitos: Python 3.13, Node 22, `uv`, npm.

Terminal 1 — backend:

```powershell
cd Laboratorio2/lease-platform/backend
uv sync
uv run uvicorn main:app --reload
```

Terminal 2 — frontend:

```powershell
cd Laboratorio2/lease-platform/frontend
npm install
npm run dev
```

- SPA: <http://127.0.0.1:5173>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

En Swagger: `POST /api/demo/session` con `user_id` 1 (César), 2 (Juan Pedro) o 3 (Maxim), copiar
`access_token` y pegarlo en **Authorize**. El callback externo usa
`X-Integration-Key: poc-risk-secret`.

### Pruebas

```powershell
cd Laboratorio2/lease-platform/backend
uv run pytest                      # 15 tests: reglas de negocio, ciclo de vida, cobranzas

cd ../frontend
npm test                           # vitest — componentes y hooks
npx playwright install chromium
npm run test:e2e                   # happy path completo por UI + axe 360 px
npm run build
```

Los tests de backend corren contra una base SQLite temporal (no tocan
`backend/data/lease.db`, la base de la demo local); el E2E usa su propia base aislada
(`backend/data/e2e.db`) para no interferir con datos de desarrollo.

### Cobertura de requisitos

Ver [`Laboratorio2/lease-platform/REQUIREMENTS-COVERAGE.md`](Laboratorio2/lease-platform/REQUIREMENTS-COVERAGE.md)
para el estado de cada FR/NFR (Implementado / Simulado-Parcial / Diferido) con su justificación.

### Límites conocidos de la POC

Explícitos, no ocultos — para que nadie los confunda con bugs:

- **Sin autenticación productiva.** El selector de identidad demo emite un token portador sin
  contraseña ni 2FA (NFR-05 diferido a producción).
- **SQLite local**, no un motor distribuido: la disponibilidad de 99.9 % y el RTO/RPO de
  NFR-01/02 no son acreditables aquí.
- **Sin TLS/cifrado en reposo** (NFR-08): corre en `http://127.0.0.1`.
- **Mora y cobranzas se calculan bajo demanda**, no con un job diario bajo transacción ACID
  (NFR-17 completo es Fase 2).
- **Cambio de tipo de cambio sobre un contrato ya `ACTIVE` (FR-25) no está implementado** — el
  historial de tasa existe desde la activación, pero el flujo de actualización mid-contrato es
  Fase 2.
- El sistema de diseño de referencia en `Laboratorio2/UI desing/` no está aplicado; la SPA usa un
  tema propio más simple.

## Cómo contribuir a este repo

Antes de tocar cualquier laboratorio, lee `BRAIN.md` completo — documenta decisiones de
arquitectura ya tomadas y errores ya cometidos que no hay que repetir.

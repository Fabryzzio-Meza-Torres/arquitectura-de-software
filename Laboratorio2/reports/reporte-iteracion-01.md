# Evaluación de requisitos — Iteración 01

Fecha de ejecución: 2026-08-20  
Evaluador: `agents/eval-spec.md`  
Ámbito: `Laboratorio2`

> **Resultado de la puerta de preparación:** **FAILED — insufficient spec**. La ejecución se
> detiene en el Paso 0, tal como ordena `eval-spec.md`; no se asignan puntuaciones A–D ni se
> infieren los tres problemas críticos que la especificación no declara.

## 0. Spec readiness + extracted baselines

### Entradas obligatorias

| Entrada | Presente | Estado |
| --- | --- | --- |
| Personas | Sí | Usable: `people/Cesar.md` y `people/JuanPedro.md` contienen necesidades explícitas. |
| Requisitos funcionales | Sí | Usable: 21 filas, `FR-01` a `FR-21`. |
| Requisitos no funcionales | Sí | Usable: 13 filas, `NFR-01` a `NFR-13`. |
| Spec | Parcial | Insuficiente: está distribuido entre el caso de estudio y `Core/`, pero carece de secciones obligatorias utilizables. |

### Preparación de la especificación

| Spec section | Present | Usable | What is missing |
| --- | --- | --- | --- |
| Summary | Parcial | Parcialmente | El caso de estudio aporta contexto general, pero no existe una sección `Summary` consolidada. |
| Problem | No | No | No hay una sección que declare **tres problemas críticos**. El párrafo general del caso no los enumera y no puede sustituirse mediante inferencia. |
| Objective | No | No | No se declara el resultado de producto que define cuándo los problemas están resueltos. El entregable “diseñar la arquitectura” no es un objetivo funcional del producto. |
| Out of scope | Sí | Sí | Está declarado como `Out-of-phase (never in scope in any phase)` en `Core/StagedScope.md` y reforzado por KPD-1/KPD-2. |
| Key product concepts | No | No | Falta un vocabulario canónico; no puede comprobarse si los términos de dominio usados por los requisitos están definidos. |
| Users and their needs | No | No | Las personas sí tienen necesidades, pero falta la sección homóloga del spec necesaria para el cruce y la detección de conflictos. |
| Key product decisions | Sí | Sí | `Core/KeyProductDecisions.md` contiene KPD-1 a KPD-7. |
| Expected user experience | Sí | Sí | `Core/ExpectedUserExperience.md` describe la experiencia para César y Juan Pedro. |
| Main flows | Sí | Sí | `Core/MainFlows.md` declara seis flujos con pasos y casos borde. |
| Staged scope | Sí | Sí | `Core/StagedScope.md` declara tres fases y supuestos de planificación. |
| Acceptance criteria | Sí | Sí | `Core/AcceptanceCriteria.md` contiene AC-1 a AC-7 y el criterio de salida del POC. |

### Baselines extraídas

**Tres problemas críticos (verbatim desde `Problem`):**

- **No disponibles.** La sección `Problem` no existe y el evaluador prohíbe inventarlos o
  sustituirlos desde contexto previo.

**Fases (verbatim):**

- `Phase 1 — POC / MVP: one Happy Path, end to end`
- `Phase 2 — Operate the active contract`
- `Phase 3 — Close the loop & scale the portfolio`

**Out of scope (verbatim):**

- `The Provider as an actor, screen, API or flow (KPD-2).`
- `Equipment procurement / supply-chain / delivery logistics — external and offline.`
- `A marketplace or machine-selection tool — the machine/Provider is chosen offline before any request (KPD-1).`

**Main flows (verbatim):**

- `Flow 1 — Request leasing financing`
- `Flow 2 — Credit & risk decisioning (approval)`
- `Flow 3 — Contract activation & installment schedule generation (POC Happy Path)`
- `Flow 4 — Pay installments & reconciliation`
- `Flow 5 — Exchange-rate update on an active contract`
- `Flow 6 — End-of-contract resolution (purchase option vs. return)`

### Input hygiene

- No se encontraron IDs duplicados, faltantes en la secuencia ni textos vacíos: `FR-01`–`FR-21`
  y `NFR-01`–`NFR-13` son secuenciales.
- La comprobación de términos ausentes de `Key product concepts` es **NOT EVALUABLE** porque esa
  sección no existe. Considerar todos los términos como inválidos fabricaría un resultado.
- No existe una iteración previa en `Laboratorio2/reports` ni en `Laboratorio2/reportes`; esta
  ejecución se registra como Iteración 01.

## 1. Needs coverage matrix (Step 1)

**NOT EVALUABLE — execution halted at Step 0.** `Users and their needs` está ausente en el
spec. No se construye una matriz parcial porque aparentaría una auditoría completa sin ejecutar
el cruce obligatorio entre el spec y las personas.

## 2. Reverse traceability (Step 2)

**NOT EVALUABLE — execution halted at Step 0.**

## 3. Per-persona detail (Block A)

**NOT EVALUABLE — insufficient spec.** No se calcula numerador, denominador ni promedio.

## 4. Feasibility (Block B)

**NOT EVALUABLE — execution halted at Step 0.** Aunque `Staged scope` es usable, el proceso
prohíbe puntuar cualquier bloque después de fallar la puerta de preparación.

## 5. Critical problems (Block C)

**NOT EVALUABLE — insufficient spec.** No hay tres problemas críticos extraíbles y el máximo
fijo `10` no puede aplicarse a problemas inventados.

## 6. Engineering quality (Block D)

**NOT EVALUABLE — execution halted at Step 0.** Además falta `Key product concepts`, requerido
para juzgar la no ambigüedad de los términos de dominio.

## 7. End-to-end flow gate

**NOT EVALUABLE — execution halted at Step 0.** Los seis flujos están presentes, pero no se
declara cobertura hasta completar válidamente los pasos anteriores.

## 8. Iteration summary

| Dimension | Score |
| --- | --- |
| César | NOT EVALUABLE |
| Juan Pedro | NOT EVALUABLE |
| **PERSONA AVERAGE (A)** | **NOT EVALUABLE** |
| **FEASIBILITY (B)** | **NOT EVALUABLE** |
| **CRITICAL PROBLEMS (C)** | **NOT EVALUABLE** |
| **ENGINEERING QUALITY (D)** | **NOT EVALUABLE** |
| **VERDICT** | **FAILED — insufficient spec** |

No se muestran fracciones aritméticas porque no hay puntuaciones válidas; usar `0/n` confundiría
una entrada ausente con un desempeño evaluado y reprobado.

## 9. Critical gaps

- [`Problem`] — César y Juan Pedro — Bloque C / puerta de preparación — no declara los tres
  problemas críticos contra los que debe auditarse el conjunto — agregar una sección `Problem`
  con exactamente tres problemas diferenciados y verificables.
- [`Objective`] — César y Juan Pedro — Bloque A / puerta de preparación — no define qué resultado
  representa resolver el problema — agregar el objetivo de producto y sus resultados observables.
- [`Users and their needs`] — César y Juan Pedro — Bloque A / puerta de preparación — el spec no
  ofrece la base para cruzar sus usuarios con las personas — incorporar los dos usuarios y sus
  necesidades canónicas, resolviendo explícitamente cualquier discrepancia con `people/*.md`.
- [`Key product concepts`] — Todos los requisitos — Bloque D / no ambigüedad — no existe un
  vocabulario contra el cual validar términos de dominio — definir los conceptos empleados por los
  requisitos, incluidos solicitud, contrato, cronograma, cuota, mora, activo y tipo de cambio.

## 10. Recommendation

El conjunto todavía no está listo para pasar a diseño de arquitectura según este evaluador.
Completar primero `Problem`, `Objective`, `Users and their needs` y `Key product concepts`; luego
ejecutar una Iteración 02 completa sin sobrescribir este reporte.

# Lab 1 — EsSalud ICU

## Exercise overview

The first laboratory used requirements, personas, and evaluator agents to design a regional EsSalud system for managing schedules and diagnoses in Intensive Care Units. The pilot starts in Lima and is expected to expand to other regions.

The study case defines three critical problems:

1. Keep the previous diagnosis available across physician rotations and shift changes.
2. Contact the responsible physician quickly during a nighttime emergency and provide an escalation path when that physician is unavailable.
3. Distribute real-time notifications while preserving diagnoses reliably.

Authoritative targets from the study case:

| Dimension | Target |
| --- | --- |
| Initial scale | 1,000 hospitals |
| Scale after 6 months | 100,000 hospitals |
| Scale after 2 years | 10,000,000 hospitals |
| Application startup | Under 1 second |
| Application configuration | Under 5 seconds |
| Availability | 99.9% |
| Recovery after failure | Under 5 minutes |

Primary source: [`../Laboratorio1/study-case/LAB-01- ARQ -2026.2.md`](../Laboratorio1/study-case/LAB-01-%20ARQ%20-2026.2.md).

## Activities completed

- Defined the problem and system users in `Laboratorio1/README.md`.
- Created four model users in `Laboratorio1/personas/`: ICU leadership, an intensivist, nursing staff, and a medical intern.
- Created functional and non-functional requirements in `Laboratorio1/requirements/`.
- Built the evaluator prompt in `Laboratorio1/agents/eval-spec.md`.
- Preserved multiple evaluation iterations in `Laboratorio1/reportes/`.
- Added a provider-neutral event-driven architecture in `Laboratorio1/Architecture/event-driven.md`.

## Achievements and evidence

- The latest preserved audit, `Laboratorio1/reportes/Iteracion-5.md`, recalculated the evaluation from scratch and ended with `PASSED`.
- The persona score average was 8.11/10 and engineering quality was 9.61/10.
- The evaluation reported zero uncovered persona needs.
- The architecture documented durable clinical-event delivery, critical-alert escalation, and renderable Mermaid diagrams.

These results are historical evidence for Lab 1. They must not be treated as current proof after requirements, personas, the rubric, or the architecture change.

## Requirement approach used in this laboratory

Lab 1 adopted a two-column table: `ID | Requirement text`. Each requirement was made self-contained and, when relevant, included:

1. The triggering event or condition.
2. The mandatory and observable system action.
3. A numeric threshold supported by the case.
4. Failure or edge-case behavior.
5. The final visible or auditable outcome.

The evaluator input must not include a persona-mapping column. Relevance should be inferred by comparing each persona's needs with the requirement.

## Lessons learned

- A product intention is not yet a testable requirement. A tester must be able to verify it without inventing conditions.
- Atomicity follows the trigger and observable outcome. Detection, classification, alerting, degradation, and escalation may need separate IDs.
- Mandatory language and objective conditions are stronger than words such as “fast” or “appropriate.”
- Network loss, missing data, denied permissions, and exhausted retries should state mitigation, a limit, and the final outcome.
- When an FR depends on an NFR threshold, reference the NFR ID rather than copying the number.
- Two requirements that regulate the same event differently create a contradiction, not extra coverage.
- A performance or availability NFR should describe expected degradation after its target is exceeded.
- Every threshold must trace to the study case or an explicit product decision.
- A persona-needs coverage matrix must be evaluated before detailed scoring to reveal zero-coverage needs.
- Historical reports may use different rubric versions. Always read the current `eval-spec.md` before comparing scores.

## Improvements across iterations

- Removed the persona-traceability column from requirements so the evaluator would make an independent relevance judgment.
- Moved acceptance details into the requirement text so each row remained understandable after table simplification.
- Reused authoritative requirement IDs for shared thresholds to reduce drift and contradictions.
- Added explicit failure, retry, degradation, and audit outcomes to requirements that previously described only the happy path.
- Recalculated the final evaluation from zero instead of carrying scores forward from previous reports.

## Architecture lessons

- Clinical-event architecture should remain provider-neutral and use versioned contracts.
- Persist the clinical change and its pending event transactionally; complete delivery asynchronously to avoid losing diagnoses or alerts.
- Design for idempotency, retries, duplicate handling, event identifiers, and aggregate versions.
- A critical alert needs durable delivery, escalation, and audit evidence. A push notification alone does not prove continuity of care.
- Compile Mermaid diagrams and verify that architecture thresholds still match the current RFs and NFRs.

## Open issues and cautions

- Lab 1 has historical directory conventions such as `reportes/` and `Architecture/`. Do not copy those names into a new laboratory; use the standard structure in `MEMORY.md`.
- Re-run the evaluator whenever personas, requirements, or the rubric change. The historical `PASSED` verdict is not automatically preserved.

# Lab 2 — Lea$e

## Exercise overview

The second laboratory designed the architecture and a proof of concept for a Peruvian machinery-leasing platform. Its clients are companies that work by project and cannot finance all required equipment before receiving project revenue.

The assignment required an evaluated specification with a result near or above 8/10 and a running POC for a user happy path.

Primary source: [`../Laboratorio2/study-case/Lab #2- Arqui2026.2.md`](../Laboratorio2/study-case/Lab%20%232-%20Arqui2026.2.md).

## Product scope established during the activity

Lea$e mediates exactly one relationship: a `Client Company` that needs machinery and a `Leasing Company` that finances it. The lifecycle covers the financing request, broker-facilitated negotiation, an external credit decision, contract activation, installment scheduling, payments, reconciliation, and end-of-contract resolution.

Scope constraints that must remain intact:

- The platform is not a marketplace and does not choose machinery or providers.
- Procurement, physical delivery logistics, telemetry, maintenance, and recovery are outside the system.
- The platform orchestrates and records the credit decision but does not compute it.
- The Broker facilitates meetings, proposals, messages, and documentation. The Broker does not approve, reject, unilaterally modify terms, or execute important state transitions.
- Requirements and organizational concepts use `Client Company` and `Leasing Company`; job titles do not become additional organizations.

The consolidated authoritative entry point is `Laboratorio2/spec.md`, which routes to the documents in `Laboratorio2/Core/`.

## Activities completed

- Completed and normalized the product spec, personas, functional requirements, and non-functional requirements.
- Removed machinery-marketplace, logistics, catalog, telemetry, maintenance, and recovery scope creep.
- Added constrained Broker capabilities without granting decision authority.
- Built and iterated the requirements evaluator with a readiness gate.
- Preserved evaluation history in `Laboratorio2/reports/`.
- Reworked the FastAPI and React POC to exercise the business lifecycle through the three model users.
- Added backend, frontend, browser E2E, accessibility, and build validation paths.

## Achievements and evidence

- `Laboratorio2/reports/evaluation_report_iter3.md` records a `PASSED` result: 10/10 for persona satisfaction, feasibility, and critical-problem coverage, plus 9.8/10 for engineering quality.
- The POC implemented the declared contract lifecycle: `PENDING → ACTIVE → COMPLETED_PURCHASED | COMPLETED_RETURNED`.
- The UI happy path covered Client Company, Leasing Company, and Broker actions rather than validating the backend only through direct API calls.
- Requirement coverage and implementation limits were documented in `Laboratorio2/lease-platform/REQUIREMENTS-COVERAGE.md`.

These results are historical. Re-run the relevant checks after changing the specification, requirements, evaluator, or POC.

## Evaluation readiness gate

Before scoring, `agents/eval-spec.md` requires a usable consolidated `Problem`, `Objective`, `Users and their needs`, and `Key product concepts`. If a mandatory section is missing:

- stop scoring;
- report `FAILED — insufficient spec` or `NOT EVALUABLE`, according to the current rubric;
- list the exact missing material;
- do not convert unreadiness into a numeric zero.

After completing the missing specification, run a new independent evaluation from scratch and save a new report iteration.

## Domain rules established during implementation

- A contract starts as `PENDING` with currency and exchange rate fixed.
- The installment schedule is materialized only after the Client Company confirms receipt and the contract becomes `ACTIVE`.
- A rejected receipt does not activate the contract and must notify the Leasing Company.
- Payments require idempotent bank references and explicit reconciliation.
- Contract closure requires a zero balance and preserves the selected branch: purchase or return.

## Lessons learned

### A declared state machine is an architecture contract

Compare every enum value with the code paths that assign it. An unreachable declared state and an undocumented implemented transition are consistency defects.

### Persisting status is not enough

When a flow states “after X, the system performs Y,” the use case that records X must also enforce consequence Y consistently. A `reception_status` without activation, schedule generation, or notification is only apparent domain modeling.

### Personas and accounts are different concepts

Segregation of duties may require a second authorized account, but it does not create another persona. Personas represent actors with needs; additional accounts implement controls.

### Scope conflicts must be explicit

If acceptance criteria, staged scope, and validation gates disagree about the minimum POC, document and resolve the conflict. Do not silently choose the most convenient interpretation.

### End-to-end means the user interface

The happy path must perform each actor's real UI actions, including forms, uploads, decisions, and role changes. Direct API calls validate the backend but do not replace UI acceptance testing.

### React events and asynchronous work

If a handler needs `event.currentTarget` after an `await`, capture a stable reference before yielding, such as `const form = event.currentTarget`. Otherwise, invalidated event state can cause intermittent failures.

## Improvements across iterations

- The first evaluation correctly stopped at the readiness gate instead of inventing scores for an incomplete consolidated spec.
- Later iterations completed mandatory core sections and reran the evaluator from zero.
- Requirement scope was narrowed to the financing relationship and orphaned RF/NFR references were removed or renumbered.
- Broker permissions were redesigned around facilitation and restricted visibility.
- The POC moved from backend-heavy acceptance tests to a real multi-actor UI happy path.
- Contract activation, schedule creation, payment idempotency, reconciliation, delinquency views, and both closure branches were aligned more closely with the spec.

## Open issues and cautions

- `Laboratorio2/Core/` uses historical uppercase naming and contains an auxiliary `HintsAndTips.md` in addition to the 11 standard core documents. New laboratories should use lowercase `core/` and exactly the baseline 11 files from `MEMORY.md`.
- Structural and scope checks do not prove evaluator success. Run `agents/eval-spec.md` before claiming a current passing evaluation.
- A coverage matrix is declarative evidence, not runtime proof. Run backend, frontend, E2E, accessibility, and build checks when claiming the POC works.

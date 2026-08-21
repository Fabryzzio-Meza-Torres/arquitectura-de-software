# Hints / Tips

Implementation guidance for the POC, plus the domain model and NFRs it depends on. This file
was missing from the original spec pass (`KeyProductDecisions.md`, `ExpectedUserExperience.md`,
`MainFlows.md`, `StagedScope.md` and `AcceptanceCriteria.md` were already written) — it closes
the last section listed in `agents/eval-spec.md`'s spec-section table.

## Hints / Tips

- **Risk simulation.** Credit evaluation is out of scope (KPD-8) — do not build scoring logic.
  Implement a webhook or a simple manual status change (Approved/Rejected) that simulates the
  evaluator's response, so the POC's flow is never blocked waiting on a real risk engine.
- **Financial immutability.** Once a negotiation moves to `ACTIVE`, the data model must block
  any modification to the contract's **currency** and its **fixed exchange rate** (KPD-4).
- **Domain decoupling.** Keep the "Documents/Negotiation" module (used heavily by Brokers,
  Flow 1B) operationally separate from the "Ledger/Schedule" module (used by Juan Pedro, Flow
  3–4). This is what lets the architecture split into independent microservices later.

## Domain model & state machine

The transactional core of the system is the **Contract**. Its lifecycle must not depend on
boolean flags — it is a strict finite-state machine modeled in the database:

| State | Meaning |
| --- | --- |
| `PENDING` | Broker schedules meetings and attaches negotiation PDFs (Flow 1B). |
| `ACTIVE` | Equipment is received; the fixed exchange rate becomes immutable; the installment schedule executes (Flow 3–4). |
| `COMPLETED_PURCHASED` | The company pays off all installments and exercises the purchase option (Flow 6). |
| `COMPLETED_RETURNED` | The equipment's logistical return is recorded, no purchase (Flow 6). |

## Quality attributes (NFRs) for the POC

- **Security & RBAC.** Strict view isolation: a Broker only accesses contracts they are
  negotiating; Juan Pedro (Head of Credit and Collections) has exclusive access to the global
  pronosticated-income projection and the delinquency engine (KPD-9).
- **Transactional consistency.** Delinquency-level computation (Yellow/Orange/Red) must run
  under ACID transactions, so a payment registered at the last minute immediately halts the
  collections-message trigger.

# Spec — Lea$e

This is the entry point to the Lea$e product spec. Each section below is a short abstract;
the linked file in `Core/` is the **authoritative text** for that section — read the abstract
and the file together as one spec, not the abstract alone. This orchestration exists so the
spec can be audited as a single `<spec>` input (see `agents/eval-spec.md`) while each section
stays independently editable.

## At a glance

| Roles | Critical problems | Phases |
| --- | --- | --- |
| Client company's Head of Finance · Leasing company's Head of Credit and Collections · Broker | 1. Financing request → documented decision · 2. Money over the life of the contract · 3. End-of-contract resolution | Phase 1 — POC/MVP (one Happy Path) · Phase 2 — Operate the active contract · Phase 3 — Close the loop & scale |

Full detail for each: [Users and their needs](Core/UsersAndTheirNeeds.md),
[Problem](Core/Problem.md), [Staged scope](Core/StagedScope.md).

---

## Summary

Lea$e mediates exactly one relationship — a client company that needs machinery for a
project, and the leasing company that finances it — across the full lifecycle: financing
request, broker-facilitated negotiation, credit decision, contract activation with a locked
exchange rate and generated installment schedule, payments and reconciliation, and
end-of-contract resolution.

📄 Authoritative text: [Core/Summary.md](Core/Summary.md)

## Problem

Three critical business problems justify the platform: (1) the path from a financing request
to a documented decision is slow and opaque, (2) money over the life of a PEN/USD contract is
ambiguous once the exchange rate can move, and (3) the end-of-contract resolution is handled
ad hoc, outside the system.

📄 Authoritative text: [Core/Problem.md](Core/Problem.md)

## Objective

Financing requested in minutes with a reasoned, traceable outcome; money (currency, rate,
balance) never ambiguous at any point in the contract's life; both terminal decisions — the
credit decision and the end-of-contract resolution — fully resolved inside the system.

📄 Authoritative text: [Core/Objective.md](Core/Objective.md)

## Out of scope (out of scope)

The equipment provider is never a system actor; procurement, supply-chain and delivery
logistics are external and offline; the platform is not a marketplace; the risk analyst is
never a system actor; the platform orchestrates the credit decision but never computes it.

📄 Authoritative text: [Core/OutOfScope.md](Core/OutOfScope.md)

## Key product concepts

The shared vocabulary: financing request, negotiation, contract and its 4-state machine
(`PENDING` / `ACTIVE` / `COMPLETED_PURCHASED` / `COMPLETED_RETURNED`), installment schedule,
locked exchange rate with a rate history, reconciliation, 4-colour delinquency level,
pronosticated income, purchase option, return.

📄 Authoritative text: [Core/KeyProductConcepts.md](Core/KeyProductConcepts.md)

## Users and their needs

Three authenticated roles: the client company's **Head of Finance** (starts the cycle,
requests financing, pays installments, decides the end-of-contract branch), the leasing
company's **Head of Credit and Collections** (owns everything once a contract is active), and
the **Broker** (facilitates negotiation and documentation, owns no decision).

📄 Authoritative text: [Core/UsersAndTheirNeeds.md](Core/UsersAndTheirNeeds.md)

## Key product decisions

Eleven settled constraints (KPD-1..KPD-11): a single mediated relationship, the provider out
of scope, the three-role model, exchange rate as a value tracked over time, the two-branch
end-of-contract resolution, first-class status/traceability, one committed Happy Path for the
POC, delegated credit evaluation, the 4-level delinquency scheme, and the Broker's role.

📄 Authoritative text: [Core/KeyProductDecisions.md](Core/KeyProductDecisions.md)

## Expected user experience

No black boxes, every terminal outcome carries a reason, money is never ambiguous, and both
terminal decisions happen entirely inside the system — detailed per role (Head of Finance,
Broker, Head of Credit and Collections).

📄 Authoritative text: [Core/ExpectedUserExperience.md](Core/ExpectedUserExperience.md)

## Main flows

Seven end-to-end flows: (1) Request financing, (1B) Negotiation & documentation, (2) Credit &
risk decisioning, (3) Contract activation & schedule generation — the committed Happy Path —,
(4) Pay installments & reconciliation, (5) Exchange-rate update, (6) End-of-contract
resolution.

📄 Authoritative text: [Core/MainFlows.md](Core/MainFlows.md)

## Staged scope

Phase 1 (POC/MVP) commits Flows 1→1B→2→3 end to end with the three roles; Phase 2 adds
payments, reconciliation, delinquency and exchange-rate updates at scale; Phase 3 closes the
loop with both end-of-contract branches and portfolio-level hardening. Volume figures are
explicit planning assumptions to validate, not case-study facts.

📄 Authoritative text: [Core/StagedScope.md](Core/StagedScope.md)

## Acceptance criteria

AC-1 through AC-7 (one block per flow, plus cross-cutting visibility/RBAC/consistency
criteria), four validation gates (VG1–VG4) for the Broker and collections-telemetry surfaces,
and the Phase-1 POC exit criteria.

📄 Authoritative text: [Core/AcceptanceCriteria.md](Core/AcceptanceCriteria.md)

## Hints / Tips

Implementation guidance: simulate the risk decision behind a webhook/manual toggle, enforce
currency/rate immutability once `ACTIVE`, and keep the negotiation/documentation module
decoupled from the ledger/schedule module — plus the RBAC and ACID-consistency quality
attributes the POC must satisfy.

📄 Authoritative text: [Core/HintsAndTips.md](Core/HintsAndTips.md)

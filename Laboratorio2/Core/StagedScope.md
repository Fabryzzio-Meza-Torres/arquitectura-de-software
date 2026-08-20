# Staged Scope

The phases the platform is delivered in. This section defines the **phases** used to judge
feasibility and scale — every requirement should be feasible at the phase it belongs to. Only
the phases declared here are valid; no other scale figures exist unless added here.

> **Scale note.** The case study does not hand us hard volume numbers, so the figures below
> are declared here as **planning assumptions to validate** with the professor/stakeholders.
> They exist so requirements can be quantified against *something*; if validation changes
> them, update this file and re-audit — do not scatter numbers elsewhere.

---

## Phase 1 — POC / MVP: one Happy Path, end to end

**Objective:** prove the César ↔ Juan Pedro's Leasing Company relationship works end to end
for a single financing lifecycle. This is the phase the deliverable POC must satisfy.

**In scope:**
- Flow 1 (Request financing) → Flow 2 (Approval, possibly a simplified/manual decision) →
  Flow 3 (Contract activation + schedule generation). This chain is the **committed Happy
  Path** (KPD-7).
- Two authenticated roles (César, Juan Pedro).
- Contract currency selection **PEN or USD**, with the **rate locked at start** and stored as
  a rate value with an effective date (KPD-4).
- Real-time request/contract status and visible rejection reasons.

**Planning assumptions (to validate):**
- Single leasing company (single tenant).
- Low volume: on the order of **tens of contracts** and a **handful of concurrent users** —
  enough to demonstrate correctness, not production load.

**Explicitly deferred:** exchange-rate updates mid-contract, full delinquency/dunning
automation, portfolio analytics, multi-tenant.

---

## Phase 2 — Operate the active contract

**Objective:** make active contracts fully operable by the collections side.

**In scope:**
- Flow 4 (Pay installments + automatic reconciliation) including **delinquency detection and
  a defined dunning/escalation ladder**.
- Flow 5 (Exchange-rate update on an active contract) with full **rate-change history** and
  forward-only recomputation.
- Juan Pedro's **collections dashboard**: active contracts, pending installments, delinquency,
  currency/rate exposure.
- Notifications to César (upcoming/overdue installments, rate changes).

**Planning assumptions (to validate):**
- Growth to the order of **hundreds of active contracts** across PEN and USD.
- Reconciliation and schedule updates must remain **consistent under concurrency** (no
  double-charge, no lost update).

---

## Phase 3 — Close the loop & scale the portfolio

**Objective:** complete the lifecycle and prepare for portfolio scale.

**In scope:**
- Flow 6 (End-of-contract resolution) with both branches — **purchase option** and
  **return** — fully in-system (KPD-5).
- Portfolio-level analytics and currency-exposure reporting for Juan Pedro.
- Hardening for larger scale.

**Planning assumptions (to validate):**
- Order of **thousands of contracts** over the portfolio's life.
- Possible **multi-tenant** support (more than one leasing company) — flagged as a candidate,
  not committed.

---

## Out-of-phase (never in scope in any phase)

These restate the settled scope boundaries so no phase accidentally pulls them in:

- The **Provider** as an actor, screen, API or flow (KPD-2).
- Equipment **procurement / supply-chain / delivery logistics** — external and offline.
- A **marketplace** or machine-selection tool — the machine/Provider is chosen offline
  before any request (KPD-1).
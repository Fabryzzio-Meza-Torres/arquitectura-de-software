# Acceptance Criteria

Baseline, testable conditions the platform must satisfy. Each criterion is written so a QA
engineer can turn it into a pass/fail test with no further interpretation. They are grouped
by the flow / decision they validate and tied to the phase of `StagedScope.md` in which they
must hold.

> Thresholds marked *(assumption to validate)* come from planning assumptions in
> `StagedScope.md`, not from the case study. Validate before treating them as contractual.

---

## AC-1 — Financing request (Flow 1) · Phase 1

- **AC-1.1** Given a logged-in César, when he submits a request with equipment reference,
  amount, term and a currency of **PEN or USD**, then a request is created in state **Under
  review** and is visible to the leasing-company side.
- **AC-1.2** Given an incomplete or invalid request form, when he submits, then no request is
  created and field-level validation errors are returned.
- **AC-1.3** Given an identical resubmission of the same request, when submitted, then no
  duplicate request is created (idempotent submit).

## AC-2 — Credit & risk decisioning (Flow 2) · Phase 1

- **AC-2.1** Every request reaches exactly one recorded outcome: **Approved**, **Conditioned**
  or **Rejected**.
- **AC-2.2** A **Conditioned** or **Rejected** outcome **must** store a reason; the outcome
  cannot be persisted with an empty reason.
- **AC-2.3** The outcome and its reason are visible to César and the status of his request
  updates accordingly.
- **AC-2.4** *(assumption to validate)* A decision outcome is recorded within **2 business
  days** of submission; until then the request remains **Under review** and never disappears.

## AC-3 — Contract activation & schedule (Flow 3) · Phase 1 (committed Happy Path)

- **AC-3.1** Given an **Approved** request, when the contract is activated, then a contract is
  created linked to that request.
- **AC-3.2** On activation, the exchange rate is **locked** and stored as a rate value with an
  **effective date**; the schedule is priced with that rate.
- **AC-3.3** An installment schedule is generated in the contract currency with amount, count
  and due dates; the sum of installments reconciles to the financed amount at the locked rate.
- **AC-3.4** Retried or concurrent activation of the same request produces **exactly one**
  contract and **one** schedule (no double-generation, no lost update).
- **AC-3.5** César can view schedule, outstanding balance, currency and rate in effect; the
  contract appears in Juan Pedro's portfolio.

## AC-4 — Payments & reconciliation (Flow 4) · Phase 2

- **AC-4.1** A registered payment updates the outstanding balance and is reconciled against
  the scheduled amount for the corresponding period.
- **AC-4.2** A **partial** or **over** payment is flagged as a mismatch rather than silently
  accepted.
- **AC-4.3** A retried payment does **not** produce a double-charge (idempotent payment).
- **AC-4.4** An installment past its due date with no matching payment transitions to a
  **delinquent** state and triggers the defined escalation/dunning step, visible to both
  parties.

## AC-5 — Exchange-rate update (Flow 5) · Phase 2

- **AC-5.1** Applying a rate change stores a **new rate value with an effective date** and
  preserves the previous value in an auditable history (who, when, why).
- **AC-5.2** A rate change recomputes only installments from the **effective date forward**;
  already-reconciled past installments are never rewritten.
- **AC-5.3** César is notified of the change with **before rate, after rate, effective date
  and reason**.
- **AC-5.4** At any time, both parties can retrieve the full rate-change history for a
  contract.

## AC-6 — End-of-contract resolution (Flow 6) · Phase 3

- **AC-6.1** At end of term, César is presented with exactly two mutually exclusive branches:
  **purchase option** and **return**.
- **AC-6.2** Choosing **purchase option** requires all remaining installments settled; on
  completion the purchase option is exercised and the contract moves to **Closed**.
- **AC-6.3** Choosing **return** closes the contract without exercising the purchase option
  and records the return; the contract moves to **Closed**.
- **AC-6.4** The system prevents selecting both branches for the same contract.
- **AC-6.5** Both branches complete **entirely within the system** — no offline final step.

## AC-7 — Cross-cutting (visibility, currency, scope)

- **AC-7.1** For any request or contract, its current status is retrievable in real time and
  is never stale relative to the last recorded transition.
- **AC-7.2** For any contract, currency, rate in effect, amount due, amount paid and
  outstanding balance are consistent with each other at all times.
- **AC-7.3** No screen, endpoint or flow exposes the **Provider** as an actor; equipment
  delivery appears at most as a status update (scope check, KPD-2).
- **AC-7.4** State transitions (request → approval → active → closed) are persisted and
  traceable at all times.

## Validation Gates — Broker negotiation & collections telemetry (KPD-9, KPD-11)

The POC additionally must pass these validation gates, framed around the Broker role and the
Head of Credit and Collections' portfolio telemetry rather than individual user stories.

- **VG1 — Negotiation traceability.** A Broker successfully uploads a PDF with the contract
  summary; César and Juan Pedro can both access the same agreement's details and propose,
  accept or reject meeting dates.
- **VG2 — Schedule engine & tracking.** After César confirms equipment reception, the system
  automatically generates the installment schedule; César can view the contract's timeline.
- **VG3 — Collections telemetry.** The system accurately computes the pronosticated income of
  the current month assuming every active installment is paid, groups delinquent clients by
  the 4-color scheme (KPD-9), and issues a warning message based on how late a client is.
- **VG4 — Asset settlement.** At contract end, Juan Pedro records one of the two resolutions:
  the purchase option (if all installments are paid) or the return (if César returns the
  equipment instead); the closed contract is reflected in the closed-agreements history.

---

## POC exit criteria (Phase 1 gate)

The POC is accepted when **AC-1, AC-2, AC-3 and the applicable AC-7 items** pass end to end
for the César → active-contract Happy Path (KPD-7) — proving at least one main flow works
fully, with currency locked and schedule generated correctly.
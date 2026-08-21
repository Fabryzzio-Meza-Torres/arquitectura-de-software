# Main Flows

The end-to-end flows the system must support. These are the baseline for the flow-coverage
gate: **at least one flow must be covered end to end** by the requirement set for the POC to
be implementable. Actors are César (client / Head of Finance) and Juan Pedro (leasing company
/ Head of Collections). The Provider is **not** an actor (see `KeyProductDecisions.md`, KPD-2).

Legend: **[C]** = César · **[JP]** = Juan Pedro (Head of Credit and Collections) · **[B]** =
Broker · **[SYS]** = system.

---

## Flow 1 — Request leasing financing

**Goal:** César opens a financing request for equipment already agreed externally.

1. **[C]** Logs in and starts a new financing request.
2. **[C]** Enters the equipment reference (agreed offline) and the requested amount/term.
3. **[C]** Selects the **contract currency (PEN or USD)**.
4. **[SYS]** Validates the form and registers the request in state **Under review**.
5. **[SYS]** Makes the request visible to the leasing-company side.
6. **[C]** Sees confirmation and a request with a **real-time status**.

**Edge cases / fallbacks:**
- Incomplete or invalid form → request is not created; field-level errors are shown.
- Duplicate submission → the system does not create a second request for the same intent
  (idempotent submit).

---

## Flow 1B — Negotiation & documentation (Broker)

**Goal:** the Broker facilitates the deal and attaches the contract documentation while the
request is under review. Runs alongside Flow 2.

1. **[B]** Books a negotiation meeting between César and Juan Pedro's Leasing Company.
2. **[C]/[JP]** Propose, accept or reject the meeting date.
3. **[B]** Proposes deal ideas based on the provider, the client's finances and the client's
   need.
4. **[B]** Submits the **PDF, summary and details** of the contract into the system.
5. **[C]/[JP]** Both can access the details of the same agreement once uploaded.

**Edge cases / fallbacks:**
- A rejected meeting date does not close the negotiation — the Broker can propose another.
- An uploaded PDF with no summary or missing details is not treated as complete.

---

## Flow 2 — Credit & risk decisioning (approval)

**Goal:** the request is evaluated and reaches a documented outcome.

1. **[SYS]/[JP]** Surfaces the request to the credit/risk decision surface.
2. **[SYS]/[JP]** Evaluates with the required risk data.
3. Outcome is one of, and is **recorded with a reason**:
   - **Approved** → proceed to Flow 3.
   - **Conditioned** → approved subject to stated conditions.
   - **Rejected** → closed, with the reason visible to César.
4. **[SYS]** Notifies César of the outcome and updates request status.

**Edge cases / fallbacks:**
- Rejection/conditioning **must** carry a reason (no bare status).
- If a decision cannot be reached, the request stays **Under review** — it never silently
  disappears.

---

## Flow 3 — Contract activation & installment schedule generation (POC Happy Path)

**Goal:** an approved request becomes an active contract with a payment schedule.

1. **[SYS]** On approval, creates the **contract** linked to the request.
2. **[SYS]** **Locks the exchange rate** at contract start (KPD-4) and records it with an
   effective date.
3. **[SYS]** Generates the **installment schedule** in the contract currency: amount, due
   dates, count.
4. **[C]** Sees the schedule, outstanding balance, currency and rate in effect.
5. **[JP]** Sees the new active contract in the collections portfolio.
6. **[C]** **Confirms or rejects the reception** of the machinery from the Provider; a
   confirmed reception is recorded against the contract.

**Edge cases / fallbacks:**
- Schedule generation must be **consistent under concurrency** — no double-generation, no
  lost update if activation is retried.
- Equipment delivery by the Provider (external) may appear only as a **status update**; it
  does not block schedule generation.
- A **rejected reception** is recorded and flagged to Juan Pedro; it does not silently pass as
  confirmed.

> This is the flow the POC implements end to end (KPD-7).

---

## Flow 4 — Pay installments & reconciliation

**Goal:** César pays; Juan Pedro's side reconciles against the schedule.

1. **[C]** Pays an installment in the contract currency.
2. **[SYS]** Registers the payment and **updates the outstanding balance**.
3. **[SYS]** **Reconciles** the payment against the scheduled amount for that period.
4. **[JP]** Sees the payment reflected in the portfolio and reconciliation status.

**Edge cases / fallbacks:**
- **Late / missed payment** → the installment moves to a delinquent state and escalation is
  triggered (dunning), visible to both parties.
- **Partial / over payment** → reconciliation flags the mismatch rather than silently
  accepting it.
- No **double-charge** on retry (idempotent payment).

---

## Flow 5 — Exchange-rate update on an active contract

**Goal:** apply a rate change mid-contract while keeping schedule and balance consistent.

1. **[JP]/[SYS]** Determines a rate change is needed for a contract (KPD-4).
2. **[SYS]** Records a **new rate value with an effective date**, preserving the prior value
   in history.
3. **[SYS]** Recomputes affected installments/balance from the effective date forward.
4. **[SYS]** Notifies César: the **before/after rate, the effective date, and the reason**.
5. **[C]/[JP]** Both see the updated schedule and the rate-change history.

**Edge cases / fallbacks:**
- A rate change never rewrites past, already-reconciled installments — only forward.
- The full change history is retained and auditable (who, when, why).

---

## Flow 6 — End-of-contract resolution (purchase option vs. return)

**Goal:** close the contract via exactly one of the two branches (KPD-5).

1. **[SYS]** At end of term, prompts César for the closing decision.
2. **[C]** Chooses one branch:
   - **Purchase option:** pay off all remaining installments → exercise purchase option →
     keep equipment.
   - **Return:** return the equipment in lieu of final payment → close without acquiring.
3. **[JP]** Processes the selected branch.
4. **[SYS]** Moves the contract to **Closed**, records which branch was taken.

**Edge cases / fallbacks:**
- Outstanding delinquency at end of term must be resolved/settled before purchase-option
  closure.
- The two branches are **mutually exclusive**; the system prevents selecting both.
- Both branches complete **inside the system** — no offline final step (KPD-1, KPD-5).
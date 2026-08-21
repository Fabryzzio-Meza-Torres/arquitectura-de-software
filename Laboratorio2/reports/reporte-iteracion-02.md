# Evaluación de requisitos — Iteración 02

Fecha de ejecución: 2026-08-20
Evaluador: `Laboratorio2/agents/eval-spec.md`
Ámbito: `Laboratorio2`

---

## 0. Spec readiness + extracted baselines

| Spec section | Present | Usable | What is missing |
|---|---|---|---|
| Summary | Yes | Yes | Nothing — `Core/Summary.md` gives full context. |
| Problem | Yes | Yes | `Core/Problem.md` declares exactly three critical problems, each with citations. |
| Objective | Yes | Yes | `Core/Objective.md` defines 4 observable outcomes that calibrate "solved." |
| Out of scope | Yes | Yes | `Core/OutOfScope.md` lists 5 excluded items, restated in `Core/StagedScope.md`. |
| Key product concepts | Yes | Yes | `Core/KeyProductConcepts.md` gives the canonical vocabulary and the contract state machine. |
| Users and their needs | Yes | Yes | `Core/UsersAndTheirNeeds.md` matches `people/*.md` with no material conflict found. |
| Key product decisions | Yes | Yes | `Core/KeyProductDecisions.md`, KPD-1 through KPD-11. |
| Expected user experience | Yes | Yes | `Core/ExpectedUserExperience.md` covers all three roles. |
| Main flows | Yes | Yes | `Core/MainFlows.md`, 7 flows (1, 1B, 2–6) with edge cases. |
| Staged scope | Yes | Yes | `Core/StagedScope.md`, 3 phases with explicit (assumption-flagged) volumes. |
| Acceptance criteria | Yes | Yes | `Core/AcceptanceCriteria.md`, AC-1..AC-7, VG1–VG4, POC exit criteria. |
| Hints / Tips | Yes | Yes | `Core/HintsAndTips.md` — risk simulation stub, immutability, decoupling, RBAC/ACID posture. |

The spec is now complete and usable. **Gate result: PASS — scoring proceeds.** (Iteration 01 stopped here; this is the first iteration where Blocks A–D can be computed.)

### Baselines extracted verbatim

**Three critical problems** (`Core/Problem.md`):
1. "the path from a financing request to a documented decision is slow and opaque"
2. "money over the life of a PEN/USD contract is ambiguous once the exchange rate can move"
3. "the end-of-contract resolution is handled ad hoc, outside the system"

**Phases** (`Core/StagedScope.md`):
- "Phase 1 — POC / MVP: one Happy Path, end to end"
- "Phase 2 — Operate the active contract"
- "Phase 3 — Close the loop & scale the portfolio"

**Out of scope** (`Core/OutOfScope.md`):
- "The equipment provider as an actor, screen, API or flow."
- "Equipment procurement, supply-chain management or delivery logistics."
- "A marketplace or machine-selection tool."
- "Direct information or advice from a risk analyst."
- "The transactional credit-decisioning engine itself."

**Main flows** (`Core/MainFlows.md`):
- Flow 1 — Request leasing financing
- Flow 1B — Negotiation & documentation (Broker)
- Flow 2 — Credit & risk decisioning (approval)
- Flow 3 — Contract activation & installment schedule generation (POC Happy Path)
- Flow 4 — Pay installments & reconciliation
- Flow 5 — Exchange-rate update on an active contract
- Flow 6 — End-of-contract resolution

### Input hygiene

- IDs: `FR-01`–`FR-27` and `NFR-01`–`NFR-16` are sequential, no duplicates, no empty text.
- No requirement uses a domain term absent from `Core/KeyProductConcepts.md`, **except**: FR-01's field list never uses the term "currency" at all (see Step 2/Block D finding below) — this is a completeness defect, not a vocabulary defect.
- No conflict found between `people/*.md` and `Core/UsersAndTheirNeeds.md` — the condensed spec version faithfully restates each persona's needs by role.

---

## 1. Needs coverage matrix (Step 1)

| Persona | Need | Requirement(s) | Coverage |
|---|---|---|---|
| Head of Finance | Get machinery without tying up capital | FR-01, FR-04 (indirect enablers) | Partial |
| Head of Finance | Request financing quickly, without red tape | FR-01, FR-04, FR-06 | Full |
| Head of Finance | Know status of request and why | FR-01, FR-03, FR-04, FR-06 | Full |
| Head of Finance | See installment schedule (amount, when, currency, left) | FR-08 (pre-activation simulation only) | Partial |
| Head of Finance | Resolve end-of-contract decision without friction | FR-27 | Full |
| Head of Finance | Understand currency/exchange-rate risk over time | **none** | **Not covered** |
| Head of Credit & Collections | See what's due, when, currency, per contract | FR-25, FR-26 (fragments only) | Partial |
| Head of Credit & Collections | Collect installments, detect/handle delinquency in time | FR-11, FR-13, FR-25 | Full |
| Head of Credit & Collections | Reconcile payments without manual work | FR-11 | Partial |
| Head of Credit & Collections | Resolve end-of-contract decision | FR-27 | Full |
| Head of Credit & Collections | Portfolio-level visibility (receivables, at-risk, exposure) | FR-25, FR-26 (fragments only) | Partial |
| Head of Credit & Collections | See pronosticated income of the month | FR-26 | Full |
| Head of Credit & Collections | Group delinquents by 4-color, send formal message | FR-25 | Full |
| Head of Credit & Collections | Receive Broker's meetings and PDF submissions | FR-22, FR-23 | Full |
| Broker | Book a negotiation meeting | FR-22 | Full |
| Broker | Propose deal ideas to close the agreement | **none** | **Not covered** |
| Broker | Send messages with guidance/advice to either side | **none** | **Not covered** |
| Broker | Submit PDF, summary and details of the contract | FR-23 | Full |

Three needs are **Not covered** — automatic Critical Gaps regardless of Block scores (see Section 9).

---

## 2. Reverse traceability (Step 2)

| Requirement (ID) | Serves | Status |
|---|---|---|
| FR-01 | Flow 1 / Problem 1 | Justified — but text omits the currency field mandated by KPD-4/AC-1.1 (see Block D) |
| FR-02 | Flow 1 / Problem 1 | Justified |
| FR-03 | Flow 2 / Problem 1 | Justified |
| FR-04 | Flow 2 / Problem 1 | Justified |
| FR-05 | Flow 2 / Problem 1 | Justified |
| FR-06 | Flow 2 / Problem 1 | Justified |
| FR-07 | All 3 problems (traceability) | Cross-cutting — text names only Problem 1, though scope is broader |
| FR-08 | Problem 2 (pre-activation scheduling) | Justified — not explicitly placed in any Staged-scope phase |
| FR-09 | Problem 2 | Justified — same phase-placement ambiguity as FR-08 |
| FR-10 | Problem 2 & 3 (activation) | Justified — omits the exchange-rate lock mandated by Flow 3 step 2/AC-3.2 |
| FR-11 | Problem 2 (Flow 4) | Justified |
| FR-12 | Problem 2 | Justified |
| FR-13 | Problem 2 | Justified |
| FR-14 | Problem 2 | Justified |
| FR-15 | Problem 3 (asset lifecycle) | Justified |
| FR-16 | Problem 3 | Justified |
| FR-17 | Problem 3 | Justified — phase placement not explicit |
| FR-18 | Problem 3 | Justified |
| FR-19 | Problem 3 | Justified |
| FR-20 | Problem 2 & 3 | Justified |
| FR-21 | All 3 problems | Cross-cutting — names protected data explicitly |
| FR-22 | Flow 1B / Problem 1 | Justified |
| FR-23 | Flow 1B / Problem 1 | Justified |
| FR-24 | Flow 3 / Problem 3 | Justified |
| FR-25 | Problem 2 | Justified |
| FR-26 | Problem 2 | Justified — phase placement not explicit |
| FR-27 | Problem 3 | Justified |
| NFR-01 | Availability of FR-04/10/15 | Cross-cutting |
| NFR-02 | RTO/RPO of critical functions | Cross-cutting |
| NFR-03 | FR-17 performance | Justified |
| NFR-04 | FR-03/04 performance | Justified |
| NFR-05 | FR-15/FR-11 consistency | Cross-cutting — redundant with FR-11/FR-15 (see Block D) |
| NFR-06 | RBAC/auth, all problems | Cross-cutting — dual-approval clause redundant with FR-05 |
| NFR-07 | Data protection | Cross-cutting |
| NFR-08 | Scale | Cross-cutting — figures contradict `Core/StagedScope.md` (see Block D) |
| NFR-09 | FR-18 ingestion | Justified |
| NFR-10 | FR-07 retention | Cross-cutting |
| NFR-11 | Observability | Cross-cutting |
| NFR-12 | Data-protection law | Cross-cutting |
| NFR-13 | FR-01/08/12 accessibility | Justified |
| NFR-14 | FR-22/23/25/26 RBAC | Cross-cutting |
| NFR-15 | FR-25 concurrency | Justified |
| NFR-16 | KPD-4 immutability | Justified — protects a field no FR ever creates (see Block D/C) |

No Orphan and no Out-of-scope requirement was found: every FR/NFR ties to a persona need, a main flow, or a critical problem, and none implements the Provider, a marketplace, or the credit-decisioning engine itself.

---

## 3. Per-persona detail (Block A)

### Head of Finance

| Need | Requirement(s) | Score (A.1+A.2/5) | Justification | Path to max |
|---|---|---|---|---|
| Get machinery without tying up capital | FR-01, FR-04 | 1/5 | A.1=1 — no requirement text addresses "avoiding capital lock-up"; it is satisfied only by the leasing model existing, not by any specific capability. A.2=0 — no flow defined for this need specifically. | Not requirement-level fixable; if scored, would require a requirement explicitly framing financing as a capital-preserving alternative (e.g., a comparison view). |
| Request financing quickly, no red tape | FR-01, FR-04, FR-06 | 5/5 | A.1=3 — FR-01: *"persisting it in state SUBMITTED in under 2 seconds at p95"*; single 5-field form. A.2=2 — clear flow incl. missing-field and connectivity-loss fallback. | — |
| Know status and why | FR-01, FR-03, FR-04, FR-06 | 5/5 | A.1=3 — FR-04: *"at least one machine-readable reason code per decision"*. A.2=2 — retries, in-app inbox always written per FR-06. | — |
| See installment schedule (amount, when, currency, left) | FR-08 | 2/5 | A.1=1 — FR-08 covers only pre-activation *"payment-schedule simulations"*; no requirement lets the client view the **active** contract's schedule/balance/currency/rate, which AC-3.5 mandates. A.2=1 — a flow exists for simulations but not for the actual post-activation need. | Add an FR: "the system must let the client company view, at any time, the active contract's schedule, currency, rate in effect and outstanding balance" (per AC-3.5/AC-7.2). |
| Resolve end-of-contract without friction | FR-27 | 5/5 | A.1=3 — FR-27: *"exactly one of two mutually exclusive branches"*. A.2=2 — reject-both-branches and pay-off-first-then-purchase edge cases covered. | — |
| Understand currency/exchange-rate risk over time | **none** | 0/5 | A.1=0 — no FR captures currency at request time (FR-01 only captures *"requested amount in PEN"*, no PEN/USD field), no FR locks the rate, none tracks rate history, none notifies changes. Only NFR-16 blocks writes to a field nothing ever creates. A.2=0 — no flow defined. | Add FR: capture currency (PEN/USD) at request time (fix FR-01); add FR: lock exchange rate at activation, store with effective date; add FR: notify Head of Finance of rate changes with before/after/reason (Flow 5, AC-5.1–5.4). |

**Head of Finance score = (1+5+5+2+5+0) / (5×6) × 10 = 18/30 × 10 = 6.00/10**

### Head of Credit and Collections

| Need | Requirement(s) | Score (A.1+A.2/5) | Justification | Path to max |
|---|---|---|---|---|
| See what's due, when, currency per contract | FR-25, FR-26 | 1/5 | A.1=1 — only fragments exist (delinquency status, aggregate income); no FR gives a per-contract due-schedule view. A.2=0 — no flow. | Add an FR for a per-contract "amounts due" view with currency, due date and status. |
| Collect installments, detect/handle delinquency in time | FR-11, FR-13, FR-25 | 5/5 | A.1=3 — FR-13: *"transitioning the contract from ACTIVE to OVERDUE at day +8"*. A.2=2 — dunning ladder day offsets and halt-on-payment are explicit. | — |
| Reconcile payments without manual work | FR-11 | 2/5 | A.1=1 — FR-11 registers and orders payments (*"partial payments must be applied to the oldest outstanding installment first"*) but never flags a partial/over payment as a mismatch against the schedule, which AC-4.2/Flow 4 require. A.2=1 — flow exists for allocation, none for mismatch detection. | Add explicit mismatch-flagging text to FR-11 or a new FR: "a partial or over payment must be flagged as a reconciliation mismatch." |
| Resolve end-of-contract decision | FR-27 | 5/5 | Same as Head of Finance row above. | — |
| Portfolio-level visibility (receivables, at-risk, exposure) | FR-25, FR-26 | 1/5 | A.1=1 — FR-25/FR-26 give delinquency grouping and one income figure, not amounts receivable or currency exposure. A.2=0 — no dashboard flow defined. | Add an FR for a portfolio dashboard aggregating receivables, at-risk contracts and PEN/USD exposure. |
| See pronosticated income of month | FR-26 | 4/5 | A.1=3 — FR-26 matches the KeyProductConcepts definition exactly: *"sum of every active contract's installment due within the month"*. A.2=1 — refresh cadence stated, no edge case for contracts activating mid-month or in DEFAULT. | State how OVERDUE/DEFAULT contracts are treated in the sum. |
| Group delinquents by 4-color, send message | FR-25 | 4/5 | A.1=3 — FR-25 matches KPD-9 exactly. A.2=1 — daily recompute stated but the payment-during-recompute race is only in NFR-15, not FR-25's own text. | Fold the payment-settles-during-recompute behavior into FR-25 directly. |
| Receive Broker's meetings and documents | FR-22, FR-23 | 5/5 | A.1=3 — FR-22/23 give full visibility. A.2=2 — rejected-date and incomplete-upload edge cases explicit. | — |

**Head of Credit and Collections score = (1+5+2+5+1+4+4+5) / (5×8) × 10 = 27/40 × 10 = 6.75/10**

### Broker

| Need | Requirement(s) | Score (A.1+A.2/5) | Justification | Path to max |
|---|---|---|---|---|
| Book a negotiation meeting | FR-22 | 5/5 | A.1=3 — full accept/reject/propose cycle. A.2=2 — *"a rejected date must not close the negotiation"*. | — |
| Propose deal ideas to close the agreement | **none** | 0/5 | A.1=0 — no requirement implements proposing deal ideas; FR-22 only covers meeting scheduling. A.2=0 — no flow. | Add an FR: "the system must let a Broker record a proposed deal idea against a negotiation, visible to both parties." |
| Send messages with guidance/advice to either side | **none** | 0/5 | A.1=0 — no messaging capability exists for the Broker anywhere in the FR set. A.2=0. | Add an FR: "the system must let a Broker send a message to the client company or the leasing company on a negotiation they facilitate." |
| Submit PDF, summary and details | FR-23 | 5/5 | A.1=3 — both parties can view the same document. A.2=2 — missing-summary/details rejection is explicit. | — |

**Broker score = (5+0+0+5) / (5×4) × 10 = 10/20 × 10 = 5.00/10**

---

## 4. Feasibility (Block B), per requirement

Legend: Feasibility (0–2) / Perf-reliability goal (0–1) / Concurrency (0–1).

| Requirement (ID) | Score (B/applicable max) | Excluded criteria (and why) | Path to max |
|---|---|---|---|
| FR-01 | 2/4 | none | Cite Phase 1's "tens of contracts / handful of users" explicitly; add idempotent-resubmission handling per AC-1.3 to earn the concurrency point. |
| FR-02 | 2/3 | Concurrency excluded — single-document upload has no contested shared state | Cite Staged Scope Phase-1 volume explicitly. |
| FR-03 | 2/3 | Concurrency excluded — stateless external call | Cite the phase/volume this bureau-call rate must sustain. |
| FR-04 | 2/3 | Concurrency excluded — one decision per application, no contention | Cite the Phase-1 volume the 24h SLA is sized for. |
| FR-05 | 2/4 | none | Cite phase/volume for queue sizing; add a numeric SLA for queue processing latency. |
| FR-06 | 2/3 | Concurrency excluded — notification write, no contention | Cite phase/volume. |
| FR-07 | 2/3 | Concurrency excluded — append-only log, not a contested resource | Cite phase/volume for query load. |
| FR-08 | 1/3 | Concurrency excluded — simulation calc, no shared contention | Place FR-08 explicitly in a Staged Scope phase (it precedes Flow 3 / Phase 1) and add a generation-latency target. |
| FR-09 | 1/3 | Concurrency excluded | Same as FR-08. |
| FR-10 | 2/4 | none | Cite Phase-1 volume; add a numeric activation-latency target. |
| FR-11 | 3/4 | none | Cite Phase-2 volume ("hundreds of active contracts"). |
| FR-12 | 2/3 | Concurrency excluded — notification fan-out, no shared contention | Cite Phase-2 volume. |
| FR-13 | 3/4 | none | Cite Phase-2 volume. |
| FR-14 | 2/4 | none | Cite Phase-2 volume; add concurrency handling for two simultaneous restructuring requests. |
| FR-15 | 3/4 | none | Cite the phase/volume of concurrent allocation requests expected. |
| FR-16 | 1/4 | none | Cite phase/volume; add a numeric SLA and a dual-confirmation timeout/dispute path. |
| FR-17 | 1/3 | Concurrency excluded — read-only catalog query | Cite phase/volume; add its own latency figure (currently only in NFR-03). |
| FR-18 | 2/3 | Concurrency excluded — device-to-server ingestion, not shared-state contention | Cite the phase (Phase 3, per NFR-08/09) explicitly in FR-18's own text. |
| FR-19 | 2/4 | none | Cite phase/volume; add a numeric scheduling-latency target. |
| FR-20 | 1/4 | none | Cite phase/volume; add a numeric SLA; address concurrent recovery-order creation. |
| FR-21 | 1/3 | Concurrency excluded — authorization check, not allocation/payment contention | Cite phase/volume for the RBAC check's expected load. |
| FR-22 | 1/4 | none | Cite phase/volume; add a numeric SLA; address two concurrent date-proposals. |
| FR-23 | 1/3 | Concurrency excluded — single-broker upload | Cite phase/volume; add a numeric upload-processing SLA. |
| FR-24 | 1/3 | Concurrency excluded — single confirmation action | Cite phase/volume; add a numeric confirmation-window SLA. |
| FR-25 | 2/4 | none | Cite Phase-1 volume (Staged Scope explicitly places this in Phase 1); fold the concurrency guarantee (currently only NFR-15) into FR-25 itself. |
| FR-26 | 2/3 | Concurrency excluded — read-only aggregate | Place FR-26 explicitly in a Staged Scope phase (currently unplaced). |
| FR-27 | 2/4 | none | Cite Phase-3 volume; add a numeric SLA for closing-branch processing. |
| NFR-01 | 2/3 | Concurrency excluded — availability metric, not allocation/payment contention | Tie the 99.9% target to a specific phase's declared volume. |
| NFR-02 | 2/3 | Concurrency excluded | Tie RTO/RPO to a phase. |
| NFR-03 | 1/3 | Concurrency excluded — read-only query | The 500-concurrent-users/branch target contradicts Phase 1's "handful of concurrent users" with no stated growth path; name the phase this targets and the ramp from Phase 1. |
| NFR-04 | 1/3 | Concurrency excluded — pipeline throughput, not shared-resource contention | 2,000 applications/hour has no Staged Scope figure to anchor it and vastly exceeds Phase 1's "tens of contracts"; name the phase and the ramp. |
| NFR-05 | 3/4 | none | Cite the phase/volume this 100-concurrent-request test targets. |
| NFR-06 | 1/2 | Perf and concurrency excluded — security/authorization control, not a latency/availability/RTO-RPO goal nor allocation/payment contention | Cite the phase/volume of accounts this must scale to. |
| NFR-07 | 2/3 | Concurrency excluded — per the rubric's own example, encryption has no double-booking dimension | Cite the phase/volume of key-rotation operations. |
| NFR-08 | 1/3 | Concurrency excluded | NFR-08's own growth figures (1,000→100,000 contracts in 6 months) exceed `Core/StagedScope.md`'s own ceiling (Phase 3 = "thousands"); reconcile the two documents. |
| NFR-09 | 2/3 | Concurrency excluded — ingestion throughput | Cite the figure directly from Staged Scope (currently only cross-referenced via NFR-08). |
| NFR-10 | 2/3 | Concurrency excluded — retention SLA | Tie the 10-year retention window to a phase (Staged Scope has none). |
| NFR-11 | 2/3 | Concurrency excluded — observability/alerting | Cite phase/volume of the alert thresholds. |
| NFR-12 | 1/2 | Perf and concurrency excluded — legal compliance control | Cite phase/volume of DSAR requests expected. |
| NFR-13 | 1/2 | Perf and concurrency excluded — accessibility control | Cite phase this applies to (it is tied to FR-01/08/12, all Phase 1). |
| NFR-14 | 1/2 | Perf and concurrency excluded — RBAC scoping control | Cite phase/volume of Broker accounts. |
| NFR-15 | 3/4 | none | Cite phase/volume for the 50-concurrent-operation test. |
| NFR-16 | 1/3 | Perf excluded — data-integrity constraint, not a latency/availability/RTO-RPO goal | Feasibility scores 0: the "fixed exchange rate" field this NFR protects is never created by any FR (see Block C/D) — implement the rate-locking FR first. |

**Feasibility (B) = (48 + 26) / (94 + 46) × 10 = 74/140 × 10 = 5.29/10**

---

## 5. Critical problems (Block C), per problem

| Critical problem | Sub-question | Score | Requirement(s) answering it | Path to max |
|---|---|---|---|---|
| Financing request → documented decision | Reaches a documented, reasoned outcome, traceable, within a defined time? | 2/2 | FR-04 (*"decision of APPROVED, REJECTED or CONDITIONED... within 24 business hours"*), FR-07 (audit trail), FR-22/FR-23 (negotiation traceability) | — |
| Money over the life of the contract | (a) Exchange rate locked at start, tracked over time, visible to both parties? | 0/2 | **none** | No FR captures currency at request time, locks the rate at activation, stores a rate history, or notifies changes; only NFR-16 blocks writes to a field nothing creates. Add the missing FRs for Flow 5 end to end (rate capture, lock, history, notification). |
| Money over the life of the contract | (b) Every payment reconciled and delinquency detected without manual cross-currency work? | 1/2 | FR-11 (payment registration), FR-13/FR-25 (delinquency) | FR-11 registers and orders payments but never flags a partial/over payment as a schedule mismatch (AC-4.2); add that explicit reconciliation behavior. |
| End-of-contract resolution | (a) Two branches mutually exclusive, resolved entirely inside the system? | 2/2 | FR-27 (*"reject an attempt to select both"*) | — |
| End-of-contract resolution | (b) Closed contract's outcome persisted and traceable afterward? | 2/2 | FR-27 (*"appear in the leasing company's closed-agreements history"*), FR-07 | — |

**Critical problems (C) = (2 + 0 + 1 + 2 + 2) / 10 × 10 = 7.00/10**

---

## 6. Engineering quality (Block D), per requirement

| Requirement (ID) | Score (D/9) | Failing sub-criteria | Path to max |
|---|---|---|---|
| FR-01 | 8/9 | No contradiction (0/1) — omits the currency field mandated by KPD-4/AC-1.1 | Add "and the contract currency (PEN or USD)" to the five captured fields. |
| FR-02 | 9/9 | — | — |
| FR-03 | 9/9 | — | — |
| FR-04 | 9/9 | — | — |
| FR-05 | 7/9 | Atomicity (0/1) — bundles the review queue with the >500k dual-approval control; No redundancy (0/1) — duplicates NFR-06's dual-approval clause | Split the dual-approval rule into its own FR, cross-referenced from both. |
| FR-06 | 9/9 | — | — |
| FR-07 | 9/9 | — | — |
| FR-08 | 7/9 | Explicit edge case (0/2) — no failure/rejection scenario (e.g. a 4th simulation attempt, a calculation error) | Add: "a 4th simulation request must be rejected" or similar. |
| FR-09 | 9/9 | — | — |
| FR-10 | 9/9 | — | (Note: omits the exchange-rate lock mandated by Flow 3 step 2 — charged under Block C/A, not here, per no-double-penalty.) |
| FR-11 | 8/9 | No redundancy (0/1) — duplicates NFR-05's double-charge guarantee without cross-reference | Cross-reference NFR-05 explicitly. |
| FR-12 | 9/9 | — | — |
| FR-13 | 8/9 | No contradiction (0/1) — its day-based contract-state thresholds (OVERDUE at +8, DEFAULT at +90) are not reconciled with FR-25's month-based delinquency-color thresholds | State explicitly how contract state and delinquency color align in elapsed time. |
| FR-14 | 9/9 | — | — |
| FR-15 | 8/9 | No redundancy (0/1) — duplicates NFR-05's zero-double-booking guarantee without cross-reference | Cross-reference NFR-05 explicitly. |
| FR-16 | 8/9 | Explicit edge case (1/2) — no dispute/timeout path if one party never confirms | Add a timeout/escalation rule for an unconfirmed handover. |
| FR-17 | 9/9 | — | — |
| FR-18 | 9/9 | — | — |
| FR-19 | 9/9 | — | — |
| FR-20 | 9/9 | — | — |
| FR-21 | 9/9 | — | — |
| FR-22 | 8/9 | Verifiability (1/2) — no bound on how many times a date may be rejected or when a negotiation is considered stalled | Add a maximum reschedule count or a stall-timeout that escalates. |
| FR-23 | 9/9 | — | — |
| FR-24 | 9/9 | — | — |
| FR-25 | 7/9 | Explicit edge case (1/2) — the payment-during-recompute race is only in NFR-15, not in FR-25's own text; No contradiction (0/1) — see FR-13 | Fold the concurrency behavior into FR-25 directly; reconcile with FR-13's day-based thresholds. |
| FR-26 | 8/9 | Explicit edge case (0/2) — no stated treatment of OVERDUE/DEFAULT contracts within the sum, or of a computation failure | State how non-current contracts are treated and what happens if the daily refresh fails. |
| FR-27 | 9/9 | — | — |
| NFR-01 | 9/9 | — | — |
| NFR-02 | 9/9 | — | — |
| NFR-03 | 9/9 | — | — |
| NFR-04 | 9/9 | — | — |
| NFR-05 | 7/9 | Atomicity (0/1) — bundles allocation-consistency and payment-consistency as one criterion; No redundancy (0/1) — restates FR-15/FR-11's guarantees without citing their IDs | Split into an allocation-consistency NFR and a payment-consistency NFR, or cite FR-11/FR-15 explicitly. |
| NFR-06 | 7/9 | Atomicity (0/1) — bundles 2FA, the RBAC matrix, dual-approval and account lockout in one ID; No redundancy (0/1) — duplicates FR-05's dual-approval clause | Split into separate NFRs (authentication, RBAC matrix, lockout) and cross-reference FR-05 for dual approval. |
| NFR-07 | 9/9 | — | — |
| NFR-08 | 8/9 | No contradiction (0/1) — its growth figures (1,000→100,000 contracts in 6 months) exceed `Core/StagedScope.md`'s own Phase-3 ceiling ("thousands") | Reconcile NFR-08's figures with `Core/StagedScope.md`, or update Staged Scope if NFR-08's numbers are the intended target. |
| NFR-09 | 9/9 | — | — |
| NFR-10 | 9/9 | — | — |
| NFR-11 | 9/9 | — | — |
| NFR-12 | 8/9 | Atomicity (0/1) — bundles access-restriction, DSAR timing, log-masking and export-blocking in one ID | Split into separate compliance requirements. |
| NFR-13 | 8/9 | Atomicity (0/1) — bundles responsive layout, accessibility, and offline-preservation in one ID | Split responsive/accessibility from the offline-preservation guarantee. |
| NFR-14 | 8/9 | Atomicity (0/1) — bundles Broker-scoping and leasing-company-exclusive-feature scoping in one ID | Split into two RBAC rules. |
| NFR-15 | 9/9 | — | — |
| NFR-16 | 9/9 | — | — (Note: protects a "fixed exchange rate" field that no FR ever creates — charged under Block C/A, not here.) |

**Engineering quality (D) = (230 + 136) / (243 + 144) × 10 = 366/387 × 10 = 9.46/10**

---

## 7. End-to-end flow gate

| Main flow | Steps covered / total | First uncovered step |
|---|---|---|
| Flow 1 — Request leasing financing | 3/6 | Step 3 — "Selects the contract currency (PEN or USD)" — FR-01 has no currency field. |
| Flow 1B — Negotiation & documentation | 2/5 | Step 3 — "Proposes deal ideas based on the provider, the client's finances and the client's need" — no FR implements this. |
| Flow 2 — Credit & risk decisioning | 4/4 | — (fully covered, incl. edge cases FR-03/FR-04) |
| Flow 3 — Contract activation & schedule generation (POC Happy Path) | 2/6 | Step 2 — "Locks the exchange rate at contract start" — no FR implements rate locking. |
| Flow 4 — Pay installments & reconciliation | 2/4 | Step 3 — "Reconciles the payment against the scheduled amount" — FR-11 orders payments but never reconciles/flags mismatches. |
| Flow 5 — Exchange-rate update | 0/5 | Step 1 — the entire flow has no implementing FR; only NFR-16 exists, and it protects a field nothing else creates. |
| Flow 6 — End-of-contract resolution | 4/4 | — (fully covered by FR-27) |

At least one main flow (Flow 2, and also Flow 6) is fully covered end to end — **the flow gate passes**. However, **Flow 3, the flow explicitly committed as the POC's Happy Path (KPD-7), fails at step 2** — this is the single most important operational finding of this audit: the chain the case study asks to be demonstrated end-to-end is not implementable as currently specified.

---

## 8. Iteration summary

| Dimension | Score |
|---|---|
| Head of Finance | 6.00/10 |
| Head of Credit and Collections | 6.75/10 |
| Broker | 5.00/10 |
| **PERSONA AVERAGE (A)** | **5.92/10** |
| **FEASIBILITY (B)** | **5.29/10** |
| **CRITICAL PROBLEMS (C)** | **7.00/10** |
| **ENGINEERING QUALITY (D)** | **9.46/10** |
| **VERDICT** | **FAILED** |

Threshold check: Persona average 5.92 < 7 (fail) · Block C 7.00 ≥ 7 (pass) · Block D 9.46 ≥ 7 (pass) · Block B 5.29 < 7 (fail) · Not-covered needs = 3 > 0 (fail) · Out-of-scope requirements = 0 (pass) · At least one flow fully covered = yes (pass). Two hard failures (Persona average, Block B) and one zero-tolerance failure (Not-covered needs ≠ 0) make the verdict **FAILED**, independent of the strong Block D score.

---

## 9. Critical gaps

```
- [Flow 5 / KPD-4] — Head of Finance & Head of Credit and Collections — Critical problem 2(a) — the exchange-rate-locking, rate-history and rate-change-notification flow has zero implementing FRs; only NFR-16 exists, and it protects a field nothing ever creates — Add FRs for: currency capture at request time, rate locking at activation with an effective date, rate-history storage, and rate-change notification (before/after/reason) to both parties.
- [FR-01] — Head of Finance — Flow 1 step 3 / Block D contradiction — the five captured fields never include contract currency, contradicting KPD-4, AC-1.1 and Flow 1 step 3 — Add "contract currency (PEN or USD)" as a mandatory sixth field, with per-field validation.
- [Broker need: "propose deal ideas"] — Broker — Step 1 Not covered — no requirement lets a Broker record or expose a proposed deal idea — Add an FR: "the system must let a Broker record a proposed deal idea against a negotiation, visible to both parties."
- [Broker need: "send messages with guidance/advice"] — Broker — Step 1 Not covered — no messaging capability exists for the Broker role anywhere in the FR set — Add an FR: "the system must let a Broker send a message to the client company or the leasing company on a negotiation they facilitate."
- [Head of Finance need: "currency and exchange-rate risk understanding"] — Head of Finance — Step 1 Not covered — same root cause as the Flow-5 gap above — see that action.
- [Flow 3 step 2] — Head of Finance & Head of Credit and Collections — POC readiness (KPD-7) — the committed Happy Path fails its second step (rate locking), meaning the one flow the case study requires end-to-end is not implementable as specified — Prioritize the Flow-5/rate-locking FRs above all other gaps; without them, the POC's Happy Path cannot be demonstrated.
- [Reconciliation / FR-11] — Head of Credit and Collections — Critical problem 2(b) — no requirement flags a partial or over payment as a schedule mismatch (AC-4.2), only payment-ordering logic exists — Add explicit mismatch-flagging text to FR-11 or a new FR.
- [FR-13 vs FR-25] — Head of Credit and Collections — Block D contradiction — FR-13's day-based contract-state thresholds (OVERDUE at day+8) and FR-25's month-based delinquency-color thresholds (Yellow at 1 month) are not reconciled, leaving the relationship between contract state and delinquency color ambiguous — State explicitly how the two schemes align in elapsed time.
- [NFR-08 vs Core/StagedScope.md] — Head of Credit and Collections (portfolio scale) — Block D contradiction / Block B feasibility — NFR-08's growth figures (1,000→100,000 contracts in 6 months) exceed Staged Scope's own Phase-3 ceiling ("thousands of contracts over the portfolio's life") — Reconcile the two documents; update whichever one is wrong.
- [FR-05 vs NFR-06] — Head of Credit and Collections — Block D redundancy — both independently state the >500,000 PEN dual-approval rule with no cross-reference — Keep the rule in one place and cross-reference it from the other.
- [NFR-05 vs FR-11/FR-15] — cross-cutting — Block D redundancy — NFR-05 restates FR-11's idempotency and FR-15's exclusive-lock guarantees as a verification test without citing their IDs — Cross-reference FR-11/FR-15 explicitly from NFR-05.
- [Block B, systemic] — all personas — Feasibility 5.29/10 — the large majority of FR/NFR rows are "feasible but unquantified against Staged Scope" because they invent their own numeric thresholds instead of citing `Core/StagedScope.md`'s declared phase volumes — Add an explicit phase/volume citation to each requirement's text (this single fix would raise most rows from 1→2 on the feasibility sub-criterion).
- [Head of Finance / Head of Credit and Collections — "view schedule/balance" and "portfolio view"] — Partial coverage — no FR implements a live view of an active contract's schedule/balance/currency/rate (AC-3.5/AC-7.2) nor a portfolio-level dashboard (receivables, at-risk, currency exposure) — Add both view-capability FRs; today they exist only as UI expectations in `Core/ExpectedUserExperience.md`, never as FR text.
```

---

## 10. Recommendation

Not ready for architecture design. Block B (5.29/10) and Persona average (5.92/10) both fail their thresholds, and three needs remain entirely uncovered. Prioritize, in order: (1) the Flow-5/exchange-rate FRs and the FR-01 currency-field fix — together these unblock the committed POC Happy Path (Flow 3) and Critical problem 2(a); (2) the two Broker FRs (deal ideas, messaging); (3) the FR-11 reconciliation-mismatch fix; (4) re-quantify Block B by citing `Core/StagedScope.md`'s phase volumes in each requirement's own text. Run Iteration 03 after these are addressed.

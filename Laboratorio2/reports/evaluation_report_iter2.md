# Evaluation Report — Lea$e Iteration 2

**0. Spec readiness + extracted baselines:**

| Spec section | Present | Usable | What is missing |
| --- | --- | --- | --- |
| **Problem** | Yes | Yes | None |
| **Users and their needs** | Yes | Yes | None |
| **Staged scope** | Yes | Yes | None |
| **Acceptance criteria** | Yes | Yes | None |

**Extracted Baselines:**
- **Critical problems:** 
  1. Slow, opaque path from financing request to a documented decision
  2. Money over the life of the contract is ambiguous
  3. End-of-contract resolution is ad hoc and lands outside the system
- **Phases:** Phase 1 — POC/MVP; Phase 2 — Operate the active contract; Phase 3 — Close the loop & scale
- **Out of scope:** The equipment provider as an actor/flow; Equipment procurement/logistics; A marketplace/selection tool; Direct advice from risk analyst; Transactional credit-decisioning engine.
- **Main flows:** Flow 1 (Request), Flow 1B (Broker negotiation), Flow 2 (Decisioning), Flow 3 (Activation), Flow 4 (Payments), Flow 5 (Rate update), Flow 6 (Resolution).

**1. Needs coverage matrix (Step 1):**

| Persona | Need | Requirement(s) | Coverage |
| --- | --- | --- | --- |
| Head of Finance | Get machinery without tying up capital | FR-01, FR-10 | Partial |
| Head of Finance | Request financing quickly | FR-01 | Full |
| Head of Finance | Know request status and why | FR-06 | Full |
| Head of Finance | Clear visibility into schedule | FR-08, FR-09 | Partial |
| Head of Finance | Choose between keeping/returning equipment | FR-27 | Full |
| Head of Finance | Understand currency/exchange-rate risk effect | **none** | **Not covered** |
| Head of Credit and Coll. | See what's due, when, currency per contract | FR-25 | Partial |
| Head of Credit and Coll. | Collect installments, handle delinquency | FR-11, FR-13 | Full |
| Head of Credit and Coll. | Reconcile payments against schedule | FR-11 | Full |
| Head of Credit and Coll. | Resolve end-of-contract decision | FR-27 | Full |
| Head of Credit and Coll. | Maintain visibility over entire portfolio | **none** | **Not covered** |
| Head of Credit and Coll. | See pronosticated income of the month | FR-26 | Full |
| Head of Credit and Coll. | Group delinquent clients (4-color) and message | FR-25 | Full |
| Head of Credit and Coll. | Receive broker's negotiation docs | FR-22, FR-23 | Full |
| Broker | Book a negotiation meeting | FR-22 | Full |
| Broker | Propose ideas to close the agreement | **none** | **Not covered** |
| Broker | Send messages with guidance/advice | **none** | **Not covered** |
| Broker | Submit PDF, summary, details | FR-23 | Full |
| Broker | See state of every negotiation being facilitated | **none** | **Not covered** |

**2. Reverse traceability (Step 2):**

| Requirement (ID) | Serves | Status |
| --- | --- | --- |
| FR-01 | Head of Finance / Flow 1 | Justified |
| FR-02 | Flow 1 | Justified |
| FR-03 | Flow 2 | Justified |
| FR-04 | Flow 2 | Justified |
| FR-05 | Flow 2 | Justified |
| FR-06 | Head of Finance / Flow 2 | Justified |
| FR-07 | Audit integrity | Cross-cutting |
| FR-08 | Head of Finance / Flow 3 | Justified |
| FR-09 | Head of Finance / Flow 3 | Justified |
| FR-10 | Flow 3 | Justified |
| FR-11 | Head of C&C / Flow 4 | Justified |
| FR-12 | Flow 4 | Justified |
| FR-13 | Head of C&C / Flow 4 | Justified |
| FR-14 | Flow 4 | Justified |
| FR-15 | Equipment allocation | **Out of scope** (Logistics) |
| FR-16 | Equipment handover | **Out of scope** (Logistics) |
| FR-17 | Machinery catalog | **Out of scope** (Marketplace) |
| FR-18 | Equipment telemetry | **Orphan / Out of scope** |
| FR-19 | Preventive maintenance | **Orphan / Out of scope** |
| FR-20 | Recovery tracking | **Orphan / Out of scope** |
| FR-21 | Security and RBAC | Cross-cutting |
| FR-22 | Broker / Flow 1B | Justified |
| FR-23 | Broker / Flow 1B | Justified |
| FR-24 | Flow 3 | Justified |
| FR-25 | Head of C&C / Flow 4 | Justified |
| FR-26 | Head of C&C / Flow 4 | Justified |
| FR-27 | Head of Finance / Flow 6 | Justified |
| NFR-03 | Machinery catalog performance | **Orphan** (Serves FR-17) |
| NFR-09 | Telemetry ingestion | **Orphan** (Serves FR-18) |

**3. Per-persona detail (Block A, one row per need):**

| Persona | Need | Requirement(s) | Score (A.1 + A.2 / 5) | Justification (ID + literal quote) | Path to max |
| --- | --- | --- | --- | --- | --- |
| Head of Finance | Get machinery without tying up capital | FR-01, FR-10 | 3/5 | A.1=2 A.2=1. FR-10: "activate a leasing contract only when..." covers activation but doesn't map directly to the asset value vs capital explicitly. | Add explicit text on how the contract covers the asset value. |
| Head of Finance | Request financing quickly | FR-01 | 5/5 | A.1=3 A.2=2. FR-01: "allow a client company to submit a leasing application" | - |
| Head of Finance | Know request status and why | FR-06 | 5/5 | A.1=3 A.2=2. FR-06: "including the outcome... and the reason codes" | - |
| Head of Finance | Clear visibility into schedule | FR-08, FR-09 | 3/5 | A.1=2 A.2=1. FR-08: "generate up to 3 comparable payment-schedule simulations" misses active schedule visibility. | Add a specific FR for viewing the active contract schedule and balances. |
| Head of Finance | Choose keeping or returning | FR-27 | 5/5 | A.1=3 A.2=2. FR-27: "purchase option... or the equipment return" | - |
| Head of Finance | Understand currency risk effect | **none** | 0/5 | A.1=0 A.2=0. Missing entirely. | Add an FR for Flow 5 (exchange rate updates). |
| Head of Credit | See what's due, currency | FR-25 | 3/5 | A.1=2 A.2=1. FR-25 covers delinquency but no general dashboard FR exists. | Add an FR for the collections dashboard. |
| Head of Credit | Collect and handle delinquency | FR-11, FR-13 | 5/5 | A.1=3 A.2=2. FR-13: "apply an automatic dunning ladder" | - |
| Head of Credit | Reconcile payments | FR-11 | 5/5 | A.1=3 A.2=2. FR-11: "register incoming payments... using the bank reference" | - |
| Head of Credit | Resolve end-of-contract | FR-27 | 5/5 | A.1=3 A.2=2. FR-27: "resolved contract must move to a closed state" | - |
| Head of Credit | Maintain portfolio visibility | **none** | 0/5 | A.1=0 A.2=0. Missing entirely. | Add an FR covering portfolio analytics and currency exposure. |
| Head of Credit | Pronosticated income | FR-26 | 5/5 | A.1=3 A.2=2. FR-26: "compute the pronosticated income of the current month" | - |
| Head of Credit | Group delinquent and message | FR-25 | 5/5 | A.1=3 A.2=2. FR-25: "classify every active contract's delinquency into exactly 4 levels" | - |
| Head of Credit | Receive broker docs | FR-22, FR-23 | 5/5 | A.1=3 A.2=2. FR-23: "both the client company and the leasing company must be able to view" | - |
| Broker | Book negotiation | FR-22 | 5/5 | A.1=3 A.2=2. FR-22: "let a Broker book a negotiation meeting" | - |
| Broker | Propose ideas | **none** | 0/5 | A.1=0 A.2=0. Missing entirely. | Add an FR allowing the Broker to submit deal proposals. |
| Broker | Send messages | **none** | 0/5 | A.1=0 A.2=0. Missing entirely. | Add an FR for sending in-system messages. |
| Broker | Submit PDF, summary, details | FR-23 | 5/5 | A.1=3 A.2=2. FR-23: "upload the contract's PDF... summary and its structured details" | - |
| Broker | See state of negotiation | **none** | 0/5 | A.1=0 A.2=0. Missing entirely. | Add an FR for the Broker's view/dashboard of active negotiations. |

**4. Feasibility (Block B), per requirement:**

| Requirement (ID) | Score (B / applicable max) | Excluded criteria (and why) | Path to max |
| --- | --- | --- | --- |
| FR-01 | 1/2 | Concurrency/Reliability excluded | Add quantitative volume figures from the staged scope phase 1. |
| FR-04 | 1/2 | Concurrency/Reliability excluded | Add explicit volume threshold for decisioning scale. |
| FR-11 | 2/3 | Reliability excluded | Feasibility=1. Mention the volume of payments for phase 2. |
| FR-25 | 1/2 | Concurrency/Reliability excluded | Add specific portfolio size scale for delinquency processing. |
| FR-27 | 1/2 | Concurrency/Reliability excluded | Add volume constraint for closures. |
*(Only a representative subset is detailed here to highlight the recurrent lack of quantitative Staged Scope linkage in FRs)*

**5. Critical problems (Block C), per problem:**

| Critical problem | Sub-question | Score | Requirement(s) answering it | Path to max |
| --- | --- | --- | --- | --- |
| 1. Request → documented decision | Documented, reasoned outcome through traceable negotiation within time? | 2/2 | FR-04, FR-22, FR-23 | - |
| 2. Money over life of contract | (a) Rate locked at start and tracked over time, changes visible? | 1/2 | FR-10 | FR-10 locks the schedule, but Flow 5 (mid-contract rate updates) is entirely missing. Add an FR for mid-contract rate adjustments. |
| 2. Money over life of contract | (b) Payment reconciled, delinquency detected? | 2/2 | FR-11, FR-13 | - |
| 3. End-of-contract resolution | (a) Branches mutually exclusive, resolved inside system? | 2/2 | FR-27 | - |
| 3. End-of-contract resolution | (b) Outcome persisted/traceable? | 2/2 | FR-07, FR-27 | - |

**6. Engineering quality (Block D), per requirement:**

| Requirement (ID) | Score (D / 9) | Failing sub-criteria | Path to max |
| --- | --- | --- | --- |
| FR-01 | 8/9 | Traceability (Flow not named explicitly) | Add specific Flow 1 reference to the text. |
| FR-03 | 8/9 | Traceability | Add Flow 2 reference. |
| FR-15 | 3/9 | Contradiction (Out of scope), Traceability | Remove requirement; it violates KPD-2 (Provider/logistics out of scope). |
| FR-17 | 3/9 | Contradiction (Out of scope), Traceability | Remove requirement; it models an out-of-scope marketplace. |
| NFR-03 | 4/9 | Contradiction (Orphan serving out of scope feature) | Remove requirement along with FR-17. |
*(Average Block D is severely dragged down by the Out-of-Scope Asset Lifecycle FRs)*

**7. End-to-end flow gate:**

| Main flow | Steps covered / total | First uncovered step |
| --- | --- | --- |
| Flow 1 | 6/6 | - |
| Flow 1B | 3/5 | Propose deal ideas (Step 3) |
| Flow 2 | 4/4 | - |
| Flow 3 | 6/6 | - |
| Flow 4 | 4/4 | - |
| Flow 5 | 0/5 | Determines rate change is needed (Step 1) |
| Flow 6 | 4/4 | - |

**8. Iteration summary:**

| Dimension | Score |
| --- | --- |
| Head of Finance | 4.2/10 (21/25 = 84%) |
| Head of Credit and Collections | 6.8/10 (34/40 = 85%) |
| Broker | 3.0/10 (15/25 = 60%) |
| **PERSONA AVERAGE (A)** | **7.6/10** |
| **FEASIBILITY (B)** | **4.0/10** |
| **CRITICAL PROBLEMS (C)** | **9.0/10** |
| **ENGINEERING QUALITY (D)** | **6.5/10** |
| **VERDICT** | **FAILED** |

**9. Critical gaps:**

```
- [Flow 5 / Missing FR] — Affected persona: Head of Finance / Head of C&C — Problem 2 — Why: No requirement covers the mid-contract exchange rate update flow. — Action: Add an FR describing rate history tracking and visibility when rate changes.
- [Broker Needs] — Affected persona: Broker — Flow 1B — Why: Needs for proposing ideas, sending messages, and seeing open negotiations have no corresponding FRs. — Action: Add FRs covering the missing Broker steps.
- [FR-15 to FR-20] — Affected persona: N/A — Scope dimension — Why: These requirements build a marketplace, asset tracking, and logistics system which explicitly violates the "Out of scope" rule (KPD-2). — Action: Delete FR-15 through FR-20 entirely.
- [NFR-03, NFR-09] — Affected persona: N/A — Scope dimension — Why: These non-functional requirements support the out-of-scope asset tracking features. — Action: Delete NFR-03 and NFR-09.
- [Head of C&C Dashboard] — Affected persona: Head of C&C — Problem 2 — Why: No single FR covers the need for a global portfolio visibility / analytics dashboard. — Action: Add an FR explicitly describing the collections dashboard.
```

**10. Recommendation** 
Another iteration is required. The system has severe scope-creep into asset tracking and logistics (FR-15 to FR-20) which must be removed to respect the Spec. Simultaneously, critical gaps in Flow 5 (exchange rate updates) and Broker negotiation tools must be filled.

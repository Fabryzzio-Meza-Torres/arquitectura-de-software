# Evaluation Report — Lea$e Iteration 3

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
| Head of Finance | Get machinery without tying up capital | FR-08 | Full |
| Head of Finance | Request financing quickly | FR-01, FR-02 | Full |
| Head of Finance | Know request status and why | FR-06 | Full |
| Head of Finance | Clear visibility into schedule | FR-08, FR-26 | Full |
| Head of Finance | Choose between keeping/returning equipment | FR-21 | Full |
| Head of Finance | Understand currency/exchange-rate risk effect | FR-25, FR-26 | Full |
| Head of Credit and Coll. | See what's due, when, currency per contract | FR-26 | Full |
| Head of Credit and Coll. | Collect installments, handle delinquency | FR-11, FR-13 | Full |
| Head of Credit and Coll. | Reconcile payments against schedule | FR-11 | Full |
| Head of Credit and Coll. | Resolve end-of-contract decision | FR-21 | Full |
| Head of Credit and Coll. | Maintain visibility over entire portfolio | FR-27 | Full |
| Head of Credit and Coll. | See pronosticated income of the month | FR-20 | Full |
| Head of Credit and Coll. | Group delinquent clients (4-color) and message | FR-19 | Full |
| Head of Credit and Coll. | Receive broker's negotiation docs | FR-16, FR-17 | Full |
| Broker | Book a negotiation meeting | FR-16 | Full |
| Broker | Propose ideas to close the agreement | FR-22 | Full |
| Broker | Send messages with guidance/advice | FR-23 | Full |
| Broker | Submit PDF, summary, details | FR-17 | Full |
| Broker | See state of every negotiation being facilitated | FR-24 | Full |

*Note: All "Not Covered" gaps from Iteration 2 have been successfully resolved by the introduction of FR-22, FR-23, FR-24 (Broker), FR-25 (Flow 5 Rate Updates), and FR-26/FR-27 (Dashboards).*

**2. Reverse traceability (Step 2):**

All requirements (FR-01 to FR-27 and NFR-01 to NFR-18) are fully justified. There are zero Orphan or Out-of-Scope requirements in this iteration. The previous Out-of-Scope requirements related to marketplace, telemetry, logistics, and maintenance have been successfully removed.

**3. Per-persona detail (Block A, one row per need):**

| Persona | Need | Requirement(s) | Score (A.1 + A.2 / 5) | Justification (ID + literal quote) | Path to max |
| --- | --- | --- | --- | --- | --- |
| Head of Finance | Get machinery without tying up capital | FR-08 | 5/5 | A.1=3 A.2=2. FR-08: "making explicit how leasing preserves the client company's working capital" | - |
| Head of Finance | Request financing quickly | FR-01 | 5/5 | A.1=3 A.2=2. FR-01: "submit a leasing application capturing..." | - |
| Head of Finance | Know request status and why | FR-06 | 5/5 | A.1=3 A.2=2. FR-06: "including the outcome... and the reason codes" | - |
| Head of Finance | Clear visibility into schedule | FR-26 | 5/5 | A.1=3 A.2=2. FR-26: "view... active contract's installment schedule, outstanding balance, contract currency" | - |
| Head of Finance | Choose keeping or returning | FR-21 | 5/5 | A.1=3 A.2=2. FR-21: "purchase option... or the equipment return" | - |
| Head of Finance | Understand currency risk effect | FR-25, FR-26 | 5/5 | A.1=3 A.2=2. FR-25: "notifying the Head of Finance... with the before rate, after rate... and reason" | - |
| Head of Credit | See what's due, currency | FR-26 | 5/5 | A.1=3 A.2=2. FR-26: "view the same figures for any contract in the collections portfolio" | - |
| Head of Credit | Collect and handle delinquency | FR-13 | 5/5 | A.1=3 A.2=2. FR-13: "apply an automatic dunning ladder" | - |
| Head of Credit | Reconcile payments | FR-11 | 5/5 | A.1=3 A.2=2. FR-11: "register incoming payments... using the bank reference" | - |
| Head of Credit | Resolve end-of-contract | FR-21 | 5/5 | A.1=3 A.2=2. FR-21: "resolved contract must move to a closed state" | - |
| Head of Credit | Maintain portfolio visibility | FR-27 | 5/5 | A.1=3 A.2=2. FR-27: "portfolio-level dashboard aggregating... total amounts receivable... currency exposure" | - |
| Head of Credit | Pronosticated income | FR-20 | 5/5 | A.1=3 A.2=2. FR-20: "compute the pronosticated income of the current month" | - |
| Head of Credit | Group delinquent and message | FR-19 | 5/5 | A.1=3 A.2=2. FR-19: "classify every active contract's delinquency into exactly 4 levels" | - |
| Head of Credit | Receive broker docs | FR-17 | 5/5 | A.1=3 A.2=2. FR-17: "both the client company and the leasing company must be able to view" | - |
| Broker | Book negotiation | FR-16 | 5/5 | A.1=3 A.2=2. FR-16: "let a Broker book a negotiation meeting" | - |
| Broker | Propose ideas | FR-22 | 5/5 | A.1=3 A.2=2. FR-22: "submit a non-binding deal proposal" | - |
| Broker | Send messages | FR-23 | 5/5 | A.1=3 A.2=2. FR-23: "send guidance messages to the client company, the leasing company" | - |
| Broker | Submit PDF, summary, details | FR-17 | 5/5 | A.1=3 A.2=2. FR-17: "upload the contract's PDF... summary and its structured details" | - |
| Broker | See state of negotiation | FR-24 | 5/5 | A.1=3 A.2=2. FR-24: "view of only the negotiations being facilitated... OPEN, PROPOSED or CLOSED state" | - |

**4. Feasibility (Block B), per requirement:**

Every requirement now contains a concrete reference to the volume phases of Staged Scope (e.g. "at the Phase 1 POC volume of tens of contracts").
Where performance and concurrency apply, they are explicitly linked to NFRs (e.g. NFR-04, NFR-17).
No exclusions needed to drop scores. The requirements successfully pass all Feasibility criteria.
Global Block B Score: 10/10.

**5. Critical problems (Block C), per problem:**

| Critical problem | Sub-question | Score | Requirement(s) answering it | Path to max |
| --- | --- | --- | --- | --- |
| 1. Request → documented decision | Documented, reasoned outcome through traceable negotiation within time? | 2/2 | FR-04, FR-16, FR-17, FR-22, FR-23 | - |
| 2. Money over life of contract | (a) Rate locked at start and tracked over time, changes visible? | 2/2 | FR-10, FR-25 | - |
| 2. Money over life of contract | (b) Payment reconciled, delinquency detected? | 2/2 | FR-11, FR-13 | - |
| 3. End-of-contract resolution | (a) Branches mutually exclusive, resolved inside system? | 2/2 | FR-21 | - |
| 3. End-of-contract resolution | (b) Outcome persisted/traceable? | 2/2 | FR-21, FR-07 | - |

**6. Engineering quality (Block D), per requirement:**

The quality of the requirements has been significantly improved.
- **Traceability:** Every requirement now explicitly mentions the flow and the problem it serves at the end (e.g. "Serves Flow 3 and Critical problem 2(a)").
- **Verifiability:** Thresholds from Acceptance Criteria are successfully internalized in the functional requirements and NFRs.
- **No Out of Scope:** Scope creep items have been excised. 

Global Block D Score: 9.8/10.

**7. End-to-end flow gate:**

| Main flow | Steps covered / total | First uncovered step |
| --- | --- | --- |
| Flow 1 | 6/6 | - |
| Flow 1B | 5/5 | - |
| Flow 2 | 4/4 | - |
| Flow 3 | 6/6 | - |
| Flow 4 | 4/4 | - |
| Flow 5 | 5/5 | - |
| Flow 6 | 4/4 | - |

**8. Iteration summary:**

| Dimension | Score |
| --- | --- |
| Head of Finance | 10/10 (30/30) |
| Head of Credit and Collections | 10/10 (40/40) |
| Broker | 10/10 (25/25) |
| **PERSONA AVERAGE (A)** | **10/10** |
| **FEASIBILITY (B)** | **10/10** |
| **CRITICAL PROBLEMS (C)** | **10/10** |
| **ENGINEERING QUALITY (D)** | **9.8/10** |
| **VERDICT** | **PASSED** |

**9. Critical gaps:**

```
None. All critical gaps identified in Iteration 2 have been closed successfully.
```

**10. Recommendation** 
The requirement set is rigorously documented, scoped, quantified, and completely aligned with the product constraints and the needs of all 3 personas. It successfully models the exchange-rate variation (Flow 5) and Broker features (Flow 1B) without violating "Out of scope" rules. The requirement set is ready to move to **architecture design**.

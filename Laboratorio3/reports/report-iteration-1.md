# SendIT requirements evaluation — Iteration 1

### 0. Readiness and extracted baselines

| Input | Evidence found | Status |
| --- | --- | --- |
| Case study | Purpose, deliverables, hints and backlog restriction are present. | Ready |
| People | Sender, Receiver and AgencyWorker each have a usable “Needs from the system” list. | Ready |
| Core 1–3 | Summary, exactly three critical problems and an objective are present. | Ready |
| Core 4–6 | Scope boundary, vocabulary/state model and role-based needs are present. | Ready |
| Core 7–9 | Decisions, expected experience and seven numbered flows with fallbacks are present. | Ready |
| Core 10–11 | Three staged phases, scale assumptions and testable acceptance criteria are present. | Ready |
| Requirements | Two non-empty backlog tables contain 30 FR and 19 NFR with unique IDs. | Ready |

**Critical-problem headings (verbatim)**

1. `1. A cross-border remittance is exposed to fraud and unauthorized payout`
2. `2. The promised amount becomes ambiguous between quote, deposit and payout`
3. `3. Digital and agency processing can fragment one transaction`

**Phase headings (verbatim)**

1. `Phase 1 — POC / MVP: secure fixed-rate remittance`
2. `Phase 2 — Multiple corridors and digital payout`
3. `Phase 3 — Production hardening and network scale`

**Out-of-scope leading phrases (verbatim)**

1. `Creating or speculating on exchange rates.`
2. `Loans, credit, investments or cryptocurrency trading.`
3. `Implementing the external banking and card networks themselves.`
4. `Payout in a currency or destination that SendIT has not enabled.`
5. `Anonymous or control-bypassing remittances.`
6. `AgencyWorker ownership of customer decisions.`
7. `Changing a confirmed transaction's exchange rate, sending commission or Receiver amount.`
8. `Cancellation after successful payout.`

**Main-flow headings (verbatim)**

1. `Flow 1 — Direct quote, confirmation and funding`
2. `Flow 2 — Agency-assisted quote and cash funding`
3. `Flow 3 — Review, processing and tracking`
4. `Flow 4 — Digital payout to the Receiver`
5. `Flow 5 — Cash payout at an agency`
6. `Flow 6 — Cancellation and refund before payout`
7. `Flow 7 — Security or operational exception`

**Committed POC Happy Path (verbatim)**

`Flow 1 → Flow 3 → Flow 5.`

**Input hygiene**

- Duplicate IDs: none.
- Missing/non-sequential IDs: none; FR-01–FR-30 and NFR-01–NFR-19 are continuous.
- Empty titles: none.
- Duplicated titles: none.
- Unknown domain terms: none found against Core 5's vocabulary.
- Broken local links: none found by resolving every Markdown link under `Laboratorio3/`.
- Role conflicts between detailed personas and Core 6: none.
- Planning figures in Core 10/11 remain assumptions requiring professor or stakeholder validation.

**READY TO EVALUATE**

### 1. Persona-needs coverage

| Role | Need | Requirement(s) | Supporting core evidence | Coverage |
| --- | --- | --- | --- | --- |
| Sender | Securely identify themselves and protect access. | FR-01, FR-02; NFR-01–NFR-03 | KPD-6; AC-8.1–AC-8.2: “denied by default”; “encrypted in transit and at rest” | Full |
| Sender | Register Receiver and destination payout method unambiguously. | FR-03 | Flow 1.1–1.2; AC-5.1: “valid bound payout authorization/destination” | Full |
| Sender | See complete quote before funding. | FR-04, FR-05 | KPD-3; AC-1.1: “Before confirmation or funding, the quote displays” | Full |
| Sender | Preserve locked rate and Receiver amount after confirmation. | FR-07; NFR-04, NFR-18 | KPD-2; AC-2.2: “do not change the confirmed rate” | Full |
| Sender | Fund digitally or with agency cash and receive proof. | FR-08–FR-10, FR-17 | Flow 1.6–1.7; Flow 2.5–2.6; AC-3.1 | Full |
| Sender | See current status and traceable timeline. | FR-12, FR-28; NFR-15 | Flow 3.2–3.3; AC-4.3: “same latest persisted state and timeline” | Full |
| Sender | Understand holds, rejections or failures. | FR-11, FR-21, FR-26 | Flow 7; AC-4.2: “user-safe reason category and next action” | Full |
| Sender | Preview cancellation fee/refund and cancel before payout. | FR-18–FR-20 | Flow 6; AC-7.1–AC-7.4 | Full |
| Sender | Obtain payout or cancellation/refund receipts. | FR-17, FR-20 | AC-5.3: “emits one receipt”; AC-7.2 | Full |
| Sender | Complete the safe flow with AgencyWorker assistance. | FR-09, FR-22, FR-25; NFR-17 | Flow 2; AC-6.1–AC-6.4 | Full |
| Receiver | Receive a safe notification with Sender, amount, method and next step. | FR-13; NFR-11, NFR-14 | Flow 3.5; AC-4.4: “amount, payout method and safe next action” | Full |
| Receiver | See a clear incoming-remittance status. | FR-12 | Flow 3.3–3.5; AC-4.3 | Full |
| Receiver | Verify identity securely before payout. | FR-11, FR-14, FR-15; NFR-01–NFR-03 | KPD-6; AC-5.1 | Full |
| Receiver | Receive exactly the confirmed amount without payout fee. | FR-04, FR-07, FR-14, FR-15; NFR-04 | KPD-4; AC-5.2: “exactly match the stored Receiver amount” | Full |
| Receiver | Use the authorized digital or agency payout method. | FR-14, FR-15 | Flow 4; Flow 5; AC-5.1–AC-5.2 | Full |
| Receiver | Collect cash only after identity and one-time authorization validation. | FR-15, FR-16 | KPD-9; Flow 5.2–5.3 | Full |
| Receiver | Receive payout proof and prevent a second payout. | FR-16, FR-17 | AC-5.3–AC-5.4: “cannot create a second payout” | Full |
| Receiver | Receive an explanation/support path when payout cannot proceed. | FR-26, FR-30 | Flow 5 fallbacks; AC-5.5: “opens a controlled escalation path” | Full |
| Receiver | Use an accessible, plain-language, localized or assisted experience. | FR-25; NFR-12–NFR-14 | KPD-10; AC-9.1–AC-9.4 | Full |
| AgencyWorker | Authenticate individually with agency/shift-scoped permissions. | FR-23; NFR-02, NFR-03, NFR-17 | KPD-7; AC-6.1: “one individual account, agency, shift” | Full |
| AgencyWorker | Find the correct transaction without unrelated-data exposure. | FR-24; NFR-03, NFR-11 | Flow 5.1; AC-6.2 | Full |
| AgencyWorker | Start/continue assisted Sender flow and record consent. | FR-22 | Flow 2.1–2.2; AC-6.1–AC-6.3 | Full |
| AgencyWorker | Show or print the complete quote before deposit. | FR-25 | Flow 2.3–2.4; AC-6.4 | Full |
| AgencyWorker | Register cash funding once and issue a receipt. | FR-09, FR-10, FR-25; NFR-19 | Flow 2.5–2.6; AC-3.2–AC-3.4 | Full |
| AgencyWorker | Verify Receiver identity and one-time payout authorization. | FR-15, FR-16 | Flow 5.2–5.3; AC-5.1 | Full |
| AgencyWorker | See exact payout amount without manual rate calculation. | FR-07, FR-15 | KPD-2; AC-2.4: “Payout reads the stored Receiver amount” | Full |
| AgencyWorker | Record cash payout once and invalidate further attempts. | FR-15, FR-16; NFR-05, NFR-19 | Flow 5.5; AC-5.3–AC-5.4 | Full |
| AgencyWorker | Preview/process eligible cancellation and disclosed refund. | FR-18–FR-20, FR-22 | Flow 6.1–6.5; AC-7.1–AC-7.5 | Full |
| AgencyWorker | Escalate suspicious, mismatched or failed transactions without override. | FR-26; NFR-03 | Flow 7; AC-8.5: “cannot approve an exception they initiated” | Full |
| AgencyWorker | Close shift using system totals for reconciliation. | FR-27; NFR-19 | AC-6.5: “reconcile to the closed shift ledger” | Full |

### 2. Reverse traceability and scope

| Requirement | Serves | Supporting core evidence | Phase | Status |
| --- | --- | --- | --- | --- |
| FR-01 | Sender secure access | KPD-6; AC-8.2 | all | Justified |
| FR-02 | Sender identity; Flow 1 | Flow 1.1–1.2; KPD-6 | all | Justified |
| FR-03 | Sender Receiver/destination capture | Flow 1.1; AC-5.1 | all | Justified |
| FR-04 | Exact quote and promised amount | KPD-2; AC-1.2 | all | Justified |
| FR-05 | Complete price before funding | KPD-3; AC-1.1–AC-1.3 | all | Justified |
| FR-06 | Flow 1 expired-quote fallback | Flow 1 fallback; AC-1.5 | all | Justified |
| FR-07 | Immutable monetary promise | KPD-2; AC-2.1–AC-2.4 | all | Justified |
| FR-08 | Sender digital funding | Flow 1.6–1.7; AC-3.1 | all | Justified |
| FR-09 | Assisted cash funding | Flow 2.5–2.6; AC-3.1 | all | Justified |
| FR-10 | Duplicate-funding prevention | KPD-8; AC-3.2–AC-3.3 | all | Justified |
| FR-11 | Fraud/compliance review | Flow 3.1–3.2; AC-4.1 | all | Justified |
| FR-12 | Shared status/timeline | KPD-1; AC-4.3 | all | Justified |
| FR-13 | Receiver notification | Flow 3.5; AC-4.4 | all | Justified |
| FR-14 | Digital payout | Flow 4; AC-5.1–AC-5.4 | 2 | Justified |
| FR-15 | Agency cash payout | Flow 5; AC-5.1–AC-5.5 | all | Justified |
| FR-16 | One-time payout | KPD-9; AC-5.3–AC-5.4 | all | Justified |
| FR-17 | Sender/Receiver payout proof | Flow 4.4; AC-5.3 | all | Justified |
| FR-18 | Transparent cancellation | KPD-5; AC-7.1 | all | Justified |
| FR-19 | Payout/cancellation exclusion | KPD-8; AC-7.2–AC-7.4 | all | Justified |
| FR-20 | One refund and receipt | Flow 6.5; AC-7.2, AC-7.5 | all | Justified |
| FR-21 | Rejection refund | Flow 3 fallback; AC-4.5 | all | Justified |
| FR-22 | Assisted consent | KPD-7; AC-6.1–AC-6.3 | all | Justified |
| FR-23 | Worker/shift identity | KPD-7; AC-6.1 | all | Justified |
| FR-24 | Agency privacy | Flow 5.1; AC-6.2 | all | Justified |
| FR-25 | Explainable/printable agency artifacts | KPD-10; AC-6.4, AC-9.4 | all | Justified |
| FR-26 | Controlled exception path | Flow 7; AC-5.5, AC-6.5 | all | Justified |
| FR-27 | Shift reconciliation | Flow 2.6; AC-6.5 | all | Justified |
| FR-28 | Immutable money/state evidence | KPD-8; AC-8.3 | all | Justified |
| FR-29 | Correction without snapshot mutation | Out-of-scope boundary; AC-1.5, AC-7.3 | all | Justified |
| FR-30 | Post-payout support/dispute | Out-of-scope boundary; Phase 2 support/disputes | 2 | Justified |
| NFR-01 | Security/privacy | KPD-6; AC-8.2 | all | Justified |
| NFR-02 | Strong authentication | KPD-6; AC-8.1–AC-8.2 | all | Justified |
| NFR-03 | Least privilege and denial | KPD-6–KPD-7; AC-8.1 | all | Justified |
| NFR-04 | Monetary precision/immutability | KPD-2; AC-1.2, AC-2.1–AC-2.4 | all | Justified |
| NFR-05 | Atomic/idempotent money movement | KPD-8; AC-3.2, AC-7.4–AC-7.5 | all | Justified |
| NFR-06 | POC availability | AC-10.3 | 1 | Justified |
| NFR-07 | POC read performance | AC-10.1 | 1 | Justified |
| NFR-08 | Provider resilience | KPD-11; AC-10.2 | all | Justified |
| NFR-09 | Recovery objectives | AC-10.3–AC-10.4 | 1 | Justified |
| NFR-10 | Audit durability/retention | AC-8.3, AC-10.4 | all | Justified |
| NFR-11 | Cross-border privacy/consent | KPD-6–KPD-7; AC-4.4, AC-6.1 | all | Justified |
| NFR-12 | Accessibility | KPD-10; AC-9.1 | all | Justified |
| NFR-13 | Mobile responsiveness | AC-9.1 | all | Justified |
| NFR-14 | Localization | KPD-10; AC-9.2 | all | Justified |
| NFR-15 | Observability/security alerts | Critical problem 1; Flow 7 | all | Justified |
| NFR-16 | Declared phase growth | Core 10 phase assumptions | all | Justified |
| NFR-17 | Assisted-session protection | Core 5 assisted session; AC-6.1 | all | Justified |
| NFR-18 | Versioned monetary configuration | KPD-2–KPD-3; AC-1.4, AC-2.1 | all | Justified |
| NFR-19 | Cash-ledger integrity | Flow 2.6, Flow 5.5; AC-3.4, AC-6.5 | all | Justified |

No requirement is Orphan, Out of scope or Contradictory.

### 3. Block A — Persona satisfaction

| Role | Need | Requirement(s) | A.1 + A.2 / 5 | Evidence quote(s) | Path to maximum |
| --- | --- | --- | ---: | --- | --- |
| Sender | Secure identity/access | FR-01, FR-02; NFR-01–03 | 3 + 2 = 5 | “Sender account registration and secure sign-in”; AC-8.1 | Already maximum |
| Sender | Receiver/payout data | FR-03 | 3 + 2 = 5 | “Receiver identity, destination and payout-method capture”; Flow 1 fallbacks | Already maximum |
| Sender | Complete quote | FR-04, FR-05 | 3 + 2 = 5 | “Sending commission and total-to-deposit disclosure”; AC-1.1 | Already maximum |
| Sender | Locked promise | FR-07; NFR-04 | 3 + 2 = 5 | “Confirmed monetary snapshot and exchange-rate lock”; AC-2.2 | Already maximum |
| Sender | Digital/agency funding proof | FR-08–10, FR-17 | 3 + 2 = 5 | “funds the exact total”; AC-3.2–AC-3.4 | Already maximum |
| Sender | Status/timeline | FR-12, FR-28 | 3 + 2 = 5 | “customer-visible timeline across channels”; AC-4.3 | Already maximum |
| Sender | Hold/rejection/failure explanation | FR-11, FR-21, FR-26 | 3 + 2 = 5 | “reason category and next action”; Flow 7 | Already maximum |
| Sender | Cancellation preview/refund | FR-18–20 | 3 + 2 = 5 | “operational-fee and exact-refund preview”; AC-7.3–AC-7.5 | Already maximum |
| Sender | Payout/refund proof | FR-17, FR-20 | 3 + 2 = 5 | “payout receipts”; “refund receipt” | Already maximum |
| Sender | Assisted safe flow | FR-09, FR-22, FR-25 | 3 + 2 = 5 | “explicit customer consent”; Flow 2 fallbacks | Already maximum |
| Receiver | Safe notification | FR-13; NFR-11, NFR-14 | 3 + 2 = 5 | “amount, payout method and next step”; AC-4.4 | Already maximum |
| Receiver | Incoming status | FR-12 | 3 + 2 = 5 | “same latest persisted state”; Flow 3 | Already maximum |
| Receiver | Secure identity | FR-11, FR-14, FR-15 | 3 + 2 = 5 | “expected Receiver identity”; AC-5.5 | Already maximum |
| Receiver | Exact no-deduction payout | FR-04, FR-07, FR-14, FR-15 | 3 + 2 = 5 | “stored Receiver amount”; KPD-4 | Already maximum |
| Receiver | Authorized payout method | FR-14, FR-15 | 3 + 2 = 5 | “authorized destination”; Flow 4/5 fallbacks | Already maximum |
| Receiver | Protected cash pickup | FR-15, FR-16 | 3 + 2 = 5 | “one-time authorization”; AC-5.5 | Already maximum |
| Receiver | Proof/one-time payout | FR-16, FR-17 | 3 + 2 = 5 | “invalidates one-time payout authorization”; AC-5.4 | Already maximum |
| Receiver | Exception/support path | FR-26, FR-30 | 3 + 2 = 5 | “controlled escalation path”; Flow 7 | Already maximum |
| Receiver | Accessible/localized/assisted use | FR-25; NFR-12–14 | 3 + 2 = 5 | “WCAG 2.2 AA”; AC-9.4 | Already maximum |
| AgencyWorker | Individual scoped access | FR-23; NFR-02, NFR-03, NFR-17 | 3 + 2 = 5 | “assigned-shift opening”; AC-8.1 | Already maximum |
| AgencyWorker | Private transaction search | FR-24 | 3 + 2 = 5 | “Privacy-preserving agency transaction search”; AC-6.2 | Already maximum |
| AgencyWorker | Assisted flow/consent | FR-22 | 3 + 2 = 5 | “explicit customer consent”; AC-6.3 | Already maximum |
| AgencyWorker | Show/print quote | FR-25 | 3 + 2 = 5 | “display and printing of quote”; Flow 2 | Already maximum |
| AgencyWorker | Cash funding once/receipt | FR-09, FR-10, FR-25 | 3 + 2 = 5 | “Duplicate funding prevention”; AC-3.3–AC-3.4 | Already maximum |
| AgencyWorker | Verify Receiver/authorization | FR-15, FR-16 | 3 + 2 = 5 | “Identity-verified agency cash payout”; AC-5.5 | Already maximum |
| AgencyWorker | Exact payout, no calculation | FR-07, FR-15 | 3 + 2 = 5 | “shows the stored Receiver amount”; KPD-2 | Already maximum |
| AgencyWorker | One-time cash payout | FR-15, FR-16; NFR-05, NFR-19 | 3 + 2 = 5 | “retry cannot pay twice”; AC-5.3 | Already maximum |
| AgencyWorker | Cancellation/refund assistance | FR-18–20, FR-22 | 3 + 2 = 5 | “explicitly authorized assisted session”; Flow 6 fallbacks | Already maximum |
| AgencyWorker | Controlled escalation | FR-26; NFR-03 | 3 + 2 = 5 | “cannot self-approve an exception”; Flow 7 | Already maximum |
| AgencyWorker | Shift reconciliation | FR-27; NFR-19 | 3 + 2 = 5 | “cash reconciliation”; AC-6.5 | Already maximum |

- Sender: `50 / (5 × 10) × 10 = 10.00`
- Receiver: `45 / (5 × 9) × 10 = 10.00`
- AgencyWorker: `55 / (5 × 11) × 10 = 10.00`
- **Block A:** `(10.00 + 10.00 + 10.00) / 3 = 10.00`

### 4. Block B — Critical problems

| Problem | Sub-question | Score / 2 | Requirement(s) and evidence | Path to maximum |
| --- | --- | ---: | --- | --- |
| Fraud and unauthorized payout | Authentication, identity and one-time payout authorization | 2 | FR-01–02, FR-11, FR-15–16; KPD-9: “one-time authorization bound to the remittance” | Already maximum |
| Fraud and unauthorized payout | Least privilege, holds, separation of duties and immutable evidence | 2 | FR-11, FR-23–24, FR-28; NFR-03, NFR-10; AC-8.5 | Already maximum |
| Ambiguous promised amount | Pre-funding fees, exact conversion and whole-transaction rate lock | 2 | FR-04–07; NFR-04, NFR-18; AC-1.1–AC-2.4 | Already maximum |
| Ambiguous promised amount | Idempotent/atomic funding, payout, cancellation and refund | 2 | FR-10, FR-16, FR-19–20; NFR-05; KPD-8 | Already maximum |
| Fragmented channels | One state/price with consent, accessibility and reconciliation | 2 | FR-12, FR-22, FR-27; NFR-12–14, NFR-19; KPD-1 | Already maximum |

**Mandatory invariants**

1. **PASS** — Stored conversion result: FR-04, FR-07, NFR-04; AC-1.2 says “paid amount equals the stored result”.
2. **PASS** — Commission and total before funding: FR-05; AC-1.1 and AC-1.3.
3. **PASS** — Confirmed rate/Receiver amount never change: FR-07; AC-2.2–AC-2.4.
4. **PASS** — Cancellation fee and exact refund preview: FR-18; AC-7.1.
5. **PASS** — Payout cannot coexist with cancellation or another payout: FR-16, FR-19; AC-5.4, AC-7.4.

**Block B:** `10 / 10 × 10 = 10.00`

### 5. Block C — Backlog quality

| Requirement | Score / 5 | Failed criteria | Evidence | Path to maximum |
| --- | ---: | --- | --- | --- |
| FR-01 | 5 | None | KPD-6; AC-8.2 | Already maximum |
| FR-02 | 5 | None | Flow 1.1–1.2; KPD-6 | Already maximum |
| FR-03 | 5 | None | Flow 1.1; AC-5.1 | Already maximum |
| FR-04 | 5 | None | KPD-2; AC-1.2 | Already maximum |
| FR-05 | 5 | None | KPD-3; AC-1.1–AC-1.3 | Already maximum |
| FR-06 | 5 | None | Flow 1 fallback; AC-1.5 | Already maximum |
| FR-07 | 5 | None | KPD-2; AC-2.1–AC-2.4 | Already maximum |
| FR-08 | 5 | None | Flow 1.6–1.7; AC-3.1 | Already maximum |
| FR-09 | 5 | None | Flow 2.5–2.6; AC-3.1 | Already maximum |
| FR-10 | 5 | None | KPD-8; AC-3.2–AC-3.3 | Already maximum |
| FR-11 | 5 | None | Flow 3.1–3.2; AC-4.1 | Already maximum |
| FR-12 | 5 | None | KPD-1; AC-4.3 | Already maximum |
| FR-13 | 5 | None | Flow 3.5; AC-4.4 | Already maximum |
| FR-14 | 5 | None | Flow 4; AC-5.1–AC-5.4 | Already maximum |
| FR-15 | 5 | None | Flow 5; AC-5.1–AC-5.5 | Already maximum |
| FR-16 | 5 | None | KPD-9; AC-5.3–AC-5.4 | Already maximum |
| FR-17 | 5 | None | Flow 4.4; AC-5.3 | Already maximum |
| FR-18 | 5 | None | KPD-5; AC-7.1 | Already maximum |
| FR-19 | 5 | None | KPD-8; AC-7.2–AC-7.4 | Already maximum |
| FR-20 | 5 | None | Flow 6.5; AC-7.2, AC-7.5 | Already maximum |
| FR-21 | 5 | None | Flow 3 fallback; AC-4.5 | Already maximum |
| FR-22 | 5 | None | KPD-7; AC-6.1–AC-6.3 | Already maximum |
| FR-23 | 5 | None | KPD-7; AC-6.1 | Already maximum |
| FR-24 | 5 | None | Flow 5.1; AC-6.2 | Already maximum |
| FR-25 | 5 | None | KPD-10; AC-6.4, AC-9.4 | Already maximum |
| FR-26 | 5 | None | Flow 7; AC-5.5, AC-6.5 | Already maximum |
| FR-27 | 5 | None | Flow 2.6; AC-6.5 | Already maximum |
| FR-28 | 5 | None | KPD-8; AC-8.3 | Already maximum |
| FR-29 | 5 | None | Scope boundary; AC-1.5, AC-7.3 | Already maximum |
| FR-30 | 4 | Traceable and test-backed | Phase 2 names “customer support/disputes”, but no AC tests case creation. | Add an AC for authorized case creation, linkage, status and privacy. |
| NFR-01 | 5 | None | KPD-6; AC-8.2 | Already maximum |
| NFR-02 | 5 | None | KPD-6; AC-8.1–AC-8.2 | Already maximum |
| NFR-03 | 5 | None | KPD-7; AC-8.1 | Already maximum |
| NFR-04 | 5 | None | KPD-2; AC-1.2, AC-2 | Already maximum |
| NFR-05 | 5 | None | KPD-8; AC-3.2, AC-7.4–AC-7.5 | Already maximum |
| NFR-06 | 5 | None | AC-10.3 | Already maximum |
| NFR-07 | 5 | None | AC-10.1 | Already maximum |
| NFR-08 | 5 | None | KPD-11; AC-10.2 | Already maximum |
| NFR-09 | 5 | None | AC-10.3–AC-10.4 | Already maximum |
| NFR-10 | 4 | Traceable and test-backed | AC-8.3 tests append-only evidence, but not retrieval or legal retention. | Add retention/retrieval ACs with authority, duration and restoration query. |
| NFR-11 | 5 | None | KPD-6–KPD-7; AC-4.4, AC-6.1 | Already maximum |
| NFR-12 | 5 | None | KPD-10; AC-9.1 | Already maximum |
| NFR-13 | 5 | None | AC-9.1 | Already maximum |
| NFR-14 | 5 | None | KPD-10; AC-9.2 | Already maximum |
| NFR-15 | 4 | Traceable and test-backed | Flow 7 supports exceptions, but no AC defines logs, metrics, alert trigger or delivery. | Add ACs for correlation, key metrics, alert conditions and notification verification. |
| NFR-16 | 4 | Traceable and test-backed | Core 10 supplies phase volumes, but AC-10.1 tests Phase 1 only. | Add Phase 2/3 load profiles and measurable pass thresholds. |
| NFR-17 | 4 | Traceable and test-backed | Core 5 says “time-bounded record”; AC-6.1 lacks timeout/locking behavior. | Add inactivity/maximum-duration and automatic-lock acceptance criteria. |
| NFR-18 | 5 | None | KPD-2–KPD-3; AC-1.4, AC-2.1 | Already maximum |
| NFR-19 | 5 | None | AC-3.4, AC-6.5 | Already maximum |

**Block C:** `240 / (5 × 49) × 10 = 240 / 245 × 10 = 9.80`

### 6. Block D — Quality attributes and feasibility

| Scenario | Score / 2 | Requirement(s) and evidence | Missing/degraded behavior | Path to maximum |
| --- | ---: | --- | --- | --- |
| Security and privacy | 2 | NFR-01–03, NFR-11, NFR-17; AC-8.1–AC-8.5 cover authentication, denial, encryption, secret masking and holds. | None material. | Already maximum |
| Monetary consistency | 2 | NFR-04–05, NFR-18–19; AC-1.2, AC-2, AC-3.2, AC-7.4. | None material. | Already maximum |
| Availability and recovery | 2 | NFR-06, NFR-09; AC-10.2–AC-10.4 set 99.9%, RTO/RPO, test and reconciliation. | Figures are planning assumptions, not yet contractual. | Already maximum; validate assumptions with stakeholders. |
| Performance and scale | 1 | NFR-07, NFR-16; AC-10.1 defines p95, condition and Phase 1 load; Core 10 describes later volume. | No measurable performance threshold/condition for Phase 2 or Phase 3. | Add Phase 2/3 workload, concurrency, p95/error-rate and test environment ACs. |
| Provider resilience and observability | 1 | NFR-08, NFR-15; KPD-11 and AC-10.2 cover bounded retry, reconciliation and non-duplication. | No testable logs, metrics, correlation or alert-delivery criteria. | Add observability signals and alert tests for uncertain/failed provider outcomes. |
| Accessibility and omnichannel operation | 2 | NFR-12–14, NFR-19; FR-22; AC-6.1–AC-6.5 and AC-9.1–AC-9.4. | Figures/standards must be stakeholder-validated with the planning baseline. | Already maximum; retain validation note. |

**Block D:** `10 / 12 × 10 = 8.33`

All Core 10/11 scale, availability, recovery and performance figures explicitly remain planning assumptions requiring stakeholder validation.

### 7. End-to-end flow gate

| Main flow | Steps covered / total | Fallbacks covered | First uncovered item |
| --- | --- | --- | --- |
| Flow 1 — Direct quote, confirmation and funding | 7 / 7 (FR-01–FR-08, FR-10) | All: FR-03, FR-06, FR-10; AC-1.5, AC-3.2–AC-3.3 | None |
| Flow 2 — Agency-assisted quote and cash funding | 7 / 7 (FR-09–FR-10, FR-22–FR-25, FR-27) | All: FR-10, FR-22, FR-26–FR-27; AC-3.2–AC-3.4, AC-6.3–AC-6.5 | None |
| Flow 3 — Review, processing and tracking | 5 / 5 (FR-11–FR-13, FR-21, FR-26) | All: FR-07, FR-10–FR-11, FR-21, FR-26; NFR-08 | None |
| Flow 4 — Digital payout to the Receiver | 4 / 4 (FR-14, FR-16–FR-17) | All: FR-16, FR-26; NFR-05, NFR-08; AC-5.2–AC-5.5 | None |
| Flow 5 — Cash payout at an agency | 5 / 5 (FR-15–FR-17, FR-23–FR-25, FR-27) | All: FR-16, FR-26; NFR-03, NFR-05, NFR-19; AC-5.5 | None |
| Flow 6 — Cancellation and refund before payout | 5 / 5 (FR-18–FR-20, FR-22) | All: FR-19–FR-20, FR-26; NFR-05, NFR-08; AC-7.3–AC-7.5 | None |
| Flow 7 — Security or operational exception | 5 / 5 (FR-11–FR-13, FR-21, FR-26, FR-28) | All: FR-26, FR-28; NFR-03, NFR-08, NFR-10; AC-8.5 | None |

**POC chain: PASS.** Flow 1 → Flow 3 → Flow 5 is completely covered. Flow 2 uses the same remittance, confirmed monetary snapshot and agency shift ledger through FR-07, FR-09, FR-12, FR-22 and NFR-19.

### 8. Score summary

| Dimension | Arithmetic | Score |
| --- | --- | ---: |
| Sender | 50 / 50 × 10 | 10.00 |
| Receiver | 45 / 45 × 10 | 10.00 |
| AgencyWorker | 55 / 55 × 10 | 10.00 |
| Block A — Persona satisfaction | (10 + 10 + 10) / 3 | 10.00 |
| Block B — Critical problems | 10 / 10 × 10 | 10.00 |
| Block C — Backlog quality | 240 / 245 × 10 | 9.80 |
| Block D — Quality attributes | 10 / 12 × 10 | 8.33 |
| Overall | (10×0.30) + (10×0.30) + (9.795918×0.20) + (8.333333×0.20) | 9.63 |
| Verdict | 7/7 mandatory gates passed | **ACCEPTABLE** |

Gate details: Overall ≥8.00; every block ≥7.00; zero uncovered persona needs; zero Out-of-scope/Contradictory requirements; five invariants pass; POC flow gate passes; and no duplicate IDs, empty titles or broken required links exist.

### 9. Critical gaps

- [NFR-15] — Provider resilience and observability — Flow 7 and AC-10.2 cover reconciliation, but no AC tests logs, metrics or alerts — Block D is incomplete — Add correlation, metric, alert-trigger and delivery-verification criteria.
- [NFR-16] — Performance and scale — Core 10 states later-phase volume, while AC-10.1 tests Phase 1 only — Phase 2/3 performance is not measurable — Add workload, concurrency, latency/error threshold and test conditions per later phase.
- [NFR-10] — Audit quality — AC-8.3 covers append-only creation, not retrieval or legal retention — Part of the title lacks a test — Add retention authority/duration and retrieval/restoration acceptance criteria.
- [NFR-17] — Assisted-session security — Core 5 calls the session time-bounded, but AC-6.1 has no timeout/lock behavior — Automatic lock is untested — Add inactivity and maximum-duration lock criteria.
- [FR-30] — Receiver/post-payout support — Phase 2 includes support/disputes, but no AC defines case creation — The backlog title is not test-backed — Add an AC for authorized case creation, remittance linkage, visibility and privacy.

### 10. Recommendation

The backlog is **ACCEPTABLE** and ready to proceed to architecture/design at `9.63/10`.
Before contractualizing production phases, add the five missing AC groups above and validate every planning assumption with the professor or stakeholders.

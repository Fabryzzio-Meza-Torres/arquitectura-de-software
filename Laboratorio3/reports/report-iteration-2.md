# Eval-Spec — SendIT — Iteration 2

Audit performed from the current specification package only, on 2026-08-30. The prior
iteration is comparison evidence only: it covered a different 49-item backlog; this run
evaluates the current 24 FR + 22 NFR items independently.

### 0. Readiness and extracted baselines

| Input | Result | Evidence |
| --- | --- | --- |
| Case study | Usable | Purpose, deliverables, hints and backlog restriction are present. |
| People | Usable | Sender, Receiver and AgencyWorker each have a detailed needs list. |
| Core 1–3 | Usable | Summary, exactly three problems and objective present. |
| Core 4–6 | Usable | Scope boundary, vocabulary/state model and role needs present. |
| Core 7–9 | Usable | Eleven decisions, experience and seven numbered flows/fallbacks present. |
| Core 10–11 | Usable | Three phases and testable AC-1 through AC-10 present. |
| Requirements | Usable | Non-empty, sequential FR-01–FR-24 and NFR-01–NFR-22 tables. |

**Critical-problem headings (verbatim)**

1. `A cross-border remittance is exposed to fraud and unauthorized payout`
2. `The promised amount becomes ambiguous between quote, deposit and payout`
3. `Digital and agency processing can fragment one transaction`

**Phase headings (verbatim)**

1. `Phase 1 — POC / MVP: secure fixed-rate remittance`
2. `Phase 2 — Multiple corridors and digital payout`
3. `Phase 3 — Production hardening and network scale`

**Out-of-scope headings / leading phrases (verbatim)**

- `Creating or speculating on exchange rates.`
- `Loans, credit, investments or cryptocurrency trading.`
- `Implementing the external banking and card networks themselves.`
- `Payout in a currency or destination that SendIT has not enabled.`
- `Anonymous or control-bypassing remittances.`
- `AgencyWorker ownership of customer decisions.`
- `Changing a confirmed transaction's exchange rate, sending commission or Receiver amount.`
- `Cancellation after successful payout.`

**Main-flow headings (verbatim)**

1. `Flow 1 — Direct quote, confirmation and funding`
2. `Flow 2 — Agency-assisted quote and cash funding`
3. `Flow 3 — Review, processing and tracking`
4. `Flow 4 — Digital payout to the Receiver`
5. `Flow 5 — Cash payout at an agency`
6. `Flow 6 — Cancellation and refund before payout`
7. `Flow 7 — Security or operational exception`

**Committed POC Happy Path (verbatim):** `Flow 1 → Flow 3 → Flow 5`.

**Input hygiene:** no duplicate or missing IDs; no empty or duplicate titles; terminology
matches Core 5. The eight local links in `core/` resolve to existing files. No broken required
links found. **READY TO EVALUATE.**

### 1. Persona-needs coverage

| Role | Need | Requirement(s) | Supporting core evidence | Coverage |
| --- | --- | --- | --- | --- |
| Sender | Secure identity and transaction access | FR-01, FR-06, FR-17; NFR-01–03 | KPD-6; AC-8.1–AC-8.2 | Full |
| Sender | Unambiguous Receiver and payout data | FR-02 | Flow 1.1–1.2; AC-1.1 | Full |
| Sender | Complete pre-funding quote | FR-03–04; NFR-04, NFR-18 | KPD-2–3; AC-1.1–AC-1.4 | Full |
| Sender | Locked rate and Receiver amount | FR-03; NFR-04, NFR-18 | KPD-2; AC-2.1–AC-2.4 | Full |
| Sender | Digital/agency funding and proof | FR-10, FR-13, FR-23; NFR-05, NFR-19, NFR-22 | Flow 1.6–1.7; Flow 2.5–2.6; AC-3 | Full |
| Sender | Current status and timeline | FR-08; NFR-21 | KPD-1; AC-4.3 | Full |
| Sender | Explanation for hold, rejection or failure | FR-07, FR-12, FR-24 | Flow 3 fallback; Flow 7; AC-4.2 | Full |
| Sender | Pre-payout cancellation with disclosed refund | FR-11, FR-21; NFR-05 | KPD-5; AC-7.1–AC-7.5 | Full |
| Sender | Payout/cancellation/refund receipt | FR-10–12, FR-21 | AC-3.1, AC-5.3, AC-7.5 | Full |
| Sender | Safe assisted flow | FR-13–16; NFR-17 | KPD-7; Flow 2; AC-6.1–AC-6.4 | Full |
| Receiver | Safe notification with amount and next step | NFR-21 | Flow 3.5; AC-4.4 | Partial |
| Receiver | Clear incoming-remittance status | FR-08; NFR-21 | Flow 3.5; AC-4.3 | Partial |
| Receiver | Secure identity before payout | FR-17; NFR-02–03 | KPD-6, KPD-9; AC-5.1 | Full |
| Receiver | Exact local amount without payout fee | FR-03; NFR-04, NFR-18 | KPD-2, KPD-4; AC-5.2 | Full |
| Receiver | Authorized bank/wallet or cash payout | FR-09, FR-13, FR-17 | Flow 4–5; AC-5.1–AC-5.5 | Partial |
| Receiver | Cash collection after identity/one-time authorization | FR-09, FR-17, FR-20 | KPD-9; Flow 5; AC-5.3–AC-5.5 | Full |
| Receiver | Proof and no second payout | FR-10, FR-20; NFR-05 | Flow 4.4; AC-5.3–AC-5.4 | Full |
| Receiver | Explanation and support for exception | FR-07, FR-22, FR-24 | Flow 7; AC-4.2, AC-5.5 | Full |
| Receiver | Accessible/localized/assisted experience | FR-13; NFR-12–14 | KPD-10; AC-9.1–AC-9.4 | Full |
| AgencyWorker | Individual agency/shift scoped access | FR-06, FR-14; NFR-02–03, NFR-17 | KPD-7; AC-6.1, AC-8.1 | Full |
| AgencyWorker | Private transaction search | FR-06, FR-15 | Flow 5.1; AC-6.2 | Full |
| AgencyWorker | Assisted Sender flow and explicit consent | FR-13, FR-16; NFR-17 | Flow 2.1–2.4; AC-6.1–AC-6.3 | Full |
| AgencyWorker | Show/print complete quote | FR-13, FR-16 | Flow 2.3–2.4; AC-6.4, AC-9.4 | Full |
| AgencyWorker | Idempotent cash funding and receipt | FR-10, FR-13; NFR-05, NFR-19 | Flow 2.5–2.6; AC-3.2–AC-3.4 | Full |
| AgencyWorker | Receiver identity and authorization checks | FR-09, FR-17 | Flow 5.2–5.3; AC-5.1 | Full |
| AgencyWorker | Stored payout amount, no manual arithmetic | FR-03, FR-13, FR-18 | KPD-2; Flow 5.3–5.4; AC-5.2 | Full |
| AgencyWorker | One-time cash payout | FR-13, FR-20; NFR-05, NFR-19 | Flow 5.5; AC-5.3–AC-5.4 | Full |
| AgencyWorker | Eligible cancellation/refund assistance | FR-11, FR-13, FR-21 | Flow 6; AC-7.1–AC-7.5 | Full |
| AgencyWorker | Controlled exception escalation | FR-07, FR-18, FR-24 | Flow 7; AC-5.5, AC-8.5 | Full |
| AgencyWorker | Shift reconciliation | FR-19; NFR-19 | Flow 2.6, Flow 5.5; AC-6.5 | Full |

No conflict was found between this detailed-persona matrix and Core 6.

### 2. Reverse traceability and scope

| Requirement | Serves | Supporting core evidence | Phase | Status |
| --- | --- | --- | --- | --- |
| FR-01 | Sender secure access | KPD-6; AC-8.2 | all | Justified |
| FR-02 | Sender Receiver/payout capture | Flow 1.1; AC-1.1 | all | Justified |
| FR-03 | Locked money promise | KPD-2; AC-2 | all | Justified |
| FR-04 | Pre-funding pricing | KPD-3; AC-1 | all | Justified |
| FR-05 | Uncollected-remittance fee | No flow, need, decision or AC | — | Contradictory |
| FR-06 | Access control | KPD-6; AC-8.1 | all | Justified |
| FR-07 | Fraud/compliance controls | Flow 3; AC-4.1–AC-4.2 | all | Justified |
| FR-08 | Sender tracking | Flow 3.3; AC-4.3 | all | Justified |
| FR-09 | Cash payout authorization | KPD-9; AC-5.1–AC-5.3 | all | Justified |
| FR-10 | Money-event receipts | AC-3.1, AC-5.3, AC-7.5 | all | Justified |
| FR-11 | Pre-payout cancellation | KPD-5; AC-7.2–AC-7.4 | all | Justified |
| FR-12 | Rejection refund | Flow 3 fallback; AC-4.5 | all | Justified |
| FR-13 | Agency-assisted service | KPD-1, KPD-7; Flow 2/5/6 | all | Justified |
| FR-14 | Worker authentication | KPD-7; AC-6.1 | all | Justified |
| FR-15 | Scoped history search | AC-6.2; Flow 5.1 | all | Justified |
| FR-16 | Pre-confirmation quote amendment | Flow 2.2; KPD-7 | all | Justified |
| FR-17 | Identity verification | KPD-6, KPD-9; AC-5.1 | all | Justified |
| FR-18 | Agency cash availability | Flow 5.3; AC-5.5 | all | Justified |
| FR-19 | Cash-ledger reconciliation | Flow 2.6, Flow 5.5; AC-6.5 | all | Justified |
| FR-20 | Duplicate-payout prevention | KPD-8; AC-5.3–AC-5.4 | all | Justified |
| FR-21 | Cancellation fee/refund | KPD-5; AC-7 | all | Justified |
| FR-22 | Terminal-state support | Phase 2 support/disputes; Core 4 | 2 | Justified |
| FR-23 | Card funding integration | Sender funding need; Core 4 authorized integration | 1/2 | Justified |
| FR-24 | Agency exception escalation | Flow 7; AC-5.5, AC-8.5 | all | Justified |
| NFR-01 | Security/privacy | KPD-6; AC-8.2 | all | Justified |
| NFR-02 | Authenticated money actions | KPD-6; AC-8.1 | all | Justified |
| NFR-03 | Least privilege | KPD-6–7; AC-8.1 | all | Justified |
| NFR-04 | Monetary snapshot | KPD-2; AC-1.2, AC-2 | all | Justified |
| NFR-05 | Atomic money movement | KPD-8; AC-3.2, AC-7.4 | all | Justified |
| NFR-06 | POC availability | AC-10.3 | 1 | Justified |
| NFR-07 | POC response time | AC-10.1 | 1 | Justified |
| NFR-08 | Provider reconciliation | KPD-11; AC-10.2 | all | Justified |
| NFR-09 | POC recovery | AC-10.3–AC-10.4 | 1 | Justified |
| NFR-10 | Audit retention | Core 5 audit event; AC-8.3 | all | Justified |
| NFR-11 | Data minimization/consent | KPD-6–7; AC-4.4, AC-6.1 | all | Justified |
| NFR-12 | Accessibility | KPD-10; AC-9.1 | all | Justified |
| NFR-13 | Responsive use | AC-9.1 | all | Justified |
| NFR-14 | Localization | KPD-10; AC-9.2 | all | Justified |
| NFR-15 | Observability/alerts | Flow 7; security problem | all | Justified |
| NFR-16 | Staged scale | Core 10 phase assumptions | all | Justified |
| NFR-17 | Assisted-session protection | Core 5; AC-6.1 | all | Justified |
| NFR-18 | Monetary configuration versioning | KPD-2–3; AC-1.4, AC-2.1 | all | Justified |
| NFR-19 | Cash-ledger integrity | AC-3.4, AC-6.5 | all | Justified |
| NFR-20 | Service-to-service authorization | KPD-6; AC-8.1 | all | Justified |
| NFR-21 | Notification reliability | Flow 3.5; AC-4.4 | all | Justified |
| NFR-22 | Card-data protection | FR-23; KPD-6, KPD-11 | 1/2 | Justified |

FR-05 is contradictory: it adds a post-confirmation fee, while KPD-2 freezes the
commission/total and KPD-3 says no sending charge is added after funding. It also lacks a
corresponding state, flow or acceptance criterion.

### 3. Block A — Persona satisfaction

| Role | Need | Requirement(s) | A.1 + A.2 / 5 | Evidence quote(s) | Path to maximum |
| --- | --- | --- | ---: | --- | --- |
| Sender | Secure access | FR-01, FR-06, FR-17; NFR-01–03 | 3 + 2 = 5 | “deny unauthorized access”; AC-8.1 | Already maximum |
| Sender | Receiver/payout data | FR-02 | 3 + 2 = 5 | “register the Receiver”; Flow 1 | Already maximum |
| Sender | Complete quote | FR-03–04 | 3 + 2 = 5 | “total amount to deposit”; AC-1.1 | Already maximum |
| Sender | Locked promise | FR-03; NFR-04 | 3 + 2 = 5 | “lock the quoted exchange rate”; AC-2.2 | Already maximum |
| Sender | Funding/proof | FR-10, FR-13, FR-23; NFR-05 | 3 + 2 = 5 | “issue an immutable receipt”; AC-3.1 | Already maximum |
| Sender | Status/timeline | FR-08 | 3 + 2 = 5 | “timestamped timeline”; AC-4.3 | Already maximum |
| Sender | Hold/failure explanation | FR-07, FR-12, FR-24 | 3 + 2 = 5 | “permitted next step”; AC-4.2 | Already maximum |
| Sender | Cancellation/refund preview | FR-11, FR-21 | 3 + 2 = 5 | “exact refund amount”; AC-7.1 | Already maximum |
| Sender | Receipts | FR-10–12, FR-21 | 3 + 2 = 5 | “payout, cancellation or refund” | Already maximum |
| Sender | Assisted safety | FR-13–16; NFR-17 | 3 + 2 = 5 | “same remittance”; AC-6.3 | Already maximum |
| Receiver | Safe notification | NFR-21 | 2 + 2 = 4 | “status, payout-token and exception notifications”; AC-4.4 | Add a FR that specifies Sender, amount, payout method, safe next step and minimization. |
| Receiver | Incoming status | FR-08; NFR-21 | 2 + 1 = 3 | FR-08 names only Sender; Flow 3.5 | State Receiver access to the common current status/timeline. |
| Receiver | Secure identity | FR-17; NFR-02–03 | 3 + 2 = 5 | “verify ... Receiver identity”; AC-5.1 | Already maximum |
| Receiver | Exact amount/no deduction | FR-03; NFR-04 | 3 + 2 = 5 | “preserve the confirmed Receiver amount”; AC-5.2 | Already maximum |
| Receiver | Authorized payout method | FR-09, FR-13, FR-17 | 2 + 2 = 4 | “cash withdrawal”; Flow 4–5 | Add explicit bank/wallet payout capability and authorized destination validation. |
| Receiver | Protected cash pickup | FR-09, FR-17, FR-20 | 3 + 2 = 5 | “one-time token”; AC-5.3 | Already maximum |
| Receiver | Proof/no second payout | FR-10, FR-20 | 3 + 2 = 5 | “only one successful payout”; AC-5.4 | Already maximum |
| Receiver | Exception/support | FR-07, FR-22, FR-24 | 3 + 2 = 5 | “support case”; Flow 7 | Already maximum |
| Receiver | Accessible/assisted use | FR-13; NFR-12–14 | 3 + 2 = 5 | “WCAG 2.2 AA”; AC-9.4 | Already maximum |
| AgencyWorker | Scoped access | FR-06, FR-14; NFR-02–03, NFR-17 | 3 + 2 = 5 | “assigned agency and active shift” | Already maximum |
| AgencyWorker | Private search | FR-06, FR-15 | 3 + 2 = 5 | “authorized scope”; AC-6.2 | Already maximum |
| AgencyWorker | Consent-assisted flow | FR-13, FR-16 | 3 + 2 = 5 | “Sender explicitly consents”; AC-6.1 | Already maximum |
| AgencyWorker | Quote before deposit | FR-13, FR-16 | 3 + 2 = 5 | “updated quote”; Flow 2.4 | Already maximum |
| AgencyWorker | Cash funding/receipt | FR-10, FR-13; NFR-05, NFR-19 | 3 + 2 = 5 | “register cash funding”; AC-3.4 | Already maximum |
| AgencyWorker | Receiver checks | FR-09, FR-17 | 3 + 2 = 5 | “validated together with ... identity” | Already maximum |
| AgencyWorker | Stored amount/no manual math | FR-03, FR-13, FR-18 | 3 + 2 = 5 | “confirmed Receiver amount”; AC-5.2 | Already maximum |
| AgencyWorker | One-time payout | FR-13, FR-20; NFR-05 | 3 + 2 = 5 | “duplicate payout prevention” | Already maximum |
| AgencyWorker | Cancellation/refund help | FR-11, FR-13, FR-21 | 3 + 2 = 5 | “explicitly consented assisted session” | Already maximum |
| AgencyWorker | Escalation | FR-07, FR-18, FR-24 | 3 + 2 = 5 | “controlled escalation path” | Already maximum |
| AgencyWorker | Reconciliation | FR-19; NFR-19 | 3 + 2 = 5 | “flag any difference for review” | Already maximum |

- Sender: `50 / (5 × 10) × 10 = 10.00`
- Receiver: `41 / (5 × 9) × 10 = 9.11`
- AgencyWorker: `55 / (5 × 11) × 10 = 10.00`
- **Block A:** `(10.00 + 9.11 + 10.00) / 3 = 9.70`

### 4. Block B — Critical problems

| Problem | Sub-question | Score / 2 | Requirement(s) and evidence | Path to maximum |
| --- | --- | ---: | --- | --- |
| Fraud and unauthorized payout | Authentication, identity and one-time authorization | 2 | FR-01, FR-09, FR-17, FR-20; NFR-02; AC-5.1–AC-5.4 | Already maximum |
| Fraud and unauthorized payout | Least privilege, holds, separation and immutable evidence | 2 | FR-06–07, FR-24; NFR-03, NFR-10, NFR-15; AC-8.1–AC-8.5 | Already maximum |
| Ambiguous promised amount | Fees, exact conversion and locked rate | 2 | FR-03–04; NFR-04, NFR-18; AC-1.1–AC-2.4 | Already maximum |
| Ambiguous promised amount | Atomic/idempotent funding, payout, cancellation/refund | 2 | FR-11, FR-20–21, FR-23; NFR-05, NFR-08, NFR-19 | Already maximum |
| Fragmented channels | One state/price, consent, accessibility, reconciliation | 2 | FR-08, FR-13–16, FR-19; NFR-12–14, NFR-19 | Already maximum |

**Mandatory invariants**

1. **PASS** — FR-03, NFR-04 and AC-1.2 require stored single-rounding conversion.
2. **PASS** — FR-04 and AC-1.1–AC-1.3 disclose commission and total before funding.
3. **PASS** — FR-03 and AC-2.2 preserve rate and Receiver amount through every channel.
4. **PASS** — FR-21 and AC-7.1 show cancellation fee and exact refund before confirmation.
5. **PASS** — FR-11, FR-20, NFR-05 and AC-5.4/AC-7.4 prevent payout plus cancellation/second payout.

**Block B:** `10 / 10 × 10 = 10.00`.

### 5. Block C — Backlog quality

| Requirement | Score / 5 | Failed criteria | Evidence | Path to maximum |
| --- | ---: | --- | --- | --- |
| FR-01 | 5 | None | KPD-6; AC-8.2 | Already maximum |
| FR-02 | 5 | None | Flow 1; AC-1.1 | Already maximum |
| FR-03 | 5 | None | KPD-2; AC-2 | Already maximum |
| FR-04 | 5 | None | KPD-3; AC-1 | Already maximum |
| FR-05 | 2 | Vocabulary, consistent, traceable/test-backed | No state/AC; conflicts with KPD-2–3 | Remove it, or define a disclosed pre-confirmation fee inside the frozen snapshot and add state/ACs. |
| FR-06 | 5 | None | KPD-6; AC-8.1 | Already maximum |
| FR-07 | 5 | None | Flow 3; AC-4.1 | Already maximum |
| FR-08 | 4 | Traceable/test-backed | AC-4.3 supports authorized channels but title/body only names Sender | Include Receiver's authorized view. |
| FR-09 | 5 | None | KPD-9; AC-5 | Already maximum |
| FR-10 | 5 | None | AC-3.1, AC-5.3, AC-7.5 | Already maximum |
| FR-11 | 5 | None | KPD-5; AC-7 | Already maximum |
| FR-12 | 5 | None | Flow 3 fallback; AC-4.5 | Already maximum |
| FR-13 | 4 | Atomic | Joins Sender funding, Receiver payout and cancellation assistance | Split into separately traceable assisted-flow titles. |
| FR-14 | 5 | None | KPD-7; AC-6.1 | Already maximum |
| FR-15 | 5 | None | AC-6.2 | Already maximum |
| FR-16 | 4 | Clear | “permitted quote data” is unspecified | Name which pre-confirmation fields may be amended. |
| FR-17 | 5 | None | KPD-6/9; AC-5.1 | Already maximum |
| FR-18 | 5 | None | Flow 5; AC-5.5 | Already maximum |
| FR-19 | 5 | None | AC-6.5 | Already maximum |
| FR-20 | 5 | None | KPD-8; AC-5.3–AC-5.4 | Already maximum |
| FR-21 | 5 | None | KPD-5; AC-7 | Already maximum |
| FR-22 | 4 | Test-backed | Phase 2 supports it; no support-case AC | Add authorization, status, linkage and privacy ACs. |
| FR-23 | 4 | Atomic | Mixes four integrations and outcome handling | Separate supported-provider configuration from idempotent outcome handling. |
| FR-24 | 5 | None | Flow 7; AC-5.5/AC-8.5 | Already maximum |
| NFR-01 | 5 | None | AC-8.2 | Already maximum |
| NFR-02 | 5 | None | AC-8.1 | Already maximum |
| NFR-03 | 5 | None | AC-8.1 | Already maximum |
| NFR-04 | 5 | None | AC-1.2; AC-2 | Already maximum |
| NFR-05 | 5 | None | KPD-8; AC-3.2/AC-7.4 | Already maximum |
| NFR-06 | 5 | None | AC-10.3 | Already maximum |
| NFR-07 | 5 | None | AC-10.1 | Already maximum |
| NFR-08 | 5 | None | KPD-11; AC-10.2 | Already maximum |
| NFR-09 | 5 | None | AC-10.3–AC-10.4 | Already maximum |
| NFR-10 | 4 | Test-backed | AC-8.3 tests append-only events, not retrieval/retention | Add retention authority/duration and retrieval/restoration ACs. |
| NFR-11 | 5 | None | AC-4.4; AC-6.1 | Already maximum |
| NFR-12 | 5 | None | AC-9.1 | Already maximum |
| NFR-13 | 5 | None | AC-9.1 | Already maximum |
| NFR-14 | 5 | None | AC-9.2 | Already maximum |
| NFR-15 | 4 | Test-backed | Flow 7 has no metrics/alert verification AC | Add correlation, metric, alert trigger/delivery ACs. |
| NFR-16 | 4 | Test-backed | AC-10.1 measures Phase 1 only | Add Phase 2/3 workload and measurable thresholds. |
| NFR-17 | 4 | Test-backed | AC-6.1 lacks timeout/auto-lock behavior | Add inactivity, maximum duration and reauthentication ACs. |
| NFR-18 | 5 | None | KPD-2–3; AC-1.4 | Already maximum |
| NFR-19 | 5 | None | AC-3.4; AC-6.5 | Already maximum |
| NFR-20 | 4 | Test-backed | AC-8.1 is user/role-focused, not service identity | Add expired/unknown service identity AC. |
| NFR-21 | 4 | Test-backed | AC-4.4 content; no retry/follow-up test | Add at-least-once, bounded retry and follow-up ACs. |
| NFR-22 | 4 | Test-backed | No PCI/tokenization acceptance criterion | Add tokenization/no-PAN/no-CVV and PCI verification ACs. |

**Block C:** `215 / (5 × 46) × 10 = 215 / 230 × 10 = 9.35`.

### 6. Block D — Quality attributes and feasibility

| Scenario | Score / 2 | Requirement(s) and evidence | Missing/degraded behavior | Path to maximum |
| --- | ---: | --- | --- | --- |
| Security and privacy | 2 | NFR-01–03, NFR-11, NFR-17, NFR-20, NFR-22; AC-8 | Service-identity/card details still lack AC tests, but controls are explicit. | Add the Block C test ACs. |
| Monetary consistency | 2 | NFR-04–05, NFR-18–19; AC-1, AC-2, AC-3.2, AC-7.4 | None material. | Already maximum |
| Availability and recovery | 2 | NFR-06, NFR-09; AC-10.3–AC-10.4 | Targets are planning assumptions. | Validate assumptions with stakeholders. |
| Performance and scale | 1 | NFR-07, NFR-16; AC-10.1 and Core 10 | No Phase 2/3 test thresholds. | Add phased p95/error/load ACs. |
| Provider resilience and observability | 1 | NFR-08, NFR-15, NFR-21; AC-10.2 | Alerts, delivery and correlated telemetry untested. | Add observable-signal and alert verification ACs. |
| Accessibility and omnichannel operation | 2 | NFR-12–14, NFR-19; FR-13; AC-6, AC-9 | Planning baselines require validation. | Validate baselines. |

**Block D:** `10 / 12 × 10 = 8.33`. All Core 10/11 scale, availability, recovery and
performance figures remain planning assumptions requiring stakeholder validation.

### 7. End-to-end flow gate

| Main flow | Steps covered / total | Fallbacks covered | First uncovered item |
| --- | --- | --- | --- |
| Flow 1 — Direct quote, confirmation and funding | 7 / 7 | Yes: expiry, invalid data, retries, failed funding | None |
| Flow 2 — Agency-assisted quote and cash funding | 7 / 7 | Yes: wrong cash, consent/identity, retry, drawer mismatch | None |
| Flow 3 — Review, processing and tracking | 5 / 5 | Yes: timeout, rejection refund, immutable snapshot | None |
| Flow 4 — Digital payout to the Receiver | 4 / 4 | Yes: mismatch, duplicate callback, uncertain result | None |
| Flow 5 — Cash payout at an agency | 5 / 5 | Yes: authorization/identity/cash block, retry, immutable amount | None |
| Flow 6 — Cancellation and refund before payout | 5 / 5 | Yes: paid-out rejection, race, reconciliation | None |
| Flow 7 — Security or operational exception | 5 / 5 | Yes: no self-approval, uncertain callback, immutable audit | None |

**POC chain: PASS.** Flow 1 → Flow 3 → Flow 5 is fully covered. Flow 2 uses the same
transaction and monetary snapshot through FR-03, FR-13, NFR-04, NFR-05 and NFR-19.

### 8. Score summary

| Dimension | Arithmetic | Score |
| --- | --- | ---: |
| Sender | 50 / 50 × 10 | 10.00 |
| Receiver | 41 / 45 × 10 | 9.11 |
| AgencyWorker | 55 / 55 × 10 | 10.00 |
| Block A — Persona satisfaction | (10 + 9.111111 + 10) / 3 | 9.70 |
| Block B — Critical problems | 10 / 10 × 10 | 10.00 |
| Block C — Backlog quality | 215 / 230 × 10 | 9.35 |
| Block D — Quality attributes | 10 / 12 × 10 | 8.33 |
| Overall | (9.703704×0.30) + (10×0.30) + (9.347826×0.20) + (8.333333×0.20) | 9.45 |
| Verdict | 6 / 7 mandatory gates passed | **NOT ACCEPTABLE** |

The numerical threshold and every block pass, no persona need is uncovered, the five
invariants pass, the POC gate passes, and hygiene passes. The required zero-
Out-of-scope/Contradictory gate fails because FR-05 is contradictory.

### 9. Critical gaps

- [FR-05] — Promised amount / scope — Adds an uncollected-remittance fee after the transaction is confirmed — KPD-2 freezes the snapshot and KPD-3 prohibits post-funding sending charges — **Why it fails:** contradictory requirement — **Minimum correction:** remove it; if a fee is required, disclose and freeze it before confirmation with new state/AC coverage.
- [Receiver notification] — Receiver — NFR-21 only guarantees delivery behavior — AC-4.4 has content, but no functional backlog title binds it to the Receiver — **Why it fails:** partial need coverage — **Minimum correction:** add an explicit Receiver-notification requirement.
- [Receiver status / digital payout] — Receiver / Flow 3–4 — FR-08 names Sender only and no FR explicitly authorizes digital bank/wallet payout — **Why it fails:** partial Receiver coverage — **Minimum correction:** extend or add scoped Receiver status and digital-payout requirements.
- [NFR-15, NFR-16, NFR-20–22] — Quality readiness — Core decisions define intent but no matching testable ACs — **Why it fails:** observability, later-scale and integration behaviors cannot be verified — **Minimum correction:** add the specific acceptance criteria listed in Block C.
- [FR-13, FR-23] — Backlog engineering — Each combines multiple independent outcomes — **Why it fails:** reduced atomicity — **Minimum correction:** split agency operations and card-provider configuration/outcome handling.

### 10. Recommendation

The backlog is **not ready** for architecture/design despite its 9.45 numerical score: remove
or reframe FR-05 first to satisfy the mandatory contradiction gate. Then close the Receiver
notification/status/digital-payout gaps and add the missing AC groups before the next audit.

### Previous-iteration comparison

Not score-comparable: iteration 1 evaluated a different 49-item backlog. The current package
has 46 items and introduces FR-05 as a contradiction; this is a regression in gate status.

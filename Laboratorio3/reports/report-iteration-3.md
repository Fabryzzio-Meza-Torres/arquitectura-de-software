# Eval-Spec — SendIT — Iteration 3

Independent audit of the current package on 2026-08-30. Iteration 2 is comparison only.

### 0. Readiness and extracted baselines

| Input | Result |
| --- | --- |
| Case study | Usable: purpose, deliverables, hints and backlog restriction present. |
| People | Usable: Sender, Receiver and AgencyWorker each have a detailed needs list. |
| Core 1–3 | Usable: summary, exactly three critical problems and objective. |
| Core 4–6 | Usable: scope, vocabulary/state model and role needs. |
| Core 7–9 | Usable: decisions, experience and seven numbered flows/fallbacks. |
| Core 10–11 | Usable: three phases and AC-1 through AC-10. |
| Requirements | Usable: 24 sequential FR and 22 sequential NFR rows. |

**Critical-problem headings:** `A cross-border remittance is exposed to fraud and unauthorized payout`; `The promised amount becomes ambiguous between quote, deposit and payout`; `Digital and agency processing can fragment one transaction`.

**Phase headings:** `Phase 1 — POC / MVP: secure fixed-rate remittance`; `Phase 2 — Multiple corridors and digital payout`; `Phase 3 — Production hardening and network scale`.

**Out-of-scope leading phrases:** `Creating or speculating on exchange rates`; `Loans, credit, investments or cryptocurrency trading`; `Implementing the external banking and card networks themselves`; `Payout in a currency or destination that SendIT has not enabled`; `Anonymous or control-bypassing remittances`; `AgencyWorker ownership of customer decisions`; `Changing a confirmed transaction's exchange rate, sending commission or Receiver amount`; `Cancellation after successful payout`.

**Main-flow headings:** `Flow 1 — Direct quote, confirmation and funding`; `Flow 2 — Agency-assisted quote and cash funding`; `Flow 3 — Review, processing and tracking`; `Flow 4 — Digital payout to the Receiver`; `Flow 5 — Cash payout at an agency`; `Flow 6 — Cancellation and refund before payout`; `Flow 7 — Security or operational exception`.

**Committed POC Happy Path:** `Flow 1 → Flow 3 → Flow 5`.

**Input hygiene:** IDs are unique and sequential, no title is empty or duplicated, Core 5 vocabulary is used, and the eight local links in `core/` resolve. **READY TO EVALUATE.**

### 1. Persona-needs coverage

| Role | Need | Requirement(s) | Supporting core evidence | Coverage |
| --- | --- | --- | --- | --- |
| Sender | Secure access | FR-01, FR-06, FR-17; NFR-01–03 | KPD-6; AC-8 | Full |
| Sender | Receiver/payout data | FR-02 | Flow 1; AC-1.1 | Full |
| Sender | Complete quote | FR-03–05; NFR-04, NFR-18 | KPD-2–3; AC-1 | Full |
| Sender | Locked amount/rate | FR-03; NFR-04, NFR-18 | KPD-2; AC-2 | Full |
| Sender | Digital/agency funding with proof | FR-10, FR-13, FR-23; NFR-05, NFR-19, NFR-22 | Flow 1–2; AC-3 | Full |
| Sender | Status/timeline | FR-08; NFR-21 | AC-4.3 | Full |
| Sender | Hold/rejection/failure explanation | FR-07, FR-12, FR-24 | Flow 3/7; AC-4.2 | Full |
| Sender | Cancellation/refund preview | FR-05, FR-11, FR-21 | KPD-5; AC-7 | Full |
| Sender | Payout/refund proof | FR-05, FR-10–12, FR-21 | AC-3.1, AC-5.3, AC-7.5 | Full |
| Sender | Safe assisted flow | FR-13–16; NFR-17 | KPD-7; Flow 2; AC-6 | Full |
| Receiver | Safe notification | FR-05; NFR-21 | Flow 3.5; AC-4.4 | Partial |
| Receiver | Incoming status | FR-08; NFR-21 | Flow 3.5; AC-4.3 | Partial |
| Receiver | Secure identity | FR-17; NFR-02–03 | KPD-6/9; AC-5.1 | Full |
| Receiver | Exact no-deduction payout | FR-03; NFR-04, NFR-18 | KPD-2/4; AC-5.2 | Full |
| Receiver | Authorized payout method | FR-09, FR-13, FR-17 | Flow 4–5; AC-5 | Partial |
| Receiver | Protected cash collection | FR-09, FR-17, FR-20 | KPD-9; AC-5 | Full |
| Receiver | Proof/no second payout | FR-10, FR-20; NFR-05 | AC-5.3–5.4 | Full |
| Receiver | Exception/support | FR-07, FR-22, FR-24 | Flow 7; AC-4.2/5.5 | Full |
| Receiver | Accessible/assisted service | FR-13; NFR-12–14 | KPD-10; AC-9 | Full |
| AgencyWorker | Individual scoped access | FR-06, FR-14; NFR-02–03, NFR-17 | KPD-7; AC-6.1/8.1 | Full |
| AgencyWorker | Private search | FR-06, FR-15 | Flow 5.1; AC-6.2 | Full |
| AgencyWorker | Assisted consent flow | FR-13, FR-16; NFR-17 | Flow 2; AC-6.1–6.3 | Full |
| AgencyWorker | Quote before deposit | FR-13, FR-16 | Flow 2.4; AC-6.4/9.4 | Full |
| AgencyWorker | Cash funding/receipt | FR-10, FR-13; NFR-05, NFR-19 | Flow 2; AC-3 | Full |
| AgencyWorker | Receiver checks | FR-09, FR-17 | Flow 5; AC-5.1 | Full |
| AgencyWorker | Stored amount/no manual math | FR-03, FR-13, FR-18 | KPD-2; AC-5.2 | Full |
| AgencyWorker | One-time cash payout | FR-13, FR-20; NFR-05 | Flow 5; AC-5.3–5.4 | Full |
| AgencyWorker | Cancellation/refund assistance | FR-11, FR-13, FR-21 | Flow 6; AC-7 | Full |
| AgencyWorker | Exception escalation | FR-07, FR-18, FR-24 | Flow 7; AC-5.5/8.5 | Full |
| AgencyWorker | Shift reconciliation | FR-19; NFR-19 | Flow 2/5; AC-6.5 | Full |

The detailed personas and Core 6 have no conflicting needs.

### 2. Reverse traceability and scope

| Requirement | Serves | Supporting core evidence | Phase | Status |
| --- | --- | --- | --- | --- |
| FR-01 | Sender secure access | KPD-6; AC-8.2 | all | Justified |
| FR-02 | Sender data capture | Flow 1.1; AC-1.1 | all | Justified |
| FR-03 | Locked money promise | KPD-2; AC-2 | all | Justified |
| FR-04 | Pre-funding pricing | KPD-3; AC-1 | all | Justified |
| FR-05 | Sender refund/proof | KPD-5; Flow 6; AC-7 | all | Justified |
| FR-06 | Access control | KPD-6; AC-8.1 | all | Justified |
| FR-07 | Fraud/compliance review | Flow 3; AC-4 | all | Justified |
| FR-08 | Tracking | Flow 3; AC-4.3 | all | Justified |
| FR-09 | Payout authorization | KPD-9; AC-5 | all | Justified |
| FR-10 | Receipts | AC-3.1/5.3/7.5 | all | Justified |
| FR-11 | Pre-payout cancellation | KPD-5; AC-7 | all | Justified |
| FR-12 | Denial refund | Flow 3 fallback; AC-4.5 | all | Justified |
| FR-13 | Assisted service | KPD-1/7; Flow 2/5/6 | all | Justified |
| FR-14 | Worker authentication | KPD-7; AC-6.1 | all | Justified |
| FR-15 | Scoped search | Flow 5.1; AC-6.2 | all | Justified |
| FR-16 | Pre-confirmation amendment | Flow 2.2; KPD-7 | all | Justified |
| FR-17 | Identity verification | KPD-6/9; AC-5.1 | all | Justified |
| FR-18 | Agency cash availability | Flow 5; AC-5.5 | all | Justified |
| FR-19 | Shift reconciliation | Flow 2/5; AC-6.5 | all | Justified |
| FR-20 | Duplicate-payout prevention | KPD-8; AC-5.3–5.4 | all | Justified |
| FR-21 | Cancellation/refund | KPD-5; AC-7 | all | Justified |
| FR-22 | Support/dispute | Phase 2 support/disputes | 2 | Justified |
| FR-23 | Card funding | Sender funding; authorized integration boundary | 1/2 | Justified |
| FR-24 | Agency escalation | Flow 7; AC-5.5/8.5 | all | Justified |
| NFR-01 | Security/privacy | KPD-6; AC-8.2 | all | Justified |
| NFR-02 | Money action authentication | KPD-6; AC-8.1 | all | Justified |
| NFR-03 | Least privilege | KPD-6–7; AC-8.1 | all | Justified |
| NFR-04 | Monetary snapshot | KPD-2; AC-1.2/2 | all | Justified |
| NFR-05 | Atomic monetary outcomes | KPD-8; AC-3.2/7.4 | all | Justified |
| NFR-06 | POC availability | AC-10.3 | 1 | Justified |
| NFR-07 | POC response time | AC-10.1 | 1 | Justified |
| NFR-08 | Provider reconciliation | KPD-11; AC-10.2 | all | Justified |
| NFR-09 | POC recovery | AC-10.3–10.4 | 1 | Justified |
| NFR-10 | Audit retention | Core 5; AC-8.3 | all | Justified |
| NFR-11 | Privacy/consent | KPD-6–7; AC-4.4/6.1 | all | Justified |
| NFR-12 | Accessibility | KPD-10; AC-9.1 | all | Justified |
| NFR-13 | Responsive use | AC-9.1 | all | Justified |
| NFR-14 | Localization | KPD-10; AC-9.2 | all | Justified |
| NFR-15 | Observability | Flow 7; security problem | all | Justified |
| NFR-16 | Staged scale | Core 10 assumptions | all | Justified |
| NFR-17 | Assisted sessions | Core 5; AC-6.1 | all | Justified |
| NFR-18 | Versioned monetary configuration | KPD-2–3; AC-1.4/2.1 | all | Justified |
| NFR-19 | Cash ledger | AC-3.4/6.5 | all | Justified |
| NFR-20 | Service authentication | KPD-6; AC-8.1 | all | Justified |
| NFR-21 | Notifications | Flow 3.5; AC-4.4 | all | Justified |
| NFR-22 | Card-data protection | FR-23; KPD-6/11 | 1/2 | Justified |

No requirement is Orphan, Out of scope or Contradictory. FR-05 now describes a separate
pre-disclosed expiry/refund terminal outcome; it leaves the stored Receiver amount intact
and atomically prevents payout.

### 3. Block A — Persona satisfaction

| Role | Need | Requirement(s) | A.1 + A.2 / 5 | Evidence quote(s) | Path to maximum |
| --- | --- | --- | ---: | --- | --- |
| Sender | Secure access | FR-01, FR-06, FR-17; NFR-01–03 | KPD-6; AC-8 | 3 + 2 = 5 | All maximum |
| Sender | Receiver/payout data | FR-02 | Flow 1; AC-1.1 | 3 + 2 = 5 | All maximum |
| Sender | Complete quote | FR-03–05 | KPD-2–3; AC-1 | 3 + 2 = 5 | All maximum |
| Sender | Locked rate/amount | FR-03; NFR-04/18 | KPD-2; AC-2 | 3 + 2 = 5 | All maximum |
| Sender | Funding/proof | FR-10, FR-13, FR-23; NFR-05 | Flow 1–2; AC-3 | 3 + 2 = 5 | All maximum |
| Sender | Status/timeline | FR-08; NFR-21 | AC-4.3 | 3 + 2 = 5 | All maximum |
| Sender | Hold/failure explanation | FR-07, FR-12, FR-24 | Flow 3/7; AC-4.2 | 3 + 2 = 5 | All maximum |
| Sender | Cancellation/refund preview | FR-05, FR-11, FR-21 | KPD-5; AC-7 | 3 + 2 = 5 | All maximum |
| Sender | Payout/refund proof | FR-05, FR-10–12, FR-21 | AC-3.1/5.3/7.5 | 3 + 2 = 5 | All maximum |
| Sender | Safe assisted flow | FR-13–16; NFR-17 | KPD-7; Flow 2 | 3 + 2 = 5 | All maximum |
| Receiver | Safe notification | FR-05; NFR-21 | “notify the Sender and Receiver”; AC-4.4 | 2 + 2 = 4 | Add a general Receiver-notification FR. |
| Receiver | Incoming status | FR-08; NFR-21 | FR-08 says “Sender”; AC-4.3 | 2 + 1 = 3 | State Receiver access to the status/timeline. |
| Receiver | Identity | FR-17; NFR-02–03 | AC-5.1 | 3 + 2 = 5 | All maximum |
| Receiver | Exact amount | FR-03; NFR-04/18 | AC-5.2 | 3 + 2 = 5 | All maximum |
| Receiver | Authorized method | FR-09, FR-13, FR-17 | Flow 4–5 | 2 + 2 = 4 | Add explicit bank/wallet payout FR. |
| Receiver | Cash authorization | FR-09, FR-17, FR-20 | AC-5.3 | 3 + 2 = 5 | All maximum |
| Receiver | Proof/no duplicate | FR-10, FR-20 | AC-5.3–5.4 | 3 + 2 = 5 | All maximum |
| Receiver | Exception/support | FR-07, FR-22, FR-24 | Flow 7 | 3 + 2 = 5 | All maximum |
| Receiver | Accessible assisted service | FR-13; NFR-12–14 | AC-9 | 3 + 2 = 5 | All maximum |
| AgencyWorker | Individual scoped access | FR-06, FR-14; NFR-02–03/17 | KPD-7; AC-6.1/8.1 | 3 + 2 = 5 | All maximum |
| AgencyWorker | Private transaction search | FR-06, FR-15 | Flow 5.1; AC-6.2 | 3 + 2 = 5 | All maximum |
| AgencyWorker | Assisted Sender flow/consent | FR-13, FR-16 | Flow 2; AC-6.1–6.3 | 3 + 2 = 5 | All maximum |
| AgencyWorker | Quote before deposit | FR-13, FR-16 | Flow 2.4; AC-6.4/9.4 | 3 + 2 = 5 | All maximum |
| AgencyWorker | Cash funding/receipt | FR-10, FR-13; NFR-05/19 | Flow 2; AC-3 | 3 + 2 = 5 | All maximum |
| AgencyWorker | Receiver checks | FR-09, FR-17 | Flow 5; AC-5.1 | 3 + 2 = 5 | All maximum |
| AgencyWorker | Stored amount/no manual math | FR-03, FR-13, FR-18 | KPD-2; AC-5.2 | 3 + 2 = 5 | All maximum |
| AgencyWorker | One-time cash payout | FR-13, FR-20; NFR-05 | Flow 5; AC-5.3–5.4 | 3 + 2 = 5 | All maximum |
| AgencyWorker | Cancellation/refund help | FR-11, FR-13, FR-21 | Flow 6; AC-7 | 3 + 2 = 5 | All maximum |
| AgencyWorker | Exception escalation | FR-07, FR-18, FR-24 | Flow 7; AC-5.5/8.5 | 3 + 2 = 5 | All maximum |
| AgencyWorker | Shift reconciliation | FR-19; NFR-19 | Flow 2/5; AC-6.5 | 3 + 2 = 5 | All maximum |

- Sender: `50 / (5 × 10) × 10 = 10.00`
- Receiver: `41 / (5 × 9) × 10 = 9.11`
- AgencyWorker: `55 / (5 × 11) × 10 = 10.00`
- **Block A:** `(10.00 + 9.11 + 10.00) / 3 = 9.70`

### 4. Block B — Critical problems

| Problem | Sub-question | Score / 2 | Requirement(s) and evidence | Path to maximum |
| --- | --- | ---: | --- | --- |
| Fraud and unauthorized payout | Authentication, identity, one-time authorization | 2 | FR-01, FR-09, FR-17, FR-20; NFR-02; AC-5 | Already maximum |
| Fraud and unauthorized payout | Least privilege, holds, separation, immutable evidence | 2 | FR-06–07, FR-24; NFR-03/10/15; AC-8 | Already maximum |
| Ambiguous promised amount | Fees, conversion, rate lock | 2 | FR-03–05; NFR-04/18; AC-1–2 | Already maximum |
| Ambiguous promised amount | Atomic/idempotent outcomes | 2 | FR-05, FR-11, FR-20–21, FR-23; NFR-05/08/19 | Already maximum |
| Fragmented channels | Shared state/price, consent, accessibility, reconciliation | 2 | FR-08, FR-13–16, FR-19; NFR-12–14/19 | Already maximum |

**Mandatory invariants:**

1. **PASS** — FR-03, NFR-04 and AC-1.2: stored single-rounding conversion.
2. **PASS** — FR-04 and AC-1.1–1.3: commission and total before funding.
3. **PASS** — FR-03 and AC-2.2: rate/Receiver amount unchanged after confirmation.
4. **PASS** — FR-21 and AC-7.1: cancellation fee and exact refund preview.
5. **PASS** — FR-05, FR-11, FR-20, NFR-05 and AC-5.4/7.4: one terminal money outcome.

**Block B:** `10 / 10 × 10 = 10.00`.

### 5. Block C — Backlog quality

| Requirement | Score / 5 | Failed criteria | Evidence | Path to maximum |
| --- | ---: | --- | --- | --- |
| FR-01 | 5 | None | KPD-6; AC-8.2 | Already maximum |
| FR-02 | 5 | None | Flow 1; AC-1.1 | Already maximum |
| FR-03 | 5 | None | KPD-2; AC-2 | Already maximum |
| FR-04 | 5 | None | KPD-3; AC-1 | Already maximum |
| FR-05 | 4 | Test-backed | AC-7 covers refund/race, not deadline expiry | Add deadline-expiry AC. |
| FR-06 | 5 | None | KPD-6; AC-8.1 | Already maximum |
| FR-07 | 5 | None | Flow 3; AC-4 | Already maximum |
| FR-08 | 4 | Test-backed | AC-4.3; body names Sender only | Include Receiver status. |
| FR-09 | 5 | None | KPD-9; AC-5 | Already maximum |
| FR-10 | 5 | None | AC-3.1/5.3/7.5 | Already maximum |
| FR-11 | 5 | None | KPD-5; AC-7 | Already maximum |
| FR-12 | 5 | None | Flow 3; AC-4.5 | Already maximum |
| FR-13 | 4 | Atomic | Funding, payout and cancellation assistance | Split operations. |
| FR-14 | 5 | None | KPD-7; AC-6.1 | Already maximum |
| FR-15 | 5 | None | AC-6.2 | Already maximum |
| FR-16 | 4 | Clear | “permitted quote data” unspecified | Name permitted fields. |
| FR-17 | 5 | None | KPD-6/9; AC-5.1 | Already maximum |
| FR-18 | 5 | None | Flow 5; AC-5.5 | Already maximum |
| FR-19 | 5 | None | AC-6.5 | Already maximum |
| FR-20 | 5 | None | KPD-8; AC-5 | Already maximum |
| FR-21 | 5 | None | KPD-5; AC-7 | Already maximum |
| FR-22 | 4 | Test-backed | No support-case AC | Add case ACs. |
| FR-23 | 4 | Atomic | Four network integrations plus outcomes | Split configuration/outcomes. |
| FR-24 | 5 | None | Flow 7; AC-5.5/8.5 | Already maximum |
| NFR-01 | 5 | None | AC-8.2 | Already maximum |
| NFR-02 | 5 | None | AC-8.1 | Already maximum |
| NFR-03 | 5 | None | AC-8.1 | Already maximum |
| NFR-04 | 5 | None | AC-1.2/2 | Already maximum |
| NFR-05 | 5 | None | AC-3.2/7.4 | Already maximum |
| NFR-06 | 5 | None | AC-10.3 | Already maximum |
| NFR-07 | 5 | None | AC-10.1 | Already maximum |
| NFR-08 | 5 | None | AC-10.2 | Already maximum |
| NFR-09 | 5 | None | AC-10.3–10.4 | Already maximum |
| NFR-10 | 4 | Test-backed | Retention/retrieval untested | Add retention/retrieval AC. |
| NFR-11 | 5 | None | AC-4.4/6.1 | Already maximum |
| NFR-12 | 5 | None | AC-9.1 | Already maximum |
| NFR-13 | 5 | None | AC-9.1 | Already maximum |
| NFR-14 | 5 | None | AC-9.2 | Already maximum |
| NFR-15 | 4 | Test-backed | No telemetry/alert AC | Add alert ACs. |
| NFR-16 | 4 | Test-backed | Only Phase 1 measured | Add Phase 2/3 ACs. |
| NFR-17 | 4 | Test-backed | No timeout/lock AC | Add timeout/lock AC. |
| NFR-18 | 5 | None | AC-1.4/2.1 | Already maximum |
| NFR-19 | 5 | None | AC-3.4/6.5 | Already maximum |
| NFR-20 | 4 | Test-backed | No service-identity AC | Add denial/log AC. |
| NFR-21 | 4 | Test-backed | No retry/follow-up AC | Add delivery AC. |
| NFR-22 | 4 | Test-backed | No PCI/tokenization AC | Add PCI AC. |

**Block C:** `217 / (5 × 46) × 10 = 217 / 230 × 10 = 9.43`.

### 6. Block D — Quality attributes and feasibility

| Scenario | Score / 2 | Requirement(s) and evidence | Missing/degraded behavior | Path to maximum |
| --- | ---: | --- | --- | --- |
| Security and privacy | 2 | NFR-01–03, NFR-11, NFR-17, NFR-20, NFR-22; AC-8 | Service/card ACs pending | Add Block C ACs. |
| Monetary consistency | 2 | NFR-04–05, NFR-18–19; AC-1/2/3.2/7.4 | None material | Already maximum |
| Availability and recovery | 2 | NFR-06, NFR-09; AC-10.3–10.4 | Planning assumptions | Validate stakeholders. |
| Performance and scale | 1 | NFR-07, NFR-16; AC-10.1 | No Phase 2/3 measures | Add phased load ACs. |
| Provider resilience and observability | 1 | NFR-08, NFR-15, NFR-21; AC-10.2 | Telemetry/alerts untested | Add signal/alert ACs. |
| Accessibility and omnichannel operation | 2 | NFR-12–14, NFR-19; FR-13; AC-6/9 | Planning baselines | Validate baselines. |

**Block D:** `10 / 12 × 10 = 8.33`. Core 10/11 figures remain planning assumptions requiring stakeholder validation.

### 7. End-to-end flow gate

| Main flow | Steps covered / total | Fallbacks covered | First uncovered item |
| --- | --- | --- | --- |
| Flow 1 — Direct quote, confirmation and funding | 7 / 7 | Yes | None |
| Flow 2 — Agency-assisted quote and cash funding | 7 / 7 | Yes | None |
| Flow 3 — Review, processing and tracking | 5 / 5 | Yes | None |
| Flow 4 — Digital payout to the Receiver | 4 / 4 | Yes | None |
| Flow 5 — Cash payout at an agency | 5 / 5 | Yes | None |
| Flow 6 — Cancellation and refund before payout | 5 / 5 | Yes | None |
| Flow 7 — Security or operational exception | 5 / 5 | Yes | None |

**POC chain: PASS.** Flow 1 → Flow 3 → Flow 5 is complete. Flow 2 retains the same transaction and monetary snapshot through FR-03, FR-13, NFR-04, NFR-05 and NFR-19.

### 8. Score summary

| Dimension | Arithmetic | Score |
| --- | --- | ---: |
| Sender | 50 / 50 × 10 | 10.00 |
| Receiver | 41 / 45 × 10 | 9.11 |
| AgencyWorker | 55 / 55 × 10 | 10.00 |
| Block A — Persona satisfaction | (10 + 9.111111 + 10) / 3 | 9.70 |
| Block B — Critical problems | 10 / 10 × 10 | 10.00 |
| Block C — Backlog quality | 217 / 230 × 10 | 9.43 |
| Block D — Quality attributes | 10 / 12 × 10 | 8.33 |
| Overall | (9.703704×0.30) + (10×0.30) + (9.434783×0.20) + (8.333333×0.20) | 9.46 |
| Verdict | 7 / 7 mandatory gates passed | **ACCEPTABLE** |

### 9. Critical gaps

- [FR-05] — Sender / expiry refund — Deadline-triggered refund is clear but AC-7 has no deadline trigger — **Why it fails:** partial test backing — **Minimum correction:** add expiry, one refund, payout block and notification acceptance criteria.
- [Receiver notification/status/digital payout] — Receiver — Requirements remain partial outside expiry — **Why it fails:** three needs lack explicit complete title support — **Minimum correction:** add Receiver notification, status and bank/wallet payout titles.
- [NFR-15, NFR-16, NFR-20–22] — Quality readiness — Intent is present but verification ACs are missing — **Why it fails:** not completely measurable — **Minimum correction:** add the Block C AC groups.
- [FR-13, FR-23] — Backlog quality — Multiple independent outcomes in one title — **Why it fails:** lower atomicity — **Minimum correction:** split the titles.

### 10. Recommendation

The backlog is **ACCEPTABLE** and can proceed to architecture/design. Add the FR-05 expiry
acceptance criteria first, then close Receiver digital/status coverage and the missing quality
attribute acceptance criteria before treating later-phase targets as contractual.

### Previous-iteration comparison

**Improved:** FR-05 now models a pre-disclosed expiry/refund outcome, prevents payout and
preserves the Receiver amount; the contradiction gate now passes. **Unchanged:** the remaining
Receiver and quality-attribute gaps. **Regressed/new:** none.

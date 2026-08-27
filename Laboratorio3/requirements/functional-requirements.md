# Functional requirements — SendIT backlog

Per the case-study restriction, each item is a clear backlog title rather than an extended
requirement description. Testable detail is defined in `core/11. acceptance-criteria.md`.

| ID | Backlog item title |
| --- | --- |
| FR-01 | Sender account registration and secure sign-in |
| FR-02 | Sender identity verification before remittance confirmation |
| FR-03 | Receiver identity, destination and payout-method capture |
| FR-04 | Exact local-currency Receiver amount calculation in the remittance quote |
| FR-05 | Sending commission and total-to-deposit disclosure before funding |
| FR-06 | Expired unconfirmed quote refresh |
| FR-07 | Confirmed monetary snapshot and exchange-rate lock |
| FR-08 | Exact-total digital funding and funding receipt |
| FR-09 | Exact-total agency cash funding and cash receipt |
| FR-10 | Duplicate funding prevention across retries and provider callbacks |
| FR-11 | Identity, fraud, limit and compliance review before payout |
| FR-12 | Shared remittance status and customer-visible timeline across channels |
| FR-13 | Safe Receiver notification with amount, payout method and next step |
| FR-14 | Exact local-currency digital payout to the authorized destination |
| FR-15 | Identity-verified agency cash payout with one-time authorization |
| FR-16 | Duplicate payout prevention and one-time authorization invalidation |
| FR-17 | Sender and Receiver payout receipts |
| FR-18 | Pre-cancellation operational-fee and exact-refund preview |
| FR-19 | Atomic pre-payout cancellation eligibility and payout exclusion |
| FR-20 | Idempotent cancellation refund and refund receipt |
| FR-21 | Full funded-total refund after post-funding SendIT rejection |
| FR-22 | Agency-assisted Sender session with explicit customer consent |
| FR-23 | Individual AgencyWorker sign-in and assigned-shift opening |
| FR-24 | Privacy-preserving agency transaction search |
| FR-25 | Agency display and printing of quote, consent summary and receipts |
| FR-26 | Security, identity, cash and provider-exception escalation |
| FR-27 | Agency shift ledger closure and cash reconciliation |
| FR-28 | Append-only audit events for every money and state transition |
| FR-29 | Confirmed-transaction correction through cancellation and a new quote |
| FR-30 | Post-payout support and dispute case creation |

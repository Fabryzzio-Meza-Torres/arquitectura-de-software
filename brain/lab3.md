# Lab 3 — SendIT

## Exercise overview

The third laboratory applied Top-Down Design and the R.E.D.A.L.E. framework to SendIT, an international-remittance system. Because the product moves money, security and data consistency were central guarantees.

The study case required:

- a requirements evaluation, with 8/10 considered acceptable;
- all R.E.D.A.L.E. framework deliverables;
- clearly preserved design iterations;
- requirements shown as a backlog with clear titles and no extended descriptions.

Primary source: [`../Laboratorio3/study-case/Lab #3 - Arqui2026.2.md`](../Laboratorio3/study-case/Lab%20%233%20-%20Arqui2026.2.md).

## Product scope established during the activity

SendIT allows a `Sender` to fund a transfer in an origin currency and a `Receiver` to obtain the exact confirmed amount in the destination country's local currency. The same transaction can be handled through web/mobile or with an `AgencyWorker` at a physical agency.

Invariants maintained across people, core, requirements, and design:

- Before funding, SendIT shows the origin amount, exchange rate, Receiver amount, fee, and total deposit.
- Once the quote is confirmed, the exchange rate and Receiver amount remain fixed for that transaction.
- The flow preserves traceability from funding through review, processing, and payout.
- An eligible transaction cancelled before payout refunds the funded amount minus a small operational fee disclosed in advance.
- Agency operations reconcile cash while preserving the same transaction identity used by digital channels.
- Security, monetary consistency, and cross-channel traceability are product guarantees, not optional enhancements.

## Activities completed

- Defined the three model users: Sender, Receiver, and AgencyWorker.
- Completed the 11-document Top-Down product core.
- Created the functional and non-functional requirement backlogs.
- Added technical endpoint design derived from the product flows.
- Built the evaluator prompt and preserved three report iterations.
- Reconciled persona needs, monetary invariants, physical-agency behavior, and reverse traceability across the specification.

## Achievements and evidence

- `Laboratorio3/reports/report-iteration-3.md` records an overall score of 9.46/10 and an `ACCEPTABLE` verdict with all seven mandatory gates passed.
- The report records 9.70/10 for persona satisfaction, 10/10 for critical-problem coverage, 9.43/10 for backlog quality, and a passing POC chain.
- The final specification maintained the same transaction and monetary snapshot across the core flows.
- The repository preserved each evaluation report instead of overwriting earlier results.

These results are historical evidence. They must be recalculated if the people, core, requirements, or evaluator change.

## Standard structure validated by this laboratory

Lab 3 is the closest existing example of the standard structure for future laboratories:

1. `study-case/` defines the assignment and constraints.
2. `people/` defines model users.
3. `core/` contains exactly 11 product-specification documents.
4. `requirements/` contains the FR and NFR backlogs.
5. `agents/eval-spec.md` defines the audit.
6. `reports/` preserves each evaluation iteration.

`design/` is an allowed extension when the assignment includes technical design; it is not a replacement for any baseline folder.

## Special backlog rule

Each Lab 3 requirement is a short, atomic, understandable title. Detailed behavior and acceptance semantics live in:

- key product concepts and decisions;
- expected user experience;
- main flows;
- staged scope;
- acceptance criteria;
- technical design.

Traceability must evaluate those sources together. Lab 1's self-contained requirement style must not be copied into Lab 3 because it conflicts with this study case's explicit backlog restriction.

## Lessons learned

- Evaluate every Sender, Receiver, and AgencyWorker need; do not assume implicit coverage.
- Maintain reverse traceability so every requirement is justified by a need, decision, flow, or acceptance criterion.
- Treat rate locking, fee disclosure, cancellation, refund, payout, agency reconciliation, security, and monetary consistency as first-class audit areas.
- Preserve the physical agency as an explicit product channel rather than reducing AgencyWorker to secondary documentation.
- Keep the exact Receiver amount stable after quote confirmation.
- A passing link or ID check does not establish an acceptable evaluation result.
- “Acceptable” does not mean perfect. Preserve critical gaps and improvement paths even after passing the threshold.

## Improvements across iterations

- Strengthened persona-to-need coverage and reverse traceability.
- Clarified the quote snapshot and ensured the exchange rate, destination amount, fees, and deposit total remain consistent through the transaction.
- Made cancellation and refund behavior explicit, including the pre-disclosed operational fee.
- Connected physical-agency cash handling to the same transaction identity and reconciliation model.
- Improved report arithmetic, denominators, mandatory-gate evidence, and paths to maximum scores.
- Preserved short backlog titles while moving detailed behavior into core flows, decisions, and acceptance criteria.

## Open issues and cautions

- Always execute the current `agents/eval-spec.md` from scratch after changing the specification or backlog. Historical report scores are not automatically current.
- Do not expand SendIT into a general banking platform or introduce unrelated financial products.
- Do not hide exchange rates, fees, refunds, or payout amounts behind implicit calculations.

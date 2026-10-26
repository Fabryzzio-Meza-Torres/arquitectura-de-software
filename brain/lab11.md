# Laboratory 11 Memory

## Exercise overview

Spotty expands a university's laptop-based automatic grader to Programming, Architecture and AI courses using only AWS Spot sandbox/worker compute. The [study case](../Laboratorio11/study-case/Lab%20%2311.md) supplies runtime P99s of 1, 10 and 40+ minutes, 3–5 GB course images, GPU scarcity, final-30-minute bursts, untrusted code and grades within two days. User clarification supplies per-Spot concurrency envelopes of 20/4/2 and a global ten-Spot limit.

## Activities completed

- Reviewed the assignment, functional/non-functional backlogs, `diagram/proposal_1.jpeg` and existing editable drawing labels.
- Added [scheduler-design.md](../Laboratorio11/plan/scheduler-design.md) with priority criteria, red-black-tree ordering, capacity calendars, dispatcher ownership, recovery and requirement impacts.
- Created editable architecture and tree drawings under `Laboratorio11/plan/`, with PNG exports for visual review.

## Achievements and validation evidence

- The design separates reception, task ordering, placement and attempt dispatch. It recommends SQS per course type for ingestion/recovery plus a database-led execution scheduler; it also describes direct database ingestion.
- A read-only independent builder check identified two material ambiguities. The report now requires enforced occupancy bounds for backfilling before protected starts and preserves healthy running attempts during graceful drain. The follow-up review found no remaining material planning contradiction.
- Artifact validation results and limitations are recorded in the report's final validation section. They establish document/diagram properties, not runtime correctness or assignment-evaluator success.

## Lessons learned

- The current assignment explicitly requires course queues and SQS. A queue-free proposal must identify the contract changes rather than silently claiming compliance.
- Submission closure, useful correction feedback and the two-day grading obligation are distinct deadlines. The grading-clock origin remains a documented proposed decision.
- Spot age alone is not an interruption predictor. Use actual rebalance/interruption signals, readiness, resource compatibility and measured completion estimates.
- A P99 estimate cannot guarantee a hard protected start behind nonpreemptive work. Require a proven occupancy limit or completed drain; expose overruns and capacity loss.
- A database-backed scheduler still implements pending-work/queue semantics and needs durability, idempotency, leases, fencing and reconciliation.

## Improvements across iterations

- Replaced the unexplained backlog-times-runtime priority product with eligibility gates, protected aged service and a deterministic lexicographic key.
- Separated tree ordering from multi-resource placement and persistent state; documented that scans/rekeying can exceed logarithmic cost.
- Distinguished graceful drain from actual infrastructure failure and separated transport DLQs from execution quarantine.
- Included launch/replacement permits in the ten-instance cap; AWS automatic Capacity Rebalancing can otherwise temporarily exceed an Auto Scaling group's maximum.
- On 2026-10-25, translated all 38 architecture text elements into Spanish at the user's request and replaced `plan/scheduler-architecture.png`. Preserved all 38 non-text elements, including the 17 arrows. The final 1890 × 1350 export was visually inspected; source-hash/render coverage and reciprocal-binding checks passed. Updated the design report's export metadata and `plan/validation.json`; priority-tree artifacts were unchanged.
- Later on 2026-10-25, translated the eight priority-tree prose labels into Spanish, including the user's existing long-task aging annotation, and replaced `plan/priority-tree.png`. Preserved task IDs, keys, node colors and every non-text element. Visual inspection and source/render coverage checks passed; updated the design report and validation metadata. This supersedes the previous note's unchanged-tree status.
- Created `plan/scheduler-integrated.excalidraw` and its PNG on 2026-10-25 to evolve the user's screenshot planning block into distinct priority, reservation and dispatch stages. Added explicit READY-tree insert/remove/reinsert/rekey operations, committed reservation output (`spot_id` and `schedule_at`), a three-node example and a state timeline. Preserved prior scenes. Inspected the overview and all four full-scale tiles; source/render coverage, unique IDs, reciprocal bindings, required operation labels and the example's ordering/colors passed checks. The design report and `plan/validation.json` record scope and evidence; no runtime or evaluator was executed.
- The user then requested a simpler integrated drawing and specified semantic colors: blue services, yellow reliability patterns, green databases and red conditions. Replaced the comprehensive integrated layout with eight components and short tree-operation notes; retained `spot_id + schedule_at`, post-commit removal and telemetry/replanning. This palette overrides the generic skill palette for the drawing. The replacement PNG was visually inspected; role-color, binding and render/source checks passed. The preceding integrated-layout evidence is historical; the standalone architecture and priority-tree scenes remain separate.

## Open issues or unverified claims

- This is an architecture proposal. No application, AWS deployment, burst simulation, benchmark or laboratory requirements evaluator was executed.
- Confirm grading deadline origin, feedback/correction target, workload limits/checkpoint support, fairness parameters and queue-contract acceptance before implementation.
- The 20/4/2 envelopes need measured CPU/RAM/GPU profiles; ten available GPU Spots and arbitrary-code checkpoint restoration are not guaranteed.
- `Laboratorio11/core/` and a laboratory evaluator are absent. Existing source documents, requirements and original drawings remain unchanged.

# Laboratory 8 Memory

## Exercise overview

The midterm in `Laboratorio8/ep.excalidraw` supplies iteration #3 of an undocumented, unscaled system. It requests reverse engineering, requirements, iterations #2 and #1, justified corrections to iteration #3, a critical path, SPOF/bottleneck analysis, six conditional reliability cases, and two fitness functions. The supplied weights total 20 points. Answers and brief justifications belong in the drawing; no separate report is required. No `study-case/` directory was present when adapting the evaluator.

## Activities completed

- Adapted `.agents/skills/excalidraw-architecture-evaluator/references/rubric.md` to the new eight-point assignment on 2026-10-01.
- Updated the local skill's evaluation-row instruction to match both earlier iterations and the six reliability cases.

## Achievements and validation evidence

- Confirmed the user's assignment wording against the active text in `Laboratorio8/ep.excalidraw`.
- Preserved the supplied weights: 2, 2, 5, 2, 1.5, 1, 4.5, and 2; reliability comprises six cases at 0.75 each, with Order API / Order DB treated as one case.
- The current rubric distinguishes iterations #2/#1 from corrections to #3, and conditional reliability scenarios from the student's independent SPOF/bottleneck analysis.

## Lessons learned

An evaluator reused from a mock exam must update its criteria and output-row routing together. Previous domain-specific tasks must not become obligations in a new exam.

## Improvements across iterations

The Laboratory 8 rubric supersedes the local skill's game-distribution mock-exam rubric. It removes the previous two-module decomposition task, minimum of four generic reliability mechanisms, and download-balancing requirement. Laboratory 7 assessments remain historical and use their original rubric.

## Open issues or unverified claims

- This task adapts evaluator instructions; it does not evaluate the student's architecture or validate runtime behavior.
- The drawing, bundled professor's theory, global skill copy, and historical reports were not changed.
- The assignment supplies no partial-credit formula or division of point 3's five points between the two iterations.

## Scoped evaluator run: point 1, 2026-10-01

- Evaluated point 1 from the current drawing, reading the local rubric and bundled professor's theory. Preserved the result in `Laboratorio8/reports/eval-report-it01.md`; points 2–8 remain unevaluated.
- Fresh evidence: `C:/Users/jeffr/AppData/Local/Temp/excalidraw-evaluation-OMPjNF/`. Viewed the overview and all 18 tiles. The evidence checker verified the source hash, all 244 active elements (80 texts and 76 arrows), coverage, and pixel-exact crops; no network failures were recorded.
- Source SHA-256: `576cc9b730bccc0cacc09e31b1ddc8643011ecdbb5f679bdbd3744f3345793b3`.
- Verdict: partially complies. The wholesale order-management title and Buyer, Driver, and Finance Worker roles fit the visible workflow. Two solution placeholders remain in iteration #1/#2 titles. Replacing these titles completes the missing point-1 obligation; constructing those architectures is a separate point-3 task.
- The drawing was unchanged; no numeric partial-credit score or runtime claims were made. Temporary render evidence may be removed by the host; the scoped report preserves findings and source identity.

## Scoped evaluator run: updated actors, 2026-10-01

- Preserved an actor-only review in `Laboratorio8/reports/eval-report-it02.md`. Company Buyer/Buyer, Driver, and Finance Worker fit their visible interactions; Company Buyer and Buyer need consistent naming or an explicit equivalence.
- Inspected the fresh overview and all 18 tiles for source SHA-256 `bb6705b9fb0b8496ea5045043aed3b7cb74e4a51cc6891fae8510c99092c46e8`. Evidence in `C:/Users/jeffr/AppData/Local/Temp/excalidraw-evaluation-WySWwV/` contains 257 active elements, 84 texts, and 81 arrows. The evidence checker passed; no network failures were recorded.
- Regenerated evidence after detecting a source change during inspection. Authentication and purchase submission should have distinct responsibilities: the visible Login Service to Purchase Service arrow labeled Purchase Order PDF needs clarification, independently of actor correctness.
- The drawing was unchanged; no full-rubric score or runtime validation was claimed.

## Scoped analysis: SPOFs and bottlenecks

- Preserved `Laboratorio8/reports/eval-report-it03.md`: Purchase Service and Customer Ranking Service are potential SPOFs under single-instance/no-fallback assumptions; Stock Evaluation Service and shared Order API/Order DB are potential bottlenecks under rising load.
- Fresh source SHA-256 `147387d203847bc625b16f0a6b584ed175affd30cb66851c6c20c3e3f9dbd3fc`; inspected all 451 active elements/145 texts and the overview plus 21 tiles. Evidence checker passed. No drawing changes or runtime measurements were made.
- Failure consequences and throughput constraints must justify these categories; arrow count alone does not. Repeated API/DB icons require an explicit shared-resource assumption.
- The user selected enterprise technology-equipment sales and distribution as the domain, superseding provisional wholesale/logistics/furniture interpretations. The current iteration titles reflect this choice.

## Scoped evaluator run: critical path

- Preserved item-5 review in `Laboratorio8/reports/eval-report-it04.md`. Verdict: partially complies. The green path needs a named scenario, completion condition, brief justification, reservation/persistence dependencies, and a distinction between scheduling alternatives and asynchronous notifications.
- Source SHA-256 `0f130fac9c458c2ed023ed652ec8dc38b64020b26ffe75c23710f333b7c2e8d9`; inspected 653 active elements/212 texts/199 arrows, the fresh overview, and all 30 tiles. Evidence checker passed in `C:/Users/jeffr/AppData/Local/Temp/excalidraw-evaluation-s9Bdkc/`.
- A partial-stock branch is valid when its buyer-acceptance scenario is explicit. Required stock reservation and API/DB persistence cannot be omitted merely because they are drawn as side branches. Logistics dependencies can be included or declared satisfied preconditions.
- The lower critical-path copy omits reliability elements present in the upper iteration #3; identify which version it represents. An asynchronous order-to-delivery-to-payment workflow must not be equated with a single blocking HTTP request. No drawing changes, timed longest-path calculation, or numeric score were made.

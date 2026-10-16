# Default rubric: Software Architecture Midterm — Laboratory 8

The starting artifact is iteration #3 of an undocumented, unscaled system. This rubric follows the user-supplied assignment, confirmed against the active exam text in `Laboratorio8/ep.excalidraw`, and supersedes the previous game-distribution mock-exam rubric.

The entire student's answer belongs in the Excalidraw. Brief answers and justifications within the canvas are sufficient where requested; chat answers and separate reports do not complete the submission. A separate report is not required. Read the mandatory professor's theory as specified in SKILL.md and use its applicable concepts when judging these rows. Do not impose the previous two-module decomposition exercise, a minimum of four generic reliability mechanisms, or download balancing.

## Criteria and supplied weights

| Point | Required work | Points |
| --- | --- | ---: |
| 1 | Reverse engineering, actors, and replacement of every solution placeholder | 2 |
| 2 | Five functional and five non-functional requirements | 2 |
| 3 | Iterations #2 and #1, applying modularization, coupling, and cohesion | 5 |
| 4 | Corrections to iteration #3, with justification | 2 |
| 5 | Critical path | 1.5 |
| 6 | SPOFs and bottlenecks in iteration #3 | 1 |
| 7 | Reliability for six specified cases, 0.75 per case | 4.5 |
| 8 | Two appropriate fitness functions | 2 |
| **Total** | | **20** |

Use these supplied weights only if a score is requested. The assignment does not specify how to divide point 3's five points between iterations or how to award partial credit; do not invent an official scoring formula. Compliance statuses remain the default output.

## 1. Reverse engineering and actors — 2 points

Deduce the system's purpose, identify its actors, and replace every `???` placeholder in the solution, including iteration titles and actor/component labels. Exclude placeholders quoted in the assignment. Confirm meaning through workflow names, operations, and a description or equivalent explicit context. Actor identities must fit their interactions; technical actors are acceptable if their role is clear. Do not prescribe an inferred domain or actor list as the only valid answer. Distinguish unclear identities from cosmetic typos.

## 2. Five functional and five non-functional requirements — 2 points

Count distinct requirements, not headings or duplicates. Require five functional behaviors and five quality/constraint requirements consistent with the inferred system and proposed architecture. More than five is not itself a failure unless exactly five is explicitly required. Identify vague or contradictory conditions without inventing thresholds. Teacher examples guide interpretation; do not blindly deduct for examples copied from the theory without noting the source of the ambiguity.

## 3. Iterations #2 and #1 — 5 points jointly

Assess this point in two rows: **3a: iteration #2** and **3b: iteration #1**. Both iterations must be drawn, clearly labeled, and traceable to the same system represented by iteration #3. A title, empty frame, generic definition, or prose list of services alone does not constitute an architectural iteration.

For each iteration, inspect meaningful responsibility grouping, visible named module boundaries or equivalent unambiguous grouping, cohesion within modules, and coupling through explicit dependencies or interfaces. Require enough concrete labels or brief annotations to explain the grouping and dependency choices. The iterations should show a coherent progression in architectural detail, preserving essential actors and behaviors while explaining deliberate changes. Do not require every fine-grained service from iteration #3 to appear separately in earlier iterations, impose a module count, or require an arbitrary technology or deployment style.

Apply the theory's Modularity, Cohesion, and Coupling sections. Small or numerous services alone do not prove low cohesion; inspect whether each module's responsibilities belong together. Repeated API/DB icons do not prove separate resources; check or flag unclear ownership. The five-point weight covers both iterations together, with no supplied subweights.

## 4. Correct iteration #3 and justify — 2 points

Require visible corrections to iteration #3 and brief justifications tied to concrete architectural problems. Inspect responsibility ownership, inappropriate fragmentation, resource duplication/ambiguity, or unnecessary dependencies as applicable. Generic advice or a named pattern alone does not establish a correction.

Compare against an authoritative baseline if available. Otherwise assess the current correction annotations and disclose that before/after changes cannot be confirmed. The original unscaled iteration is context, not proof that every service must be replicated under this point; point 7 defines the specific reliability cases. Editor-binding defects are not automatically architecture failures. Use the course's synchronous/asynchronous distinction when evaluating decoupling.

## 5. Critical path — 1.5 points

Require an identified operation and its necessary sequence, visibly highlighted or explicitly enumerated in the canvas with a brief explanation of why it gates completion. Anchor the path to iteration #3 or explicitly explain its mapping to the corrected design. Separate alternative branches and asynchronous side work from the selected completion path. Apply the theory's Critical path and synchronous/asynchronous distinctions. Do not invent a timed longest path without timing data or count every dependency as critical.

## 6. SPOFs and bottlenecks in iteration #3 — 1 point

Require both categories to be identified in iteration #3 and briefly explained through failure consequences, capacity/throughput constraints, and relevant deployment assumptions. Apply the theory's definitions: a SPOF concerns failure; a bottleneck concerns capacity/throughput. A singleton icon alone does not prove a singleton deployment. Repeated API/DB icons may denote a shared resource.

The conditional cases supplied in point 7 do not by themselves count as the student's analysis for point 6. Do not require measured runtime evidence for this drawing assignment. Mitigation is assessed under point 7; distinguish identified risks from corrected risks.

## 7. Reliability for six specified cases — 4.5 points, 0.75 per case

Assess each case separately. The assignment asks what to add **if** the named component is a SPOF or bottleneck; these are supplied scenarios, not empirical claims that the drawing proves each risk. Require visible mechanisms connected to the affected component and a brief explanation of how their placement addresses the specified failure or saturation condition. A generic reliability legend, an unconnected pattern name, or repeating the assignment text is insufficient.

| Evaluation row | Supplied scenario | What to inspect |
| --- | --- | --- |
| 7a | SPOF: Purchase Service | Continued purchase processing or bounded degradation when the service fails; make redundancy/routing/recovery or another defensible protection explicit. |
| 7b | SPOF: Customer Ranking Service | Protection of the dependent workflow when ranking fails, with explicit recovery, redundancy, or a justified fallback and its business consequences. |
| 7c | SPOF: Payment Confirmation Service | Protection and recovery of payment confirmation, including duplicate-effect prevention where retries or replay can repeat confirmation effects. |
| 7d | Bottleneck: Stock Evaluation Service | Protection or relief of stock-evaluation saturation, with explicit capacity/routing, buffering, isolation, or another justified mechanism and consistent stock decisions. |
| 7e | Bottleneck: Delivery Service | Protection or relief of delivery-processing saturation, distinguishing software-service capacity from physical delivery constraints where relevant. |
| 7f | Bottleneck: Order API / Order DB | An explicit account of the API/database dependency and protection or relief of the constrained resource; scaling only the API must not silently leave an identified database constraint unresolved. This pair is one case. |

These are review lenses, not a mandatory pattern list. Accept technically defensible alternatives supported by the drawing and professor's theory. No minimum count of distinct mechanisms applies beyond addressing all six cases. A shared mechanism may serve multiple cases if its placement and explanation cover each one; repeated icons alone do not prove coverage.

Use the professor's protection-of-experience/resources framing: check circuit breakers near failing dependencies, health checks for routing, bulkheads for isolation, rate limiting/throttling for saturation, and bounded retries where applicable. Circuit breaking alone does not prove continued availability; replicas alone do not prove failover or database capacity. For asynchronous buffering/recovery, inspect the declared acknowledgement, retry, and failure-handling behavior as relevant. Do not blindly retry payments or claim queues remove sustained capacity limits. Do not presume replicas, durability, or recovery from a service label. No implemented infrastructure or measured resilience tests are required.

With an authoritative baseline, distinguish additions from pre-existing features. Without one, disclose the inability to confirm additions rather than automatically failing a supported design.

## 8. Two appropriate fitness functions — 2 points

Require at least two distinct, architecture-relevant checks with observable measures, acceptance conditions, and a measurement method or unambiguous test context. Connect them to the proposed architecture's important properties rather than accepting generic metrics without a check. More than two is not itself a failure unless exactly two is explicitly required. Apply the course's automated/continuous verification framing, percentiles, and availability/reliability definitions where relevant. No implemented test code is required for this drawing assignment.

Additional weaker functions do not invalidate two adequate checks unless contradictions invalidate their targets; distinguish contradictions already present in teacher examples. Different observation windows are not automatically contradictory: they may be compatible targets of different strictness. Explain whether the problem is an actual inconsistency, unclear mapping, or a stronger additional check. Do not invent acceptance thresholds on the student's behalf.

## Original assignment wording

Problema: Se le ha dado la iteración 3 ( sin escalar ) de un sistema que el arquitecto previo dejo sin documentar.

1. (2 pts) Haga ingeniería inversa: deduzca de qué se trata el sistema e identifique a los actores. Reemplace TODOS los ??? por lo que ha identificado.
2. (2 pts) Elabore 5 requerimientos funcionales y 5 no funcionales.
3. (5 pts) Elabore la iteración #2 y #1. (aplique modularizacion, coupling y cohesion)
4. (2 pts) Corrija la arquitectura de la iteración #3. (justifique)
5. (1.5 pts) Identifique el critical path.
6. (1 pt) SPOF(s) y bottleneck(s) de la iteración 3.
7. (4.5 pts, 0.75 por caso) Agregue elementos de reliability para cada caso si:

   SPOF:

   - a) Purchase Service
   - b) Customer Ranking Service
   - c) Payment Confirmation Service

   Bottleneck:

   - a) Stock Evaluation Service
   - b) Delivery Service
   - c) Order API / Order DB

8. (2 pts) Elija 2 Fitness Functions adecuados para la arquitectura planteada.

TOTAL: 20 puntos

(*) Todos los cambios son en su excalidraw.

(**) Hacer un reporte no es necesario. Responda/Justifique brevemente lo preguntado.

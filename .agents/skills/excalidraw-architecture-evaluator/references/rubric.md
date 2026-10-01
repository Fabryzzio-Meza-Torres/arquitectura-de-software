# Default rubric: Software Architecture Midterm

The entire student's answer belongs in the Excalidraw. Brief explanations within the canvas are valid where requested; chat answers and separate reports do not complete the submission. Read the mandatory professor's theory as specified in SKILL.md and use its applicable concepts when judging these rows.

## 1. Reverse engineering and actors

Deduce the system's purpose, identify its actors, and replace every `???` placeholder in the solution. Exclude placeholders quoted in the assignment. Confirm meaning through workflow names, operations, and a description or equivalent explicit context. Technical actors such as a scheduler are acceptable if their role is clear. Distinguish unclear identities from cosmetic typos.

## 2. Five functional and five non-functional requirements

Count distinct requirements, not headings or duplicates. Require five functional behaviors and five quality/constraint requirements consistent with the drawing. More than five is not itself a failure unless exactly five is explicitly required. Identify vague or contradictory conditions without inventing thresholds. Teacher examples guide interpretation; do not blindly deduct for examples copied from the theory without noting the source of the ambiguity.

## 3a. Additional modular decomposition

The starting diagram has only two modules. Require an additional meaningful decomposition with **drawn boundaries and names**. Service names or a prose domain list alone do not satisfy this. Check ownership and cohesion of contents. Workflow frames may coexist with domain modules if their relationship is explained; do not impose an arbitrary final module count.

## 3b. Cohesion and coupling

Require specific analysis of responsibilities and dependencies, including relevant repeated APIs/DBs and cross-dependencies. Generic definitions are insufficient. Repeated icons do not prove separate resources; explain unclear ownership. Concrete written annotations may satisfy the analysis; highlighting is not mandatory when equivalent specific prose is present. Apply the theory's Modularity, Cohesion, and Coupling sections.

Small or numerous services alone do not prove low cohesion; inspect whether the responsibilities within each proposed module belong together.

## 4. Architectural corrections

Require visible corrections addressing the identified problems: responsibility ownership, inappropriate fragmentation, resource duplication/ambiguity, or unnecessary dependencies as applicable. Compare against an authoritative baseline if available. Otherwise assess the current proposal/correction annotations and disclose that before/after changes cannot be confirmed. A named pattern alone does not resolve an unrelated problem. Editor-binding defects are not automatically architecture failure. Use the course's synchronous/asynchronous distinction when evaluating decoupling.

## 5. Reliability: at least four elements, placement justified

Require at least four distinct mechanisms with visible placement and brief explanations connecting each to a failure/saturation condition and protection. Count meaningful mechanisms rather than repeated icons or parts of one recovery flow. Use the professor's reliability patterns and resource-protection framing. A cache/CDN needs an explained resilience role, not just a speed claim. Do not presume replicas, failover, durability, or recovery from a service label. With a baseline, distinguish additions from pre-existing features; without one, disclose the inability to confirm additions rather than automatically failing the design.

## 6. Critical path

Require an identified operation and its necessary sequence, visibly highlighted or explicitly enumerated in the canvas with a brief explanation of why it gates completion. Buying, downloading, and publishing may have different paths. Apply the theory's Critical path and synchronous/asynchronous distinctions. Do not invent a timed longest path without timing data or count every dependency as critical.

## 7. SPOF and bottleneck

Require both categories to be identified and explained through consequences and deployment assumptions. Apply the theory's definitions: SPOF concerns failure; bottleneck concerns capacity/throughput. A singleton icon alone does not prove a singleton deployment. Mitigation is not an additional obligation under this row unless requested elsewhere; distinguish identified from corrected risks.

## 8. Download load balancing

Require a named algorithm, its location, and justification based on download workload and server capacity. A CDN label is not an algorithm. Use the theory's Round Robin, Weighted Round Robin, Least Connection, and Weighted Least Connection descriptions. Accept a defensible choice under the stated assumptions, rather than treating one algorithm as universally correct. Verify unfamiliar external claims against primary documentation when necessary.

## 9. Two appropriate fitness functions

Require at least two distinct, architecture-relevant checks with observable measures, acceptance conditions, and a measurement method or unambiguous test context. More than two is not itself a failure unless exactly two is explicitly required. Apply the course's automated/continuous verification framing, percentiles, and availability/reliability definitions where relevant. No implemented test code is required for this drawing assignment. Additional weaker functions do not invalidate two adequate checks unless contradictions invalidate their targets; distinguish contradictions already present in teacher examples.

Different observation windows (for example monthly and annual availability) are not automatically contradictory: they may be compatible targets of different strictness. Explain whether the problem is an actual inconsistency, unclear mapping, or simply a stronger additional check.

## Original assignment wording

1. Haga ingeniería inversa: deduzca de qué se trata el sistema e identifique a los actores. Reemplace TODOS los ??? por lo que ha identificado.
2. Elabore 5 requerimientos funcionales y 5 no funcionales.
3. Modularidad: el sistema está agrupado en solo 2 módulos. a) Proponga una descomposición adicional en módulos, dibuje sus límites y nómbrelos. b) Identifique problemas de cohesión y acoplamiento (ej. BD y APIs repetidas, dependencias cruzadas).
4. Corrija la arquitectura.
5. Agregue elementos de reliability (mínimo 4). Justifique su ubicación.
6. Identifique el critical path.
7. SPOF y bottleneck.
8. Elija el algoritmo adecuado de balanceo de carga para la descarga de juegos. Justifique.
9. Elija 2 Fitness Functions adecuados para la arquitectura planteada.

(*) Todos los cambios son en su excalidraw.
(**) Hacer un reporte no es necesario. Responda/Justifique brevemente lo preguntado.

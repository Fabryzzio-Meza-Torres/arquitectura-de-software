# Midterm analysis — iteration 03

Scope: identify two potential SPOFs and two potential bottlenecks in iteration #3, as requested. No compliance verdict or score is assigned.

The current drawing was freshly extracted and rendered in `C:/Users/jeffr/AppData/Local/Temp/excalidraw-evaluation-pNl5Mn/`. Source SHA-256: `147387d203847bc625b16f0a6b584ed175affd30cb66851c6c20c3e3f9dbd3fc`. Read all 145 texts and inspected geometry/endpoints of 451 active elements, including 134 arrows. Viewed the overview and all 21 tiles. The evidence checker passed source identity, coverage, and crop validation; no network failures occurred. Read the local rubric and bundled theory completely, applying its SPOF and Bottleneck definitions.

| Category | Candidate | Reason and assumption |
| --- | --- | --- |
| SPOF | Purchase Service | The visible order-intake route passes through this service before Priority Service. If it is a single instance without failover, its failure prevents new purchase orders from entering this workflow; previously accepted work need not stop. |
| SPOF | Customer Ranking Service | The route from Pending Orders passes through ranking to Order Validation, and ranking also connects to Scheduling. If ranking is a mandatory dependency with one instance and no fallback, failure blocks progression through these routes. |
| Bottleneck | Stock Evaluation Service | It receives validated orders, consults Product API, and selects no/partial/complete-stock branches and reservation work. Large orders or high arrival rates can exhaust its processing capacity and delay downstream preparation. This is a capacity hypothesis, not a measured slowdown. |
| Bottleneck | Order API / Order DB | Pending orders, scheduling, new orders, delivery confirmation, payment confirmation, and exception handling access Order API/DB icons. If these icons denote shared resources, concurrent reads/writes can saturate database I/O, connection pools, or contend on records, limiting API throughput. Shared ownership is not explicit in the drawing. |

Arrow count alone establishes neither failure impact nor capacity limits. A service with few arrows can be an essential entry point; a highly connected component can have sufficient capacity and redundant deployment. The point-7 scenarios do not prove point-6 risks. The drawing was not modified and no runtime tests were performed.

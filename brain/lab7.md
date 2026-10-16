# Laboratory 7 Memory

## Exercise overview

The reviewed artifact is `Laboratorio7/solucion-simulacro-ep.excalidraw`, a LATAM game-distribution architecture drawing containing purchase/download and publication/patch/deletion workflows. No `study-case/` directory was available during this review; assignment-level compliance remains unverified.

## Activities completed

- Extracted editable text, components, and arrow bindings from the existing drawing.
- Rendered the drawing and visually reviewed both workflow sections on 2026-10-01.

## Achievements and validation evidence

- Export: `Laboratorio7/solucion-simulacro-ep.png`.
- Detailed inspection crops: `Laboratorio7/validacion-compra.png` and `Laboratorio7/validacion-publicacion.png`.
- Findings: `Laboratorio7/reports/connection-validation-it01.md`.
- Of 98 arrows, 83 have two bindings and 15 have one binding. All referenced IDs exist. The intended relationships of the 15 one-sided arrows are visually identifiable.
- Three double-bound arrows incorrectly reference the same shape at both ends; their visual geometry connects distinct components.

## Lessons learned

- A free endpoint is not sufficient evidence of a missing visual relationship: actors and branch junctions can convey an identifiable path without a shape binding.
- Conversely, existing endpoint IDs do not prove correct bindings. Compare binding semantics with rendered geometry.

## Improvements across iterations

The initial JSON-only interpretation was refined through visual inspection: the three apparent self-connections are incorrect bindings rather than visually drawn self-loops.

## Open issues or unverified claims

- No bindings or source elements were changed.
- Binding repair and clarification of small endpoint gaps remain pending.
- This review does not validate assignment compliance, architecture fitness targets, evaluator results, or runtime behavior.

## Reusable architecture evaluator

- Created the global skill `C:/Users/jeffr/.codex/skills/excalidraw-architecture-evaluator/SKILL.md` using the nine-item midterm rubric supplied by the user. Its output has ten rows (3a and 3b separated) and the columns `Punto`, `Evaluación`, `Evidencia`, and `Solución`; statuses are `Cumple`, `Parcialmente`, and `No cumple`.
- Every evaluation must read the current `Laboratorio8/SA_theory.md`, extract the current drawing, and inspect fresh renders before issuing a completed table. The rubric defines the requested work; the professor's theory guides technical judgments and concrete remedies without adding unrelated obligations.
- The helper was exercised on the 317-element submission: all active element records and 105 text records were preserved; 98 arrows were extracted; the source hash remained unchanged; the full render and 20 overlapping tiles covered an 8046-by-6950 scene with no failed network requests. An additional fixture verified embedded-image rendering and separation of deleted evidence.
- Validation evidence is under `C:/Users/jeffr/.codex/visualizations/2026/10/01/01a0f8ac-34a9-7b90-b225-97e1a78edf00/evaluator-skill-smoke-test/`. The skill frontmatter passed `quick_validate.py`. These are helper/packaging checks and representative visual inspections, not a new full evaluator run or independent behavioral validation.
- Reliability additions cannot be proven without an authoritative baseline. A similarly named drawing is not automatically authoritative. Extra requirements or fitness functions alone are not grounds for failure unless exact counts are explicitly required.
- At the user's request, added the repository-local skill at `.agents/skills/excalidraw-architecture-evaluator/` with `references/SA_theory.md` copied byte-for-byte from `Laboratorio8/SA_theory.md`. The local skill reads this bundled reference through a relative link, superseding its original dependency on the absolute laboratory path. The global skill was retained. Matching SHA-256 hashes and skill validation confirm the copy and packaging; this relocation does not constitute a new architecture evaluation.
- Optimized both evaluator helper copies to reuse a minified export bundle and crop the full-resolution PNG with native canvas instead of taking a screenshot per tile. A cached-runtime comparison on the same source snapshot measured 21.494 seconds before and 11.843 seconds after (one measurement each; not a benchmark median). The original and optimized overviews were pixel-identical, and `scripts/check-evidence.py` verified the source hash, element preservation, all 20 tiles, pixel-exact crops, and full scene coverage. Scenes requiring a scaled overview retain full-resolution tile screenshots. Evidence is in the `speed-before/` and `speed-after-warm/` directories beside the original skill validation artifacts. Initial dependency installation and visual evaluation time are outside the warm-runtime speed claim.

## Full evaluator run: 2026-10-01

- Tested the repository-local evaluator against the current `Laboratorio7/solucion-simulacro-ep.excalidraw`, using the user-supplied midterm rubric and reading the bundled professor's theory completely. This full assessment supersedes the earlier statement that assignment compliance had not been evaluated; the earlier connection review and helper checks remain separate historical evidence.
- Fresh evidence is in `C:/Users/jeffr/.codex/visualizations/2026/10/01/01a0f8ac-34a9-7b90-b225-97e1a78edf00/evaluator-run-01/`. Read all 317 active elements, including 105 text records and 98 arrows, and visually inspected the overview and all 20 tiles. Rendering reported zero network failures. `check-evidence.py` verified the source hash, active records, full tile coverage, and pixel-exact crops.
- Source SHA-256: `a2ab07beb6e8d97fe4104679a06b156cad0087320930187087650c07314e7505`. The drawing and theory were left unchanged. No separate evaluation report was created; the assessment was returned in chat as requested.
- Findings: rows 1, 2, and 9 comply; rows 3b, 4, and 5 partially comply; rows 3a, 6, 7, and 8 do not comply. There are 12 functional requirements, 9 non-functional requirements, and 9 fitness functions; extra items alone are not failures. Only the two workflow boundaries are drawn. Critical-path identification, explicit SPOF/bottleneck analysis, and a justified download-balancing algorithm are absent from the solution content.
- Circuit breaking and download recovery are visible, but four distinct reliability mechanisms with placement justifications are not established. Repeated API/DB icons have unclear ownership; they do not establish separate resources or singleton deployments. The payment-validation branch needs an explicit success condition before granting library access. Without an authoritative baseline, before/after corrections and added reliability mechanisms cannot be confirmed.
- Verification scope: this is a complete artifact-level evaluation, not runtime validation or execution of the declared fitness tests. The 15 one-sided arrows remain visually interpretable; the three incorrect self-bindings are editor defects rather than drawn self-loops.

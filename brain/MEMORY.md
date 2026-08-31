# Architecture Course Project Memory

This directory is the durable memory of the Software Architecture laboratory monorepo. It records what was built, what worked, what failed, and which improvements should guide the next laboratory.

This file contains the stable conventions and cross-laboratory lessons. Each `labN.md` file contains the activity history, achievements, lessons, and improvements specific to that laboratory.

## Required reading order

1. Always read this file before working in the repository.
2. For an existing laboratory, read its `brain/labN.md` file.
3. For a new laboratory, read all previous laboratory memories, starting with the most recent one, to reuse accumulated lessons.
4. Read the target laboratory's `study-case/` before changing its specification, requirements, evaluator, design, or implementation.

| Scope           | Laboratory memory    | Primary assignment source                                    |
| --------------- | -------------------- | ------------------------------------------------------------ |
| `Laboratorio1/` | [`lab1.md`](lab1.md) | [`../Laboratorio1/study-case/`](../Laboratorio1/study-case/) |
| `Laboratorio2/` | [`lab2.md`](lab2.md) | [`../Laboratorio2/study-case/`](../Laboratorio2/study-case/) |
| `Laboratorio3/` | [`lab3.md`](lab3.md) | [`../Laboratorio3/study-case/`](../Laboratorio3/study-case/) |

Memory provides a starting point, not permission to copy domain assumptions. The current study case and the user's explicit instructions always take precedence.

## Standard structure for new laboratories

Starting with the next laboratory, preserve this baseline structure:

```text
LaboratorioN/
├── agents/
│   └── eval-spec.md
├── core/
│   ├── summary.md
│   ├── problem.md
│   ├── objective.md
│   ├── out-of-scope.md
│   ├── key-product-concepts.md
│   ├── users-and-their-needs.md
│   ├── key-product-decisions.md
│   ├── expected-user-experience.md
│   ├── main-flows.md
│   ├── staged-scope.md
│   └── acceptance-criteria.md
├── people/
│   └── <one-file-per-user>.md
├── reports/
│   └── report-iteration-NN.md
├── requirements/
│   ├── functional-requirements.md
│   └── no-functional-requirements.md
└── study-case/
    └── <assignment-source>.md
```

The six required areas are:

- `agents/`: the evaluator prompt, always `eval-spec.md`.
- `core/`: exactly the 11 product-specification documents listed above.
- `people/`: one Markdown file per model user or persona.
- `reports/`: immutable evaluation history, one file per iteration.
- `requirements/`: the functional and non-functional requirement backlogs.
- `study-case/`: the original task or assignment source.

Additional folders such as `design/`, `architecture/`, or an implementation directory are allowed only when the assignment needs them. They extend the baseline; they do not replace it.

## Standard workflow

Work in this order unless the user explicitly requests another sequence:

1. Read `study-case/` and extract the problem, constraints, deliverables, actors, and quantitative targets.
2. Define the model users in `people/` without inventing actors outside the case.
3. Complete all 11 `core/` documents from summary through acceptance criteria.
4. Write `requirements/` using the format required by the study case.
5. Configure or update `agents/eval-spec.md` so its readiness gate, rubric, and output are explicit.
6. Run the evaluation from scratch and save a new immutable file in `reports/`.
7. Apply improvements, rerun the evaluator, and preserve every iteration.
8. Record durable achievements, lessons, and improvements in the corresponding `brain/labN.md` file.

## Cross-laboratory conventions

- Keep work inside the requested laboratory unless the task is explicitly cross-cutting.
- Treat the study case as the primary source for scope, deliverables, constraints, and numeric targets. Do not invent thresholds.
- Maintain traceability across `people/`, `core/`, `requirements/`, `agents/`, and `reports/`.
- Evaluators are Markdown prompts stored in `agents/eval-spec.md`, not application code.
- Never overwrite an evaluation report. Use a new sequential iteration file.
- Use lowercase directory names for new laboratories and verify exact paths before editing older laboratories with historical naming differences.
- After deleting or renumbering requirements, mechanically verify IDs, cross-references, and links.
- A structural check does not prove that the evaluator ran or that a POC works. State exactly what was validated.

## Cross-laboratory lessons

### Independent evaluation

- Do not pre-label relationships the evaluator is meant to infer. A persona-mapping column can bias relevance and coverage judgments.
- Detect zero-coverage needs before scoring individual requirements. Otherwise, a missing requirement is invisible to pair-based scoring.
- Keep `eval-spec.md` as the single source of truth for the rubric. Historical reports may use older scales and must remain clearly historical.
- Every partial score must include the concrete path to the maximum score.
- Honor the evaluator's readiness gate. If mandatory spec sections are missing, report `NOT EVALUABLE` or the rubric's equivalent instead of inventing a numeric score.

### Requirement quality

- Use mandatory, observable, testable language. Avoid words such as “fast,” “adequate,” or “friendly” without objective conditions.
- Keep each requirement atomic. Split independent features that happen to be joined with “and.”
- Do not duplicate rules or thresholds. Reference the authoritative requirement ID when possible.
- When the case demands resilience, describe the failure condition, mitigation, limit, and observable outcome.
- Derive quantitative thresholds from the study case or an explicit documented product decision.
- Follow the requirement format imposed by each assignment. Lab 1 used self-contained requirement text, while Lab 3 explicitly required short backlog titles.

### Specification and implementation consistency

- A state machine declared in the spec is an architecture contract. Every state and transition must be reachable and enforced in code.
- Persisting a status is insufficient if it does not trigger the promised business consequence.
- Distinguish domain personas from secondary or technical accounts required by security controls.
- Surface conflicts between authoritative documents instead of silently choosing the easiest interpretation.
- An end-to-end happy path must exercise the interface used by every actor. Direct API tests validate a different layer.

## Memory maintenance standard

After a meaningful activity, update the relevant `labN.md` with only durable information:

- **Activity:** what was attempted and its scope.
- **Achievement:** what was completed and the evidence that supports it.
- **Lesson:** what should be reused or avoided later.
- **Improvement:** what changed between iterations and why it produced a better result.
- **Open issue:** what remains unverified or intentionally deferred.

Do not turn memory into a raw activity log. Exclude transient command output, speculative ideas, and details that can be recovered cheaply from Git. Preserve corrections and explain what superseded the previous rule.

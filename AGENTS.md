# AGENTS.md — Project Memory Router

These instructions apply to the entire monorepo.

## Purpose of `brain/`

The `brain/` directory is the project's durable context. It records the work completed in each laboratory, the evidence-backed achievements, the lessons learned, and the improvements made across iterations. Its purpose is to give an agent a reliable starting point for both ongoing work and future laboratories.

Memory is guidance, not a replacement for current evidence. The target laboratory's study case, current files, and explicit user instructions remain authoritative.

## Mandatory context routing

Before doing any work:

1. Read [`brain/MEMORY.md`](brain/MEMORY.md).
2. Identify whether the task concerns an existing laboratory, a new laboratory, or the whole monorepo.
3. Follow the matching route below.

| Task scope | Additional context to read |
| --- | --- |
| `Laboratorio1/` | [`brain/lab1.md`](brain/lab1.md), then [`Laboratorio1/study-case/`](Laboratorio1/study-case/) |
| `Laboratorio2/` | [`brain/lab2.md`](brain/lab2.md), then [`Laboratorio2/study-case/`](Laboratorio2/study-case/) |
| `Laboratorio3/` | [`brain/lab3.md`](brain/lab3.md), then [`Laboratorio3/study-case/`](Laboratorio3/study-case/) |
| A new `LaboratorioN/` | Read all existing `brain/lab*.md` files from newest to oldest, then read the new `study-case/` |
| Cross-laboratory work | Read every affected laboratory memory and the directly relevant source files |

For a new laboratory, reuse the standard structure and workflow from `brain/MEMORY.md`, but derive actors, domain rules, scope, requirement format, and thresholds from the new study case.

## Working rules

- Keep changes inside the laboratory requested by the user unless the task is explicitly cross-cutting.
- Use the local `study-case/` as the primary assignment source and the current `core/` as the product specification.
- Do not transfer domain-specific rules from a previous laboratory into a new one without evidence.
- Preserve all evaluation reports. Every evaluator run must create a new iteration file in `reports/`.
- Distinguish document/link/ID validation from evaluator execution and runtime or end-to-end validation.
- Respect existing user changes and historical naming in older laboratories; apply the standardized lowercase structure to new laboratories.

## Project-local skills

Reusable project skills live in [`.agents/skills/`](.agents/skills/). Before starting a specialized task, inspect the available skill names and read the matching `SKILL.md` completely. Load only skills relevant to the current task; do not apply every skill indiscriminately.

Current routing:

- Specification-first feature or POC work: `spec-driven-development`.
- FastAPI backend work: `fastapi`.
- React frontend implementation or performance: `vercel-react-best-practices`.
- UI and accessibility review: `web-design-guidelines`.
- Markdown architecture diagrams and rendered exports: `mermaid-skill`.
- Editable hand-drawn architecture diagrams and Excalidraw exports: `excalidraw`.
- Current library or framework documentation: `context7-mcp`.
- Token-efficient responses when explicitly requested: `caveman`.

Remote skill versions are recorded in `skills-lock.json`. Review external skill changes before updating them because skills execute with the agent's permissions.

## Maintaining project memory

When a task produces a durable achievement, lesson, correction, or improvement, update the corresponding `brain/labN.md` before considering the work complete. Record the result and its evidence, not a transcript of the work.

For a newly created laboratory, also create `brain/labN.md` with these sections:

1. Exercise overview.
2. Activities completed.
3. Achievements and validation evidence.
4. Lessons learned.
5. Improvements across iterations.
6. Open issues or unverified claims.

Update `brain/MEMORY.md` only when a convention or lesson is reusable across laboratories. Do not weaken or erase prior learning without documenting what supersedes it.

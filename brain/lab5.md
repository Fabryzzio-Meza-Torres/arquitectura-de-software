# Lab 5 - Genius-x

## Exercise overview

This laboratory designs a reliable Harness around an existing local LLM to manage incidents for Balbuena Consulting Enterprise ERP products. The original source is [`../Laboratorio5/study-case/Lab5.pdf`](../Laboratorio5/study-case/Lab5.pdf); [`../Laboratorio5/study-case/contexto.md`](../Laboratorio5/study-case/contexto.md) separates PDF facts from the image and user clarifications.

## Activities completed

- Created `study-case/` with a faithful PDF copy, the context image, and documented provenance.
- Completed the eleven `core/` documents and aligned the three `people/` profiles.
- Reworked 20 FRs and 15 NFRs into sequential-ID tables, with verifiable semantics in flows and AC.
- Created `agents/eval-spec.md` to inspect sources, people, core, backlog, diagram, failures, and single points of failure, then performed the first document-level evaluation.
- Added `Laboratorio5/README.md` as the lab entry point, covering the problem, human-control boundary, architecture principles, reading path, and documented validation limits.

## Achievements and validation evidence

- [`../Laboratorio5/reports/report-iteration-01.md`](../Laboratorio5/reports/report-iteration-01.md) records 18 needs, 35 requirements, 7 documentary gates, and a 9.45/10 diagnostic score; the verdict is `COHERENT FOR REVIEW`, not runtime validation.
- The PDF copy has the same SHA-256 hash as the source. Reviewed local Markdown links resolve; FR-01-FR-20 and NFR-01-NFR-15 are unique and sequential; `git diff --check` found no errors.
- The final model keeps people as the only solution executors and closure decision-makers; the LLM and its tools do not write to production. Client incidents preserve their deadline when escalated.

## Lessons learned

- The case sets a **response** SLA, not a resolution SLA; measuring until the first substantive human response is an explicit product decision.
- The diagram's `Nightly Retrain` label points to the embeddings store: the documented scope interprets it as a nightly RAG-index update without training the LLM.
- Deduplicating tickets and notifications requires an operation identity and retention of the pending event if Slack fails; exactly-once external delivery must not be promised without evidence.

## Improvements across iterations

- First iteration: drafts let the LLM resolve or close tickets and mixed capabilities with attributes in NFRs. The specification moved execution and closure to support/engineering, separated FR/NFR, and documented load, cache, and recovery scenarios.
- Normalized the architecture-artifact directory to lowercase `diagram/`, removing the `Diagram/` versus `diagram/` Git path collision on case-insensitive Windows filesystems.

## Open issues or unverified claims

- The diagram does not establish recovery or redundancy for the ticket database, queue, deduplication store, RAG index, or LLM service; these single points of failure require design and testing.
- Executed tests for 10,000+ weekly incidents, 50-100 engineers, SLA, Slack integration, permissions, sandbox, and recovery are missing.
- A future revision can clarify `Nightly Retrain` and add explicit ACs for peak/failure alerts and role-based data isolation.

# Lab 5 — Genius-x

## Overview

This week, the architecture exercise defines **Genius-x**, a reliable Harness around an existing local LLM for managing ERP incidents at Balbuena Consulting Enterprise. The organization receives many reports that are caused by user error, so the design helps Support resolve straightforward cases while escalating technical incidents to Engineering with their full context.

Genius-x assists investigation through grounded retrieval and controlled tools, but it is not an autonomous incident resolver: people review every proposal, perform every production intervention, and decide when a ticket can be closed.

## Challenge and goals

The study case requires an architecture that can handle three incident types, incorrect or outdated LLM answers, and failures of the local LLM or integrations. It must also account for an initial peak of **10,000 or more incidents per week** and **50–100 engineers**.

The design targets these response commitments:

- **Customer Escalations:** first substantive human response within one day.
- **Engineering Escalations:** first substantive human response within three days.

Total resolution time is recorded separately because the case does not define a closure deadline.

## Architecture principles

- **Human authority:** the LLM proposes; Support and Engineering review, act, and close tickets.
- **Safe assistance:** guardrails block destructive or sensitive tool actions, MCP queries are read-only, and trials run in an isolated sandbox.
- **Reliable workflow:** idempotency and notification deduplication prevent duplicate work; bounded retries, circuit breaking, fallback, and a dead-letter queue keep incidents visible when dependencies fail.
- **Traceable recovery:** ticket history is retained when a proposal is rejected, an incident is reopened, or a case is escalated.
- **Grounded answers:** RAG uses validated sources; the nightly process updates the RAG index rather than training the LLM.

The editable architecture source is [final_architecture.excalidraw](diagram/final_architecture.excalidraw). Additional diagram artifacts are available in [diagram/](diagram/).

## Main flows

1. **Client report and Support resolution:** Support registers a customer escalation, optionally consults the Harness, reviews the proposal, performs the solution, and records the outcome.
2. **Engineering escalation:** unresolved Support tickets retain their context and deadline, are assigned to Engineering, and produce one effective notification.
3. **Engineering incident:** an engineer registers and investigates a technical escalation with contextual assistance, then records the human outcome.
4. **Reopening:** a wrong or outdated response can reopen a ticket, preserve its history, and trigger reassessment or escalation.
5. **Dangerous proposal or outage:** guardrails stop unsafe actions; timeout, retry, circuit breaker, and fallback route the incident to human review without blocking it.

## Repository guide

| Directory | Contents |
| --- | --- |
| [study-case/](study-case/) | Original assignment, source context, and clarifications. |
| [people/](people/) | Personas for Support, Engineering, and Engineering Management. |
| [core/](core/) | Product summary, decisions, scope, main flows, and acceptance criteria. |
| [requirements/](requirements/) | Functional and non-functional requirement backlogs. |
| [diagram/](diagram/) | Editable architecture diagrams and the exported image. |
| [agents/](agents/) | The specification-evaluation prompt. |
| [reports/](reports/) | Immutable results of specification evaluation iterations. |

## How to review the lab

1. Start with [study-case/contexto.md](study-case/contexto.md) to distinguish the original assignment from the supplied clarifications.
2. Read the personas in [people/](people/) and the product definition in [core/](core/).
3. Trace the flows to the backlogs in [requirements/](requirements/) and to [diagram/final_architecture.excalidraw](diagram/final_architecture.excalidraw).
4. Review [agents/eval-spec.md](agents/eval-spec.md) and [reports/eval-report-it01.md](reports/eval-report-it01.md) for the documented evaluation evidence.

## Validation status

The first specification evaluation found the documentation ready for review, with 20 functional requirements, 15 non-functional requirements, 18 documented needs, and no uncovered need. It is a document-and-diagram evaluation only: no LLM, Slack integration, load test, permission test, or end-to-end implementation was executed.

Known architecture risks include recovery for the ticket database, queue, deduplication store, RAG index, and LLM service. These require implementation-level design and testing in a subsequent phase.

# Software Engineer — Julia Saenz

## Who they are

Julia represents the **Engineer in the Engineering Area** of Balbuena Consulting
Enterprise. She works on more complex technical incidents, whether generated directly by
her own area (Engineering Escalations) or forwarded from Support when the Harness fails to
resolve them. She has deeper technical access than Eric (databases, repositories, internal
documentation), and her time is more expensive, so the system must avoid escalating tickets
to her that the LLM could have solved on its own.

## Role in the system

Julia can generate tickets directly toward the Harness (Engineering Escalations), query
relevant information to resolve a problem (via RAG, MCP to databases, documentation and
repositories), and receive tickets that were automatically escalated from Support. When she
resolves a ticket, she returns it to the Harness indicating whether it was fixed or not. If
the Harness's original answer was wrong, she is the one who receives the reopened ticket to
give it a definitive fix. She can also close tickets, just like the Support area.

## Goals

- Only receive incidents that genuinely require engineering intervention.
- Get enough context from the Harness (code, databases, past tickets) to resolve issues
  quickly without repeating investigation the LLM already did.
- Meet the 3-day SLA for Engineering Escalations even during load spikes.
- Avoid the same escalated ticket reaching her twice (idempotency in the Slack escalation).
- Trust that the Harness did not execute any risky action without approval before the
  ticket reached her.

## Needs from the system

- A clear channel (Slack via MCP) to receive escalated tickets, routed to her manager
  (Jesús Bellido) and forwarded to her team, without duplicates.
- MCP access to the company's databases and documentation to investigate the incident with
  full context.
- Visibility into the ticket's history: what the Harness tried, which RAG results it used,
  why it couldn't resolve the issue.
- The ability to generate her own tickets (Engineering Escalations) toward the Harness to
  ask for help or log internal findings.
- The ability to mark a ticket as resolved or "not resolved" so it is correctly cataloged
  and feeds the RAG during the nightly retraining.
- An approval mechanism (guardrails) that asks her for explicit confirmation before the LLM
  executes sensitive actions such as deleting data.

## Pain points

- Receiving escalations that the Harness could have resolved with better context or
  memory.
- The LLM wasn't learning from previously resolved tickets, generating repeated work.
- Lack of traceability: it isn't always clear what steps the Harness followed before
  escalating.
- Risk of a poorly handled escalation (without idempotency) reaching her duplicated via
  Slack, causing confusion about who owns it.
- Pressure from spikes of 10,000+ incidents per week, especially in the first week of the
  month, which can overload both the LLM and her own work queue.

## Main flows this role participates in

1. Generate a ticket (Engineering Escalation) directly toward the Harness.
2. Query relevant information from the Harness to resolve an incident.
3. Receive a ticket automatically escalated from Support (via Slack/MCP).
4. Resolve the ticket and return the result to the Harness.
5. Receive a reopened ticket because the Harness's original answer was incorrect.

## What this role expects from Genius-x (Harness)

- Only genuinely requiring incidents reach her, matching her access level and expertise.
- Accumulated, up-to-date context (self-feeding RAG, MCP to databases) so she doesn't start
  from zero on every ticket.
- Idempotent escalation: the same incident never generates duplicate notifications or
  tickets in Slack.
- Compliance with the 3-day SLA even during load spikes, thanks to priority queues and load
  balancing.
- Strong guardrails that prevent the LLM from executing destructive actions without her or
  her manager's approval.

## Success criteria

- Julia only receives escalations that genuinely required engineering intervention.
- She resolves 100% of her assigned tickets within the 3-day SLA.
- No escalation ever reaches her duplicated due to missing idempotency.
- Knowledge generated while resolving a ticket becomes available to the Harness the next
  time a similar incident occurs.

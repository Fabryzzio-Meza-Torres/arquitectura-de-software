# Functional requirements - Genius-x

Each row identifies one capability. Observable conditions and outcomes are detailed in [`../core/9. main-flows.md`](../core/9.%20main-flows.md) and [`../core/11. acceptance-criteria.md`](../core/11.%20acceptance-criteria.md).

| ID | Requirement |
| --- | --- |
| FR-01 | Register a client-origin ticket. |
| FR-02 | Register an engineering-origin ticket. |
| FR-03 | Prevent duplicate registrations with an idempotency key. |
| FR-04 | Retrieve a ticket's live status, owner, deadline, and history. |
| FR-05 | Classify and prioritize tickets by type, urgency, and deadline. |
| FR-06 | Request missing information about an incident. |
| FR-07 | Propose a diagnosis with sources and warnings through the local LLM. |
| FR-08 | Record the human review and decision about a proposal. |
| FR-09 | Record the solution performed by support or engineering and close the ticket through human action. |
| FR-10 | Mark a ticket as unresolved. |
| FR-11 | Escalate to engineering a support ticket that needs specialized human intervention. |
| FR-12 | Notify the engineering manager of an escalation through Slack. |
| FR-13 | Humanly assign an escalated ticket to an engineer. |
| FR-14 | Consult approved knowledge and authorized read-only data for investigation. |
| FR-15 | Reopen a ticket with a reason and preserved history. |
| FR-16 | Notify stakeholders of status changes. |
| FR-17 | Block risky-action proposals and request human review. |
| FR-18 | Update the knowledge index with resolved and validated tickets. |
| FR-19 | Show engineering deadline, workload, and escalation tracking. |
| FR-20 | Route no-response or repeatedly failing cases to human review. |

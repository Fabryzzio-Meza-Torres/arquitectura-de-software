# Support Engineer — Eric Biagioli

## Who they are

Eric represents the **Support Area Worker** in Genius-x's daily operation. He is the first
point of contact for incidents reported by Balbuena Consulting Enterprise's clients
(companies that run the ERP systems built by the consultancy). He handles dozens of tickets
per shift and relies on the Harness to resolve cases that go beyond his direct knowledge.

## Role in the system

Eric registers every client-reported incident in Harness. If the incident is simple, he
resolves it himself and marks the ticket as solved. If the incident is difficult, he asks
Harness (the LLM with its context tools) for help, and if the answer convinces him, he
closes the ticket as a resolved **Support Escalation**. If Harness cannot resolve it, the
ticket is automatically escalated to the Engineering Area. Eric can also reopen a ticket if
Harness gave a wrong answer and the client reports that the problem persists.

## Goals

- Resolve as many customer incidents as possible without needing to escalate them.
- Get fast, reliable answers from Harness for incidents outside his own expertise.
- Close tickets with confidence that the solution was actually correct.
- Avoid the same incident being reprocessed or duplicated.
- Escalate without friction when a problem exceeds his scope or the LLM's capability.

## Needs from the system

- Register new tickets quickly (Ticket Service) with minimal required data.
- Query the Harness and get a prioritized response based on incident type (Customer
  Escalation with a 1-day SLA).
- See a ticket's status without having to wait indefinitely (timeouts, retries, fallback
  when the LLM doesn't respond in time).
- Reopen a ticket when the solution was incorrect, without losing its history.
- Receive automatic notifications when Engineering resolves an escalated ticket.
- Have the system prevent the same incident from being processed twice (idempotency).

## Pain points

- The LLM sometimes fails to learn from past interactions and repeats the same mistakes.
- During the first week of the month, incident volume is so high that the LLM either fails
  to respond or answers the same question differently each time (lack of
  consistency/caching).
- Risk of the LLM taking a destructive action (e.g., deleting a database) without human
  confirmation.
- Genius sometimes reports the status of a ticket that was already closed hours ago (poor
  cache invalidation).
- Without a request limit, the local LLM sessions can get overloaded during peak periods.

## Main flows this role participates in

1. Register a Customer Escalation or Support Escalation ticket.
2. Query the Harness for a difficult incident and evaluate its response.
3. Close a resolved ticket (by himself or confirmed by the Harness).
4. Automatically escalate a ticket the Harness cannot resolve.
5. Reopen a ticket when the given solution turned out to be wrong.

## What this role expects from Genius-x (Harness)

- Consistent answers to the same question, even during load spikes.
- A guardrail mechanism that blocks dangerous actions without his explicit confirmation.
- Real-time, up-to-date status notifications, with no stale data.
- Automatic prioritization of tickets by SLA (Customer Escalations ahead of others).
- Fault tolerance for the LLM: retries, timeouts, and a fallback response instead of total
  silence.

## Success criteria

- Eric resolves or correctly escalates 100% of the incidents he opens, with no duplicates
  or reprocessing.
- The Harness responds within the 1-day SLA for Customer Escalations, even during the
  highest-load week.
- No destructive action ever happens without explicit human confirmation.
- The ticket status Eric sees always reflects the current reality (no stale data from an
  outdated cache).

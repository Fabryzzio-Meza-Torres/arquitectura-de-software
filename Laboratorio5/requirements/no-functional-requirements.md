# Non-functional requirements - Genius-x

Numerical targets come from the study case. Test scenarios for other attributes are specified in [`../core/11. acceptance-criteria.md`](../core/11.%20acceptance-criteria.md), without inventing availability or latency percentages.

| ID | Requirement |
| --- | --- |
| NFR-01 | Prevent the LLM, its subagents, and its tools from writing to production or closing tickets; only a person performs the solution and decides closure. |
| NFR-02 | Attribute and restrict actions by role using Balbuena-provided credentials, with no Harness-native registration or login. |
| NFR-03 | Protect client data and limit MCP queries to the minimum authorized read-only access. |
| NFR-04 | Support at least 10,000 incidents per week, including first-week-of-the-month peaks. |
| NFR-05 | Support access by 50 to 100 engineers. |
| NFR-06 | Measure and meet a one-day substantive human response for client incidents and a three-day response for engineering incidents. |
| NFR-07 | Keep tickets available and recoverable when the LLM or integrations fail, through persistent queuing and fallback. |
| NFR-08 | Prioritize critical decisions with observable latency and alert when their delay threatens the SLA. |
| NFR-09 | Limit requests and tokens per session to protect the local LLM during peaks. |
| NFR-10 | Bound timeout, retries, and loops; use circuit breaker and dead-letter queue without losing tickets. |
| NFR-11 | Prevent duplicate notifications and assignments when escalations are retried. |
| NFR-12 | Show a ticket's live status after closure or reopening by invalidating related cache. |
| NFR-13 | Reuse common answers only when sources are validated, current, and traceable. |
| NFR-14 | Retain an audit trail of human actions, LLM proposals, blocks, and status changes. |
| NFR-15 | Isolate every code trial in a sandbox without write access to production environments. |

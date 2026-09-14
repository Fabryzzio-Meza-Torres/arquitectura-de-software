# Specification evaluation - iteration 01

Date: 2026-09-13. Evaluator applied: [`../agents/eval-spec.md`](../agents/eval-spec.md). Scope: documents and diagram; no software, LLM, Slack, or load test was executed.

## 0. Readiness and baselines

| Input | Result |
| --- | --- |
| Assignment, image, and clarifications | Available in `study-case/`; the PDF copy has the same SHA-256 hash as the source. |
| People | 3 profiles, 18 numbered needs. |
| Core | 11 ordered files; usable problem, objective, concepts, flows, and AC. |
| Backlogs | 20 FR and 15 NFR with sequential, unique IDs. |
| Architecture | `diagram/final_architecture.excalidraw` is available; non-deleted elements were considered. |

**READY TO EVALUATE.** Reviewed local Markdown links resolve. `git diff --check` found no errors in the modified tracked files. The prior removal of `Diagram/diagramaIteracionFinal.excalidraw` and the two untracked diagram files were already present in the working tree; this evaluation uses only `final_architecture.excalidraw` as requested by the user.

The PDF defines Customer, Engineering, and Support Escalations; a local LLM; a deletion incident; erroneous or stale answers; a first-week peak; 10,000+ tickets/week; 50-100 engineers; 1/3-day response SLAs; and fault tolerance. The ERP company, frequent user errors, the three existing people, and the prohibition of autonomous solutions come from the request and its image. Measuring SLA through the first substantive human response is a decision in `core/3. objective.md`, not a literal PDF definition.

## 1. Forward coverage of people

| Role/item | Summarized need | FR/NFR | Core/AC | Coverage |
| --- | --- | --- | --- | --- |
| Eric 1 | Minimal registration without duplicates | FR-01, FR-03, NFR-11 | F1, AC-01 | Full |
| Eric 2 | Distinguish simple and technical cases; deadline | FR-05, NFR-06 | F1-F2, AC-02 | Full |
| Eric 3 | Grounded proposal and human closure | FR-07-FR-09, NFR-01 | F1, AC-03-AC-05 | Full |
| Eric 4 | Live status, information, and fallback | FR-04, FR-06, FR-20, NFR-07, NFR-12 | F1, F5, AC-04, AC-06, AC-09 | Full |
| Eric 5 | Escalate with history and no duplicate notices | FR-11, FR-12, NFR-11 | F2, AC-07 | Full |
| Eric 6 | Reopen and receive changes | FR-15, FR-16 | F4, AC-06, AC-11 | Full |
| Julia 1 | Create internal ticket and see deadline | FR-02, NFR-06 | F3, AC-02 | Full |
| Julia 2 | Receive duplicate-free, contextual assignment | FR-11-FR-13, NFR-11 | F2, AC-07, AC-11 | Full |
| Julia 3 | Sources and read-only queries | FR-07, FR-14, NFR-03 | F3, AC-04, AC-11 | Full |
| Julia 4 | Review risk and perform the intervention herself | FR-08, FR-17, NFR-01, NFR-15 | F5, AC-05 | Full |
| Julia 5 | Record resolution or non-resolution | FR-09, FR-10, NFR-14 | F3, AC-03, AC-11 | Full |
| Julia 6 | Resume reopening and validate knowledge | FR-15, FR-18, NFR-13 | F4, KPD-4, AC-11 | Full |
| Jesus 1 | Slack notice without duplication | FR-12, NFR-11 | F2, AC-07 | Full |
| Jesus 2 | Reasons, attempts, and blocks | FR-04, FR-17, NFR-14 | F2, F5, AC-11 | Full |
| Jesus 3 | Assign and follow pending items | FR-13, FR-19 | F2, AC-07 | Full |
| Jesus 4 | Monitor 1/3-day deadlines | FR-19, NFR-06 | KPD-2, AC-02 | Full |
| Jesus 5 | Observe peaks and failures | FR-19, FR-20, NFR-08 | KPD-6, AC-08-AC-09 | Partial: workload is shown, but no peak or failure alert criterion is set. Add it to AC. |
| Jesus 6 | Prevent autonomous destructive action | FR-17, NFR-01, NFR-14 | F5, AC-05, AC-11 | Full |

No need is uncovered. `core/6` summarizes the same three roles without adding a client as a direct user.

## 2. Reverse traceability and scope

| ID | Justification and evidence | Status |
| --- | --- | --- |
| FR-01 | Eric 1; F1; AC-01 | Justified |
| FR-02 | Julia 1; F3; AC-02 | Justified |
| FR-03 | Eric 1; KPD-5; AC-01 | Justified |
| FR-04 | Eric 4, Jesus 2; F1/F4; AC-06/11 | Justified |
| FR-05 | Eric 2; KPD-2; F1/F2; AC-02 | Justified |
| FR-06 | Eric 4; F1; AC-04 | Justified |
| FR-07 | Eric 3, Julia 3; F1/F3; AC-04 | Justified |
| FR-08 | Eric 3, Julia 4; KPD-1; AC-03/05 | Justified |
| FR-09 | Eric 3, Julia 5; F1/F3; AC-03 | Justified |
| FR-10 | Julia 5; F2/F3; AC-04 | Justified |
| FR-11 | Eric 5; F2; AC-07 | Justified |
| FR-12 | Jesus 1; F2; AC-07 | Justified |
| FR-13 | Jesus 3, Julia 2; F2; AC-07 | Justified |
| FR-14 | Julia 3; KPD-7; F3; AC-04/05 | Justified |
| FR-15 | Eric 6, Julia 6; F4; AC-06 | Justified |
| FR-16 | Eric 6; F2/F4; AC-06 | Justified |
| FR-17 | Jesus 6, Julia 4; F5; AC-05 | Justified |
| FR-18 | Julia 6; KPD-4; AC-11 | Justified |
| FR-19 | Jesus 3-5; KPD-2; AC-02/08 | Justified; peak-alert AC is partial |
| FR-20 | Eric 4, Jesus 5; F5; AC-09 | Justified |
| NFR-01 | Human authority; KPD-1; AC-03/05 | Justified |
| NFR-02 | Provided credentials; Core 6; AC-11 | Justified; an explicit role-permission test is missing |
| NFR-03 | Sensitive case data; KPD-7; AC-05 | Justified; an explicit data-isolation test is missing |
| NFR-04 | 10,000+ in PDF; AC-08 | Justified |
| NFR-05 | 50-100 in PDF; AC-08 | Justified |
| NFR-06 | 1/3 days in PDF; KPD-2; AC-02 | Justified |
| NFR-07 | LLM/Slack failure in PDF and diagram; F2/F5; AC-07/09 | Justified |
| NFR-08 | Critical decisions in PDF; KPD-2; AC-02 | Justified; a verifiable alert criterion is missing |
| NFR-09 | Rate Limiter/Token Budget in diagram; KPD-6; AC-08 | Justified |
| NFR-10 | Circuit Breaker/DLQ in diagram; F5; AC-09 | Justified |
| NFR-11 | Dedup Store/Slack in diagram; F2; AC-07 | Justified |
| NFR-12 | Stale status in PDF; F4; AC-06/10 | Justified |
| NFR-13 | Inconsistent answers in PDF; KPD-4/5; AC-10 | Justified |
| NFR-14 | Previous deletion and traceability; KPD-1; AC-11 | Justified |
| NFR-15 | Code Sandbox in diagram; KPD-7; AC-05 | Justified |

No orphaned, out-of-scope, or contradictory requirements were detected. The quality conditions in NFR-02/03/08 have partial acceptance evidence and reduce Block C.

## 3. Flows and architecture

| Flow | Traced steps | Alternative | Diagram components |
| --- | --- | --- | --- |
| F1 | 4/4 | Missing information / F2 | Support, Ticket, idempotency, queue, Harness/LLM, Evaluate/Resolve, cache invalidator |
| F2 | 4/4 | Slack -> retry/DLQ; persistent ticket | Escale Ticket, Notification, dedup, Channel Router, MCP Slack, Engineer Service |
| F3 | 3/3 | Human fallback | Ticket, Harness/LLM, RAG, MCP DataBase, Code Sandbox, Resolve |
| F4 | 3/3 | Engineering review | Reopen, Escale, Engineer, Event Invalidator |
| F5 | 3/3 | Timeout/retry/circuit breaker/DLQ | Guardrails, Approval Gates, Loop Control, Fallback, DLQ |

The diagram's `Nightly Retrain` text connects to `Embeddings Store`; `core/4` and KPD-4 limit it to a nightly RAG-index update, not LLM training. Its label should be changed in a future revision to avoid ambiguity. The diagram's arrows show tools connected to the LLM but do not express read-only permissions; NFR-01/03 and KPD-7 establish the required boundary.

## 4. Reliability, failures, and single points

| Scenario | Documented outcome | D score / 2 |
| --- | --- | ---: |
| 10,000+/week peak and 50-100 engineers | Persistent queue, priority, balancing, and limits in KPD-6; AC-08 requires a test. No runtime evidence or documented ticket-store/queue redundancy exists. | 1 |
| LLM outage or erroneous answer | F5, FR-20, NFR-07/10, and AC-09 preserve the ticket and refer it to a person. | 2 |
| Slack outage or retried notice | F2, NFR-11, and AC-07 preserve the event and deduplicate assignment. | 2 |
| Stale ticket status | F4, KPD-5, NFR-12, and AC-06/10 invalidate cache and read live status. | 2 |
| Destructive deletion | KPD-1/7, F5, NFR-01/03/15, and AC-05 block LLM writes and require human action. | 2 |
| Stale knowledge | KPD-4/5, FR-18, NFR-13, and AC-10/11 require a validated source and index update. | 2 |

**Single points of failure pending design or validation:** ticket and status database, persistent queue, deduplication store, RAG index, and local LLM node or service. Slack is an external integration: an outage has a retry/DLQ route but has not been tested. The diagram does not prove replicas or recovery for these stores; none are inferred. The missing explicit database and queue redundancy is the principal remaining availability risk for the technical design.

## 5. Diagnostic score

| Block | Calculation | Score |
| --- | --- | ---: |
| A. People | 35 / (2 x 18) x 10 | 9.72 |
| B. Critical problems | 11 / 12 x 10: 4/4 overload, 4/4 unsafe/stale answers, 3/4 peak/failure because SPOFs remain | 9.17 |
| C. FR/NFR quality | 171 / (5 x 35) x 10: FR-19 and NFR-02/03/08 each lose 1 point for incomplete test criteria | 9.77 |
| D. Reliability and architecture | 11 / 12 x 10 | 9.17 |
| **Total** | 0.30A + 0.25B + 0.20C + 0.25D | **9.45** |

The total was calculated with unrounded fractions. The score measures specification quality, not actual performance.

## 6. Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| 1. Needs | PASS | 18/18 have at least partial coverage; section 1. |
| 2. Human authority | PASS | KPD-1/7, F1/F3/F5, FR-08/09/17, NFR-01, AC-03/05. |
| 3. Scope and contradictions | PASS | 35/35 justified; section 2. |
| 4. Flows and deadlines | PASS | F1-F5 traced; KPD-2 and AC-02 preserve the client deadline. |
| 5. Failures, cache, and peaks | Documentary PASS | Six routes documented; load testing remains pending. |
| 6. Diagram consistency | PASS with observation | Components and routes agree; `Nightly Retrain` needs a more precise label. |
| 7. Hygiene | PASS | Sequential IDs, valid links, and PDF-sourced numbers. |

## 7. Prioritized corrections

1. **State/queue availability:** document how the ticket database and queue recover from their own outage and test it; the current diagram leaves single points of failure. This would provide 4/4 for critical problem 3 and 2/2 for the peak/outage scenario.
2. **Observability AC:** add a verifiable alert result for peak and failure visibility to AC-08/09; this completes Eric/Jesus and FR-19/NFR-08.
3. **Permissions and privacy AC:** add role-access and client-data-isolation tests for NFR-02/03; this completes Block C.
4. **Index name:** clarify `Nightly Retrain` in Excalidraw as a RAG-index update without changing the LLM, to remove ambiguity.

## 8. Verdict and validation boundary

**COHERENT FOR REVIEW**, with a 9.45/10 diagnostic score and 7/7 documentary gates. Execution evidence for capacity, availability, permissions, sandbox, LLM, Slack, and recovery routes is still missing; this evaluation does not validate the production system.

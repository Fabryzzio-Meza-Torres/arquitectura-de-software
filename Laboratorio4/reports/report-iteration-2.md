# Requirements evaluation — iteration 2

**Evaluator:** `agents/eval-spec.md` (run from scratch)  
**Scope:** current Lab 4 specification package only. The supplied architecture diagram was
not reviewed; this report evaluates its specification readiness.

## 0. Readiness and extracted baselines

| Input | Result | Evidence |
| --- | --- | --- |
| Case study | Usable | Rural education, limited connectivity, deliverables and the 40% token target are present. |
| People | Usable | Government Teacher, Rural Teacher and Rural Student each have a detailed needs list. |
| Core 1–3 | Usable | Summary, three problem headings and objective are present. |
| Core 4–6 | Usable | Scope, vocabulary and condensed role needs are present. |
| Core 7–9 | Usable | KPDs, experience and five numbered flows with fallbacks are present. |
| Core 10–11 | Usable | Three phases, committed Happy Path and testable ACs are present. |
| Requirements | Usable | Non-empty FR and NFR tables contain sequential unique IDs. |

**Critical-problem headings (verbatim):**

1. Interrupted distribution can leave rural schools with incomplete material
2. Limited connectivity and digital skills threaten the two-month learning cycle
3. AI-assisted content creation consumes too many tokens

**Phase headings:** Phase 1 — Central preparation and controlled AI; Phase 2 — Verified
rural distribution; Phase 3 — Local learning experience.

**Never in scope:** Ministry integration or grade export; 100% availability or advanced HA;
student forums/social communication; built-in collaborative editing; Rural Teacher creation
of official curriculum.

**Main flows:** Flow 1 — Prepare and publish a two-month package; Flow 2 — Synchronize Lima
with a rural school; Flow 3 — Plan and conduct a class; Flow 4 — Manage a task and
submission; Flow 5 — Record two-month grades. **Committed architecture Happy Path:** Flow 1,
then Flow 2, then Flow 3.

**Extracted targets/invariants:** at least 40% fewer AI tokens against the same representative
workload; 12 physical classrooms; chunk preservation; manifest verification; activation only
of a complete version; previous-version fallback; automatic deletion of period files after
the two-month period.

**Input hygiene.** FR-01–FR-41 and NFR-01–NFR-25 are unique and sequential; no empty or
duplicate backlog titles were found. Required local links resolve, including the staged-scope
link to Out of scope and the case-study pipeline image. `functional.md` and
`no-functional.md` were excluded as superseded notes. The evaluator threshold is 8.00/10,
while the assignment pipeline says score `> 8`; this wording conflict remains documented and
the evaluator's fixed 8.00 threshold was used.

**Conflict found:** Gaspar's detailed persona says a technical account configures courses,
classrooms, groups and enrollments and that Gaspar never configures them. Core 2, Core 5,
Core 6, KPD-9, Flow 3, staged scope and AC-1.4 instead grant that work to trained Rural
Teachers. NFR-18 then hides academic-structure configuration from Rural Teachers. The package
is still **READY TO EVALUATE**, but the conflict is scored below.

## 1. Persona-needs coverage

| Role | Need | Requirement(s) | Supporting core evidence | Coverage |
| --- | --- | --- | --- | --- |
| Government Teacher | Authorized sign-in | FR-01, NFR-22 | AC-1.1; Flow 1.1 | Full |
| Government Teacher | Organize material by period, course, grade and classroom | FR-05–06 | AC-2.1; Flow 1.1–2 | Full |
| Government Teacher | Upload and preview supported formats | FR-07–08 | AC-2.1; Flow 1.3–4 | Full |
| Government Teacher | Controlled AI with limits and explanation | FR-09–13; NFR-13–14,24 | KPD-7; AC-2.2–3 | Full |
| Government Teacher | Version and destination distribution status | FR-14,16–18 | AC-2.1; AC-3.1; Flow 1.5–6 | Full |
| Government Teacher | Correct without replacing active version | FR-15,21–22 | KPD-6; AC-2.4 | Full |
| Rural Teacher | Assigned-only sign-in, courses, classrooms and students | FR-01–02,04; NFR-18,20 | AC-1.1,1.3; Flow 3.1 | Partial — configuration-role conflict |
| Rural Teacher | Current period and active version | FR-24,34 | AC-4.1; Flow 3.2–3 | Full |
| Rural Teacher | LAN view, download, print and play | FR-25; NFR-02–03 | AC-4.2; Flow 3.4–5 | Full |
| Rural Teacher | Add complementary official material | FR-26 | KPD-9; Phase 3 | Full |
| Rural Teacher | Create/schedule tasks and announcements | FR-27–29 | AC-6.1; Flow 4.1–2 | Full |
| Rural Teacher | Review submissions, grade and feedback | FR-30–32 | AC-6.2; Flow 4.4 | Full |
| Rural Teacher | Record/consult period grades | FR-33 | AC-6.3; Flow 5.1–2 | Full |
| Rural Teacher | Clear version/sync/pending notices | FR-34; NFR-16 | Expected experience; Flow 2.6 | Full |
| Rural Student | Assisted sign-in and enrollment-only access | FR-01–02,35; NFR-19 | AC-1.1–2; Flow 3.6–7 | Full |
| Rural Student | Current material by course/activity | FR-35–36 | AC-5.1; Flow 3.7 | Full |
| Rural Student | LAN material access | FR-36; NFR-02,17 | KPD-2; AC-5.1 | Full |
| Rural Student | Editable-file compatibility | FR-37 | AC-5.2; Flow 3 fallback | Full |
| Rural Student | Task review and permitted submission | FR-38–39 | AC-6.2; Flow 4.3 | Full |
| Rural Student | Personal grades and feedback only | FR-40; NFR-19 | AC-1.2; AC-6.2–3 | Full |

No detailed persona need is Not covered. The Rural Teacher access need is partial because
the detailed persona's no-configuration boundary conflicts with current core and NFR-18.

## 2. Reverse traceability and scope

| Requirement | Serves | Supporting core evidence | Phase | Status |
| --- | --- | --- | --- | --- |
| FR-01 | All role sign-in | AC-1.1; Flows 1/3 | 1/3 | Justified |
| FR-02 | Access authorization and enrollment management | AC-1.1; KPD-8/9 | 1/3 | Contradictory — detailed Rural Teacher persona |
| FR-03 | Academic-structure configuration | KPD-9; AC-1.4; Flow 3.1 | 1 | Contradictory — detailed Rural Teacher persona |
| FR-04 | Minimum teacher roster | AC-1.3; Flow 5.1 | 3 | Justified |
| FR-05 | Package period creation | AC-2.1; Flow 1 | 1 | Justified |
| FR-06 | Destination assignment | AC-2.1; Flow 1 | 1 | Justified |
| FR-07 | Required file types | AC-2.1; Flow 1 | 1 | Justified |
| FR-08 | File preview | AC-2.1; Flow 1 | 1 | Justified |
| FR-09 | AI-assisted creation | KPD-7; AC-2.2 | 1 | Justified |
| FR-10 | AI skill selection | KPD-7 | 1 | Justified |
| FR-11 | AI model selection | KPD-7 | 1 | Justified |
| FR-12 | AI-token limits | AC-2.2 | 1 | Justified |
| FR-13 | AI limit explanation | AC-2.2 | 1 | Justified |
| FR-14 | Versioned publication | AC-2.1 | 1 | Justified |
| FR-15 | Non-destructive correction | AC-2.4 | 1 | Justified |
| FR-16 | Destination status | Flow 2.6 | 1 | Justified |
| FR-17 | Hierarchical distribution | AC-3.1; Flow 2 | 2 | Justified |
| FR-18 | Manifest preservation | AC-3.1; Flow 2 | 2 | Justified |
| FR-19 | Transfer retry/resume | AC-3.2; Flow 2 | 2 | Justified |
| FR-20 | Integrity verification | AC-3.3; Flow 2 | 2 | Justified |
| FR-21 | Complete activation | AC-3.3; Flow 2 | 2 | Justified |
| FR-22 | Previous-version fallback | AC-3.4; Flow 2 | 2 | Justified |
| FR-23 | Cache cleanup | AC-3.5; Flow 2 | 2 | Justified |
| FR-24 | Teacher active-package view | AC-4.1; Flow 3 | 3 | Justified |
| FR-25 | Teacher LAN material use | AC-4.2; Flow 3 | 3 | Justified |
| FR-26 | Complementary material | Phase 3 | 3 | Justified |
| FR-27 | Task creation | AC-6.1; Flow 4 | 3 | Justified |
| FR-28 | Announcement creation | AC-6.1; Flow 4 | 3 | Justified |
| FR-29 | Scheduled publication | AC-6.1; Flow 4 | 3 | Justified |
| FR-30 | Submission review | AC-6.2; Flow 4 | 3 | Justified |
| FR-31 | Grading | AC-6.2; Flow 4 | 3 | Justified |
| FR-32 | Feedback | AC-6.2; Flow 4 | 3 | Justified |
| FR-33 | Period grades | AC-6.3; Flow 5 | 3 | Justified |
| FR-34 | Teacher notifications | Expected UX; Flow 2.6 | 3 | Justified |
| FR-35 | Student enrollment home | AC-5.1; Flow 3 | 3 | Justified |
| FR-36 | Student LAN access | AC-5.1; Flow 3 | 3 | Justified |
| FR-37 | Editable-file opening | AC-5.2; Flow 3 fallback | 3 | Justified |
| FR-38 | Student task review | Flow 4.3 | 3 | Justified |
| FR-39 | Student file submission | AC-6.2; Flow 4.3 | 3 | Justified |
| FR-40 | Personal feedback/grades | AC-1.2; AC-6.2–3 | 3 | Justified |
| FR-41 | No student comments | AC-5.3 | 3 | Justified |
| NFR-01 | Network topology | KPD-2; AC-3.1 | 2/3 | Justified |
| NFR-02 | LAN continuity | AC-7.2 | 2/3 | Justified |
| NFR-03 | 12-classroom capacity | AC-7.1 | 3 | Justified |
| NFR-04 | Chunked resume | AC-3.2 | 2 | Justified |
| NFR-05 | Retry initiation | KPD-4 | 2 | Justified |
| NFR-06 | Single retry worker | Coordinated retry quality concern | 2 | Justified |
| NFR-07 | Multicast repair | AC-3.2–4 | 2 | Justified |
| NFR-08 | Batch preservation | KPD-4/5 | 2 | Justified |
| NFR-09 | Manifest integrity | AC-3.3–4 | 2 | Justified |
| NFR-10 | Atomic activation | AC-3.3 | 2 | Justified |
| NFR-11 | Cache lifecycle | AC-3.5 | 2/3 | Justified |
| NFR-12 | Period deletion | Lifecycle invariant | 3 | Justified |
| NFR-13 | 40% token target | AC-2.3 | 1 | Justified |
| NFR-14 | Token audit | KPD-7 | 1 | Justified |
| NFR-15 | Teacher usability | AC-4.3 | 3 | Justified |
| NFR-16 | Plain states | Expected UX | 3 | Justified |
| NFR-17 | XO compatibility | AC-5.1 | 3 | Justified |
| NFR-18 | Role-appropriate interface exposure | Conflicts with KPD-9, Flow 3.1 and AC-1.4 | 1/3 | Contradictory |
| NFR-19 | Student-record isolation | AC-1.2 | 1/3 | Justified |
| NFR-20 | Student-data minimization | AC-1.3 | 3 | Justified |
| NFR-21 | Change traceability | Flow 5 fallback | 1/3 | Justified |
| NFR-22 | Credential protection | AC-1.1 | 1 | Justified |
| NFR-23 | Component boundaries | Staged scope | all | Justified |
| NFR-24 | AI failure isolation | AC-7.3 | 1 | Justified |
| NFR-25 | Limited resilience | Core 4; KPD-4 | all | Justified |

There are no orphans or requirements that implement a Core-4/Core-10 never-in-scope item.
FR-02, FR-03 and NFR-18 are contradictory against the authoritative detailed Rural Teacher
persona; those three rows fail the zero-contradictory-requirements gate.

## 3. Block A — Persona satisfaction

| Role | Need | Requirement(s) | A.1 + A.2 / 5 | Evidence quote(s) | Path to maximum |
| --- | --- | --- | ---: | --- | --- |
| Government Teacher | Authorized sign-in | FR-01, NFR-22 | 5 / 5 | AC-1.1; Flow 1.1 | Already maximum |
| Government Teacher | Organize package context | FR-05–06 | 5 / 5 | AC-2.1; Flow 1.1–2 | Already maximum |
| Government Teacher | Upload and preview formats | FR-07–08 | 5 / 5 | AC-2.1; Flow 1.3–4 | Already maximum |
| Government Teacher | AI limits and explanation | FR-09–13; NFR-13–14,24 | 5 / 5 | KPD-7; AC-2.2–3 | Already maximum |
| Government Teacher | Version/status visibility | FR-14,16–18 | 5 / 5 | AC-2.1; AC-3.1; Flow 1.5–6 | Already maximum |
| Government Teacher | Non-destructive correction | FR-15,21–22 | 5 / 5 | KPD-6; AC-2.4 | Already maximum |
| Rural Teacher | Assigned-only access | FR-01–02,04; NFR-18,20 | 4 / 5 | AC-1.3 conflicts with AC-1.4 | Make persona, core and NFR-18 name one configuration owner. |
| Rural Teacher | Current period and active version | FR-24,34 | 5 / 5 | AC-4.1; Flow 3.2–3 | Already maximum |
| Rural Teacher | LAN material use | FR-25; NFR-02–03 | 5 / 5 | AC-4.2; Flow 3.4–5 | Already maximum |
| Rural Teacher | Complementary material | FR-26 | 5 / 5 | Phase 3 | Already maximum |
| Rural Teacher | Tasks/announcements | FR-27–29 | 5 / 5 | AC-6.1; Flow 4.1–2 | Already maximum |
| Rural Teacher | Review, grade, feedback | FR-30–32 | 5 / 5 | AC-6.2; Flow 4.4 | Already maximum |
| Rural Teacher | Period grades | FR-33 | 5 / 5 | AC-6.3; Flow 5.1–2 | Already maximum |
| Rural Teacher | Actionable notices | FR-34; NFR-16 | 5 / 5 | Expected UX; Flow 2.6 | Already maximum |
| Rural Student | Assisted, enrollment-only sign-in | FR-01–02,35; NFR-19 | 5 / 5 | AC-1.1–2; Flow 3.6–7 | Already maximum |
| Rural Student | Current material | FR-35–36 | 5 / 5 | AC-5.1; Flow 3.7 | Already maximum |
| Rural Student | LAN material access | FR-36; NFR-02,17 | 5 / 5 | KPD-2; AC-5.1 | Already maximum |
| Rural Student | Editable-file compatibility | FR-37 | 5 / 5 | AC-5.2; Flow 3 fallback | Already maximum |
| Rural Student | Task/submission | FR-38–39 | 5 / 5 | AC-6.2; Flow 4.3 | Already maximum |
| Rural Student | Personal grades/feedback | FR-40; NFR-19 | 5 / 5 | AC-1.2; AC-6.2–3 | Already maximum |

Government Teacher: 30 / (5 x 6) x 10 = **10.00**. Rural Teacher: 39 / (5 x 8) x 10 =
**9.75**. Rural Student: 30 / (5 x 6) x 10 = **10.00**. Block A =
(10.00 + 9.75 + 10.00) / 3 = **9.92**.

## 4. Block B — Critical problems

| Problem | Sub-question | Score / 2 | Requirement(s) and evidence | Path to maximum |
| --- | --- | ---: | --- | --- |
| Interrupted distribution | Chunking, initiation, coordination and preservation | 2 | FR-19,23; NFR-04–08; AC-3.2/5 | Already maximum |
| Interrupted distribution | Manifest, repair, atomic activation, fallback | 2 | FR-20–22; NFR-07,09–10; AC-3.3–4 | Already maximum |
| Connectivity/digital skills | LAN, XO and 12-classroom continuity | 2 | FR-25,36; NFR-01–03,17; AC-5.1,7.1–2 | Already maximum |
| Connectivity/digital skills | Restriction, minimum data, plain states, usability | 2 | FR-01,04,35,40; NFR-15–16,19–22; AC-1,4.3 | Already maximum |
| AI token cost | Controlled generation, measurement and comparable 40% benchmark | 2 | FR-09–13; NFR-13–14,24; AC-2.2–3 | Already maximum |

| Mandatory invariant | Result | Evidence |
| --- | --- | --- |
| Confirmed chunk survives interruption | PASS | NFR-04,08 |
| No partial/mixed version activates | PASS | NFR-09–10; FR-21 |
| Multicast loss repaired before activation | PASS | NFR-07,09 |
| Active package readable on LAN without external internet | PASS | NFR-02; FR-25,36 |
| 40% reduction uses same representative baseline | PASS | NFR-13; AC-2.3 |
| Period files automatically deleted after close | PASS | NFR-12 |

Block B = 10 / 10 x 10 = **10.00**.

## 5. Block C — Backlog quality

| Requirement | Score / 5 | Failed criteria | Evidence | Path to maximum |
| --- | ---: | --- | --- | --- |
| FR-01 | 5 | — | AC-1.1; Flow 1 | Already maximum |
| FR-02 | 2 | Clear; Atomic; Unique/consistent | Repeated lead phrase; grants management contrary to detailed persona | Remove duplication and align owner. |
| FR-03 | 3 | Unique/consistent; Traceable/test-backed | Conflicts with detailed persona configuration boundary | Reconcile the persona or assign a technical account consistently. |
| FR-04 | 5 | — | AC-1.3 | Already maximum |
| FR-05 | 5 | — | AC-2.1 | Already maximum |
| FR-06 | 5 | — | AC-2.1 | Already maximum |
| FR-07 | 5 | — | AC-2.1 | Already maximum |
| FR-08 | 5 | — | AC-2.1 | Already maximum |
| FR-09 | 5 | — | AC-2.2 | Already maximum |
| FR-10 | 5 | — | KPD-7 | Already maximum |
| FR-11 | 5 | — | KPD-7 | Already maximum |
| FR-12 | 5 | — | AC-2.2 | Already maximum |
| FR-13 | 5 | — | AC-2.2 | Already maximum |
| FR-14 | 5 | — | AC-2.1 | Already maximum |
| FR-15 | 5 | — | AC-2.4 | Already maximum |
| FR-16 | 5 | — | Flow 2.6 | Already maximum |
| FR-17 | 5 | — | AC-3.1 | Already maximum |
| FR-18 | 5 | — | AC-3.1 | Already maximum |
| FR-19 | 5 | — | AC-3.2 | Already maximum |
| FR-20 | 5 | — | AC-3.3 | Already maximum |
| FR-21 | 5 | — | AC-3.3 | Already maximum |
| FR-22 | 5 | — | AC-3.4 | Already maximum |
| FR-23 | 5 | — | AC-3.5 | Already maximum |
| FR-24 | 5 | — | AC-4.1 | Already maximum |
| FR-25 | 5 | — | AC-4.2 | Already maximum |
| FR-26 | 5 | — | Phase 3 | Already maximum |
| FR-27 | 5 | — | AC-6.1 | Already maximum |
| FR-28 | 5 | — | AC-6.1 | Already maximum |
| FR-29 | 5 | — | AC-6.1 | Already maximum |
| FR-30 | 5 | — | AC-6.2 | Already maximum |
| FR-31 | 5 | — | AC-6.2 | Already maximum |
| FR-32 | 5 | — | AC-6.2 | Already maximum |
| FR-33 | 5 | — | AC-6.3 | Already maximum |
| FR-34 | 5 | — | Expected UX | Already maximum |
| FR-35 | 5 | — | AC-5.1 | Already maximum |
| FR-36 | 5 | — | AC-5.1 | Already maximum |
| FR-37 | 5 | — | AC-5.2 | Already maximum |
| FR-38 | 5 | — | Flow 4.3 | Already maximum |
| FR-39 | 5 | — | AC-6.2 | Already maximum |
| FR-40 | 5 | — | AC-1.2 | Already maximum |
| FR-41 | 5 | — | AC-5.3 | Already maximum |
| NFR-01 | 5 | — | KPD-2; AC-3.1 | Already maximum |
| NFR-02 | 5 | — | AC-7.2 | Already maximum |
| NFR-03 | 5 | — | AC-7.1 | Already maximum |
| NFR-04 | 5 | — | AC-3.2 | Already maximum |
| NFR-05 | 5 | — | KPD-4 | Already maximum |
| NFR-06 | 5 | — | Coordinated retry decision | Already maximum |
| NFR-07 | 5 | — | AC-3.2–4 | Already maximum |
| NFR-08 | 5 | — | KPD-4/5 | Already maximum |
| NFR-09 | 5 | — | AC-3.3–4 | Already maximum |
| NFR-10 | 5 | — | AC-3.3 | Already maximum |
| NFR-11 | 5 | — | AC-3.5 | Already maximum |
| NFR-12 | 5 | — | Extracted lifecycle invariant | Already maximum |
| NFR-13 | 5 | — | AC-2.3 | Already maximum |
| NFR-14 | 5 | — | KPD-7 | Already maximum |
| NFR-15 | 5 | — | AC-4.3 | Already maximum |
| NFR-16 | 5 | — | Expected UX | Already maximum |
| NFR-17 | 5 | — | AC-5.1 | Already maximum |
| NFR-18 | 3 | Unique/consistent; Traceable/test-backed | Conflicts with KPD-9, Flow 3.1 and AC-1.4 | State the selected owner consistently. |
| NFR-19 | 5 | — | AC-1.2 | Already maximum |
| NFR-20 | 5 | — | AC-1.3 | Already maximum |
| NFR-21 | 5 | — | Flow 5 fallback | Already maximum |
| NFR-22 | 5 | — | AC-1.1 | Already maximum |
| NFR-23 | 5 | — | Phase boundaries | Already maximum |
| NFR-24 | 5 | — | AC-7.3 | Already maximum |
| NFR-25 | 5 | — | Core 4; KPD-4 | Already maximum |

All 66 rows were evaluated once: 63 x 5 + FR-02 (2) + FR-03 (3) + NFR-18 (3) = 323;
5 x 66 = 330. Block C = 323 / 330 x 10 = **9.79**.

## 6. Block D — Quality attributes and feasibility

| Scenario | Score / 2 | Requirement(s) and evidence | Missing or degraded behavior | Path to maximum |
| --- | ---: | --- | --- | --- |
| Distribution integrity and recovery | 2 | FR-19–23; NFR-04–10; AC-3 | — | Already maximum |
| Local continuity and capacity | 2 | FR-25,36; NFR-01–03,11–12,17; AC-5.1,7 | — | Already maximum |
| AI efficiency and observability | 2 | FR-09–13; NFR-13–14,24; AC-2.2–3 | — | Already maximum |
| Security, privacy and traceability | 1 | FR-01,04,35,40; NFR-18–22; AC-1/6 | Rural Teacher configuration authorization is contradictory | Select one owner and align NFR-18, persona, KPD, flow and AC. |
| Usability and modular feasibility | 2 | NFR-15–16,23; AC-4.3; staged scope | — | Already maximum |

Block D = 9 / 10 x 10 = **9.00**.

## 7. End-to-end flow gate

| Main flow | Steps covered / total | Fallbacks covered | First uncovered item |
| --- | --- | --- | --- |
| Flow 1 — Prepare/publish | 6 / 6 | All | None |
| Flow 2 — Synchronize | 6 / 6 | All | None |
| Flow 3 — Plan/conduct class | 7 / 7 | All | None |
| Flow 4 — Task/submission | 5 / 5 | All | None |
| Flow 5 — Period grades | 4 / 4 | All | None |

**Committed Happy Path: PASS (specification coverage only).** Flow 1 is covered by
FR-05–14 and NFR-13–14,24; Flow 2 by FR-17–23 and NFR-04–11; Flow 3 by FR-01–04,24–25,
35–37 and NFR-02–03,17–20. The diagram itself was not supplied or validated.

## 8. Score summary

| Dimension | Arithmetic | Score |
| --- | --- | ---: |
| Government Teacher | 30 / 30 x 10 | 10.00 |
| Rural Teacher | 39 / 40 x 10 | 9.75 |
| Rural Student | 30 / 30 x 10 | 10.00 |
| Block A — Persona satisfaction | (10.00 + 9.75 + 10.00) / 3 | 9.92 |
| Block B — Critical problems | 10 / 10 x 10 | 10.00 |
| Block C — Backlog quality | 323 / 330 x 10 | 9.79 |
| Block D — Quality attributes | 9 / 10 x 10 | 9.00 |
| Overall | (9.916667 x .30) + (10 x .30) + (9.787879 x .20) + (9 x .20) | 9.73 |
| Verdict | Gates: score/blocks/invariants/Happy Path pass; contradictory requirements fail | **NOT ACCEPTABLE** |

## 9. Critical gaps

- [FR-02] — Rural Teacher access — It grants enrollment-management privileges despite the
  detailed persona reserving configuration to a technical account — Contradictory requirement
  fails the mandatory gate — Choose one owner and remove the conflicting grant or change the
  persona and all dependent documents.
- [FR-03] — Rural Teacher academic configuration — Detailed persona says a technical account
  configures courses, classrooms, groups and enrollments, while this row assigns it to Rural
  Teacher — Contradictory requirement fails the mandatory gate — Use the selected owner
  consistently in people, core, requirements and ACs.
- [NFR-18] — Role-appropriate interface — It hides academic-structure configuration from
  Rural Teachers, contradicting KPD-9, Flow 3.1 and AC-1.4 — Contradictory requirement fails
  the mandatory gate — Either permit those controls to the defined owner or remove the core
  grant.

## 10. Recommendation

Do not mark Requirements Eval as passed despite the 9.73 weighted score. Resolve the
academic-configuration owner and rerun the evaluator in a new iteration. The specification
Happy Path is covered, but no architecture diagram has been evaluated.

## Previous-iteration comparison

Iteration 1 treated FR-02/FR-03 as conflicting with a technical-account policy in core.
Current core instead grants configuration to trained Rural Teachers, but the detailed Gaspar
persona and NFR-18 retain the opposite policy. The defect therefore remains, now as a
cross-document regression rather than the same core-rule conflict; all other evaluated
coverage remains materially unchanged.

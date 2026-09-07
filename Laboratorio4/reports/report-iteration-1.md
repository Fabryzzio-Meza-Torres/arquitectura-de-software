# Eval-Spec report — iteration 1

## 0. Readiness and extracted baselines

| Input | Result | Evidence |
| --- | --- | --- |
| Case study | Usable | Remote rural education, limited connectivity, 40% target and deliverables are stated. |
| People | Usable | Government Teacher, Rural Teacher and Rural Student each have a detailed `Needs from the system` list. |
| Core 1–3 | Usable | Summary, three numbered problems and objective present. |
| Core 4–6 | Usable | Scope boundary, vocabulary and condensed role needs present. |
| Core 7–9 | Usable | Eleven KPDs, role experience and five numbered flows with fallbacks present. |
| Core 10–11 | Usable | Three phases, committed path and testable AC-1 through AC-7 present. |
| Requirements | Usable | FR-01–FR-41 and NFR-01–NFR-25 are non-empty, unique and sequential. |

Critical-problem headings:

1. Interrupted distribution can leave rural schools with incomplete material.
2. Limited connectivity and digital skills threaten the two-month learning cycle.
3. AI-assisted content creation consumes too many tokens.

Phases: **Phase 1 — Central preparation and controlled AI**; **Phase 2 — Verified rural distribution**; **Phase 3 — Local learning experience**.

Never in scope: Ministry integration/grade export; 100% availability or advanced HA; student forums/social communication; built-in collaborative editing; Rural Teacher creation of official curriculum or academic structure.

Main flows: **Flow 1 — Prepare and publish a two-month package**; **Flow 2 — Synchronize Lima with a rural school**; **Flow 3 — Plan and conduct a class**; **Flow 4 — Manage a task and submission**; **Flow 5 — Record two-month grades**. The committed architecture happy path is **Flow 1, then Flow 2, then Flow 3**.

Quantitative targets: at least **40% fewer AI tokens** against the same representative baseline workload; **12 physical classrooms** in parallel. Required distribution invariants extracted: chunk preservation, manifest verification, complete-version activation, previous-version fallback and automatic end-of-period file deletion.

Input hygiene: IDs are sequential and unique; titles are non-empty and non-duplicated; vocabulary is defined; local links resolve; `functional.md` and `no-functional.md` were excluded as superseded notes. Core links are intact. The exception is a semantic conflict: FR-02 and FR-03 grant Rural Teachers enrollment/academic-structure configuration, contradicting Core 4, KPD-9, AC-1.4 and NFR-18. The case study says score `> 8`, while this rubric fixes acceptance at `>= 8.00`; the fixed rubric threshold is used.

**READY TO EVALUATE**

## 1. Persona-needs coverage

| Role | Need | Requirement(s) | Supporting core evidence | Coverage |
| --- | --- | --- | --- | --- |
| Government Teacher | Authorized sign-in | FR-01, NFR-22 | AC-1.1; Flow 1.1 | Full |
| Government Teacher | Organize by period/course/grade/classroom | FR-05, FR-06 | AC-2.1; Flow 1.1–2 | Full |
| Government Teacher | Upload and preview formats | FR-07, FR-08 | AC-2.1; Flow 1.3–4 | Full |
| Government Teacher | Controlled, explained AI use | FR-09–FR-13, NFR-13–14, NFR-24 | KPD-7; AC-2.2–3 | Full |
| Government Teacher | Publish version and see destination status | FR-14, FR-16–18 | AC-2.1; AC-3.1; Flow 1.5–6 | Full |
| Government Teacher | Correct without replacing active version | FR-15, FR-21–22 | KPD-6; AC-2.4 | Full |
| Rural Teacher | Assigned-only sign-in and records | FR-01, FR-04, NFR-18, NFR-20 | AC-1.1, AC-1.3; Flow 3.1 | Full |
| Rural Teacher | Identify period and active version | FR-24, FR-34 | KPD-1; AC-4.1; Flow 3.2 | Full |
| Rural Teacher | LAN view/download/print/play | FR-25, NFR-02–03 | KPD-2; AC-4.2; Flow 3.3–4 | Full |
| Rural Teacher | Add complementary official material | FR-26 | KPD-9; Phase 3 | Full |
| Rural Teacher | Create/schedule tasks and announcements | FR-27–29 | AC-6.1; Flow 4.1–2 | Full |
| Rural Teacher | Review, grade and feedback | FR-30–32 | AC-6.2; Flow 4.4 | Full |
| Rural Teacher | Record/consult period grades | FR-33 | AC-6.3; Flow 5.1–2 | Full |
| Rural Teacher | Clear version/sync/pending notices | FR-34, NFR-16 | Expected experience; Flow 2.6 | Full |
| Rural Student | Assisted sign-in; enrollment-only access | FR-01–02, FR-35, NFR-19 | AC-1.1–2; Flow 3.5–6 | Full |
| Rural Student | Current material by course/activity | FR-35–36 | AC-5.1; Flow 3.6 | Full |
| Rural Student | LAN material access | FR-36, NFR-02, NFR-17 | KPD-2; AC-5.1 | Full |
| Rural Student | Editable-file compatibility | FR-37 | AC-5.2; Flow 3 fallback | Full |
| Rural Student | Task review and permitted submission | FR-38–39 | AC-6.2; Flow 4.3 | Full |
| Rural Student | Personal grades and feedback only | FR-40, NFR-19 | AC-1.2; AC-6.2–3 | Full |

No detailed persona need is Not covered.

## 2. Reverse traceability and scope

| Requirement | Serves | Supporting core evidence | Phase | Status |
| --- | --- | --- | --- | --- |
| FR-01 | All role sign-in | AC-1.1; Flows 1/3 | 1/3 | Justified |
| FR-02 | Authorization; adds Rural Teacher enrollment management | KPD-8 conflicts with KPD-9; AC-1.4 | 1/3 | Contradictory |
| FR-03 | Rural Teacher academic configuration | Core 4; KPD-9; AC-1.4 | 1 | Out of scope / Contradictory |
| FR-04 | Minimum teacher roster | AC-1.3; Flow 5.1 | 3 | Justified |
| FR-05 | Government package preparation | AC-2.1; Flow 1 | 1 | Justified |
| FR-06 | Government package preparation | AC-2.1; Flow 1 | 1 | Justified |
| FR-07 | Government package preparation | AC-2.1; Flow 1 | 1 | Justified |
| FR-08 | Government package preparation | AC-2.1; Flow 1 | 1 | Justified |
| FR-09 | Controlled AI material creation | KPD-7; AC-2.2–3; Flow 1 | 1 | Justified |
| FR-10 | Controlled AI material creation | KPD-7; AC-2.2–3; Flow 1 | 1 | Justified |
| FR-11 | Controlled AI material creation | KPD-7; AC-2.2–3; Flow 1 | 1 | Justified |
| FR-12 | Controlled AI material creation | KPD-7; AC-2.2–3; Flow 1 | 1 | Justified |
| FR-13 | Controlled AI material creation | KPD-7; AC-2.2–3; Flow 1 | 1 | Justified |
| FR-14 | Version publication/correction/status | KPD-1/6; AC-2.1/4 | 1 | Justified |
| FR-15 | Version publication/correction/status | KPD-1/6; AC-2.1/4 | 1 | Justified |
| FR-16 | Version publication/correction/status | KPD-1/6; AC-2.1/4 | 1 | Justified |
| FR-17 | Verified distribution and recovery | KPD-3–5; AC-3; Flow 2 | 2 | Justified |
| FR-18 | Verified distribution and recovery | KPD-3–5; AC-3; Flow 2 | 2 | Justified |
| FR-19 | Verified distribution and recovery | KPD-3–5; AC-3; Flow 2 | 2 | Justified |
| FR-20 | Verified distribution and recovery | KPD-3–5; AC-3; Flow 2 | 2 | Justified |
| FR-21 | Verified distribution and recovery | KPD-3–5; AC-3; Flow 2 | 2 | Justified |
| FR-22 | Verified distribution and recovery | KPD-3–5; AC-3; Flow 2 | 2 | Justified |
| FR-23 | Verified distribution and recovery | KPD-3–5; AC-3; Flow 2 | 2 | Justified |
| FR-24 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-25 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-26 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-27 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-28 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-29 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-30 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-31 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-32 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-33 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-34 | Rural Teacher learning workflow | AC-4/6; Flows 3–5 | 3 | Justified |
| FR-35 | Rural Student local learning/privacy | KPD-8/11; AC-5/6; Flows 3–4 | 3 | Justified |
| FR-36 | Rural Student local learning/privacy | KPD-8/11; AC-5/6; Flows 3–4 | 3 | Justified |
| FR-37 | Rural Student local learning/privacy | KPD-8/11; AC-5/6; Flows 3–4 | 3 | Justified |
| FR-38 | Rural Student local learning/privacy | KPD-8/11; AC-5/6; Flows 3–4 | 3 | Justified |
| FR-39 | Rural Student local learning/privacy | KPD-8/11; AC-5/6; Flows 3–4 | 3 | Justified |
| FR-40 | Rural Student local learning/privacy | KPD-8/11; AC-5/6; Flows 3–4 | 3 | Justified |
| FR-41 | Rural Student local learning/privacy | KPD-8/11; AC-5/6; Flows 3–4 | 3 | Justified |
| NFR-01 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-02 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-03 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-04 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-05 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-06 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-07 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-08 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-09 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-10 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-11 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-12 | Distribution, LAN continuity and lifecycle | KPD-2–5; AC-3/7 | 2/3 | Justified |
| NFR-13 | AI efficiency and isolation | KPD-7; AC-2.3; AC-7.3 | 1 | Justified |
| NFR-14 | AI efficiency and isolation | KPD-7; AC-2.3; AC-7.3 | 1 | Justified |
| NFR-15 | Teacher usability, states and XO use | Expected UX; AC-4.3; AC-5.1 | 3 | Justified |
| NFR-16 | Teacher usability, states and XO use | Expected UX; AC-4.3; AC-5.1 | 3 | Justified |
| NFR-17 | Teacher usability, states and XO use | Expected UX; AC-4.3; AC-5.1 | 3 | Justified |
| NFR-18 | Access, privacy and traceability | KPD-8–11; AC-1/6 | 1/3 | Justified |
| NFR-19 | Access, privacy and traceability | KPD-8–11; AC-1/6 | 1/3 | Justified |
| NFR-20 | Access, privacy and traceability | KPD-8–11; AC-1/6 | 1/3 | Justified |
| NFR-21 | Access, privacy and traceability | KPD-8–11; AC-1/6 | 1/3 | Justified |
| NFR-22 | Access, privacy and traceability | KPD-8–11; AC-1/6 | 1/3 | Justified |
| NFR-23 | Architecture boundaries/limited resilience | Staged scope; Core 4 | all | Justified |
| NFR-24 | AI efficiency and isolation | KPD-7; AC-2.3; AC-7.3 | 1 | Justified |
| NFR-25 | Architecture boundaries/limited resilience | Staged scope; Core 4 | all | Justified |

## 3. Block A — Persona satisfaction

| Role | Need | Requirement(s) | A.1 + A.2 / 5 | Evidence quote(s) | Path to maximum |
| --- | --- | --- | ---: | --- | --- |
| Government Teacher | Authorized sign-in | FR-01, NFR-22 | 5 | AC-1.1; Flow 1.1 | Already maximum |
| Government Teacher | Organize period, course, grade and classroom | FR-05–06 | 5 | AC-2.1; Flow 1.1–2 | Already maximum |
| Government Teacher | Upload and preview supported formats | FR-07–08 | 5 | AC-2.1; Flow 1.3–4 | Already maximum |
| Government Teacher | AI with limits and explanations | FR-09–13, NFR-13–14,24 | 5 | KPD-7; AC-2.2–3 | Already maximum |
| Government Teacher | Version publication and destination status | FR-14,16–18 | 5 | AC-2.1; AC-3.1; Flow 1.5–6 | Already maximum |
| Government Teacher | Correction without active-version replacement | FR-15,21–22 | 5 | KPD-6; AC-2.4 | Already maximum |
| Rural Teacher | Assigned-only sign-in, courses, classrooms and students | FR-01,04; NFR-18,20 | 5 | AC-1.1/3; Flow 3.1 | Already maximum |
| Rural Teacher | Current period and active version | FR-24,34 | 5 | AC-4.1; Flow 3.2 | Already maximum |
| Rural Teacher | LAN view/download/print/play | FR-25; NFR-02–03 | 5 | AC-4.2; Flow 3.3–4 | Already maximum |
| Rural Teacher | Complementary official material | FR-26 | 5 | Phase 3; KPD-9 | Already maximum |
| Rural Teacher | Create/schedule tasks and announcements | FR-27–29 | 5 | AC-6.1; Flow 4.1–2 | Already maximum |
| Rural Teacher | Review, grade and feedback | FR-30–32 | 5 | AC-6.2; Flow 4.4 | Already maximum |
| Rural Teacher | Record/consult period grades | FR-33 | 5 | AC-6.3; Flow 5.1–2 | Already maximum |
| Rural Teacher | Clear version, sync and pending notices | FR-34; NFR-16 | 5 | Expected UX; Flow 2.6 | Already maximum |
| Rural Student | Assisted sign-in and enrollment-only access | FR-01–02,35; NFR-19 | 5 | AC-1.1–2; Flow 3.5–6 | Already maximum |
| Rural Student | Current material by course/activity | FR-35–36 | 5 | AC-5.1; Flow 3.6 | Already maximum |
| Rural Student | LAN material access | FR-36; NFR-02,17 | 5 | KPD-2; AC-5.1 | Already maximum |
| Rural Student | Editable-file compatible opening | FR-37 | 5 | AC-5.2; Flow 3 fallback | Already maximum |
| Rural Student | Task review and permitted submission | FR-38–39 | 5 | AC-6.2; Flow 4.3 | Already maximum |
| Rural Student | Personal grades and feedback only | FR-40; NFR-19 | 5 | AC-1.2; AC-6.2–3 | Already maximum |

Government Teacher: 30 / (5 × 6) × 10 = **10.00**. Rural Teacher: 40 / (5 × 8) × 10 = **10.00**. Rural Student: 30 / (5 × 6) × 10 = **10.00**. Block A = (10 + 10 + 10) / 3 = **10.00**.

## 4. Block B — Critical problems

| Problem | Sub-question | Score / 2 | Requirement(s) and evidence | Path to maximum |
| --- | --- | ---: | --- | --- |
| Interrupted distribution | Chunking, initiation, coordination and preservation | 2 | NFR-04–08; FR-19,23; AC-3.2/5 | Already maximum |
| Interrupted distribution | Manifest, repair, atomic activation, fallback | 2 | NFR-07,09–10; FR-20–22; AC-3.3–4 | Already maximum |
| Connectivity/digital skills | LAN, XO and 12-classroom continuity | 2 | NFR-01–03,17; FR-25,36; AC-5.1, AC-7.1–2 | Already maximum |
| Connectivity/digital skills | Restriction, minimum data, plain states, usability | 2 | NFR-15–16,18–20,22; AC-1, AC-4.3 | Already maximum |
| AI token cost | Controlled generation, measurement and comparable 40% benchmark | 2 | FR-09–13; NFR-13–14,24; AC-2.2–3 | Already maximum |

Mandatory invariants:

| Invariant | Result | Evidence |
| --- | --- | --- |
| Confirmed chunk survives interruption | PASS | NFR-04; NFR-08 |
| No partial/mixed version activates | PASS | NFR-09–10; FR-21 |
| Multicast loss repaired before activation | PASS | NFR-07; NFR-09 |
| Active package readable on LAN without external internet | PASS | NFR-02; FR-25/36 |
| 40% reduction uses same representative baseline | PASS | NFR-13; AC-2.3 |
| Period files automatically deleted after close | PASS | NFR-12 |

Block B = 10 / 10 × 10 = **10.00**.

## 5. Block C — Backlog quality

| Requirement | Score / 5 | Failed criteria | Evidence | Path to maximum |
| --- | ---: | --- | --- | --- |
| FR-01 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-02 | 2 | Clear; Atomic; Unique and consistent | Duplicated wording and forbidden Rural Teacher management | Remove duplicated wording and management grant. |
| FR-03 | 3 | Unique and consistent; Traceable and test-backed | Conflicts with Core 4, KPD-9, AC-1.4 and NFR-18 | Assign this capability to the technical account. |
| FR-04 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-05 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-06 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-07 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-08 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-09 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-10 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-11 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-12 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-13 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-14 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-15 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-16 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-17 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-18 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-19 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-20 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-21 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-22 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-23 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-24 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-25 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-26 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-27 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-28 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-29 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-30 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-31 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-32 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-33 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-34 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-35 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-36 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-37 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-38 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-39 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-40 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| FR-41 | 5 | — | AC/flow/KPD traceability in Sections 1–2 | Already maximum |
| NFR-01 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-02 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-03 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-04 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-05 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-06 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-07 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-08 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-09 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-10 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-11 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-12 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-13 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-14 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-15 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-16 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-17 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-18 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-19 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-20 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-21 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-22 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-23 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-24 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |
| NFR-25 | 5 | — | AC/KPD/phase traceability in Section 2 | Already maximum |

All 66 backlog rows were evaluated once: 64 × 5 + FR-02 (2) + FR-03 (3) = 325 points; 5 × 66 = 330 maximum. Block C = 325 / 330 × 10 = **9.85**.

## 6. Block D — Quality attributes and feasibility

| Scenario | Score / 2 | Requirement(s) and evidence | Missing or degraded behavior | Path to maximum |
| --- | ---: | --- | --- | --- |
| Distribution integrity and recovery | 2 | NFR-04–10; FR-19–23; AC-3 | — | Already maximum |
| Local continuity and capacity | 2 | NFR-01–03,11–12,17; AC-5.1, AC-7 | — | Already maximum |
| AI efficiency and observability | 2 | FR-09–13; NFR-13–14,24; AC-2.2–3 | — | Already maximum |
| Security, privacy and traceability | 2 | FR-01,04,35,40; NFR-18–22; AC-1 | — | Already maximum |
| Usability and modular feasibility | 2 | NFR-15–16,23; AC-4.3; staged scope | — | Already maximum |

Block D = 10 / 10 × 10 = **10.00**.

## 7. End-to-end flow gate

| Main flow | Steps covered / total | Fallbacks covered | First uncovered item |
| --- | --- | --- | --- |
| Flow 1 — Prepare/publish | 6 / 6 | All | None |
| Flow 2 — Synchronize | 6 / 6 | All | None |
| Flow 3 — Plan/conduct class | 6 / 6 | All | None |
| Flow 4 — Task/submission | 5 / 5 | All | None |
| Flow 5 — Period grades | 4 / 4 | All | None |

**Committed Happy Path: PASS.** Flow 1 is covered by FR-05–14 and NFR-13–14/24; Flow 2 by FR-17–23 and NFR-04–11; Flow 3 by FR-01,24–25,35–37 and NFR-02–03/17–19. This is only a specification-coverage result; no architecture diagram was reviewed.

## 8. Score summary

| Dimension | Arithmetic | Score |
| --- | --- | ---: |
| Government Teacher | 30 / 30 × 10 | 10.00 |
| Rural Teacher | 40 / 40 × 10 | 10.00 |
| Rural Student | 30 / 30 × 10 | 10.00 |
| Block A — Persona satisfaction | (10 + 10 + 10) / 3 | 10.00 |
| Block B — Critical problems | 10 / 10 × 10 | 10.00 |
| Block C — Backlog quality | 325 / 330 × 10 | 9.85 |
| Block D — Quality attributes | 10 / 10 × 10 | 10.00 |
| Overall | (10 × .30) + (10 × .30) + (9.848484 × .20) + (10 × .20) | 9.97 |
| Verdict | Gates: 6 passed, 1 failed (zero out-of-scope/contradictory requirements) | **NOT ACCEPTABLE** |

## 9. Critical gaps

- [FR-03] — Scope and academic configuration — Core 4 excludes Rural Teacher academic structure creation; KPD-9 and AC-1.4 reserve it to a technical account — It is out of scope and contradictory, failing a mandatory verdict gate — Replace Rural Teacher with the secondary technical account.
- [FR-02] — Access-control requirement — It grants `enrollment management privileges for Rural Teachers`; KPD-9 and AC-1.4 prohibit that role — The row is contradictory, non-atomic and unclear, failing the same mandatory gate — Delete that grant and state only role/assignment/enrollment authorization.

## 10. Recommendation

Do not mark the requirements evaluation as passed yet, despite the 9.97 weighted score. Correct FR-02 and FR-03, then rerun this evaluator as iteration 2. The specification currently covers the architecture happy path but this evaluation does not validate a diagram.

## Previous-iteration comparison

No previous `report-iteration-*.md` exists; this is the baseline evaluation.

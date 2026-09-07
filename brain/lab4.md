# Lab 4 — RemoteSchooly

## Exercise overview

The fourth laboratory addresses RemoteSchooly. The Government of Peru must distribute
official learning material from Lima to remote communities with limited connectivity. The
assignment also requires at least 40% lower token expenditure for AI-assisted content
creation.

Primary source: [`../Laboratorio4/study-case/Lab #4- Arqui2026.2.md`](../Laboratorio4/study-case/Lab%20%234-%20Arqui2026.2.md).

## Activities completed

- Created the standard laboratory structure and converted the assignment document to
  Markdown in `study-case/`.
- Defined the three primary personas: Melchor, Gaspar and Baltasar.
- Completed all 11 `core/` documents and consolidated the functional and non-functional
  requirements.
- Translated the Lab 4 Markdown package to English and aligned its structure with Lab 3.

## Achievements and validation evidence

- The six baseline directories and all 11 `core/` documents are present.
- The case study preserves the problem, quantitative target, deliverables, rubric and source
  pipeline.
- The specification distinguishes RemoteSchooly as the initiative and Balbuena EduKanvas as
  the platform.
- The two-month package, Lima-to-school topology, integrity-gated activation and 40% token
  reduction are traceable across people, core and requirements.
- The final backlogs use the Lab 3 `ID | requirement` table structure and unique `FR-XX` and
  `NFR-XX` identifiers.
- The NFR backlog now defines chunk-preserving retries, coordinated retry triggers,
  point-to-point repair after multicast loss, batch synchronization and automatic
  end-of-period file deletion.

## Lessons learned

- The package is planned and retained by two-month academic period; it is not distributed as
  independent weekly packages.
- Temporary cache is removed after synchronization and integrity confirmation, while the
  active package remains available throughout the period.
- Regional multicast may start distribution, but missing chunks must be repaired through a
  resumable point-to-point transfer before a package can become active.
- Files in active school storage are deleted automatically after the academic period closes.
- Official Ministry grade entry is manual and external; the platform does not export grades.
- A technical account can configure courses, classrooms and enrollments without becoming a
  fourth primary persona.

## Improvements across iterations

- Removed forums, public courses and expanded profiles because they conflict with the
  confirmed scope.
- Replaced indiscriminate file deletion with temporary-cache cleanup after verification.
- Reworked personas, core, FRs and NFRs to follow the established Lab 3 structure.
- Expanded the NFR backlog from 20 to 25 items to incorporate the revised transfer,
  synchronization, backup and storage-lifecycle rules.
- No evaluator iteration exists yet.

## Open issues or unverified claims

- The evaluator and architecture diagram remain pending.
- No Requirements Eval has run, and no happy-path evidence exists yet.

# Functional requirements — Balbuena EduKanvas backlog

This backlog follows the Lab 3 structure: stable IDs, clear capability titles and observable
behavior supported by the product decisions, flows and acceptance criteria in `core/`.

| ID | Functional requirement |
| --- | --- |
| FR-01 | **Assigned-credential sign-in.** The system must allow Government Teachers, Rural Teachers, Rural Students and technical accounts to sign in with assigned credentials. Invalid credentials must be rejected without opening a user session. |
| FR-02 | **Role, assignment and enrollment authorization.** The system must authorize each action and record according to the authenticated role, assigned classroom and student enrollment. An unauthorized request must be denied without returning protected academic data. |
| FR-03 | **Technical academic-structure configuration.** The system must allow a technical account to configure courses, grades, classrooms, groups, enrollments and teacher assignments. Rural Teachers and Rural Students must not receive this capability. |
| FR-04 | **Minimum student roster for assigned teachers.** The system must show a Rural Teacher the full name and enrollment identifier of students in assigned classrooms without exposing an expanded student profile. |
| FR-05 | **Two-month package creation.** The system must allow a Government Teacher to create an official material package for one identified two-month academic period. |
| FR-06 | **Package assignment to configured destinations.** The system must allow a Government Teacher to associate a package with preconfigured courses, grades, classrooms, departments and schools. It must reject an unknown or unauthorized destination. |
| FR-07 | **Support for required educational file types.** The system must accept PDFs, informational documents, teacher guides, digital books, worksheets, activities, infographics, images and videos as package material. An unsupported file must be rejected with an understandable reason. |
| FR-08 | **Pre-publication file preview.** The system must allow the Government Teacher to preview each supported file before publishing the package. A file that cannot be rendered must remain identifiable and downloadable for validation. |
| FR-09 | **AI-assisted material creation.** The system must provide Government Teachers with an AI assistant for creating or improving educational material. Failure of the assistant must not prevent manual file upload. |
| FR-10 | **AI skill selection.** The AI assistant must select the configured skills relevant to the requested material and record which skills were used for the generation. |
| FR-11 | **AI model selection.** The system must select an appropriate enabled AI model for the request and record the selected model with its token usage. |
| FR-12 | **Configurable AI-token limits.** The system must enforce configured token limits by Government Teacher, day and course. The active limits must be visible before a new generation begins. |
| FR-13 | **AI limit enforcement and explanation.** When a token limit is reached, the system must block further generation under that limit and show the affected limit and recorded consumption. Manual content work must remain available. |
| FR-14 | **Versioned package publication.** The system must publish a package with its academic period, version number and file manifest. Publication must preserve the identity of the Government Teacher who performed it. |
| FR-15 | **Non-destructive package correction.** A correction to published material must create a new package version without overwriting the version currently active at a school. |
| FR-16 | **Destination distribution status.** The system must show the Government Teacher each version's status by department and school using the defined synchronization states and an actionable reason for failure. |
| FR-17 | **Hierarchical package distribution.** The system must transfer each published package from Lima through the cloud and target departmental server to each target school server. |
| FR-18 | **End-to-end version and manifest preservation.** Every distribution level must preserve the package version identity and file manifest received from the preceding level. |
| FR-19 | **Automatic large-file retry or resume.** If a large-file transfer is interrupted, the system must automatically retry or resume it without requiring the entire package to restart manually. |
| FR-20 | **School-side file-integrity verification.** The school server must verify every received file against the package manifest before marking it as complete. A mismatch must identify the file that requires another transfer. |
| FR-21 | **Complete-version activation.** The school server must activate a new version only after every file passes integrity verification. Activation must make that one version available as the current package. |
| FR-22 | **Previous-version fallback.** If a replacement version is incomplete or fails verification, the school server must continue serving the previous active version and report the failed replacement. |
| FR-23 | **Confirmed temporary-cache cleanup.** The system must delete transfer chunks and transient copies only after synchronization and integrity are confirmed. It must not delete the active package as part of this cleanup. |
| FR-24 | **Assigned active-package view for Rural Teachers.** The system must show each Rural Teacher the current period and active package for assigned courses and classrooms. |
| FR-25 | **LAN-based teacher material use.** A Rural Teacher must be able to view, download, play and print active material over the school LAN without external internet access. |
| FR-26 | **Complementary official-material publication.** A Rural Teacher must be able to add complementary material derived from or selected from official content to an assigned classroom without modifying the central curriculum or package. |
| FR-27 | **Classroom task creation.** A Rural Teacher must be able to create a task for an assigned classroom with instructions, attachments, a publication time and a due date. |
| FR-28 | **Classroom announcement creation.** A Rural Teacher must be able to create an announcement for an assigned classroom. |
| FR-29 | **Scheduled task and announcement publication.** A Rural Teacher must be able to publish a task or announcement immediately or schedule its publication for an assigned classroom. |
| FR-30 | **Task-submission review.** A Rural Teacher must be able to list and open submissions received for a task in an assigned classroom. |
| FR-31 | **Submission and activity grading.** A Rural Teacher must be able to assign a grade to a student submission or evaluated activity in an assigned classroom. |
| FR-32 | **Teacher feedback on graded work.** A Rural Teacher must be able to record feedback associated with a student's grade. The feedback must be visible only to authorized users. |
| FR-33 | **Two-month grade recording.** A Rural Teacher must be able to record and consult period grades for students in an assigned classroom. The system must not export those grades to the Ministry of Education. |
| FR-34 | **Actionable Rural Teacher notifications.** The system must notify a Rural Teacher about a newly active package version, a visible synchronization error or a submission awaiting review, and link the notice to the relevant item. |
| FR-35 | **Enrollment-filtered Rural Student home.** The system must show a Rural Student only the courses, material, tasks and announcements associated with the current enrollment and classroom. |
| FR-36 | **LAN-based student material access.** A Rural Student must be able to view or download available documents, PDFs, images and videos over the school LAN without external internet access. |
| FR-37 | **External opening of editable files.** A Rural Student must be able to download or open an editable file through a compatible application installed on the XO laptop. The platform does not provide collaborative editing. |
| FR-38 | **Student task review.** A Rural Student must be able to view the instructions, attachments, publication state and due date of a task assigned to the enrolled classroom. |
| FR-39 | **Student file submission.** A Rural Student must be able to attach and submit a supported file when the task accepts digital delivery. An invalid file must be rejected without losing the task view. |
| FR-40 | **Personal grade and feedback view.** A Rural Student must be able to view personal grades and the corresponding Rural Teacher feedback without seeing another student's records. |
| FR-41 | **No student forum or comment publication.** The system must not offer Rural Students controls to create forums, publish comments or reply to feedback. Questions remain part of the in-person class. |

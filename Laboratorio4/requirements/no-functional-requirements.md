# Non-functional requirements — Balbuena EduKanvas

These quality requirements use only confirmed case-study targets and product decisions. No
unsupported national scale, latency, availability, RTO or RPO figure is treated as a
contractual target.

| ID | Non-functional requirement |
| --- | --- |
| NFR-01 | **Required hierarchical network topology.** The solution must operate through the defined Lima, cloud, departmental-server, school-server and school-LAN topology. A classroom client must obtain active material from the school server rather than requiring a direct Lima connection. |
| NFR-02 | **Classroom operation without external internet.** After a package becomes active, the material-access flows for Rural Teachers and Rural Students must remain usable over the school LAN while the external connection is unavailable. |
| NFR-03 | **Twelve-classroom school capacity.** A school server must support simultaneous material-access flows from 12 physical classrooms without requests failing because of server saturation. The test must use the school LAN and representative package files. |
| NFR-04 | **Resumable progress for large-file transfers.** A large-file transfer must preserve enough confirmed progress to retry or resume after connectivity interruption without manually restarting the complete package. |
| NFR-05 | **Manifest-based file integrity.** A received file must be considered complete only when its computed integrity value matches the value in the package manifest. A mismatch must leave the file inactive and visible for retry. |
| NFR-06 | **Atomic package-version activation.** Users must see either the previous complete version or the new complete version, never mixed versions or partial files during activation. |
| NFR-07 | **Safe temporary-cache lifecycle.** Temporary transfer cache must remain available until synchronization and integrity are confirmed, then be deleted without removing the active package. |
| NFR-08 | **At least 40% lower AI-token consumption.** The optimized AI assistant must consume at least 40% fewer total tokens than the baseline when both execute the same representative workload and produce equivalent required educational outputs. |
| NFR-09 | **Auditable AI-token measurement.** The system must retain token consumption by Government Teacher, course, model and academic period so the configured limits and 40% reduction can be reproduced and verified. |
| NFR-10 | **Rural Teacher task usability after orientation.** In a representative usability test after initial orientation, a Rural Teacher must complete sign-in, active-package lookup, material opening, task creation and grading without technical assistance. |
| NFR-11 | **Plain-language package and synchronization states.** Interfaces must present package and synchronization state with the defined labels `pending`, `synchronizing`, `verified`, `active` or `failed`, plus an actionable explanation when the state is `failed`. |
| NFR-12 | **XO-laptop classroom compatibility.** The Rural Student flow for sign-in, material access, file submission and grade viewing must run on the target XO laptop without requiring an external service during class. |
| NFR-13 | **Role-appropriate interface exposure.** The interface must hide academic-configuration and comment-publication controls from Rural Students and must hide academic-structure configuration from Rural Teachers. |
| NFR-14 | **Student academic-record isolation.** A Rural Student must be unable to retrieve another student's courses, submissions, grades or feedback through the interface or a direct request. The denied request must return none of the protected record. |
| NFR-15 | **Student-data minimization.** Teacher-facing student data must be limited to full name, enrollment identifier and academic records required for the assigned classroom. The platform must not require an expanded social or personal profile. |
| NFR-16 | **Traceable academic and publication changes.** Package publications, version changes, submissions and grades must record the acting identity, time, target and affected object identifier so an authorized reviewer can reconstruct the change. |
| NFR-17 | **Protected credentials.** User credentials must not be stored or transmitted in plaintext. Authentication failures must not expose credential values or another user's protected data. |
| NFR-18 | **Explicit component boundaries.** The architecture must separate identity, content production, AI consumption, distribution and synchronization, and academic activity into components with explicit responsibilities and interfaces. |
| NFR-19 | **AI failure isolation.** An unavailable or failed AI assistant must not prevent a Government Teacher from uploading, previewing or publishing material created without AI. |
| NFR-20 | **Scope-limited resilience.** The solution does not claim 100% availability or advanced high availability. It must demonstrate only local continuity for active content, large-file retry or resume, manifest integrity and previous-version fallback required by this scope. |

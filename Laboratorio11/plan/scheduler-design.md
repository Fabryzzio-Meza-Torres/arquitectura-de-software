# Spotty: deadline-aware scheduling on a bounded Spot fleet

Design proposal · 2026-10-22 · No application implementation or deployment.

## 1. Decision and scope

Replace the `priority = submissions × estimated time × deadline urgency` block in [proposal_1.jpeg](../diagram/proposal_1.jpeg) with an explicit scheduling policy, a durable task ledger, a capacity calendar and a dispatcher. The scheduler chooses **which task**, placement chooses **which compatible Spot**, and the dispatcher starts **only an authorized attempt**. A database records every decision; an in-memory red-black tree accelerates ordering and can be rebuilt.

**Recommendation: retain SQS queues per course type for ingestion and recovery, but remove them as the authority for execution order.** Drain messages into the ledger without waiting for execution. Workers never compete for messages in those queues. This retains burst buffering and the current assignment contract while enabling global priority decisions. SQS does not provide arbitrary message priority out of the box; AWS illustrates separate queues for differentiated service in its [priority discussion](https://aws.amazon.com/blogs/messaging-and-targeting/prevent-email-throttling-concurrency-limit/).

A fully queue-free alternative is also viable: the API commits task rows directly and the dispatcher polls due reservations. It replaces a managed broker with a **database-backed work queue**, not with an absence of pending work. It needs a requirements change and capacity evidence before adoption. Neither alternative guarantees an instant grade under unlimited arrivals or missing Spot capacity.

Deliverables:

- [Architecture preview](scheduler-architecture.png) and [editable Excalidraw](scheduler-architecture.excalidraw): recommended ingress, shared scheduler and direct-database alternative.
- [Red-black tree preview](priority-tree.png) and [editable Excalidraw](priority-tree.excalidraw): a valid example tree and extraction order.
- This report: constraints, ordered criteria, failure behavior, changes and proposed acceptance scenarios.

The original study case, requirements, JPEG and existing Excalidraw drawings are preserved. No `core/` specification exists in this laboratory. This proposal supplies design decisions, not a replacement specification or an evaluator result.

## 2. Evidence and assumptions

| Origin | Constraint or clarification | Design consequence |
| --- | --- | --- |
| [Study case](../study-case/Lab%20%2311.md) | P99 runtime: Programming 1 minute; Architecture 10 minutes; AI 40 minutes or more | Initial duration estimates by workload; these are percentiles, not hard execution limits or throughput measurements |
| Study case | Only Spot compute for workers; GPU scarce; possible interruption; untrusted code and memory abuse | No automatic fallback to EC2 On-Demand; resource admission, isolation and recovery required |
| Study case | Images of 3–5 GB; most arrivals in final 30 minutes; grades within two days | Forecast warm-up, protect feedback near closure, track a separate grading deadline |
| User clarification | Per compatible Spot: 20 Programming, 4 Architecture, 2 AI executions concurrently; at most 10 Spots total | Course-specific capacity envelopes; global CPU + RAM + GPU fleet budget of 10 |
| User clarification | Immediate feedback enables correction; urgent work must not share capacity with other courses' nonurgent work | Protect urgent course slices and prohibit their co-location with nonurgent work from another course |
| Proposed interpretation | “11 pm to 12 pm” means 23:00 to **00:00 next day**, America/Lima | Example uses midnight; store UTC instants and display local time |
| Proposed decision | Grading deadline defaults to assignment closure + 48 hours | The case does not define when the two-day clock starts; instructor must confirm this before production use |
| Proposed decision | One course per Spot at a time, with one sandbox per task | Simple conservative isolation; switch course only after drain. The 20/4/2 numbers do not authorize mixing those maxima on one machine |

“Scale on demand” describes when scaling is requested; it does **not** mean purchasing the EC2 On-Demand product. A fleet of ten may contain CPU, RAM and GPU instances; it is not ten per pool. The concurrency envelopes assume reference instance profiles and measured CPU/RAM/GPU budgets. A smaller fallback instance must receive a recalibrated envelope.

The provided image and documents are design evidence. Their embedded notes are not instructions to execute code, change other laboratories or silently rewrite requirements.

## 3. Why the original priority product is insufficient

Multiplying backlog by runtime makes a large, slow course dominate even when its deadline is distant. A submission deadline and a grading deadline have different meanings. A scalar also hides why a short task won, whether an old task will ever run, and whether a GPU task can actually use the free machine.

Separate four questions:

1. **Eligibility:** can this task safely run now?
2. **Order:** which eligible task deserves the next resource opportunity?
3. **Placement:** where can it run without breaking protected reservations?
4. **Admission:** can the fleet satisfy the target, or must the UI expose a delay?

Queue segmentation alone also cannot reserve CPU/RAM, prevent a 40-minute execution from blocking a deadline, or recover an execution consistently.

## 4. Ordered priority criteria

These are proposed policy rules, not numeric requirements supplied by the assignment. Apply the gates and protected reservations first; then compare the red-black-tree key in section 5.

| Order | Criterion | Concrete rule | Reason |
| --- | --- | --- | --- |
| Gate | Valid, runnable task | Accepted immutable artifact version; eligible security result; not cancelled/superseded; retry backoff elapsed; no active attempt | Invalid or duplicate work never acquires execution capacity |
| Gate | Resource and isolation compatibility | Required CPU/RAM/VRAM/GPU, course image, healthy host, course occupancy and future reservations all fit | An AI task cannot block the CPU tree while waiting for a GPU |
| Guard | Previously protected service | Honor committed running work and the next feasible reservation for an aged long task; new priority changes cannot repeatedly erase it | Prevent starvation and unstable schedules |
| 1 | Hard grading SLA danger | Band 0 when forecast finish is at or beyond the grading deadline; otherwise assess feedback urgency | Two-day grading obligation takes precedence over optional fast feedback |
| 2 | Feedback before closure | Band 1 while the correction window is active and forecast finish threatens the feedback target | An 11 pm Programming rush should outrank Architecture work due tomorrow |
| 3 | Waiting age | Band 2 when runnable waiting time reaches `W_max`; otherwise band 3 | Short-job preference must not postpone a long task forever |
| 4 | Deadline slack | Compare latest safe start in one-minute buckets within the band | Long tasks with the same due time need to start earlier |
| 5 | Fair service across courses | Lower normalized service `V_course` wins within the same urgency bucket | A course with hundreds of submissions cannot win every tie by raw count |
| 6 | Short remaining duration | Smaller `p_remaining` wins only after the preceding criteria tie | Improves feedback latency without making “short always wins” the policy |
| 7 | Stable arrival order | Earlier `accepted_at`, then unique `task_id` | Deterministic behavior for exact ties |

### Deadlines and estimates

For each task:

```text
grading_due = assignment_close + 48 hours                  # proposed clock origin
feedback_due = assignment_close - correction_budget        # only while useful
runtime = estimate(assignment, image_version, resource_profile, checkpoint)
latest_start = active_due - setup_estimate - runtime - result_margin
slack = latest_start - now
forecast_finish = earliest_feasible_start + setup_estimate + runtime + result_margin
```

Compute band 0 against `grading_due`; otherwise band 1 applies when live feedback is requested, `now < feedback_due`, and `forecast_finish >= feedback_due`. For band 1 use `active_due = feedback_due`; for all other bands use `grading_due`. At the feedback cutoff, reclassify pending work against grading obligations instead of preserving a permanently overdue live-feedback priority. If feedback is already infeasible, mark that fact and continue trying; do not reject an accepted submission or fabricate a grade.

Start with course P99s only as conservative priors; AI's “40+” requires an assignment-specific upper estimate and an instructor-defined timeout. Reestimate from observed execution and restore times, including 3–5 GB image downloads and artifact staging. A checkpoint reduces remaining time only when its compatibility and resumability were verified. Log estimate error; P99 is not a promise that all jobs finish within that duration.

### Population, workload and fairness

Use `w_course = sqrt(max(1, active_students))` as an initial, configurable weight. Count distinct enrolled students with current pending/running work, not resubmission messages. This gives a 100-student course about 2.24 times the tie-breaking share of a 20-student course, not five times. Population affects fair shares and capacity forecasts; it never overrides a higher urgency band.

Maintain `V_course += dominant_resource_fraction × charged_minutes / w_course` in each compatible resource pool. The dominant fraction is the maximum CPU/RAM/GPU fraction of the reference host reserved by that task, at least its concurrency-slot fraction. Charge predicted service when reserving and reconcile actual service at completion/cancellation; infrastructure replay is not a second student penalty. On activation initialize service at the pool's current virtual-time floor, so a returning course does not gain an unlimited historical advantage. Recompute weights at planning epochs, not for each duplicated message.

Total pending resource-minutes, active students, deadline distribution and image readiness drive autoscaling. A heavy course gets appropriate resources and earlier safe starts, not an unconditional priority bonus.

### Anti-starvation and saturation

Initial tuning proposal: planning tick 5 seconds, priority bucket 60 seconds, `W_max = 30 minutes`, correction budget 5 minutes. These need workload experiments; they are not new assignment targets.

When a runnable task reaches `W_max`, commit its **next feasible compatible reservation** using the minimum capacity it needs. Backfill before a protected start only when an enforced maximum occupancy bound, including staging and cleanup, fits before that start; a P99 estimate alone is insufficient. Without such a bound or supported preemption, leave the reserved capacity idle rather than borrowing it. Existing protected starts cannot slide on every new short-job arrival. This guard can reserve a start even for band 2 while other work is band 1; record the tradeoff and resulting feedback delay. It is more meaningful than claiming that aging below an endless urgent stream guarantees service.

Already running nonpreemptive work may exceed its estimate; a reservation behind it is a forecast until the host is drained, or its enforced occupancy bound proves the start feasible. Mark an overrun as a reservation conflict and expose a revised ETA/risk. A hard protected start is promised only with capacity made available by a proven bound or completed drain. Infrastructure loss can still invalidate that availability.

No unconditional maximum wait is possible with insufficient GPU supply, continuing overload or tasks with no bounded runtime. Under overload, report `deadline_at_risk`, stop issuing confident ETAs, alert the instructor and retain durable pending work. Hard-SLA emergencies may override an aged reservation only as an explicit audited exception; that forfeits the starvation guarantee and requires an alert.

### Slow versus fast: two different ties

- **Same due time:** a 10-minute task needs to start earlier than a 1-minute task. Latest safe start normally puts the long task first.
- **Same full urgency bucket and fair-service value:** run the shorter remaining task first, unless an aged reservation requires otherwise. The long task retains its protected start; neither job is interrupted merely to reorder a tie.

## 5. Red-black tree design

Use one logical READY index per resource class (`CPU`, `RAM`, `GPU`) under one active scheduler leader. Every task belongs to exactly one class. CPU-compatible fallback placement is checked against the same ledger identity; do not duplicate nodes across trees. Course-dedicated occupied Spots expose only compatible course opportunities; a minimum incompatible with a particular Spot is skipped for that opportunity, not deleted globally.

```text
K(task) = (
  urgency_band,                         # 0 < 1 < 2 < 3
  floor(latest_start_utc_seconds / 60),    # absolute instant, not now() comparator
  V_course_snapshot,
  estimated_remaining_seconds,
  accepted_at_utc,
  task_id
)
```

The smallest lexicographic key wins among feasible candidates. Red/black colors balance the tree; **they do not mean urgent/nonurgent**. Root and NIL leaves are black, no red node has a red child, every path to NIL has equal black height, and keys follow binary-search order. A minimum node need not be the root. The [Linux rbtree documentation](https://www.kernel.org/doc/html/latest/core-api/rbtree.html) explains ordered traversal, cached leftmost lookup and the need to remove/reinsert changed keys.

Example snapshot (remaining accepted-time and ID tie-breakers omitted):

| Task | Key prefix `(band, bucket, V, seconds)` | Meaning |
| --- | --- | --- |
| P1 | `(1, 100, 0, 60)` | First urgent Programming task |
| P2 | `(1, 101, 0, 60)` | Later latest-start bucket |
| A1 | `(2, 90, 0, 600)` | Aged Architecture task; protected start can supersede normal extraction |
| A2 | `(3, 200, 0, 600)` | Normal Architecture task |
| P3 | `(3, 201, 0, 60)` | Fast task in a tie |
| A3 | `(3, 201, 0, 600)` | Slow task in the same bucket and service tie |
| P4 | `(3, 202, 0, 60)` | Later normal task |

The drawing uses black root A2, red children P2/A3 and black grandchildren P1/A1/P3/P4. Its in-order sequence is P1, P2, A1, A2, P3, A3, P4. The example combines CPU-capable workloads to teach key order; actual placement still respects course occupancy and resource classes.

Operational rules:

1. On durable READY transition, insert `(K, task_id, row_version)` and retain `task_id → node` for removal.
2. Extract the smallest feasible candidate; validate its current row/version before creating a reservation. If no host fits, leave it pending and consider a compatible candidate; preserve the blocked task's protected start.
3. On age/feedback boundaries, telemetry, reservation or course-service changes, remove affected nodes and insert new keys. Never use a comparator reading the clock or mutate a linked key in place.
4. Persist tasks, decisions, fairness accounting and reservation versions; rebuild all indexes from the ledger after leader change. A standby does not schedule concurrently without ownership.
5. A single insert/remove/key change costs `O(log N)`; cached minimum lookup is `O(1)`, and feasible-candidate scans can be `O(N)`. Updating every affected task can cost `O(M log N)` or require a full rebuild. The tree does not solve multi-resource placement in logarithmic time.

PostgreSQL's persisted indexes are separate implementation details; a PostgreSQL index is not this in-memory red-black tree. For this lab, a reviewed tree implementation is preferable to a handwritten balancing algorithm. A sorted SQL query would be a simpler starting implementation if the red-black tree were not part of the requested design.

## 6. Spot placement and autoscaling

Filter before ranking hosts: healthy and READY, fresh heartbeat, enough unreserved resources over the entire estimated interval, correct image/runtime/GPU, compatible course epoch, and no interruption/drain signal. BOOTING does not mean available; a new host becomes eligible after image preparation and agent health checks.

Among eligible hosts, minimize predicted completion time including staging and existing reservations; then favor lower measured pool interruption risk and image locality. Resolve an otherwise exact tie deterministically by instance ID. **Instance age is not used as an interruption probability.** The cited AWS signals describe interruption risk and recovery opportunities, not a lifetime after which a Spot becomes unsafe.

On `EC2 Instance Rebalance Recommendation`, mark the host DRAINING and stop assigning new work. The signal can arrive together with an interruption notice; do not assume extra time. This follows [AWS rebalance guidance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/rebalance-recommendations.html). Thus a freshly READY Spot beats an older **draining/full** Spot; a warm healthy old host can beat a cold new one.

On `EC2 Spot Instance Interruption Warning`, attempt a supported checkpoint, persist recovery state and release/replan affected reservations. Notices are best effort; stop/terminate normally provide two minutes, while hibernation does not provide that advance interval. Heartbeat expiry handles loss without a notice. See [AWS interruption notices](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html). Application checkpoints must be periodic for long work and written outside the host; arbitrary student programs cannot be assumed to resume from a generic memory snapshot.

Autoscaling consumes pending **resource-time by deadline**, not only task count. For a homogeneous resource class, an initial lower-bound calculation is:

```text
required_spots = ceil(sum(task_runtime_minutes / course_concurrency)
                      / useful_window_minutes)
useful_window = target_window - expected_boot_and_image_warmup
```

Then validate CPU/RAM/VRAM feasibility and the per-Spot calendar. This aggregate estimate is not a packing proof. A single AI task can still require one GPU host even if fractional demand is small. Sum fleet requests across all pools and bound launch reservations plus live instances by 10. Diversify compatible types/AZs, recalibrating resource profiles.

**A strict ten-instance cap requires special replacement handling.** AWS Auto Scaling Capacity Rebalancing can temporarily exceed a group's maximum by up to 10% of desired capacity. Do not enable that behavior and claim a hard cap. Use a global launch-permit controller covering scale-out, warm-up and replacement, and a replacement path that releases/terminates one host before launching another when all ten permits are occupied. This can reduce available capacity during recovery. AWS documents the behavior in [Capacity Rebalancing](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-capacity-rebalancing.html).

### Protecting the 23:00 rush

Before the known final-30-minute burst, drain selected CPU Spots and warm Programming images. During the protected window, those Spots accept urgent Programming only. Size this reservation from expected arrivals and completion capacity; unused slices can be borrowed only if an enforced maximum occupancy bound proves the borrower will release capacity before protection starts. Do not launch a 10-minute Architecture task at 23:29 on a Spot reserved for Programming at 23:30.

All ten full at 23:59 means a new task waits for completion or an explicitly supported checkpoint/preemption. The default is nonpreemptive execution: do not kill an arbitrary long task merely because a short urgent one arrived. Without prior reservation, the scheduler cannot undo already consumed capacity. Show the delay and risk rather than inventing an eleventh Spot.

Illustration, assuming steady 1-minute Programming executions, warmed images and no failures: 600 tasks on ten dedicated Spots need `ceil(600 / 200) = 3` one-minute waves; eight Spots need `ceil(600 / 160) = 4` waves. These are idealized examples, not P99 response-time guarantees. Cold start, actual runtime distribution, fairness and retries increase elapsed time. Likewise, homogeneous maximum concurrency is 200 Programming **or** 40 Architecture **or** 20 AI, not their sum; availability of ten GPU Spots is not guaranteed.

## 7. Durable schedule and dispatcher protocol

| Record | Minimum fields |
| --- | --- |
| `tasks` | task/submission/version IDs, course/assignment/student IDs, S3 object version and checksum, image digest, acceptance/closure/grading/feedback instants, runtime/resource estimates, band/key snapshot, status, row version, retry eligibility |
| `spots` | instance ID, resource profile/AZ, lifecycle/heartbeat, CPU/RAM/VRAM capacity and measured use, course epoch, cached images, drain/risk signals |
| `reservations` | reservation/task IDs, `planned_start_at`, `planned_finish_at`, nullable `spot_id`, requested resources, plan version, status, protection reason |
| `attempts` | attempt/task/spot IDs, monotonic fencing token, lease owner/expiry, actual start/finish, checkpoint pointer, outcome, infrastructure and application error counters |
| `outbox` / `manual_review` | durable pending transport/notification events and quarantined failures |

Long-range plans can have `spot_id = null` with a resource class and estimated window. Assign a concrete ID only after an actual instance registers; a requested instance may never launch. A date/time in the database is a **revisable estimate**, distinct from a short-lived execution authorization. Running work and protected reservations are not casually rewritten.

Workflow (same execution core for both ingestion options):

1. API authenticates/rate-limits, uploads the immutable artifact to S3, verifies completion, then commits the submission/task identity and outbox event. Respond with durable acceptance; a DB failure must not produce a false accepted response. Clean up orphaned S3 uploads separately.
2. Recommended path: outbox relay sends a small ID/version event to the appropriate SQS course queue. An importer validates/upserts the ledger transition and acknowledges only after commit. Poll all three queues fairly; importer lag counts toward forecast latency. A `RECEIVED` row becomes READY after import and required validation. Direct-DB variant commits that runnable transition without the adapter.
3. Leader computes keys and calendars. A short transaction locks the chosen task and Spot capacity row, rechecks versions/resources and inserts the reservation with a unique live-attempt constraint. It never holds locks while transferring artifacts. Scheduler leadership uses a renewable database lease and a fencing epoch; reservation writes require the current unexpired epoch.
4. Dispatcher workers claim due PLANNED reservations with a short `SELECT ... FOR UPDATE SKIP LOCKED` transaction, create the fenced attempt and set DISPATCHING. Multiple dispatchers can run; this statement avoids claim contention but does not replace the capacity transaction. [PostgreSQL documents its use for queue-like tables](https://www.postgresql.org/docs/current/sql-select.html).
5. The trusted host agent validates the lease, fencing token, plan version and host state, downloads S3 artifacts, verifies checksums/image digest and stages a read-only input mount. The dispatcher sends IDs and manifests, not multi-GB files through its own process. Student sandboxes have no network or AWS credentials; the trusted agent performs transfers outside them.
6. Agent rechecks authorization immediately before starting, starts one sandbox per attempt, enforces CPU/RAM/VRAM/process/time limits and reports RUNNING plus heartbeats. Long staging renews the dispatch lease. Sandbox starts are idempotent on attempt ID.
7. Results/checkpoints upload to attempt-specific S3 keys. The result service accepts a grade only with the current fencing token and active attempt, commits the result and notification outbox, then updates cache/read views. Stale attempts cannot overwrite a grade.
8. Reconciler detects missed starts, lost heartbeats, expired leases and incomplete staging. It invalidates stale tokens, releases reservations, retains original acceptance/deadlines and returns recoverable work to READY after backoff. A graceful DRAINING transition replans only unstarted work; healthy RUNNING attempts retain leases and drain until completion or actual interruption. Do not replay them merely because a rebalance recommendation arrived. In the hybrid path, a transactional recovery outbox also sends the course retry event; importer replay never resets a RUNNING/GRADED task.

SQS Standard delivery may duplicate/reorder events; importer and result handling must be idempotent ([AWS delivery semantics](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html)). Likewise, a lease cannot guarantee that partitioned code stops executing. Host agents must stop work when authorization expires; fencing prevents stale **effects**, while retries may briefly overlap physically. Do not promise exactly-once execution. Do not reuse a host's uncertain local capacity until its agent reconciles it or the host is terminated.

State outline:

```text
RECEIVED -> READY -> PLANNED -> DISPATCHING -> RUNNING -> GRADED
                 ^                 |           |
                 +---- RETRY_WAIT <+-----------+   infrastructure failure
RECEIVED/READY -> SECURITY_HOLD -> READY | REJECTED
RETRY_WAIT -> READY | MANUAL_REVIEW
READY/PLANNED -> SUPERSEDED | CANCELLED
```

RUNNING may reference durable checkpoints without pretending every execution is resumable. OOM/timeout caused by violating published student limits produces an evaluation outcome; failed host infrastructure creates a free retry. Unknown failures use a separate bounded counter, proposed initial limit three attempts, then quarantine/manual review. Cloud interruptions never reduce the student's grade; repeated infrastructure loss triggers an operational alert rather than silently exhausting a student error allowance. `MANUAL_REVIEW` may finish through the existing teacher interface. The broker DLQ handles failed imports/events; task quarantine handles failed executions after import.

## 8. Queue decision and requirement impact

| Option | Advantages | Costs and contract impact |
| --- | --- | --- |
| Existing course queues directly consumed by workers | Familiar buffering and parallel consumers | No global reservation calendar or arbitrary reprioritization; broker delivery order becomes an accidental policy |
| **Recommended: SQS ingress/retry + DB scheduler + tree + dispatcher** | Burst isolation; RF4/RNF1 retained; explicit placement and execution order; persistent recovery | Importer/outbox complexity; measure broker lag; ledger still needs HA and capacity |
| Direct DB ingress + DB scheduler + tree + dispatcher | Fewer transport components; arbitrary plan updates; matches the professor's queue-free alternative | Peak writes contend with planning/status; implement leases, retries, quarantine, cleanup and backpressure; RF4/RNF1/RF9/RF10/RNF4 need revised wording |

The drawing's dashed direct-DB path is an **alternative** to the SQS adapter, not a second parallel submission route. Activate one ingestion mode for a given task version.

| Current requirement | Proposed effect; no backlog files changed |
| --- | --- |
| RF1/RF2/RNF9 | Preserve mobile/teacher submission and S3 durability; add durable receipt identity |
| RF3 | Preserve legacy routing before this subsystem; unmigrated courses remain on the laptop |
| RF4 | Hybrid retains three course-type queues; fully queue-free variant must replace this requirement with logical workload partitions |
| RF5/RNF7 | Preserve asynchronous specialized workers; enforce runtime isolation, not merely a static scan |
| RF6/RF10 | Preserve manual review and DLQ; distinguish execution quarantine from transport DLQ. Queue-free variant uses a durable quarantine table instead |
| RF7/RF8/RNF5/RNF6 | Publish estimated start/finish, actual status and final grade; preserve read replicas/cache/push. Claims and scheduling read the primary, never a stale replica |
| RF9/RNF2 | Persist infrastructure recovery and fenced retries; hybrid re-enqueues an event, direct DB marks a task runnable again |
| RNF1 | Hybrid retains SQS buffering; direct DB needs a new peak-load/backpressure contract |
| RNF3/RNF4 | Spot-only workers, strict fleet limit 10, scale by queued workload and ledger resource-time; direct DB replaces queue-depth wording |
| RNF8/RNF10 | Distinct scheduler/dispatcher/agent boundaries, decision reasons, traces, queue/import lag, reservation delay and recovery metrics |

The assignment text itself lists RF4/RNF1. A verbal alternative should be reconciled with that assignment before claiming full compliance. This report recommends a design without changing the source assignment or declaring it satisfied.

## 9. Proposed validation scenarios

These are acceptance and fitness-function proposals, **not executed system tests**.

| Scenario | Observable expected result |
| --- | --- |
| 23:30 burst with later Architecture deadline | Protected Programming Spots admit only the urgent course; pending nonurgent work cannot consume those slices |
| All ten occupied by long work | No eleventh launch; queued task shows revised estimate/risk; existing work is not arbitrarily killed |
| Same due time, 1-minute and 10-minute work | Latest safe start favors long work when necessary; short-job tie rule is applied only after urgency/fairness ties |
| Same bucket/service, 1-minute and 10-minute work | Short runs first, aged long reservation retains a start despite repeated short arrivals |
| 20 versus 100 active students | Equal-urgency tie allocation follows the documented weighted service accounting; higher urgency still wins |
| Free CPU, pending GPU | CPU work continues; GPU task remains durable, raises capacity risk and never runs on an incompatible host |
| Old draining Spot and new READY Spot | No new work on draining host; ready host used. Healthy warm old host is not rejected just for age |
| Rebalance, sudden loss and stale heartbeat | Stop assigning, recover from supported checkpoint or restart, preserve deadlines and grade allowance |
| Duplicate event/dispatcher crash/network partition | At most one accepted result; stale fencing token rejected; expired claims recovered without lost tasks |
| Peak uploads + status reads + scheduling writes | Measure DB/queue lag and scheduling latency; establish a supported load envelope before claiming availability |
| RAM abuse or forbidden network access | Sandbox limits/isolation hold; neighboring task resources and credentials remain protected |
| Three imported execution failures | Execution quarantine reaches teacher review; broker retries do not independently rerun the same task |
| Rebalancing at the ten-instance limit | Global permits include replacements and BOOTING hosts; observed total never exceeds ten |
| Scheduler restart/key updates | Rebuild produces identical order at the same policy snapshot; validate RB invariants and changed-key reinsertion |

Measure: feedback turnaround by course, grading SLA misses, oldest runnable age, service share/resource-minute error, forecast versus actual finish, image-hit rate, wasted compute on interruptions, fencing rejections, capacity overruns, importer lag, DLQ/quarantine age and launch-permit usage. Compare policies on replayed burst traces; report starvation and SLA tradeoffs alongside average response time.

## 10. Change record and review status

- Added this proposed policy and the architecture/tree drawings under `Laboratorio11/plan/`.
- Replaced the unexplained priority product with gates, protected service and a reproducible comparison key.
- Distinguished submission closure, correction feedback target and grading SLA.
- Added course-aware capacity calendars, strict global launch permits, revocable estimates and concrete attempt fencing.
- Corrected the Spot-age assumption and removed any unconditional checkpoint/resume or deadline guarantee.
- Preserved original files and requirement IDs; recorded proposed changes rather than silently applying them.
- Recorded durable laboratory context in `brain/lab11.md`, as required by the repository's memory instructions.

Validation of these deliverables is recorded below after document, diagram and visual checks. A builder review checks material ambiguities; it is not the laboratory's requirements evaluator. No workload simulation, AWS deployment or performance experiment is included.

### Authoring checklist

- [x] Read assignment, both backlogs, supplied image, existing drawing labels and laboratory routing context.
- [x] Verify external technical claims against official AWS, PostgreSQL and Linux sources.
- [x] Define ordering, red-black-tree key, placement, dispatch, recovery and requirement impacts.
- [x] Independent builder check and resulting corrections.
- [x] Render both Excalidraw scenes, inspect PNGs and correct layout.
- [x] Verify file links, IDs, bindings, RB example invariants and preservation of source files.

Open policy approvals before production: grading-clock origin, correction target, timeout/checkpoint support per assignment, fairness parameters, overload communication, and whether the professor accepts replacing explicit SQS requirements. These do not block reviewing the proposed design.

### Deliverable validation results

- Architecture: 76 elements, 38 texts, 17 arrows; PNG 1890 × 1355. Tree: 36 elements, 21 texts, one selection arrow; PNG 1530 × 1135. Both were rendered from their final source scenes and visually inspected.
- Checked unique IDs, existing targets and reciprocal arrow bindings, readable text settings, and source hashes matching render manifests. The render evidence checker verified complete image coverage and pixel-exact crops. Final renders had zero failed network requests.
- Mechanically checked the illustrated tree's search order, black root, absence of red/red adjacency and equal black height of three including NIL. Verified the reported in-order sequence. This validates the example, not a production tree implementation.
- Independent builder review found two issues: estimated backfill could overrun a protected start, and graceful drain was conflated with failure recovery. Both were corrected; follow-up review reported no important questions remaining within the proposed scope.
- Checked local document links and `git diff --check`; original assignment, backlogs and drawings were not edited. Machine-readable counts, hashes and validation scope are in [validation.json](validation.json).
- The skill's initial CDN-based renderer failed before scene loading because an `esm.sh` dependency returned HTTP 404. Used the repository's existing pinned local Excalidraw export helper instead; no skill code or runtime package manifest in the repository was changed.
- No AWS deployment, runtime benchmark, load simulation, fitness-function execution or laboratory evaluator run was performed. The scenarios in section 9 remain proposed tests.

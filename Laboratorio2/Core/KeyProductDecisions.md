# Key Product Decisions

These are constraints that are **already settled** for the Lea$e platform. They are not
open design questions — a requirement that contradicts one of these is a defect. Each
decision traces back to the roles defined in [Users and their needs](UsersAndTheirNeeds.md)
(`people/Cesar.md`, `people/JuanPedro.md`, `people/Maxim.md`) and the scope boundaries they
declare.

## KPD-1 — The system mediates exactly one relationship: the client company ↔ the leasing company

The platform's only job is to mediate the relationship between the **client company**
(represented by its Head of Finance) and the **leasing company** (represented by its Head of
Credit and Collections). Every screen, flow and data object exists to support that single
relationship: financing request → approval → payments → end-of-contract resolution.

- We do **not** model a marketplace, a procurement tool, or a multi-party negotiation.
- Rationale: keeps the scope narrow and the POC implementable end to end.

## KPD-2 — The Provider (equipment seller) is out of scope as an actor

The Provider is real business context — the Head of Finance needs a specific machine from a specific
Provider before anything starts — but the Provider is **not a persona, actor, screen, API
or flow** in this system.

- Choosing the machine/Provider is a commercial negotiation that happens entirely outside
  the platform, before the Head of Finance ever logs in.
- The leasing company's purchase of the equipment from the Provider is also external
  (offline purchase order, logistics, delivery).
- Inside the system, equipment delivery appears at most as a **status update**, never as a
  flow the platform orchestrates.

## KPD-3 — Two roles, two distinct authenticated users

There are exactly two authenticated human roles in the POC:

- **Client company's Head of Finance:** starts the leasing cycle, requests financing, pays
  installments, makes the end-of-contract decision.
- **Leasing company's Head of Collections:** owns everything once a contract is active —
  schedule generation, collections, delinquency, end-of-contract processing.

The credit/risk **approval decision** may conceptually sit with a separate credit/risk role,
but for the POC it is treated as a decision surfaced to (and tracked by) the leasing-company
side, not a third role.

> **Update (architecture-diagram walkthrough):** the diagram review surfaced a **third
> authenticated role, the Broker**, and refined the leasing company's collections role to
> **Head of Credit and Collections**. KPD-3 above is kept as the original two-role decision
> for traceability; see **KPD-11** below, which supersedes the "exactly two roles" statement
> with the current, three-role model. Nothing in KPD-1/KPD-2/KPD-4/KPD-5 changes as a result —
> the Broker acts as a facilitator between the client company and the leasing company, not as
> a new relationship.

## KPD-4 — Contracts are denominated in PEN or USD, and the exchange rate is a value tracked over time

This is the most load-bearing business rule and it directly shapes the data model:

- A contract is denominated in **Peruvian Soles (PEN)** or **US Dollars (USD)**, chosen by
  the Head of Finance at request time.
- The exchange rate is **fixed/locked at contract start**, so the initial installment
  schedule is predictable.
- That rate is **not guaranteed permanent**: depending on how payments unfold (delays,
  renegotiation, specific contract terms), the applicable rate **may be revisited at later
  points** in the contract.
- Therefore the architecture must treat exchange rate as a **variable over time per
  contract** (a history of rate values with effective dates), **never** a static field set
  once at contract creation.
- Every rate change must be **visible to both the Head of Finance and the Head of Credit and Collections**: what changed, when, and
  why.

> Status: this rule is currently an **assumption to validate** with stakeholders/the
> professor. It is treated as settled for design purposes because it materially affects how
> much the client company owes; if it is later relaxed, the rate-history model still holds.

## KPD-5 — The end-of-contract decision has exactly two branches, both resolved inside the system

At the end of the contract term the Head of Finance chooses one of two mutually exclusive paths, and **both
are fully resolved within the platform** with no manual steps outside it:

- **Purchase option:** pay off all remaining installments and exercise the purchase option,
  keeping the equipment.
- **Return:** return the equipment in lieu of a final payment, closing the contract without
  acquiring the asset.

The leasing company's side processes whichever branch the Head of Finance selects.

## KPD-6 — Status and traceability are first-class, not an afterthought

Both roles' top pain point is **lack of visibility**. Therefore:

- Every financing request exposes a **clear, real-time status** (under review, approved,
  rejected/conditioned) and, on rejection, a **reason**.
- Every contract exposes its **schedule, outstanding balance, currency and rate in effect**,
  plus a **history** of rate changes and payments.
- State transitions (request → approval → active → closed) are persisted and traceable at all
  times.

## KPD-7 — The POC targets one fully working Happy Path

Per the case deliverables, the POC must run **at least one Happy Path end to end** for one of
the users. The chosen Happy Path is the Head of Finance's financing request through to an
active contract with a generated installment schedule (see [Main flows](MainFlows.md), Flow
1 + Flow 3). Everything else is designed but may be stubbed in the POC.

## KPD-8 — Credit evaluation is delegated; the system only orchestrates the outcome

Risk analysis is explicitly **out of scope** for the platform. The system never scores or
decides credit — it acts as an **orchestrator that tracks approval or rejection**, even if
the decision itself sits elsewhere (a risk analyst, an external bureau, a manual call).
Getting information and advice directly from the risk analyst is likewise out of scope: the
Broker (KPD-11) may relay that advice informally to the client, but the platform does not
model the risk analyst as an actor.

## KPD-9 — Delinquency is standardized into exactly 4 time-based levels

Delinquency is classified strictly by elapsed time since the missed due date, with no
external benchmarks or configurable typologies:

| Level | Meaning |
| --- | --- |
| Green | Paid on time |
| Yellow | 1 month without payment |
| Orange | 2 months without payment |
| Red | More than 2 months without payment |

This 4-level scheme is the only delinquency taxonomy the POC needs to support.

## KPD-10 — Contract closing stays binary (cross-reference)

Restates KPD-5: the two closing branches (purchase option vs. equipment return) are the only
supported ways to end a contract. No third closing path is introduced by the Broker role.

## KPD-11 — A third role: the Broker facilitates negotiation and documentation

The architecture-diagram review adds a **third authenticated role**, sitting alongside the
client company's Head of Finance and the leasing company's Head of Credit and Collections
(see the title update in KPD-3):

- **Broker:** a tactical facilitator, not a decision-maker. Schedules negotiation meetings
  between the Head of Finance and the leasing company, proposes deal ideas based on the
  client's need, and uploads the contract documentation — the PDF, its summary and its
  details — into the system.
- The Broker never replaces the Head of Finance's or the Head of Credit and Collections'
  decisions; the Broker's output (meetings, proposals, uploaded PDFs) feeds the negotiation
  that the Head of Finance and the leasing company ultimately close.
- Access is scoped narrowly: a Broker only sees the contracts they are actively negotiating
  (see [Acceptance criteria](AcceptanceCriteria.md) and the RBAC note in
  [Hints / Tips](HintsAndTips.md)).
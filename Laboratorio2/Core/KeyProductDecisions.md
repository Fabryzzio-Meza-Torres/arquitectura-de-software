# Key Product Decisions

These are constraints that are **already settled** for the Lea$e platform. They are not
open design questions — a requirement that contradicts one of these is a defect. Each
decision traces back to the two personas (`people/Cesar.md`, `people/JuanPedro.md`) and the
scope boundaries they declare.

## KPD-1 — The system mediates exactly one relationship: César ↔ Juan Pedro's Leasing Company

The platform's only job is to mediate the relationship between the **client company**
(represented by César, Head of Finance) and the **leasing company** (represented by Juan
Pedro, Head of Collections). Every screen, flow and data object exists to support that
single relationship: financing request → approval → payments → end-of-contract resolution.

- We do **not** model a marketplace, a procurement tool, or a multi-party negotiation.
- Rationale: keeps the scope narrow and the POC implementable end to end.

## KPD-2 — The Provider (equipment seller) is out of scope as an actor

The Provider is real business context — César needs a specific machine from a specific
Provider before anything starts — but the Provider is **not a persona, actor, screen, API
or flow** in this system.

- Choosing the machine/Provider is a commercial negotiation that happens entirely outside
  the platform, before César ever logs in.
- The leasing company's purchase of the equipment from the Provider is also external
  (offline purchase order, logistics, delivery).
- Inside the system, equipment delivery appears at most as a **status update**, never as a
  flow the platform orchestrates.

## KPD-3 — Two roles, two distinct authenticated users

There are exactly two authenticated human roles in the POC:

- **Client / Head of Finance (César):** starts the leasing cycle, requests financing, pays
  installments, makes the end-of-contract decision.
- **Leasing company / Head of Collections (Juan Pedro):** owns everything once a contract is
  active — schedule generation, collections, delinquency, end-of-contract processing.

The credit/risk **approval decision** may conceptually sit with a separate credit/risk role,
but for the POC it is treated as a decision surfaced to (and tracked by) the leasing-company
side, not a third persona.

## KPD-4 — Contracts are denominated in PEN or USD, and the exchange rate is a value tracked over time

This is the most load-bearing business rule and it directly shapes the data model:

- A contract is denominated in **Peruvian Soles (PEN)** or **US Dollars (USD)**, chosen by
  César at request time.
- The exchange rate is **fixed/locked at contract start**, so the initial installment
  schedule is predictable.
- That rate is **not guaranteed permanent**: depending on how payments unfold (delays,
  renegotiation, specific contract terms), the applicable rate **may be revisited at later
  points** in the contract.
- Therefore the architecture must treat exchange rate as a **variable over time per
  contract** (a history of rate values with effective dates), **never** a static field set
  once at contract creation.
- Every rate change must be **visible to both César and Juan Pedro**: what changed, when, and
  why.

> Status: this rule is currently an **assumption to validate** with stakeholders/the
> professor. It is treated as settled for design purposes because it materially affects how
> much the client company owes; if it is later relaxed, the rate-history model still holds.

## KPD-5 — The end-of-contract decision has exactly two branches, both resolved inside the system

At the end of the contract term César chooses one of two mutually exclusive paths, and **both
are fully resolved within the platform** with no manual steps outside it:

- **Purchase option:** pay off all remaining installments and exercise the purchase option,
  keeping the equipment.
- **Return:** return the equipment in lieu of a final payment, closing the contract without
  acquiring the asset.

Juan Pedro's side processes whichever branch César selects.

## KPD-6 — Status and traceability are first-class, not an afterthought

Both personas' top pain point is **lack of visibility**. Therefore:

- Every financing request exposes a **clear, real-time status** (under review, approved,
  rejected/conditioned) and, on rejection, a **reason**.
- Every contract exposes its **schedule, outstanding balance, currency and rate in effect**,
  plus a **history** of rate changes and payments.
- State transitions (request → approval → active → closed) are persisted and traceable at all
  times.

## KPD-7 — The POC targets one fully working Happy Path

Per the case deliverables, the POC must run **at least one Happy Path end to end** for one of
the users. The chosen Happy Path is César's financing request through to an active contract
with a generated installment schedule (see `MainFlows.md`, Flow 1 + Flow 3). Everything else
is designed but may be stubbed in the POC.
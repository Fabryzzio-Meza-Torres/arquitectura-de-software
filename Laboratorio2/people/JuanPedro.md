# Head of Credit and Collections — Leasing Company

> Title updated from "Head of Collections" to **Head of Credit and Collections** after the
> architecture-diagram review — same responsibilities below, now with explicit visibility into
> the credit side of the pipeline (this role receives and tracks financing requests, even
> though the risk decision itself sits elsewhere — see
> [Key product decisions](../Core/KeyProductDecisions.md) KPD-8).

## Who they are

The Head of Credit and Collections leads collections at the leasing company, the financial
institution this case study asks you to architect. This role's job is to make sure the
installments companies owe on active leasing contracts actually get collected — on time, in
the right currency, and reconciled correctly. This role is not the one deciding whether to
approve a new financing request (that may sit with a separate credit/risk role), but **owns
everything that happens once a contract is active**: the payment schedule, delinquency, and
the end-of-contract resolution.

Like the Head of Finance, the Head of Credit and Collections is not "the leasing company" as
an abstract entity — it is the actual user who logs into the system to track who owes what,
chase overdue installments, and close out contracts.

## Role in the system

The system's job is to mediate everything between the client company and the leasing company:
financing requests reaching the Head of Credit and Collections for tracking, installment
schedules, payments coming in, delinquency handling, and the end-of-contract resolution
(purchase option vs. equipment return).

## Out of scope: the equipment provider

In the real business, the leasing company is the one who buys the equipment from the provider
— but that relationship is **deliberately not part of this system**, and it's not part of the
Head of Credit and Collections' day-to-day either:

- Purchasing the equipment from the provider is an external, offline operation (negotiation,
  purchase order, physical logistics, delivery coordination) handled elsewhere in the
  organization. It has no screen, no API, and no flow inside this system.
- The **only reason it's worth mentioning at all** is to make the scope boundary explicit: this
  is not a procurement or supply-chain system. It's a financing and contract-management system
  between the client company and the leasing company.
- The Head of Credit and Collections' own concern starts once the contract is active — this
  role cares about collecting, not about how the equipment was sourced.

So, as with the Head of Finance persona, the provider shows up here only as business context,
never as a system actor, screen, or flow.

## Needs (Jobs to be done)

- See, contract by contract, what's due, when, and in which currency.
- Collect installments from every client company and detect/handle delinquency in a timely
  way.
- Reconcile payments against the schedule without manual spreadsheet work.
- Resolve the end-of-contract decision: if the client company pays off all installments,
  process the purchase option in its favor; if the client company chooses to return the
  equipment instead, process that as an alternative closing path.
- Maintain visibility over the entire portfolio of active contracts (amounts receivable,
  contracts at risk, currency exposure).
- See the **pronosticated income of the month**, assuming every active contract pays its
  installment.
- Group delinquent clients by a standardized **4-color delinquency level**
  (Green/Yellow/Orange/Red) and send a formal message based on how late they are.
- Receive the Broker's negotiation meetings and PDF contract submissions for the deals being
  tracked (see [Main flows](../Core/MainFlows.md), Flow 1B).

## Pain points

- Default risk: if a client company doesn't pay, the leasing company has already committed
  capital to the equipment purchase (an external, sunk cost from the system's perspective) —
  the Head of Credit and Collections is the one who has to chase that down.
- Reconciling installment payments across many active contracts, potentially in two different
  currencies, without centralized visibility.
- No clear, automated process for the end-of-contract decision — today it's unclear whether the
  flow that follows differs (purchase option vs. equipment return) or is handled ad hoc.
- Lack of portfolio-level visibility: hard to see, at a glance, which contracts are healthy,
  which are delinquent, and how much is exposed to exchange-rate movement.

## Constraint: currency & exchange rate (PEN / USD)

Same underlying business rule as in the Head of Finance persona, but from the collections
side — this is arguably where it matters most operationally:

- Contracts can be denominated in **Peruvian Soles (PEN)** or **US Dollars (USD)**.
- The exchange rate is **fixed/locked at contract start**, so the initial schedule is
  predictable.
- That rate **can be revisited later in the contract's life** depending on how payments
  unfold — meaning this role can't assume the schedule generated on day one stays valid in the
  original currency conversion forever.
- For the Head of Credit and Collections specifically, this means the system needs to expose,
  per contract: the currency, the rate in effect, and a history of any rate changes —
  otherwise reconciling "did they actually pay what they owed" becomes guesswork.
- **This is currently flagged as an assumption to validate**, not a closed rule — but the
  architecture should treat exchange rate as a value tracked over time per contract, not a
  static field.

## Main flows this role participates in (inside the system)

1. **Receives the financing request** from the client company (visibility into new requests
   entering the pipeline).
2. Tracks approval/rejection of the request (even if the decision itself sits elsewhere).
3. **Generates the installment schedule** and **collects payments** from the client company
   throughout the contract term, in the contract's currency.
4. Handles **exchange-rate updates** on active contracts when they occur, and keeps the
   schedule/balance consistent.
5. At the **end of the contract term**, resolves the closing decision the client company
   makes:
   - If the client company **pays off all installments**, processes the **purchase option**
     in its favor.
   - If the client company chooses to **return the equipment** instead, processes that as the
     alternative contract closure — no purchase option is exercised.

## What this role expects from the system

- A collections dashboard: active contracts, pending installments, delinquency, currency and
  exchange-rate exposure.
- Automatic generation of installment schedules per contract, with currency clearly attached.
- Alerts when an exchange-rate change needs to be applied to an active contract.
- An end-of-contract flow that clearly branches between the purchase-option path and the
  equipment-return path, with no manual work required.

## Success criteria

- Zero mismatch between what's collected and what the schedule (in the correct currency/rate)
  says should be collected.
- Real-time visibility into the full contract portfolio, including currency exposure.
- The end-of-contract decision (purchase vs. return) is fully resolved inside the system, with
  no steps handled outside it.

# Juan Pedro — Head of Collections at Juan Pedro's Leasing Company

## Who they are

Juan Pedro is the Head of Collections at Juan Pedro's Leasing Company, the financial institution this case study asks you to architect. His job is to make sure the installments companies owe on active leasing contracts actually get collected — on time, in the right currency, and reconciled correctly. He's not the one deciding whether to approve a new financing request (that may sit with a credit/risk role), but he **owns everything that happens once a contract is active**: the payment schedule, delinquency, and the end-of-contract resolution.

Like César, Juan Pedro is not "the leasing company" as an abstract entity — he's the actual user who logs into the system to track who owes what, chase overdue installments, and close out contracts.

## Role in the system

Juan Pedro is the **counterpart to César** inside the system. The system's job is to mediate everything between César and Juan Pedro: financing requests reaching him for tracking, installment schedules, payments coming in, delinquency handling, and the end-of-contract resolution (purchase option vs. equipment return).

## Out of scope: the Provider

In the real business, Juan Pedro's Leasing Company is the one who buys the equipment from the Provider — but that relationship is **deliberately not part of this system**, and it's not part of Juan Pedro's day-to-day either:

- Purchasing the equipment from the Provider is an external, offline operation (negotiation, purchase order, physical logistics, delivery coordination) handled elsewhere in the organization. It has no screen, no API, and no flow inside this system.
- The **only reason it's worth mentioning at all** is to make the scope boundary explicit: this is not a procurement or supply-chain system. It's a financing and contract-management system between César and Juan Pedro's Leasing Company.
- Juan Pedro's own concern starts once the contract is active — he cares about collecting, not about how the equipment was sourced.

So, like in `Cesar.md`, the Provider shows up here only as business context, never as a system actor, screen, or flow.

## Needs (Jobs to be done)

- See, contract by contract, what's due, when, and in which currency.
- Collect installments from César (and every other client company) and detect/handle delinquency in a timely way.
- Reconcile payments against the schedule without manual spreadsheet work.
- Resolve the end-of-contract decision: if César pays off all installments, process the purchase option in his favor; if César chooses to return the equipment instead, process that as an alternative closing path.
- Maintain visibility over his entire portfolio of active contracts (amounts receivable, contracts at risk, currency exposure).

## Pain points

- Default risk: if César's company doesn't pay, the Leasing Company has already committed capital to the equipment purchase (an external, sunk cost from the system's perspective) — Juan Pedro is the one who has to chase that down.
- Reconciling installment payments across many active contracts, potentially in two different currencies, without centralized visibility.
- No clear, automated process for the end-of-contract decision — today it's unclear whether the flow that follows differs (purchase option vs. equipment return) or is handled ad hoc.
- Lack of portfolio-level visibility: hard to see, at a glance, which contracts are healthy, which are delinquent, and how much is exposed to exchange-rate movement.

## Constraint: currency & exchange rate (PEN / USD)

Same underlying business rule as in `Company.md`, but from the collections side — this is arguably where it matters most operationally:

- Contracts can be denominated in **Peruvian Soles (PEN)** or **US Dollars (USD)**.
- The exchange rate is **fixed/locked at contract start**, so the initial schedule is predictable.
- That rate **can be revisited later in the contract's life** depending on how payments unfold — meaning Juan Pedro can't assume the schedule generated on day one stays valid in the original currency conversion forever.
- For Juan Pedro specifically, this means the system needs to let him see, per contract: the currency, the rate in effect, and a history of any rate changes — otherwise reconciling "did they actually pay what they owed" becomes guesswork.
- **This is currently flagged as an assumption to validate**, not a closed rule — but the architecture should treat exchange rate as a value tracked over time per contract, not a static field.

## Main flows he participates in (inside the system)

1. **Receives the financing request** from César (visibility into new requests entering the pipeline).
2. Tracks approval/rejection of the request (even if the decision itself sits elsewhere).
3. **Generates the installment schedule** and **collects payments** from César throughout the contract term, in the contract's currency.
4. Handles **exchange-rate updates** on active contracts when they occur, and keeps the schedule/balance consistent.
5. At the **end of the contract term**, resolves the closing decision César makes:
   - If César **pays off all installments**, processes the **purchase option** in his favor.
   - If César chooses to **return the equipment** instead, processes that as the alternative contract closure — no purchase option is exercised.

## What he expects from the system

- A collections dashboard: active contracts, pending installments, delinquency, currency and exchange-rate exposure.
- Automatic generation of installment schedules per contract, with currency clearly attached.
- Alerts when an exchange-rate change needs to be applied to an active contract.
- An end-of-contract flow that clearly branches between the purchase-option path and the equipment-return path, with no manual work required.

## Success criteria

- Zero mismatch between what's collected and what the schedule (in the correct currency/rate) says should be collected.
- Real-time visibility into the full contract portfolio, including currency exposure.
- The end-of-contract decision (purchase vs. return) is fully resolved inside the system, with no steps handled outside it.

# César — Head of Finance at Cesar's Company

## Who they are

César is the Head of Finance at Cesar's Company, a Peruvian corporate/SME that works on a project basis (construction, mining, agro-industry, logistics, etc.). He's the one who owns the cash-flow problem at the root of this whole case: the company needs machinery *now* to execute a project, but its own client only pays out at the end of the project. César can't justify locking up working capital buying equipment outright, so he's the one who evaluates and pushes for financing the acquisition through leasing instead.

César is not "the company" as an abstract entity — he's the actual user who logs into the system, requests financing, and is accountable for every sol/dollar the company owes on active leasing contracts.

## Role in the system

César is the one who **starts** the leasing cycle, and his **only counterpart inside the system is Juan Pedro, Head of Collections at Juan Pedro's Leasing Company**. César never talks to the Provider through the platform — identifying which machine and which provider to use is a negotiation that happens entirely outside the system, before César ever opens it. Once that's settled, everything César does *in the system* is with Juan Pedro's Leasing Company: requesting financing, tracking approval, paying installments, and closing out the contract.

## Out of scope: the Provider

The Provider (equipment seller) is real and necessary to the business — César needs a specific machine from a specific Provider before any of this starts. But the Provider is **not a persona or actor of this system**, and this is a deliberate scope decision, not an oversight:

- César never talks to the Provider *through the platform*. Choosing the machine and the Provider is a commercial negotiation that happens entirely outside the system, before he ever opens it.
- The system's job is narrowly to mediate the **César ↔ Juan Pedro's Leasing Company** relationship (financing request → approval → payments → end-of-contract decision). It is not a marketplace or procurement tool.
- Any interaction Juan Pedro's Leasing Company has with the Provider (purchasing the equipment) also happens outside the system — see `JuanPedro.md` for that scope note.

So the Provider is mentioned here only as **business context** that explains *why* César needs financing in the first place — never as a flow, screen, or actor the system needs to support.

## Needs (Jobs to be done)

- Get the machinery the project requires without tying up capital.
- Request leasing financing quickly, without red tape that blocks the project from starting.
- Know the status of the financing request (approved, under review, rejected) and why.
- Have clear visibility into the installment schedule: how much, when, in which currency, and how much is left.
- At the end of the contract, be able to choose between keeping the equipment (paying it off / exercising the purchase option) or returning it — without friction either way.
- Understand exactly how currency and exchange-rate risk affects what the company owes over time (see constraint below).

## Pain points

- Tight cash flow — can't afford to lock up capital buying machinery outright.
- Traditional credit evaluation processes are slow and opaque (no visibility into why a request was rejected or what's missing).
- Risk of the project stalling if equipment delivery is delayed — even though that delay is entirely outside his control (it depends on Juan Pedro's Leasing Company's arrangement with the Provider).
- Lack of visibility: not always clear how much is owed, how much has been paid, or what happens after a missed installment.
- Uncertainty at end-of-contract: needs a clear, low-friction way to decide between purchasing the equipment or returning it.
- As Head of Finance specifically, César is the one exposed to **currency risk** — he needs to know, contract by contract, what exchange rate applies and when it can move.

## Constraint: currency & exchange rate (PEN / USD)

This is a business rule that directly shapes what César needs from the system, so it's worth stating explicitly as a constraint rather than leaving it implicit:

- Leasing contracts can be denominated in **Peruvian Soles (PEN)** or **US Dollars (USD)**.
- At the **start of the contract**, the exchange rate used to price the installment schedule is **fixed/locked** — so early in the contract, César sees a stable, predictable rate.
- That fixed rate is **not necessarily permanent for the life of the contract**: depending on how the payments unfold (e.g., delays, renegotiation, or specific contract terms), the applicable exchange rate **may need to be revisited or updated at later points** in the contract.
- This means the system can't treat the exchange rate as a one-time constant baked into the schedule — it needs to be a value that can be re-evaluated over the life of a contract, and every rate change needs to be visible to César (what changed, when, and why).
- **This is currently an assumption to validate with stakeholders/the professor**, not a fully closed business rule — but it's important enough (it directly affects how much César's company owes) that the architecture should account for exchange rate as a *variable over time*, not a static field set once at contract creation.

## Main flows he participates in (inside the system)

1. **Request leasing financing** from Juan Pedro's Leasing Company, referencing the equipment already agreed upon externally, and specifying the contract currency (PEN or USD).
2. Track the **approval status** of the financing request.
3. **Pay installments** to Juan Pedro's Leasing Company throughout the contract term, in the contract's currency. (Physical delivery of the equipment by the Provider happens outside the system — César only sees it reflected as a status update, if at all.)
4. Monitor **exchange-rate changes** affecting the contract, if/when they occur.
5. At the **end of the contract term**, choose one of two paths with Juan Pedro's Leasing Company:
   - **Pay off all remaining installments and exercise the purchase option**, keeping the equipment.
   - **Return the equipment** in lieu of a final payment, closing the contract without acquiring the asset.

## What he expects from the system

- A simple financing request flow, with real-time status visibility and clear currency selection.
- Notifications for approval/rejection, upcoming/overdue installments, and any exchange-rate change affecting his contract.
- A dashboard showing the payment schedule, outstanding balance, and the currency/rate in effect.
- A clear end-of-contract flow letting him choose between the purchase option and equipment return, entirely within the system.

## Success criteria

- Reduced financing approval time (no manual back-and-forth).
- Zero ambiguity about the status of his request, his payment schedule, or the applicable exchange rate at any point in time.
- The end-of-contract decision (purchase vs. return) is resolved entirely within the system, with no steps outside it.

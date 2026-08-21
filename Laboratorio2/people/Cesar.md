# Head of Finance — Client Company

## Who they are

The Head of Finance leads finance at a Peruvian corporate/SME client company that works on a
project basis (construction, mining, agro-industry, logistics, etc.). This role owns the
cash-flow problem at the root of this whole case: the company needs machinery *now* to execute
a project, but its own client only pays out at the end of the project. The Head of Finance
can't justify locking up working capital buying equipment outright, so this role is the one
who evaluates and pushes for financing the acquisition through leasing instead.

The Head of Finance is not "the company" as an abstract entity — it is the actual user who
logs into the system, requests financing, and is accountable for every sol/dollar the company
owes on active leasing contracts.

## Role in the system

The Head of Finance is the one who **starts** the leasing cycle, and their **only counterpart
inside the system is the leasing company's Head of Credit and Collections**. The Head of
Finance never talks to the equipment provider through the platform — identifying which machine
and which provider to use is a negotiation that happens entirely outside the system, before
the Head of Finance ever opens it. Once that's settled, everything this role does *in the
system* is with the leasing company: requesting financing, tracking approval, paying
installments, and closing out the contract.

## Out of scope: the equipment provider

The provider (equipment seller) is real and necessary to the business — the client company
needs a specific machine from a specific provider before any of this starts. But the provider
is **not a persona or actor of this system**, and this is a deliberate scope decision, not an
oversight:

- The Head of Finance never talks to the provider *through the platform*. Choosing the machine
  and the provider is a commercial negotiation that happens entirely outside the system, before
  this role ever opens it.
- The system's job is narrowly to mediate the **client company ↔ leasing company** relationship
  (financing request → approval → payments → end-of-contract decision). It is not a
  marketplace or procurement tool.
- Any interaction the leasing company has with the provider (purchasing the equipment) also
  happens outside the system — see the Head of Credit and Collections persona for that scope
  note.

So the provider is mentioned here only as **business context** that explains *why* the client
company needs financing in the first place — never as a flow, screen, or actor the system needs
to support.

## Needs (Jobs to be done)

- Get the machinery the project requires without tying up capital.
- Request leasing financing quickly, without red tape that blocks the project from starting.
- Know the status of the financing request (approved, under review, rejected) and why.
- Have clear visibility into the installment schedule: how much, when, in which currency, and
  how much is left.
- At the end of the contract, be able to choose between keeping the equipment (paying it off /
  exercising the purchase option) or returning it — without friction either way.
- Understand exactly how currency and exchange-rate risk affects what the company owes over
  time (see constraint below).

## Pain points

- Tight cash flow — can't afford to lock up capital buying machinery outright.
- Traditional credit evaluation processes are slow and opaque (no visibility into why a
  request was rejected or what's missing).
- Risk of the project stalling if equipment delivery is delayed — even though that delay is
  entirely outside this role's control (it depends on the leasing company's arrangement with
  the provider).
- Lack of visibility: not always clear how much is owed, how much has been paid, or what
  happens after a missed installment.
- Uncertainty at end-of-contract: needs a clear, low-friction way to decide between purchasing
  the equipment or returning it.
- As Head of Finance specifically, this role is the one exposed to **currency risk** — it needs
  to know, contract by contract, what exchange rate applies and when it can move.

## Constraint: currency & exchange rate (PEN / USD)

This is a business rule that directly shapes what the Head of Finance needs from the system,
so it's worth stating explicitly as a constraint rather than leaving it implicit:

- Leasing contracts can be denominated in **Peruvian Soles (PEN)** or **US Dollars (USD)**.
- At the **start of the contract**, the exchange rate used to price the installment schedule
  is **fixed/locked** — so early in the contract, the Head of Finance sees a stable,
  predictable rate.
- That fixed rate is **not necessarily permanent for the life of the contract**: depending on
  how the payments unfold (e.g., delays, renegotiation, or specific contract terms), the
  applicable exchange rate **may need to be revisited or updated at later points** in the
  contract.
- This means the system can't treat the exchange rate as a one-time constant baked into the
  schedule — it needs to be a value that can be re-evaluated over the life of a contract, and
  every rate change needs to be visible to the Head of Finance (what changed, when, and why).
- **This is currently an assumption to validate with stakeholders/the professor**, not a fully
  closed business rule — but it's important enough (it directly affects how much the client
  company owes) that the architecture should account for exchange rate as a *variable over
  time*, not a static field set once at contract creation.

## Note: the Broker, a third role in the system

A **Broker** now sits between the client company and the leasing company as a negotiation
facilitator — unlike the provider, the Broker *is* an in-system actor. The Broker books
negotiation meetings (which the Head of Finance can accept or reject), proposes deal ideas,
and uploads the contract's PDF, summary and details. The Head of Finance never negotiates the
deal terms alone — the Broker's job is to help close it faster. See
`Core/KeyProductDecisions.md` (KPD-11) and `Core/MainFlows.md` (Flow 1B).

## Main flows this role participates in (inside the system)

1. **Request leasing financing** from the leasing company, referencing the equipment already
   agreed upon externally, and specifying the contract currency (PEN or USD).
2. Track the **approval status** of the financing request.
3. Watches the leasing company's plans, has the chance to select the ideal plan for the
   contract, and can **accept/reject/propose another time** for a Broker-scheduled negotiation
   meeting; afterwards can ask for the negotiation details.
4. If the negotiation goes well, can **view the PDF, summary and details** of the contract the
   Broker uploaded.
5. **Confirm or reject the reception** of the machinery from the provider.
6. **Pay installments** to the leasing company throughout the contract term, in the contract's
   currency. (Physical delivery of the equipment by the provider happens outside the system —
   the Head of Finance only sees it reflected as a status update, if at all.)
7. Monitor **exchange-rate changes** affecting the contract, if/when they occur.
8. Can track the **timeline of the contract**.
9. At the **end of the contract term**, choose one of two paths with the leasing company:
   - **Pay off all remaining installments and exercise the purchase option**, keeping the
     equipment.
   - **Return the equipment** in lieu of a final payment, closing the contract without
     acquiring the asset.

## What this role expects from the system

- A simple financing request flow, with real-time status visibility and clear currency
  selection.
- Notifications for approval/rejection, upcoming/overdue installments, and any exchange-rate
  change affecting the contract.
- A dashboard showing the payment schedule, outstanding balance, and the currency/rate in
  effect.
- A clear end-of-contract flow to choose between the purchase option and equipment return,
  entirely within the system.

## Success criteria

- Reduced financing approval time (no manual back-and-forth).
- Zero ambiguity about the status of the request, the payment schedule, or the applicable
  exchange rate at any point in time.
- The end-of-contract decision (purchase vs. return) is resolved entirely within the system,
  with no steps outside it.

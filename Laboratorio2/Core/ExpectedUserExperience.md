# Expected User Experience

How each role should experience the Lea$e platform. This section calibrates flow
completeness: it describes the *feel* and the *guarantees* the user expects, not the
step-by-step (that lives in [Main flows](MainFlows.md)). Grounded in
[Users and their needs](UsersAndTheirNeeds.md) (`people/Cesar.md`, `people/JuanPedro.md`,
`people/Maxim.md`).

## Principles that apply to all roles

- **No black boxes.** Every request and every contract shows its current state at all times.
  A user never has to email or call to find out "what's happening now".
- **The reason is always attached.** A rejection, a conditioned approval, or an exchange-rate
  change is never a bare status — it carries the *why*.
- **Money is never ambiguous.** At any moment the user can see currency, rate in effect,
  amount due, amount paid, and outstanding balance for a contract.
- **Everything terminal happens inside the system.** Neither the approval nor the
  end-of-contract decision requires a step outside the platform.

## Client company's Head of Finance

Logs in with a project deadline pressing and tight cash flow. The experience should feel
like the **opposite of a traditional bank credit process**: fast, transparent, and
predictable.

What this role should be able to do without friction:

1. **Request financing** for equipment already agreed externally, choosing the contract
   currency (PEN or USD), in a single short form — no red tape that blocks the project from
   starting.
2. **See request status in real time** (under review / approved / conditioned / rejected),
   and on a negative outcome, **see exactly why** and what would change it.
3. **See the installment schedule** the moment the contract is active: how much, when, in
   which currency, and how much is left.
4. **Pay installments** in the contract currency and immediately see the balance update.
5. **Be notified** of anything that affects what is owed: upcoming/overdue installments and
   any **exchange-rate change** on the contract (with the before/after and the reason).
6. **Decide the end-of-contract** entirely in-app: choose between exercising the purchase
   option (pay off + keep) or returning the equipment (close without acquiring).

What this role should never experience:

- Silence after submitting a request.
- A rejection with no explanation.
- Discovering a change to the exchange rate after the fact, with no record of when or why.
- Being told to "handle the last step offline".

## Broker (negotiation facilitator)

The Broker's main pain point is closing the deal and the contract between the client company
and the leasing company, with all the pertinent documentation attached. This role's
experience should optimize for **speed to close**, not for owning the decision.

What this role should be able to do without friction:

1. **Book a negotiation meeting** between the client company and the leasing company, and
   propose ideas to close the agreement based on knowledge of the provider, the client's
   finances and the client's need.
2. **View open negotiations and agreements** being facilitated.
3. **Send messages** to the client company or the leasing company with guidance and advice to
   help close the agreement.
4. **Submit the PDF, summary and details** of the contract into the system.

What this role should never experience:

- Losing track of which negotiations are still open versus closed.
- Uploading a document with no confirmation that both the client company and the leasing
  company can now see it.

## Leasing company's Head of Credit and Collections

Lives in a **portfolio view**. The experience should feel like a control tower: knowing at a
glance what is healthy, what is at risk, and where the money and currency exposure sit.

What this role should be able to do without friction:

1. **See new financing requests** entering the pipeline and their approval/rejection status.
2. **Get an installment schedule generated automatically** per contract, with the currency
   clearly attached — no spreadsheets.
3. **Track collections and delinquency** across many active contracts, in two currencies,
   from one dashboard, with clients grouped by the **4-color delinquency level** (KPD-9).
4. **Reconcile payments** against the schedule automatically — "did they pay what they owed"
   is answered by the system, not by manual math.
5. **Apply and see exchange-rate updates** on active contracts, keeping schedule and balance
   consistent, with an audit trail per contract.
6. **Process the end-of-contract branch** the Head of Finance selects (purchase option vs.
   return) with no manual work and a clear record of which path was taken.
7. **See the pronosticated income of the current month** at a glance, assuming every active
   installment is paid, and send a formal message to a delinquent client based on how late
   they are.

What this role should never experience:

- Reconciliation that requires manual spreadsheets across currencies.
- Not knowing which contracts are delinquent or exposed to rate movement until it is too
  late.
- An ad-hoc, undocumented end-of-contract process that differs case by case.

## Experience quality bar (qualitative, refined into numbers in [Acceptance criteria](AcceptanceCriteria.md))

- Requesting financing feels like **minutes, not weeks**.
- Status is **always current**, never stale.
- Currency, rate, and balance are **never in question**.
- The two terminal decisions (approve/reject and purchase/return) are **fully in-system**.

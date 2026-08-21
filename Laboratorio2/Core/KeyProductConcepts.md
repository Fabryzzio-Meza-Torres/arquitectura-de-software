# Key product concepts

The vocabulary every requirement is expected to use. A requirement using a domain term absent
from this list, or using one of these terms inconsistently, loses Block D non-ambiguity in
`agents/eval-spec.md`.

- **Financing request** — the client company's ask to finance a specific piece of equipment,
  carrying an amount, a term and a currency (PEN or USD). States: Under review → Approved /
  Conditioned / Rejected.
- **Negotiation** — the broker-facilitated process of scheduling meetings, proposing deal
  ideas, and attaching contract documentation while a request is under review.
- **Contract** — the financing agreement once a request is approved and activated. See the
  contract state machine below.
- **Contract state machine** — the contract's lifecycle is a strict finite-state machine, not
  boolean flags:

  | State | Meaning |
  | --- | --- |
  | `PENDING` | Broker schedules meetings and attaches negotiation documentation. |
  | `ACTIVE` | Equipment is received; the fixed exchange rate becomes immutable; the installment schedule executes. |
  | `COMPLETED_PURCHASED` | All installments paid off; purchase option exercised. |
  | `COMPLETED_RETURNED` | Equipment returned; no purchase. |

- **Installment schedule** — the amount, due dates and count of payments generated on
  contract activation, priced in the contract currency at the locked exchange rate.
- **Locked exchange rate / rate history** — the exchange rate is fixed at contract start but
  is a value tracked over time: every change is stored with an effective date, alongside the
  prior value, and is visible to both parties. Never a static field set once.
- **Reconciliation** — matching a registered payment against the scheduled amount for its
  period, flagging (not silently accepting) partial or over payments.
- **Delinquency level** — a contract's payment health, classified into exactly 4 time-based
  levels (Green / Yellow / Orange / Red) by elapsed time since a missed due date. See
  [Key product decisions](KeyProductDecisions.md) KPD-9.
- **Pronosticated income** — the sum of every active contract's installment due within the
  current month, assuming full payment.
- **Purchase option** — the end-of-contract branch in which the client company pays off all
  remaining installments and keeps the equipment.
- **Return** — the end-of-contract branch in which the client company returns the equipment
  in lieu of a final payment, closing the contract without acquiring the asset.

See also [Hints / Tips](HintsAndTips.md) for the implementation-facing version of this model.

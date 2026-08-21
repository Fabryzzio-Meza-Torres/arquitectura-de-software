# Hints / Tips

Implementation guidance for the POC, plus the quality attributes it depends on. The domain
model and contract state machine referenced below live in
[Key product concepts](KeyProductConcepts.md) — this file only adds the implementation-facing
rules on top of that model.

- **Risk simulation.** Credit evaluation is out of scope (KPD-8) — do not build scoring logic.
  Implement a webhook or a simple manual status change (Approved/Rejected) that simulates the
  evaluator's response, so the POC's flow is never blocked waiting on a real risk engine.
- **Financial immutability.** Once a contract moves to `ACTIVE`, the data model must block
  any modification to the contract's **currency** and its **fixed exchange rate** (KPD-4).
- **Domain decoupling.** Keep the "Documents/Negotiation" module (used heavily by Brokers,
  Flow 1B) operationally separate from the "Ledger/Schedule" module (used by the Head of
  Credit and Collections, Flow 3–4). This is what lets the architecture split into
  independent microservices later.

## Quality attributes (NFRs) for the POC

- **Security & RBAC.** Strict view isolation: a Broker only accesses contracts they are
  negotiating; the Head of Credit and Collections has exclusive access to the global
  pronosticated-income projection and the delinquency engine (KPD-9).
- **Transactional consistency.** Delinquency-level computation (Yellow/Orange/Red) must run
  under ACID transactions, so a payment registered at the last minute immediately halts the
  collections-message trigger.

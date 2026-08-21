# Problem

Three critical business problems are the reason this platform is being built. Every
requirement should trace to at least one of them (see `agents/eval-spec.md`, Block C).

## 1. Slow, opaque path from financing request to a documented decision

Traditional credit evaluation is slow and gives the requester no visibility into why a
request was rejected or what is missing. The deal and its documentation can stall between
the client company and the leasing company while a broker tries to close it. The platform
must make the path from request to a documented, reasoned outcome fast and transparent — see
[Main flows](MainFlows.md), Flows 1, 1B and 2, and
[Key product decisions](KeyProductDecisions.md) KPD-6, KPD-8, KPD-11.

## 2. Money over the life of the contract is ambiguous

Contracts are denominated in PEN or USD; the exchange rate is locked at contract start but
is not guaranteed permanent, and can be revisited later in the contract's life. Without a
tracked rate history, reconciling payments across currencies becomes manual guesswork, and
delinquency is spotted late. The platform must treat the exchange rate as a value tracked
over time, reconcile every payment automatically, and classify delinquency continuously —
see [Main flows](MainFlows.md), Flows 3, 4 and 5, and
[Key product decisions](KeyProductDecisions.md) KPD-4, KPD-9.

## 3. End-of-contract resolution is ad hoc and lands outside the system

Today it is unclear whether the closing flow differs between "the client keeps the
equipment" and "the client returns it" — it is handled case by case, often outside the
platform. The platform must resolve exactly one of two mutually exclusive branches, entirely
in-system — see [Main flows](MainFlows.md), Flow 6, and
[Key product decisions](KeyProductDecisions.md) KPD-5, KPD-10.

# Users and their needs

Three authenticated roles use the platform. Full detail lives in `people/*.md`; this section
is the condensed, spec-facing version — by role, never by personal name — used as the
coverage checklist in `agents/eval-spec.md`, Step 1.

## Client company's Head of Finance

Owns the cash-flow problem this platform solves: the company needs machinery now, but its
own client only pays out at project end, so it finances the equipment instead of buying it.
Starts the leasing cycle and is the only party (besides the broker) the client company deals
with inside the system.

**Needs:** get machinery without tying up capital · request financing with no red tape ·
know the request's status and, on a negative outcome, why · see the installment schedule
(amount, dates, currency, balance) · resolve the end-of-contract decision without friction ·
understand how currency and exchange-rate risk affects what is owed over time.

**Pain points:** tight cash flow · slow, opaque traditional credit evaluation · no visibility
into what's owed, paid, or what happens after a missed installment · uncertainty at
end-of-contract · exposure to currency risk with no visibility into when the rate can move.

## Leasing company's Head of Credit and Collections

Owns everything once a contract is active: the payment schedule, delinquency, and the
end-of-contract resolution. Not the one deciding whether to approve a request (that decision
may sit elsewhere), but the one tracking it and everything downstream.

**Needs:** see what's due, when, and in which currency, per contract · collect installments
and detect/handle delinquency in time · reconcile payments without manual spreadsheet work ·
resolve the end-of-contract decision on whichever branch the client company chose · maintain
portfolio-level visibility (amounts receivable, contracts at risk, currency exposure) · see
the pronosticated income of the month · group delinquent clients by the 4-colour scheme and
send a formal message based on how late they are · receive the broker's negotiation meetings
and documentation for tracked deals.

**Pain points:** default risk with capital already committed · reconciling payments across
many contracts and two currencies with no centralized visibility · no automated,
non-ad-hoc end-of-contract process · no portfolio-level view of health and currency exposure.

## Broker (negotiation facilitator)

A tactical facilitator between the two decision-owning roles above. Never owns a decision;
the job is to close the deal and the contract, with all pertinent documentation, as fast as
possible.

**Needs:** book a negotiation meeting between the two sides · propose deal ideas to close the
agreement · send messages with guidance/advice to either side · submit the contract's PDF,
summary and details into the system · see, at a glance, the state of every negotiation being
facilitated.

**Pain points:** the deal/documentation process stalling on either side before it closes.

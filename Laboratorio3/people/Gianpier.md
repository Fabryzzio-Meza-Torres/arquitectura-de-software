# AgencyWorker — Gianpier

## Who they are

Gianpier represents the **AgencyWorker**: the authenticated operator who serves people at a
physical SendIT agency. This role is especially important for older adults and anyone who
does not confidently use web or mobile technology, lacks reliable connectivity, or needs
help understanding the remittance process.

## Role in the system

The AgencyWorker performs an **assisted channel**, not a separate kind of remittance. They
may capture data, verify documents, explain the quote, register cash funding, and complete a
cash payout. The resulting transaction follows the same exchange-rate lock, fee,
authorization, status and audit rules as web/mobile transactions.

The AgencyWorker is not the owner of the Sender's or Receiver's decision. Sensitive actions
require the customer's explicit consent, and the worker cannot alter a confirmed quote,
bypass identity/security controls, cancel after payout or access transactions outside the
assigned agency scope.

## Goals

- Serve customers quickly without weakening security.
- Explain every amount and step in plain language.
- Register cash received or delivered without reconciliation errors.
- Resolve ordinary exceptions through a controlled support path.
- Maintain an auditable record of who performed each assisted action.

## Needs from the system

- Authenticate with an individual worker account and only the permissions of the assigned
  agency and shift.
- Find the correct transaction without exposing unrelated customer data.
- Start or continue an assisted Sender flow and record explicit customer consent.
- Show or print the complete quote before accepting the Sender's deposit.
- Count and register cash funding, with a receipt and protection against duplicate posting.
- Verify the Receiver's identity and one-time payout authorization before releasing cash.
- See the exact local-currency amount to pay, without manually calculating exchange rates.
- Record cash payout once and immediately invalidate further payout attempts.
- Preview and process an eligible cancellation/refund with the operational fee disclosed.
- Escalate suspicious, mismatched or technically failed transactions without overriding
  controls.
- Close the cash drawer/shift with the system totals needed for reconciliation.

## Pain points

- Manual exchange-rate or fee calculations that can cause monetary loss.
- Shared credentials and no accountability for assisted transactions.
- Pressure to bypass identity checks when a customer lacks a document or code.
- Duplicate posting after connectivity loss or repeated button presses.
- Differences between agency records and the web/mobile transaction status.
- Complex screens that make it hard to explain the operation to a customer.

## Main flows this role participates in

1. Assist a Sender with quote, consent and cash funding.
2. Verify a Receiver and complete cash payout.
3. Assist with an eligible cancellation and refund.
4. Escalate a security, identity, cash or technical exception.
5. Reconcile the agency shift.

## What this role expects from SendIT

- A guided workflow with no need for manual rate, fee or payout calculations.
- Clear stop conditions when identity, authorization or transaction state is invalid.
- Receipts for customer and agency, with the worker identity in the audit trail.
- Resilient retry behavior that never duplicates cash movements.

## Success criteria

- Every assisted action is attributable to one worker, agency, shift and consenting customer.
- Agency processing preserves the same confirmed quote and Receiver amount as digital use.
- Cash received, paid and refunded reconciles to the shift ledger.
- The worker cannot bypass payout, cancellation or access-control rules.

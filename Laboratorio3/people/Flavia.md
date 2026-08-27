# Receiver — Flavia

## Who they are

Flavia represents the **Receiver**: the person in another country who receives the remittance
in the local currency of that country. The Receiver may use a digital payout method or visit
a physical agency. A SendIT account is not required merely to be named as a Receiver, but
identity and payout authorization must be verified before money is released.

## Role in the system

The Receiver does not choose the Sender's exchange rate or commission. Their central concern
is that SendIT clearly identifies the incoming remittance, protects it from unauthorized
collection and delivers exactly the local-currency amount confirmed when the Sender funded
the transaction.

## Goals

- Receive the full promised amount safely and promptly.
- Understand where and how the money can be collected.
- Avoid fraud, impersonation and unexpected deductions.
- Have a usable agency option when digital service is not suitable.

## Needs from the system

- Receive a notification that identifies the Sender, local-currency amount, payout method
  and safe next step without exposing sensitive data.
- See a clear status for the incoming remittance.
- Verify identity securely before payout.
- Receive **exactly** the confirmed Receiver amount in the local currency, with no fee
  deducted at payout.
- Choose or use the payout method authorized for the transaction: supported bank/wallet
  deposit or cash pickup at an agency.
- Collect cash through an AgencyWorker only after identity and one-time payout authorization
  are validated.
- Receive proof of payment and know that the remittance cannot be paid a second time.
- Get a clear explanation and support path if payout is held, rejected or unavailable.
- Use an accessible, plain-language experience or assisted agency service.

## Pain points

- Receiving less than the Sender said because the rate or a fee changed.
- Someone else collecting the funds using stolen information.
- Arriving at an agency without knowing which documents or code are required.
- Repeatedly checking a vague status with no expected next action.
- Digital interfaces that assume high technical literacy.

## Main flows this role participates in

1. Receive notification and track an incoming remittance.
2. Complete identity and payout authorization checks.
3. Receive the local-currency amount digitally or collect cash at an agency.
4. Obtain a payout receipt or follow an exception/support path.

## What this role expects from SendIT

- The amount announced after funding is the amount actually paid.
- Payout data and one-time codes are protected and never reusable.
- Digital and agency channels show the same transaction status.
- Instructions are short, localized and explicit about the next action.

## Success criteria

- The Receiver obtains exactly `origin amount × locked exchange rate`, rounded once under the
  destination currency rule recorded at quote confirmation.
- No commission is subtracted from the confirmed Receiver amount.
- Successful payout makes every later payout attempt fail safely.
- The Receiver receives an auditable receipt without unnecessary exposure of personal data.

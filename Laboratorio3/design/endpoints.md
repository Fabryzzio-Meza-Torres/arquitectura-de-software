# SendIT

Conventions:

- **Auth:** `Authorization: Bearer <JWT>` on every protected route (issued by the Auth Service).
- **Money → idempotency:** every `POST` that moves money (fund, payout, refund) requires the header **`Idempotency-Key: <uuid>`**. Retrying with the same key never duplicates the operation (FR-6, 20).
- **Style:** REST at the edge (through the API Gateway). Anything marked _internal_ travels over gRPC/events and is not exposed to the client.

---

## 1. Endpoint table

### Auth / Identity

| Method | Endpoint                          | What it's used for                                                         | FR    |
| ------ | --------------------------------- | -------------------------------------------------------------------------- | ----- |
| `POST` | `/auth/register`                  | Registers a new Sender (creates the account).                              | 1     |
| `POST` | `/auth/login`                     | Authenticates the Sender and returns the session JWT.                      | 1     |
| `POST` | `/auth/worker/login`              | Authenticates an AgencyWorker to operate at the agency.                    | 14    |
| `POST` | `/identity/verify`                | Identity verification (KYC) before confirming a remittance.                | 17    |
| `POST` | `/identity/tokens`                | Generates the temporary withdrawal token for the Receiver.                 | 9     |
| `POST` | `/identity/tokens/{token}/redeem` | Validates and **consumes the token once** at withdrawal (anti double-use). | 9, 20 |

### Receiver

| Method | Endpoint                  | What it's used for                                                           | FR  |
| ------ | ------------------------- | ---------------------------------------------------------------------------- | --- |
| `POST` | `/senders/{id}/receivers` | The Sender registers the Receiver's data (name, destination, payout method). | 2   |
| `GET`  | `/receivers/{id}`         | Fetches an already-registered Receiver.                                      | 2   |

### Quote / Currency

| Method | Endpoint       | What it's used for                                                                            | FR   |
| ------ | -------------- | --------------------------------------------------------------------------------------------- | ---- |
| `GET`  | `/rates`       | Returns the current exchange rate to show before quoting.                                     | 3    |
| `POST` | `/quotes`      | Creates the quote: **locks the exchange rate** and breaks down fees and the total to deposit. | 3, 4 |
| `GET`  | `/quotes/{id}` | Fetches an existing quote (and whether it's still valid).                                     | 3, 4 |

### Transaction / Tracking

| Method | Endpoint                      | What it's used for                                                 | FR        |
| ------ | ----------------------------- | ------------------------------------------------------------------ | --------- |
| `POST` | `/transactions`               | Creates the transaction from a confirmed quote.                    | 6         |
| `POST` | `/transactions/{id}/fund`     | Funds the transaction and **triggers the send saga** (idempotent). | 6, 20, 23 |
| `GET`  | `/transactions/{id}`          | Full transaction detail.                                           | 6         |
| `GET`  | `/transactions/{id}/status`   | Deposit status tracking for Sender and Receiver.                   | 8         |
| `GET`  | `/transactions/{id}/receipts` | Downloads payment receipts (quote, receipt, consent).              | 10, 16    |

### Cancellation & Refund

| Method | Endpoint                            | What it's used for                                                           | FR     |
| ------ | ----------------------------------- | ---------------------------------------------------------------------------- | ------ |
| `GET`  | `/transactions/{id}/cancel-preview` | Shows the operational fee and the **exact** refund amount before cancelling. | 11     |
| `POST` | `/transactions/{id}/cancel`         | Cancels the transaction before the payment completes (with fee charge).      | 11, 21 |
| `POST` | `/transactions/{id}/refund`         | Executes the refund (denied transaction or saga compensation).               | 12, 21 |

### Worker (in-person agency)

| Method | Endpoint                    | What it's used for                                                            | FR  |
| ------ | --------------------------- | ----------------------------------------------------------------------------- | --- |
| `POST` | `/worker/transactions`      | Registers an in-person assisted remittance (with customer consent).           | 13  |
| `GET`  | `/worker/transactions`      | Fetches the agency's transaction history.                                     | 15  |
| `GET`  | `/worker/cash-availability` | Shows the cash available today for in-person payout.                          | 18  |
| `POST` | `/worker/shift/close`       | Closes the shift and **reconciles** physical cash vs. the transaction ledger. | 19  |

### Exceptions & Support

| Method | Endpoint                    | What it's used for                                         | FR  |
| ------ | --------------------------- | ---------------------------------------------------------- | --- |
| `POST` | `/exceptions`               | Logs a provider error or exception detected by the worker. | 24  |
| `POST` | `/exceptions/{id}/escalate` | Escalates the error to a higher level for resolution.      | 24  |
| `POST` | `/support/cases`            | Creates a post-transaction support case.                   | 22  |

## 2. Swagger-style detail (critical endpoints)

### `POST /auth/register`

Registers a new Sender. Public.

- **Body:** `{ "name": str, "email": str, "password": str }`
- **200:** `{ "senderId": uuid, "status": "created" }`
- **409:** email already exists.

### `POST /auth/login`

Authenticates and opens a session.

- **Body:** `{ "email": str, "password": str }`
- **200:** `{ "token": jwt, "expiresIn": 3600 }`
- **401:** invalid credentials.

### `POST /identity/verify`

Identity verification (KYC), mandatory before confirming a remittance.

- **Auth:** Bearer
- **Body:** `{ "documentType": str, "documentId": str, "selfie": base64 }`
- **200:** `{ "verified": true }`
- **422:** identity not verified → blocks confirmation.

### `POST /quotes`

Creates the quote and **locks** the exchange rate.

- **Auth:** Bearer
- **Body:** `{ "senderId": uuid, "receiverId": uuid, "amount": decimal, "sourceCurrency": str, "targetCurrency": str }`
- **200:**
  ```json
  {
    "quoteId": "uuid",
    "exchangeRate": 3.75,
    "commission": 5.0,
    "totalToDeposit": 105.0,
    "receiverGets": 375.0,
    "expiresAt": "2026-08-29T15:00:00Z"
  }
  ```

### `POST /transactions/{id}/fund`

Funds the transaction and triggers the saga (Payment → AML → PayoutAuthorized).

- **Auth:** Bearer · **Header:** `Idempotency-Key`
- **Body:** `{ "channel": "card" | "cash", "paymentToken": str }`
- **202:** `{ "transactionId": uuid, "status": "funding" }` (async processing)
- **409:** already funded (idempotent response, no duplication).
- **402:** payment declined by the card network.

### `POST /identity/tokens/{token}/redeem`

Redeems the temporary token at withdrawal. Single use.

- **Auth:** Bearer (Receiver or Worker) · **Header:** `Idempotency-Key`
- **200:** `{ "authorized": true, "transactionId": uuid }`
- **410:** token expired or already used → prevents double payout.

### `GET /transactions/{id}/cancel-preview`

Previews how much is charged and how much is refunded before cancelling.

- **Auth:** Bearer
- **200:** `{ "operationalFee": 2.00, "refundAmount": 103.00 }`

### `POST /transactions/{id}/refund`

Refund (denial or saga compensation).

- **Auth:** Bearer · **Header:** `Idempotency-Key`
- **200:** `{ "refundId": uuid, "amount": 103.00, "status": "refunded" }`

### `POST /worker/shift/close`

Closes the shift and reconciles cash against the transaction ledger.

- **Auth:** Bearer (Worker)
- **Body:** `{ "countedCash": decimal }`
- **200:** `{ "expectedCash": decimal, "difference": 0.00, "status": "balanced" }`
- **409:** `{ "difference": 12.00, "status": "mismatch" }` → shift doesn't balance, needs review.

# Midterm evaluation — iteration 02

Date: 2026-10-01 (America/Lima). Scope: actor identities and their visible interactions in the updated drawing. This is not a full rubric evaluation.

## Source and verification

- Drawing: `../ep.excalidraw`.
- Read the local evaluator skill, rubric, and bundled professor's theory.
- Fresh evidence: `C:/Users/jeffr/AppData/Local/Temp/excalidraw-evaluation-WySWwV/` (temporary files).
- Source SHA-256: `bb6705b9fb0b8496ea5045043aed3b7cb74e4a51cc6891fae8510c99092c46e8`.
- Read the extracted text and element geometry/bindings: 257 active elements, 84 text elements, and 81 arrows. Inspected the fresh overview and all 18 tiles. No network failures were recorded. The evidence checker passed source identity, element coverage, tile coverage, and pixel-exact crops after inspection.
- The source changed during the first inspection, so evidence was regenerated and all views inspected again before reporting.

## Actor findings

The three actor roles are coherent with a wholesale order-management system:

| Actor | Assessment | Visible evidence | Suggested clarification |
| --- | --- | --- | --- |
| Company Buyer / Buyer | Appropriate role; naming is inconsistent | Company Buyer enters registration/login; Buyer makes the partial-stock decision and receives scheduling, shipping, and payment notifications | Use Company Buyer consistently, or explicitly state that Buyer is the same role. Define it as a representative of the customer company. |
| Driver | Appropriate | Sends Delivery Confirmation to Order Confirmation | No actor correction needed. |
| Finance Worker | Appropriate | Sends Payment Confirmation to Payment Confirmation Service and Bad Payment to After-sales Service | No actor correction needed if payment verification is performed by staff. |

Repeated buyer figures may represent the same actor role in different parts of the drawing. No additional actor is required solely because a warehouse, administrator, or bank might exist in a real system.

An adjacent flow issue is separate from actor identity: Login Service sends Purchase Order PDF to Purchase Service. Clarify that authentication enables the buyer to submit the order; login should not own purchase-order processing.

No numeric score was assigned. The drawing was not changed. Findings concern the artifact and do not establish runtime behavior.

# Excalidraw Connection Validation — Iteration 01

Date: 2026-10-01

## Scope and evidence

Source: `../solucion-simulacro-ep.excalidraw`.

Rendered with Excalidraw 0.18.1 `exportToSvg` and headless Chromium. The skill renderer's remote module failed because an esm.sh dependency returned HTTP 404; a locally bundled copy of Excalidraw completed the export. Evidence: `../solucion-simulacro-ep.png`, `../validacion-compra.png`, and `../validacion-publicacion.png`. Both workflow crops were visually inspected.

This is a visual and JSON connection review, not an evaluator run or runtime validation. The source drawing was not modified.

## Structural results

- 316 elements; 98 arrows.
- 83 arrows have both endpoint bindings; 15 have one free endpoint (9 free starts and 6 free ends).
- No arrow binding references a missing element ID.
- All 15 one-sided arrows have a visually identifiable intended connection. Some endpoints use branch junctions or stop short of a shape, so visual meaning does not imply a complete editable binding.

## One-sided arrows

| Arrow ID | Visually interpreted relationship | Observation |
| --- | --- | --- |
| `RnwIdEwEobq3ved97qbjw` | Game Buyer → Login Service | Actor-side endpoint is free. |
| `nnpI297FeCdPztO0Uwe2q` | Game Buyer → Register Service | Starts at the login path's branch junction. |
| `mxt7SLaGPEmF158uv_EvX` | Payment Method Selection Service → Third Party Payment Service | Branch approaches the selection service but leaves a visible gap. |
| `sjpZSgfCPQy6Dloe_C0Ec` | Payment Validation Service → Payment Success Service | Starts at the validation-to-library branch. |
| `10ztgEahjOF-gmCuCGDpR` | Receipt Service → Game Buyer | Actor-side endpoint is free. |
| `LHLqyVJaT-nHdRj2QDpf5` | Dev → Login Service | Actor-side endpoint is free and separated from the actor. |
| `ocrXvkzJujaC3EDm4Ak5J` | Dev → Register Service | Starts at the login path's branch junction. |
| `IRuKfvFj8V6x-At8k5cCo` | On Demand Service → On Demand Cache (publication) | Cache-side endpoint is free. |
| `6puJTZpu68NyCKaY4hbCW` | On Demand → CDN (download) | CDN-side endpoint is free. |
| `87YxP13rrqyM_XKi9qL8T` | On Demand Service → On Demand (publication) | Service-side endpoint is free. |
| `xLjmgSpzMxfE9icww0565` | On Demand → CDN (publication) | CDN-side endpoint is free. |
| `-dQvLW9XPODw-dlQrN-JL` | On Demand Service → No Demand (publication) | Service-side endpoint is free. |
| `rB-n2ioA4tU47W7FCokiC` | User Download Preferences Service → Download Game | Preferences-side endpoint is free. |
| `aHPEHx32dszn4jNWEN16t` | Game Resume Service <<CRON>> → Missing Chunks Service | Target endpoint is free; label is Local Downloaded Chunks. |
| `GMykR7Z4uNSe1DLzBoeoM` | Chunking Service → Chunk | Chunk-side endpoint is free. |

## Incorrect double bindings

Three arrows bind both ends to the same shape, although their geometry clearly connects different components. These are not visually drawn self-loops.

| Current JSON relationship | Visually intended relationship |
| --- | --- |
| External Currency API → External Currency API | Currency Selection Service → External Currency API (publication) |
| Delete Game Service → Delete Game Service | Game Management Service → Delete Game Service |
| Patch Upload Service → Patch Upload Service | Patch Game Service → Patch Upload Service |

## Conclusion

The workflow relationships are visually recoverable, but a binding-only graph loses 15 relationships and misrepresents three additional arrows. Any future binding repair should preserve the current visual layout and explicitly decide how to represent branch junctions and multipart actor figures. No repair was applied in this review.

# Scoped evaluation: critical path

## Scope and evidence

Evaluated rubric item 5 only, against the project-local evaluator rubric and bundled `SA_theory.md`. This is a structural and visual assessment, without runtime timings or a numeric partial-credit score. The drawing was not modified.

- Source: `Laboratorio8/ep.excalidraw`.
- SHA-256: `0f130fac9c458c2ed023ed652ec8dc38b64020b26ffe75c23710f333b7c2e8d9`.
- Fresh evidence: `C:/Users/jeffr/AppData/Local/Temp/excalidraw-evaluation-s9Bdkc/`.
- Inspected the complete extracted text and element/binding inventory, overview, and all 30 full-scale tiles. The extraction contains 653 active elements, 212 texts, and 199 arrows; no deleted elements or network failures were recorded.
- The evidence checker passed source identity, element counts, tile coverage, and crop-pixel checks. Temporary evidence is host-managed and may later disappear.

## Verdict

**Partially complies.** The separate `CRITICAL PATH` frame highlights a substantial workflow in green, including Purchase, validation, stock evaluation, packaging, truck selection, delivery, completion, and payment recording. However, it does not name the operation's completion condition or provide the required brief justification. Green branches include both partial-stock fulfilment and scheduling/notification, without stating whether they are alternatives or mandatory dependencies.

## Findings and remedies

1. **Define the scenario and endpoint.** Half Stock and New Order are green, while Complete Stock is white. This can be valid for a partial-stock order accepted by the buyer, but acceptance and that scenario must be explicit. Identify whether the result is order acceptance, delivery, or delivery plus registered payment. Login can be included for an unauthenticated starting actor, or stated as a precondition.
2. **Show completion-gating dependencies.** Stock Reservation is white despite the drawing's stock-reservation requirement and fitness function. Stock Evaluation's Product API/DB and New Order's Order API/DB are also white. Mark or enumerate their dependencies when their successful result is required; show reservation as a gate before committing the order. Payment Confirmation's Order API/DB also need inclusion if completion means the order's payment status has been persisted.
3. **Separate alternative and asynchronous branches.** The green Scheduling branch does not continue into delivery. Explain whether it represents a deferred order instead of immediate fulfilment. Scheduling Notification normally need not gate fulfilment unless the chosen completion condition explicitly requires successful notification. Do not present alternative stock cases as a single mandatory sequence.
4. **Clarify logistics prerequisites.** Driver Validation/Schedule, Truck Schedule/Reservation, and Route are white. Include required logistics dependencies or explicitly state that their results are already available. The same reasoning applies to Product Size/Box Selection if Packaging Optimization waits for them.
5. **Map the path to the intended iteration #3.** The upper architecture includes queues and other reliability additions absent from the lower path copy. Label the lower copy as the original unscaled iteration #3, or update its mapping to the corrected architecture. Delivery and later payment may form a business process spanning asynchronous stages; they are not automatically one blocking HTTP request.

The professor's theory supports identifying operations required to complete the selected request and distinguishing synchronous dependencies from asynchronous work. With no service timings, this assessment cannot establish which branch is the longest by duration.

## Suggested annotation for the drawing

Choose a scenario such as: "Partial-stock order accepted by the buyer; finishes when delivery and payment are recorded." Number the required stages and their API/DB dependencies, distinguish deferred-order alternatives, and briefly explain that failure of any mandatory stage prevents that selected outcome. Adapt this annotation to the actual reservation and confirmation dependencies rather than assuming the existing green blocks already form a complete sequence.

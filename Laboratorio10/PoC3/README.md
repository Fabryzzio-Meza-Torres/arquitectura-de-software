# PoC3 — high-priority audit fixes

Standalone copy based on PoC 2. Previous PoCs and diagrams are unchanged.
Only the five high-priority findings are addressed:

1. Backend exceptions are retrieved and treated as failures. A hedge wins only
   with a successful response; pending tasks are cleaned up, including cancellation.
2. Baseline and PoC3 use the same primary samples (attempt 1), seed and warm
   condition. Each pair includes a sample fingerprint for verification.
3. Calibration evaluates three candidate pairs on separate seeds, under load,
   timeout and failure constraints. It selects the lowest measured fresh-success
   CVaR99 among feasible candidates; it does not claim a global optimum or assume
   monotonicity. Every candidate is retained. No feasible clean candidate means
   no selection. This replaces the unproven binary-search optimization claim.
4. Experiments retain every repetition, alternate variant order and mark excessive
   event-loop lag. Only pairs with both measurements valid enter summaries.
   Seed-level mean/range/SD describe variability; they are not confidence intervals.
   Jitter uses request-specific seeded randomness; OS scheduling still varies.
5. p50/p95/p99/CVaR99 and counts are reported separately for fresh successes,
   degraded responses and failures, alongside totals. Empty groups show no percentile.

Alpha/beta remain adaptive per service, using PoC 2's moving median. Cache, retry
budget, simulated capacity and diagram notation are unchanged. Initial values
17/34.1 ms come from PoC 2 and are explicitly marked as not recalibrated for PoC3.

## Run (PowerShell, from this folder)

```powershell
python -B -m unittest discover -s tests -v
python -B run.py experiment --scenario tails
python -B run.py report
# Optional: recalibrate first; evaluation seeds must remain separate.
python -B run.py calibrate --seeds 7 11
```

Python standard library only. Experiments default to 4000 requests at 250 rps,
seeds 42/43/44 and two repetitions per seed. Use `--scenario all` for five scenarios.
Results and the generated report stay in `results/`; a new experiment replaces
that file. The default lag limit is 20 ms: noisy trials remain visible and provide
no clean performance conclusion. Calibration exits with code 2 if no candidate
qualifies, preserves the full trace and blocks experiments until recalibrated.

Validation: 15 tests passed; all five scenarios ran with two seeds and two repeats.
A longer outage verified failed-response reporting after cache expiry. The short
calibration validation rejected noisy candidates; `calibration-validation.json`
is evidence only, not the active calibration. No performance win is claimed from
invalid pairs.

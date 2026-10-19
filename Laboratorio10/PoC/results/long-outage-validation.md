# PoC3 results

All trials retained; noisy pairs excluded from summaries.
Seed means: descriptive spread, not a confidence interval.

## outage_long_svc9

Valid pairs: 0/2

| Seed/repeat | Variant | Valid | Outcome | N | % requests | p50 | p95 | p99 | CVaR99 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 44/0 | baseline | False | all | 1500 | 100.00 | 2008.72 | 2024.23 | 2029.61 | 2042.62 |
| 44/0 | baseline | False | ok | 1500 | 100.00 | 2008.72 | 2024.23 | 2029.61 | 2042.62 |
| 44/0 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 44/0 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 44/0 | poc3 | False | all | 1500 | 100.00 | 28.99 | 55.65 | 79.95 | 93.20 |
| 44/0 | poc3 | False | ok | 368 | 24.53 | 29.69 | 55.02 | 78.55 | 86.12 |
| 44/0 | poc3 | False | degraded | 754 | 50.27 | 28.51 | 54.58 | 66.15 | 70.66 |
| 44/0 | poc3 | False | failed | 378 | 25.20 | 28.51 | 57.97 | 93.66 | 112.94 |
| 45/0 | poc3 | False | all | 1500 | 100.00 | 27.86 | 54.77 | 79.22 | 99.30 |
| 45/0 | poc3 | False | ok | 370 | 24.67 | 26.61 | 43.77 | 54.69 | 60.05 |
| 45/0 | poc3 | False | degraded | 753 | 50.20 | 28.92 | 55.66 | 70.02 | 78.98 |
| 45/0 | poc3 | False | failed | 377 | 25.13 | 27.85 | 64.90 | 104.84 | 118.33 |
| 45/0 | baseline | False | all | 1500 | 100.00 | 2008.45 | 2022.71 | 2026.91 | 2028.64 |
| 45/0 | baseline | False | ok | 1500 | 100.00 | 2008.45 | 2022.71 | 2026.91 | 2028.64 |
| 45/0 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 45/0 | baseline | False | failed | 0 | 0.00 | — | — | — | — |

No clean paired measurement; no performance conclusion.

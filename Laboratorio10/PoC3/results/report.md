# PoC3 results

All trials retained; noisy pairs excluded from summaries.
Seed means: descriptive spread, not a confidence interval.

## tails

Valid pairs: 2/4

| Seed/repeat | Variant | Valid | Outcome | N | % requests | p50 | p95 | p99 | CVaR99 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 42/0 | baseline | False | all | 400 | 100.00 | 33.30 | 1006.57 | 1092.74 | 1107.26 |
| 42/0 | baseline | False | ok | 400 | 100.00 | 33.30 | 1006.57 | 1092.74 | 1107.26 |
| 42/0 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 42/0 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 42/0 | poc3 | True | all | 400 | 100.00 | 32.99 | 56.05 | 64.83 | 83.59 |
| 42/0 | poc3 | True | ok | 398 | 99.50 | 32.89 | 56.06 | 64.95 | 83.66 |
| 42/0 | poc3 | True | degraded | 2 | 0.50 | 45.09 | 46.80 | 46.95 | 47.01 |
| 42/0 | poc3 | True | failed | 0 | 0.00 | — | — | — | — |
| 42/1 | poc3 | True | all | 400 | 100.00 | 31.92 | 55.21 | 61.31 | 65.77 |
| 42/1 | poc3 | True | ok | 399 | 99.75 | 31.91 | 55.22 | 61.31 | 65.78 |
| 42/1 | poc3 | True | degraded | 1 | 0.25 | 54.88 | 54.88 | 54.88 | 54.88 |
| 42/1 | poc3 | True | failed | 0 | 0.00 | — | — | — | — |
| 42/1 | baseline | True | all | 400 | 100.00 | 34.76 | 1011.51 | 1085.82 | 1099.89 |
| 42/1 | baseline | True | ok | 400 | 100.00 | 34.76 | 1011.51 | 1085.82 | 1099.89 |
| 42/1 | baseline | True | degraded | 0 | 0.00 | — | — | — | — |
| 42/1 | baseline | True | failed | 0 | 0.00 | — | — | — | — |
| 43/0 | poc3 | True | all | 400 | 100.00 | 33.29 | 57.02 | 70.41 | 90.95 |
| 43/0 | poc3 | True | ok | 400 | 100.00 | 33.29 | 57.02 | 70.41 | 90.95 |
| 43/0 | poc3 | True | degraded | 0 | 0.00 | — | — | — | — |
| 43/0 | poc3 | True | failed | 0 | 0.00 | — | — | — | — |
| 43/0 | baseline | True | all | 400 | 100.00 | 35.58 | 989.08 | 1099.63 | 1105.06 |
| 43/0 | baseline | True | ok | 400 | 100.00 | 35.58 | 989.08 | 1099.63 | 1105.06 |
| 43/0 | baseline | True | degraded | 0 | 0.00 | — | — | — | — |
| 43/0 | baseline | True | failed | 0 | 0.00 | — | — | — | — |
| 43/1 | baseline | True | all | 400 | 100.00 | 34.92 | 994.22 | 1098.63 | 1109.63 |
| 43/1 | baseline | True | ok | 400 | 100.00 | 34.92 | 994.22 | 1098.63 | 1109.63 |
| 43/1 | baseline | True | degraded | 0 | 0.00 | — | — | — | — |
| 43/1 | baseline | True | failed | 0 | 0.00 | — | — | — | — |
| 43/1 | poc3 | False | all | 400 | 100.00 | 33.49 | 61.22 | 92.95 | 102.29 |
| 43/1 | poc3 | False | ok | 400 | 100.00 | 33.49 | 61.22 | 92.95 | 102.29 |
| 43/1 | poc3 | False | degraded | 0 | 0.00 | — | — | — | — |
| 43/1 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |

Paired p99 delta (PoC3 − baseline), all: mean -1026.86 ms; seed range [-1029.22, -1024.51] ms; 2 seeds.

Paired p99 delta (PoC3 − baseline), ok: mean -1026.86 ms; seed range [-1029.22, -1024.51] ms; 2 seeds.

## tails_heavy

Valid pairs: 0/4

| Seed/repeat | Variant | Valid | Outcome | N | % requests | p50 | p95 | p99 | CVaR99 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 42/0 | baseline | False | all | 400 | 100.00 | 39.38 | 1419.64 | 1492.80 | 1503.45 |
| 42/0 | baseline | False | ok | 400 | 100.00 | 39.38 | 1419.64 | 1492.80 | 1503.45 |
| 42/0 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 42/0 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 42/0 | poc3 | False | all | 400 | 100.00 | 38.17 | 66.37 | 72.29 | 84.53 |
| 42/0 | poc3 | False | ok | 383 | 95.75 | 36.51 | 64.83 | 70.40 | 82.11 |
| 42/0 | poc3 | False | degraded | 17 | 4.25 | 66.36 | 77.02 | 78.77 | 79.21 |
| 42/0 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |
| 42/1 | poc3 | True | all | 400 | 100.00 | 35.63 | 64.71 | 69.38 | 76.12 |
| 42/1 | poc3 | True | ok | 383 | 95.75 | 34.83 | 62.12 | 68.45 | 74.35 |
| 42/1 | poc3 | True | degraded | 17 | 4.25 | 63.71 | 70.13 | 75.85 | 77.28 |
| 42/1 | poc3 | True | failed | 0 | 0.00 | — | — | — | — |
| 42/1 | baseline | False | all | 400 | 100.00 | 33.34 | 1413.17 | 1482.88 | 1502.44 |
| 42/1 | baseline | False | ok | 400 | 100.00 | 33.34 | 1413.17 | 1482.88 | 1502.44 |
| 42/1 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 42/1 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/0 | poc3 | False | all | 400 | 100.00 | 35.89 | 68.08 | 81.77 | 84.97 |
| 43/0 | poc3 | False | ok | 384 | 96.00 | 35.03 | 65.90 | 78.31 | 84.02 |
| 43/0 | poc3 | False | degraded | 16 | 4.00 | 64.64 | 81.90 | 85.13 | 85.94 |
| 43/0 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |
| 43/0 | baseline | False | all | 400 | 100.00 | 32.93 | 1374.74 | 1496.79 | 1503.32 |
| 43/0 | baseline | False | ok | 400 | 100.00 | 32.93 | 1374.74 | 1496.79 | 1503.32 |
| 43/0 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 43/0 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/1 | baseline | False | all | 400 | 100.00 | 35.23 | 1385.34 | 1488.70 | 1499.37 |
| 43/1 | baseline | False | ok | 400 | 100.00 | 35.23 | 1385.34 | 1488.70 | 1499.37 |
| 43/1 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 43/1 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/1 | poc3 | True | all | 400 | 100.00 | 36.07 | 67.25 | 71.97 | 85.55 |
| 43/1 | poc3 | True | ok | 384 | 96.00 | 35.27 | 64.14 | 69.66 | 83.74 |
| 43/1 | poc3 | True | degraded | 16 | 4.00 | 67.43 | 74.67 | 76.67 | 77.18 |
| 43/1 | poc3 | True | failed | 0 | 0.00 | — | — | — | — |

No clean paired measurement; no performance conclusion.

## outage_svc9

Valid pairs: 0/4

| Seed/repeat | Variant | Valid | Outcome | N | % requests | p50 | p95 | p99 | CVaR99 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 42/0 | baseline | False | all | 400 | 100.00 | 38.00 | 2021.23 | 2027.84 | 2032.41 |
| 42/0 | baseline | False | ok | 400 | 100.00 | 38.00 | 2021.23 | 2027.84 | 2032.41 |
| 42/0 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 42/0 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 42/0 | poc3 | False | all | 400 | 100.00 | 30.80 | 64.21 | 75.80 | 97.25 |
| 42/0 | poc3 | False | ok | 171 | 42.75 | 31.15 | 48.90 | 59.96 | 67.48 |
| 42/0 | poc3 | False | degraded | 229 | 57.25 | 30.42 | 69.79 | 90.92 | 105.98 |
| 42/0 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |
| 42/1 | poc3 | False | all | 400 | 100.00 | 28.73 | 66.41 | 87.44 | 101.30 |
| 42/1 | poc3 | False | ok | 173 | 43.25 | 28.63 | 76.04 | 97.68 | 109.56 |
| 42/1 | poc3 | False | degraded | 227 | 56.75 | 29.23 | 65.01 | 68.82 | 84.05 |
| 42/1 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |
| 42/1 | baseline | False | all | 400 | 100.00 | 32.98 | 2016.91 | 2022.18 | 2025.29 |
| 42/1 | baseline | False | ok | 400 | 100.00 | 32.98 | 2016.91 | 2022.18 | 2025.29 |
| 42/1 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 42/1 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/0 | poc3 | False | all | 400 | 100.00 | 29.47 | 57.30 | 81.81 | 89.16 |
| 43/0 | poc3 | False | ok | 177 | 44.25 | 28.66 | 52.37 | 84.06 | 91.27 |
| 43/0 | poc3 | False | degraded | 223 | 55.75 | 30.37 | 61.28 | 78.66 | 86.31 |
| 43/0 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |
| 43/0 | baseline | False | all | 400 | 100.00 | 40.71 | 2025.61 | 2060.14 | 2084.99 |
| 43/0 | baseline | False | ok | 400 | 100.00 | 40.71 | 2025.61 | 2060.14 | 2084.99 |
| 43/0 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 43/0 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/1 | baseline | False | all | 400 | 100.00 | 38.92 | 2023.13 | 2047.01 | 2058.14 |
| 43/1 | baseline | False | ok | 400 | 100.00 | 38.92 | 2023.13 | 2047.01 | 2058.14 |
| 43/1 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 43/1 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/1 | poc3 | False | all | 400 | 100.00 | 30.16 | 63.79 | 80.00 | 82.79 |
| 43/1 | poc3 | False | ok | 172 | 43.00 | 32.77 | 64.08 | 80.46 | 84.97 |
| 43/1 | poc3 | False | degraded | 228 | 57.00 | 29.08 | 63.33 | 78.17 | 80.84 |
| 43/1 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |

No clean paired measurement; no performance conclusion.

## outage_long_svc9

Valid pairs: 1/4

| Seed/repeat | Variant | Valid | Outcome | N | % requests | p50 | p95 | p99 | CVaR99 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 42/0 | baseline | True | all | 400 | 100.00 | 2011.34 | 2023.18 | 2025.27 | 2026.10 |
| 42/0 | baseline | True | ok | 400 | 100.00 | 2011.34 | 2023.18 | 2025.27 | 2026.10 |
| 42/0 | baseline | True | degraded | 0 | 0.00 | — | — | — | — |
| 42/0 | baseline | True | failed | 0 | 0.00 | — | — | — | — |
| 42/0 | poc3 | True | all | 400 | 100.00 | 29.36 | 57.64 | 67.15 | 72.87 |
| 42/0 | poc3 | True | ok | 79 | 19.75 | 27.79 | 44.95 | 50.72 | 55.73 |
| 42/0 | poc3 | True | degraded | 321 | 80.25 | 29.74 | 59.50 | 68.46 | 73.87 |
| 42/0 | poc3 | True | failed | 0 | 0.00 | — | — | — | — |
| 42/1 | poc3 | False | all | 400 | 100.00 | 28.96 | 64.79 | 90.63 | 108.19 |
| 42/1 | poc3 | False | ok | 78 | 19.50 | 29.36 | 90.70 | 113.08 | 121.51 |
| 42/1 | poc3 | False | degraded | 322 | 80.50 | 28.94 | 61.47 | 73.11 | 80.42 |
| 42/1 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |
| 42/1 | baseline | False | all | 400 | 100.00 | 2007.78 | 2022.26 | 2026.95 | 2029.04 |
| 42/1 | baseline | False | ok | 400 | 100.00 | 2007.78 | 2022.26 | 2026.95 | 2029.04 |
| 42/1 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 42/1 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/0 | poc3 | True | all | 400 | 100.00 | 33.03 | 61.49 | 76.88 | 88.44 |
| 43/0 | poc3 | True | ok | 80 | 20.00 | 33.95 | 58.18 | 64.15 | 67.61 |
| 43/0 | poc3 | True | degraded | 320 | 80.00 | 32.95 | 62.03 | 77.97 | 91.00 |
| 43/0 | poc3 | True | failed | 0 | 0.00 | — | — | — | — |
| 43/0 | baseline | False | all | 400 | 100.00 | 2010.08 | 2026.79 | 2043.15 | 2051.32 |
| 43/0 | baseline | False | ok | 400 | 100.00 | 2010.08 | 2026.79 | 2043.15 | 2051.32 |
| 43/0 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 43/0 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/1 | baseline | True | all | 400 | 100.00 | 2006.10 | 2018.60 | 2021.59 | 2022.27 |
| 43/1 | baseline | True | ok | 400 | 100.00 | 2006.10 | 2018.60 | 2021.59 | 2022.27 |
| 43/1 | baseline | True | degraded | 0 | 0.00 | — | — | — | — |
| 43/1 | baseline | True | failed | 0 | 0.00 | — | — | — | — |
| 43/1 | poc3 | False | all | 400 | 100.00 | 31.40 | 61.11 | 74.66 | 86.38 |
| 43/1 | poc3 | False | ok | 80 | 20.00 | 33.96 | 55.95 | 67.03 | 74.64 |
| 43/1 | poc3 | False | degraded | 320 | 80.00 | 31.22 | 62.42 | 75.59 | 88.88 |
| 43/1 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |

Paired p99 delta (PoC3 − baseline), all: mean -1958.12 ms; seed range [-1958.12, -1958.12] ms; 1 seeds.

Paired p99 delta (PoC3 − baseline), ok: mean -1974.55 ms; seed range [-1974.55, -1974.55] ms; 1 seeds.

## drift_svc3

Valid pairs: 0/4

| Seed/repeat | Variant | Valid | Outcome | N | % requests | p50 | p95 | p99 | CVaR99 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 42/0 | baseline | True | all | 400 | 100.00 | 35.13 | 996.65 | 1088.84 | 1102.69 |
| 42/0 | baseline | True | ok | 400 | 100.00 | 35.13 | 996.65 | 1088.84 | 1102.69 |
| 42/0 | baseline | True | degraded | 0 | 0.00 | — | — | — | — |
| 42/0 | baseline | True | failed | 0 | 0.00 | — | — | — | — |
| 42/0 | poc3 | False | all | 400 | 100.00 | 31.06 | 55.08 | 81.02 | 90.44 |
| 42/0 | poc3 | False | ok | 398 | 99.50 | 31.01 | 54.20 | 81.16 | 90.45 |
| 42/0 | poc3 | False | degraded | 2 | 0.50 | 48.52 | 57.28 | 58.06 | 58.27 |
| 42/0 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |
| 42/1 | poc3 | False | all | 400 | 100.00 | 30.91 | 54.69 | 72.78 | 83.29 |
| 42/1 | poc3 | False | ok | 397 | 99.25 | 30.62 | 54.22 | 72.89 | 83.34 |
| 42/1 | poc3 | False | degraded | 3 | 0.75 | 46.54 | 57.48 | 58.46 | 58.71 |
| 42/1 | poc3 | False | failed | 0 | 0.00 | — | — | — | — |
| 42/1 | baseline | False | all | 400 | 100.00 | 33.50 | 1003.53 | 1085.94 | 1096.17 |
| 42/1 | baseline | False | ok | 400 | 100.00 | 33.50 | 1003.53 | 1085.94 | 1096.17 |
| 42/1 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 42/1 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/0 | poc3 | True | all | 400 | 100.00 | 36.13 | 61.80 | 78.93 | 98.01 |
| 43/0 | poc3 | True | ok | 400 | 100.00 | 36.13 | 61.80 | 78.93 | 98.01 |
| 43/0 | poc3 | True | degraded | 0 | 0.00 | — | — | — | — |
| 43/0 | poc3 | True | failed | 0 | 0.00 | — | — | — | — |
| 43/0 | baseline | False | all | 400 | 100.00 | 35.02 | 985.92 | 1101.84 | 1107.17 |
| 43/0 | baseline | False | ok | 400 | 100.00 | 35.02 | 985.92 | 1101.84 | 1107.17 |
| 43/0 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 43/0 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/1 | baseline | False | all | 400 | 100.00 | 35.86 | 990.17 | 1095.42 | 1106.42 |
| 43/1 | baseline | False | ok | 400 | 100.00 | 35.86 | 990.17 | 1095.42 | 1106.42 |
| 43/1 | baseline | False | degraded | 0 | 0.00 | — | — | — | — |
| 43/1 | baseline | False | failed | 0 | 0.00 | — | — | — | — |
| 43/1 | poc3 | True | all | 400 | 100.00 | 35.65 | 61.39 | 78.70 | 103.91 |
| 43/1 | poc3 | True | ok | 399 | 99.75 | 35.63 | 61.03 | 78.82 | 103.94 |
| 43/1 | poc3 | True | degraded | 1 | 0.25 | 66.12 | 66.12 | 66.12 | 66.12 |
| 43/1 | poc3 | True | failed | 0 | 0.00 | — | — | — | — |

No clean paired measurement; no performance conclusion.

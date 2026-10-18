# PoC3 — tail-latency benchmark

## Run

```powershell
python -B -m unittest discover -s tests -v
python -B run.py benchmark
python -B run.py plot
# Separate two-request teaching capture (JSON and editable Mermaid):
python -B run.py sequence
```

Simulation/tests use Python's standard library; plots additionally use matplotlib.

## Exactly two slow services

Each request randomly selects **two of the ten primary services**. These take
1000–1500 ms; the other eight typically take 10 ms, capped at 50 ms. Selection is
reproducible by seed and request. All ten services can be selected.

A replica is another instance of the same service. Replicas have independent
latencies and retain a 1% slow-call probability, as an explicit hedging assumption.
Shared failures affecting every replica are a different scenario.

## Random cache preload (warm-up)

At the start of each repetition, PoC3 preloads simulated cached data for **three
random distinct services out of ten**. A separate seeded random stream makes this
selection reproducible and independent of the two slow services per request;
overlap is allowed but never forced. Baseline has no cache.

All ten services can update cached data after success. Cache is used as fallback
after an unsuccessful attempt, with the existing 1 s fresh/5 s maximum TTLs;
expired data cannot prevent failure. Preload does not force response latency to
zero, train alpha/beta, or generate extra requests. Backend cold-start penalties
remain excluded; cache preload is a separate simulated state.

## Request counts

Totals include baseline, PoC3 and all five independent repetitions:

| Total API requests | Baseline | PoC3 | Per variant per repetition |
|---:|---:|---:|---:|
| 1000 | 500 | 500 | 100 |
| 10000 | 5000 | 5000 | 1000 |
| 50000 | 25000 | 25000 | 5000 |

The complete command executes **61000 API requests**, at a fixed 250 requests/s.
Calls to the ten services, replicas and retries are counted separately. Increasing
request count tests longer observation, not increased arrival-rate capacity.

Alpha/beta start at 17/34.1 ms and retain PoC2's moving-median adaptation. They are
not claimed optimal for this new workload. Each repetition starts a new controller,
so different durations also expose its learning phase.

## Results

Timestamped runs are preserved under `results/volumes/`; `latest.json` selects the
last completed run. Three simple PNG/SVG charts show p50/p95/p99, one per total,
with request counts and response quality. The short `presentation/summary.md`
explains them. Original PoC1/2 and older experiment results remain unchanged.

All repetitions and raw outcomes are retained. The 20 ms event-loop lag limit is
unchanged; only complete clean comparisons enter clean latency estimates. Noisy
observations are explicitly identified. Failure rates include all executed calls.
A larger request count alone does not prove statistical significance.

The five high-priority fixes remain: correct exception/cancellation handling,
shared primary samples, explicit calibration selection, transparent repeated
measurements and separate success/degraded/failure metrics. The previous
occasional-tail scenarios remain available via `experiment` and `plot --legacy`;
`plot --advanced` preserves the historical diagnostics.

`results/sequence/` contains measured baseline/PoC3 sequence diagrams and their
trace. The two demonstration calls are separate from the 61000-request benchmark.
PNG/SVG files correspond to the supplied capture; re-render the Mermaid files
after recording a new trace. Validation: 33 automated tests passed.

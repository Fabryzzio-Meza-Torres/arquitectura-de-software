import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from plot_results import accepted_records, historical_points, outcome_rows, read_sources


class PlotDataTests(unittest.TestCase):
    def test_historical_pair_requires_clean_baseline_too(self):
        metrics = {"p50_ms": 10, "p95_ms": 20, "p99_ms": 30, "loop_lag_max_ms": 10}
        source = {"params": {"seed": 42}, "scenarios": {"tails": {
            "baseline": {**metrics, "loop_lag_max_ms": 30}, "poc2": metrics}}}
        data = {"PoC2": source, "PoC3": {"scenarios": {}}}
        points = historical_points(data, "tails")
        self.assertFalse(points[0]["valid_pair"])
        self.assertEqual(points[0]["metrics"]["p99_ms"], 30)

    def test_cdf_excludes_entire_invalid_pairs(self):
        source = {"scenarios": {"tails": {"pairs": [
            {"paired_valid": False, "trials": {"poc3": {"records": ["noisy"]}}},
            {"paired_valid": True, "trials": {"poc3": {"records": ["clean"]}}}]}}}
        self.assertEqual(accepted_records(source, "tails", "poc3"), ["clean"])

    def test_outcome_counts_are_weighted_by_requests_not_by_trial(self):
        def trial(n, failed, age):
            return {"n": n, "metrics": {"ok": {"count": n - failed},
                    "failed": {"count": failed}, "degraded": {"count": 0}},
                    "cache_age_max_s": age}
        data = {"PoC3": {"n": 100, "rps": 10, "scenarios": {"outage_long_svc9": {
            "pairs": [{"trials": {"poc3": trial(100, 50, 3)}},
                      {"trials": {"poc3": trial(300, 0, 4)}}]}}}}
        row = outcome_rows(data)[0]
        self.assertEqual(row["failed"], 12.5)
        self.assertEqual(row["ok"] + row["degraded"] + row["failed"], 100)
        self.assertEqual(row["age"], 4)

    def test_standalone_poc3_does_not_require_legacy_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "PoC3"
            (root / "results").mkdir(parents=True)
            (root / "results/results.json").write_text(json.dumps({"scenarios": {}}), encoding="utf-8")
            data, provenance = read_sources(root)
            self.assertEqual(list(data), ["PoC3"])
            self.assertEqual(len(provenance["PoC3"]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()

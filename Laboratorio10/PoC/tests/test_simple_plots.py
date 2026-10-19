import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from simple_plots import lab_summary


class SimplePlotTests(unittest.TestCase):
    def test_counts_include_all_runs_but_latencies_exclude_noisy_runs(self):
        def pair(valid, value):
            trial = {"n": 2, "records": [
                {"latency_ms": value, "outcome": "ok"},
                {"latency_ms": value, "outcome": "failed"}]}
            return {"paired_valid": valid, "trials": {"baseline": trial, "poc3": trial}}
        result = {"n": 2, "rps": 100, "scenarios": {"tails": {
            "pairs": [pair(True, 10), pair(False, 1000)]}}}
        group = lab_summary(result)["variants"]["poc3"]
        self.assertEqual(group["requests_executed"], 4)
        self.assertEqual(group["latency_samples_used"], 2)
        self.assertEqual(group["p99_ms"], 10)
        self.assertEqual(group["failed_in_used_samples"], 1)

    def test_missing_clean_measurements_does_not_create_misleading_chart(self):
        with self.assertRaises(ValueError):
            lab_summary({"n": 10, "rps": 100, "scenarios": {}})


if __name__ == "__main__":
    unittest.main()

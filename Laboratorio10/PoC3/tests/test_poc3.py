import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import simcore as sc
import experiment as ex
from improved_api import ImprovedAPI
from run import report


class ErrorBackend(sc.Backend):
    async def call(self, *args):
        self.calls += 1
        raise ConnectionError("injected backend failure")


class APIErrors(unittest.IsolatedAsyncioTestCase):
    async def test_exception_never_returns_ok_and_reaches_breaker(self):
        backend = ErrorBackend(sc.SimConfig())
        api = ImprovedAPI(backend, 10, 50, max_attempts=3)
        self.assertEqual(await api.call_service(1, 1), "failed")
        self.assertEqual(api.backend_errors, 3)
        self.assertEqual(api.timeouts, 0)
        self.assertEqual(api.breakers[1].fail, 3)
        self.assertEqual(api.retries, 2)

    async def test_baseline_exception_is_failed(self):
        self.assertEqual(await sc.BaselineAPI(ErrorBackend(sc.SimConfig())).handle(1), "failed")

    async def test_hedge_error_does_not_hide_pending_primary_success(self):
        class Backend(sc.Backend):
            async def call(self, req, svc, replica, attempt):
                if replica == 1:
                    raise ConnectionError("hedge fails first")
                await asyncio.sleep(0.04)
        api = ImprovedAPI(Backend(sc.SimConfig()), 10, 150)
        self.assertEqual(await api._attempt(1, 1, 1), "ok")
        self.assertEqual(api.backend_errors, 1)

    async def test_primary_error_does_not_hide_pending_hedge_success(self):
        class Backend(sc.Backend):
            async def call(self, req, svc, replica, attempt):
                await asyncio.sleep(0.025 if replica == 0 else 0.04)
                if replica == 0:
                    raise ConnectionError("primary fails after hedge starts")
        api = ImprovedAPI(Backend(sc.SimConfig()), 10, 150)
        self.assertEqual(await api._attempt(1, 1, 1), "ok")

    async def test_timeout_cleans_up_both_calls(self):
        finished = []
        class Backend(sc.Backend):
            async def call(self, req, svc, replica, attempt):
                try:
                    await asyncio.sleep(5)
                finally:
                    finished.append(replica)
        api = ImprovedAPI(Backend(sc.SimConfig()), 10, 50)
        self.assertEqual(await api._attempt(1, 1, 1), "timeout")
        self.assertEqual(sorted(finished), [0, 1])

    async def test_parent_cancellation_cleans_up_calls(self):
        finished = []
        class Backend(sc.Backend):
            async def call(self, *args):
                try:
                    await asyncio.sleep(5)
                finally:
                    finished.append(True)
        api = ImprovedAPI(Backend(sc.SimConfig()), 100, 200)
        task = asyncio.create_task(api._attempt(1, 1, 1))
        await asyncio.sleep(0.02)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(finished, [True])

    async def test_baseline_and_poc_use_identical_first_primary_samples(self):
        class Backend(sc.Backend):
            def __init__(self, cfg):
                super().__init__(cfg)
                self.observed = []
            async def call(self, req, svc, replica, attempt):
                self.observed.append((req, svc, replica, attempt, self.latency_ms(req, svc, replica, attempt)))
        a, b = Backend(sc.SimConfig()), Backend(sc.SimConfig())
        a.warm_up()
        poc = ImprovedAPI(b, 10, 50)
        await sc.BaselineAPI(a).handle(123)
        await poc.handle(123)
        self.assertEqual(sorted(a.observed), sorted(b.observed))


class Measurements(unittest.TestCase):
    def test_outcome_metrics_preserve_latency_label_alignment(self):
        groups = ex.summarize([{"outcome": "failed", "latency_ms": 1},
                               {"outcome": "ok", "latency_ms": 100},
                               {"outcome": "degraded", "latency_ms": 20}])
        self.assertEqual(groups["failed"]["p99_ms"], 1)
        self.assertEqual(groups["ok"]["p99_ms"], 100)
        self.assertEqual(groups["degraded"]["p99_ms"], 20)
        self.assertEqual(groups["all"]["count"], 3)

    def test_empty_outcome_has_no_invented_percentile(self):
        self.assertIsNone(ex.metric([])["p99_ms"])

    def test_noisy_measurements_are_kept_and_marked_invalid(self):
        records = [{"request": 0, "outcome": "ok", "latency_ms": 10}]
        with patch.object(ex, "load", return_value=(records, [50], 1)):
            trial = ex.run_trial("baseline", sc.SimConfig(), 1, 1, 17, 34, 20)
        self.assertFalse(trial["measurement_valid"])
        self.assertEqual(trial["records"], records)
        pair = {"paired_valid": False, "seed": 42, "trials": {"baseline": trial, "poc3": trial}}
        summary = ex.aggregate([pair])
        self.assertEqual(summary["pairs_total"], 1)
        self.assertEqual(summary["pairs_valid"], 0)
        self.assertIsNone(summary["outcomes"]["poc3"]["ok"]["p99_ms"])

    def test_repeats_aggregate_per_seed_not_as_independent_seeds(self):
        pairs = []
        for seed, delta in ((42, 2), (43, 4)):
            for repeat in (0, 1):
                base = {"metrics": ex.summarize([{"outcome": "ok", "latency_ms": 10}])}
                poc = {"metrics": ex.summarize([{"outcome": "ok", "latency_ms": 10 + delta}])}
                pairs.append({"paired_valid": True, "seed": seed,
                              "trials": {"baseline": base, "poc3": poc}})
        summary = ex.aggregate(pairs)
        self.assertEqual(summary["paired_p99_delta_ms"]["ok"]["count"], 2)
        self.assertEqual(summary["paired_p99_delta_ms"]["ok"]["mean"], 3)

    def test_candidate_selection_uses_objective_and_constraints(self):
        def trial(kind, cfg, n, rps, alpha, beta, limit):
            # Lowest CVaR candidate violates load budget; only feasible ones compete.
            return {"measurement_valid": True, "extra_load_pct": 10 if alpha == 10 else 2,
                    "timeouts": 0, "metrics": {"failed": {"count": 0},
                    "ok": {"count": n, "cvar99_ms": alpha}}}
        with patch.object(ex, "run_trial", side_effect=trial):
            result = ex.calibrate(100, 100, [7, 11], 20, [(10, 30), (30, 60), (20, 50)])
        self.assertEqual(result["alpha_ms"], 20)
        self.assertEqual(len(result["trace"]), 3)

    def test_no_candidate_is_selected_when_measurement_is_noisy(self):
        trial = {"measurement_valid": False}
        with patch.object(ex, "run_trial", return_value=trial):
            result = ex.calibrate(100, 100, [7, 11], 20, [(20, 50)])
        self.assertEqual(result["status"], "no_valid_feasible_candidate")
        self.assertIsNone(result["alpha_ms"])

    def test_experiment_keeps_all_repeats_and_alternates_order(self):
        calls = []
        def trial(kind, cfg, *args):
            calls.append(kind)
            return {"measurement_valid": len(calls) != 1,
                    "primary_samples_sha256": "same", "metrics": ex.summarize([
                        {"outcome": "ok", "latency_ms": 10}])}
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(ex, "run_trial", side_effect=trial), patch("builtins.print"):
                result = ex.experiment("tails", 1, 1, [42, 43], 2, 17, 34, 20,
                                       Path(directory) / "results.json")
        pairs = result["scenarios"]["tails"]["pairs"]
        self.assertEqual(len(pairs), 4)
        self.assertEqual(result["scenarios"]["tails"]["summary"]["pairs_valid"], 3)
        self.assertEqual(calls, ["baseline", "poc3", "poc3", "baseline",
                                "poc3", "baseline", "baseline", "poc3"])

    def test_report_does_not_claim_success_from_fast_failures(self):
        trial = {"measurement_valid": False, "n": 2, "metrics": ex.summarize([
            {"outcome": "failed", "latency_ms": 1},
            {"outcome": "ok", "latency_ms": 100}])}
        pair = {"paired_valid": False, "seed": 42, "repeat": 0,
                "trials": {"baseline": trial, "poc3": trial}}
        text = report({"scenarios": {"tails": {"pairs": [pair], "summary": ex.aggregate([pair])}}})
        self.assertIn("no performance conclusion", text)
        self.assertIn("| failed | 1 | 50.00 | 1.00", text)
        self.assertIn("| ok | 1 | 50.00 | 100.00", text)


if __name__ == "__main__":
    unittest.main()

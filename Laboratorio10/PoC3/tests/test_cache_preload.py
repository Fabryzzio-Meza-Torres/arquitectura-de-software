import asyncio
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from improved_api import ImprovedAPI
from volume_benchmark import TwoSlowBackend, TwoSlowConfig
import experiment


class CachePreloadTests(unittest.TestCase):
    def api(self, seed=101):
        return ImprovedAPI(TwoSlowBackend(TwoSlowConfig(seed=seed)), 17, 34.1)

    def test_exactly_three_random_distinct_services_and_no_backend_calls(self):
        selections = set()
        eligible = set()
        for seed in range(30):
            api = self.api(seed)
            ids = api.initial_cache_services
            self.assertEqual(len(ids), 3)
            self.assertEqual(len(set(ids)), 3)
            self.assertEqual(set(api.cache), set(ids))
            self.assertTrue(all(1 <= s <= 10 for s in ids))
            self.assertEqual(api.backend.calls, 0)
            self.assertTrue(all(not w for w in api.window.values()))
            selections.add(ids)
            eligible.update(ids)
        self.assertGreater(len(selections), 1)
        self.assertEqual(eligible, set(range(1, 11)))
        self.assertEqual(self.api().initial_cache_services, self.api().initial_cache_services)

    def test_preload_does_not_follow_slow_service_selection(self):
        api = self.api()
        expected = tuple(sorted(random.Random('101|cache-preload').sample(range(1, 11), 3)))
        self.assertEqual(api.initial_cache_services, expected)
        overlaps = {len(set(api.initial_cache_services) & set(api.backend.slow_services(req)))
                    for req in range(200)}
        self.assertEqual(overlaps, {0, 1, 2})
        self.assertEqual(api.initial_cache_services, expected)

    def test_preload_is_usable_but_expired_data_is_rejected(self):
        api = self.api()
        svc = api.initial_cache_services[0]
        with patch('improved_api.time.monotonic', return_value=api.cache[svc] + 0.5):
            self.assertEqual(api._stale_fallback(0, svc), 'cache')
        with patch('improved_api.time.monotonic', return_value=api.cache[svc] + 6):
            self.assertEqual(api._stale_fallback(0, svc), 'failed')
        missing = next(s for s in range(1, 11) if s not in api.cache)
        self.assertEqual(api._stale_fallback(0, missing), 'failed')

    def test_success_populates_cache_for_previously_unloaded_service(self):
        api = self.api()
        svc = next(s for s in range(1, 11) if s not in api.cache)
        async def success(*args):
            return 'ok'
        with patch.object(api, '_attempt', side_effect=success):
            self.assertEqual(asyncio.run(api.call_service(0, svc)), 'ok')
        self.assertIn(svc, api.cache)
        self.assertEqual(api._stale_fallback(1, svc), 'cache')

    def test_cache_is_fallback_after_failed_attempt_not_a_cache_first_shortcut(self):
        api = self.api()
        svc = api.initial_cache_services[0]
        async def timeout(*args):
            return 'timeout'
        with patch.object(api, '_attempt', side_effect=timeout) as attempt:
            self.assertEqual(asyncio.run(api.call_service(0, svc)), 'cache')
            self.assertEqual(attempt.call_count, 1)
        self.assertEqual(api.timeouts, 1)
        self.assertEqual(api.degraded_fresh, 1)

    def test_trial_records_initial_state_and_baseline_has_no_cache(self):
        records = [{'request': 0, 'outcome': 'ok', 'latency_ms': 10}]
        with patch.object(experiment, 'load', return_value=(records, [0], 1)):
            for kind in ('baseline', 'poc3'):
                trial = experiment.run_trial(kind, TwoSlowConfig(seed=101), 1, 250,
                                             17, 34.1, 20, TwoSlowBackend)
                self.assertEqual(len(trial['initial_cache_services']), 0 if kind == 'baseline' else 3)


if __name__ == '__main__':
    unittest.main()

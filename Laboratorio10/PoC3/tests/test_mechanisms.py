import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from improved_api import HalfOpenBreaker
from mechanism_study import InstrumentedAPI, ObservedBreaker, StudyBackend, compare
from volume_benchmark import TwoSlowConfig
from mechanism_plots import paired_trials


class MechanismTests(unittest.TestCase):
    def test_observed_breaker_preserves_closed_open_probe_and_recovery(self):
        backend = StudyBackend(TwoSlowConfig())
        br = ObservedBreaker(HalfOpenBreaker(threshold=2, cooldown=1), backend, 1)
        self.assertTrue(br.allow(10))
        br.on_failure(10)
        br.on_failure(10)
        self.assertFalse(br.allow(10.5))
        self.assertTrue(br.allow(11.1))
        self.assertFalse(br.allow(11.1))
        with patch('mechanism_study.time.monotonic', return_value=11.1):
            br.on_success()
        self.assertEqual(br.state(11.1), 'closed')
        self.assertTrue(br.allow(11.1))

    def test_disabled_breaker_does_not_suppress_calls(self):
        backend = StudyBackend(TwoSlowConfig())
        br = ObservedBreaker(HalfOpenBreaker(threshold=1), backend, 1, True)
        br.on_failure(10)
        self.assertTrue(br.allow(10))
        self.assertFalse(br.is_open(10))

    def test_persistent_scenario_is_explicit_and_recovers(self):
        backend = StudyBackend(TwoSlowConfig(seed=101), 'persistent_two')
        self.assertEqual(len(backend.fault_services), 2)
        for req in (0, 10, 129, 130):
            for replica in (0, 1):
                slow = {s for s in range(1, 11) if backend.latency_ms(req, s, replica, 1) >= 1000}
                self.assertEqual(slow, set(backend.fault_services) if 10 <= req < 130 else set())

    def test_ablation_removes_only_the_intended_policy(self):
        def api(variant):
            return InstrumentedAPI(StudyBackend(TwoSlowConfig()), variant=variant)
        self.assertEqual(len(api('full').cache), 3)
        self.assertEqual(len(api('no_preload').cache), 0)
        self.assertTrue(api('no_preload')._cacheable(1))
        self.assertFalse(api('no_cache')._cacheable(1))
        self.assertEqual(api('no_retries').max_attempts, 1)
        fixed = api('fixed_thresholds')
        fixed.median[1] = 1
        self.assertEqual(fixed.thresholds(1), (0.017, 0.0341))

    def test_no_hedging_never_sends_to_a_replica(self):
        backend = StudyBackend(TwoSlowConfig(seed=101))
        api = InstrumentedAPI(backend, variant='no_hedging')
        svc = backend.slow_services(0)[0]
        self.assertEqual(asyncio.run(api._attempt(0, svc, 1)), 'timeout')
        sends = [e for e in backend.events if e['event'] == 'send']
        self.assertEqual(len(sends), 1)
        self.assertEqual(sends[0]['replica'], 0)

    def test_service_context_labels_breaker_and_cache_events(self):
        backend = StudyBackend(TwoSlowConfig())
        api = InstrumentedAPI(backend)
        asyncio.run(api.handle(99))
        self.assertTrue(all(e['req'] == 99 for e in backend.events))
        self.assertEqual(len(api.service_records), 10)

    def test_noisy_trial_cannot_enter_a_clean_component_comparison(self):
        def trial(variant, clean, latency):
            return {'variant': variant, 'seed': 1, 'scenario': 'random_two',
                    'measurement_valid': clean, 'records': [{'outcome': 'ok', 'latency_ms': latency}],
                    'backend_calls': 10, 'counters': {'hedges': 0}}
        result = compare([trial('full', False, 10), trial('no_breaker', True, 20)],
                         'no_breaker', 'random_two')
        self.assertEqual(result['clean_pairs'], 0)
        self.assertEqual(result['latency_source'], 'noisy_observations')

    def test_plots_use_the_same_eligible_seeds_in_both_bars(self):
        trials = [{'variant': variant, 'seed': seed, 'scenario': 'random_two',
                   'measurement_valid': not (variant == 'no_cache' and seed == 2)}
                  for seed in (1, 2) for variant in ('full', 'no_cache')]
        pairs, clean, total = paired_trials({'trials': trials}, 'random_two', 'no_cache')
        self.assertEqual((clean, total), (1, 2))
        self.assertEqual([(a['seed'], b['seed']) for a, b in pairs], [(1, 1)])

    def test_forced_capture_opens_both_circuits_and_avoids_backend_calls(self):
        from sequence_trace import capture_open_breaker, mermaid
        case = asyncio.run(capture_open_breaker())
        slow = set(case['slow_services'])
        self.assertEqual(len(slow), 2)
        self.assertEqual(case['outcome'], 'degraded')
        self.assertFalse(any(e['event'] == 'send' and e['svc'] in slow for e in case['events']))
        denied = [e for e in case['events'] if e['event'] == 'breaker_decision' and not e['allowed']]
        self.assertEqual({e['svc'] for e in denied}, slow)
        diagram = mermaid(case)
        self.assertIn('Abierto: evita 2 consultas', diagram)
        self.assertIn('2 respuestas con cache vigente', diagram)


if __name__ == '__main__':
    unittest.main()

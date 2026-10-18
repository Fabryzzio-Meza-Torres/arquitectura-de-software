import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import volume_benchmark as volume
from experiment import fingerprint


class VolumeBenchmarkTests(unittest.TestCase):
    def test_every_primary_request_has_exactly_two_slow_services(self):
        backend = volume.TwoSlowBackend(volume.TwoSlowConfig(seed=101))
        selected = set()
        for req in range(200):
            values = {svc: backend.latency_ms(req, svc, 0, 1) for svc in range(1, 11)}
            slow = {svc for svc, latency in values.items() if latency >= 1000}
            self.assertEqual(len(slow), 2)
            self.assertEqual(slow, set(backend.slow_services(req)))
            self.assertTrue(all(v <= 50 or 1000 <= v <= 1500 for v in values.values()))
            selected.update(slow)
        self.assertEqual(selected, set(range(1, 11)))

    def test_selection_is_reproducible_and_varies_with_seed(self):
        a = volume.TwoSlowBackend(volume.TwoSlowConfig(seed=101))
        b = volume.TwoSlowBackend(volume.TwoSlowConfig(seed=101))
        c = volume.TwoSlowBackend(volume.TwoSlowConfig(seed=202))
        self.assertEqual([a.slow_services(i) for i in range(20)], [b.slow_services(i) for i in range(20)])
        self.assertNotEqual([a.slow_services(i) for i in range(20)], [c.slow_services(i) for i in range(20)])
        self.assertEqual(fingerprint(a.cfg, 20, volume.TwoSlowBackend),
                         fingerprint(b.cfg, 20, volume.TwoSlowBackend))

    def test_totals_include_both_variants_and_all_repetitions(self):
        seeds = [101, 202, 303, 404, 505]
        for total, expected in ((1000, 100), (10000, 1000), (50000, 5000)):
            n = volume.allocation(total, seeds)
            self.assertEqual(n, expected)
            self.assertEqual(n * 2 * len(seeds), total)
        with self.assertRaises(ValueError):
            volume.allocation(1001, seeds)
        with self.assertRaises(ValueError):
            volume.TwoSlowConfig(primary_slow_count=3)

    def test_windows_timer_is_released_on_failure(self):
        with patch.object(volume.sys, "platform", "win32"), patch.object(volume.ctypes, "WinDLL", create=True) as library:
            library.return_value.timeBeginPeriod.return_value = 0
            library.return_value.timeEndPeriod.return_value = 0
            with self.assertRaises(RuntimeError):
                with volume.timer_resolution() as metadata:
                    self.assertTrue(metadata["active"])
                    raise RuntimeError("stop")
            library.return_value.timeEndPeriod.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()

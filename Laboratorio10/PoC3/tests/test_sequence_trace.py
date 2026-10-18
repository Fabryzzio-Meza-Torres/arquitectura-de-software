import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sequence_trace import mermaid


class SequenceTraceTests(unittest.TestCase):
    def test_diagram_preserves_measured_services_times_and_outcome(self):
        case = {"variant": "poc3", "slow_services": [4, 7], "total_ms": 32.5,
                "events": [
                    {"event": "send", "svc": 4, "replica": 0, "attempt": 1, "ms": 0.2},
                    {"event": "send", "svc": 4, "replica": 1, "attempt": 1, "ms": 17.4},
                    {"event": "return", "svc": 4, "replica": 1, "attempt": 1, "ms": 32.2},
                    {"event": "service_outcome", "svc": 4, "outcome": "ok", "ms": 32.3}],
                "outcome": "ok"}
        text = mermaid(case)
        self.assertIn("participant Problema as Servicio problematico", text)
        self.assertNotIn("participant Servicio4", text)
        self.assertNotIn("participant Servicio7", text)
        self.assertIn("t=17.4 ms - Superado alpha", text)
        self.assertIn("t=32.5 ms - Respuesta final: ok", text)

    def test_failed_outcome_is_not_drawn_as_success(self):
        case = {"variant": "poc3", "slow_services": [1, 2], "total_ms": 100,
                "events": [{"event": "service_outcome", "svc": 1, "outcome": "failed", "ms": 99}],
                "outcome": "failed"}
        text = mermaid(case)
        self.assertIn("Sin dato", text)
        self.assertIn("Respuesta final: failed", text)


if __name__ == "__main__":
    unittest.main()

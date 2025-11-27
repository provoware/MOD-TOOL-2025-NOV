import time
import unittest

from mod_tool.monitor import HealthMonitor


class DummyCheck:
    def __init__(self) -> None:
        self.calls = 0

    def quick_health_report(self) -> str:
        self.calls += 1
        return f"ok-{self.calls}"


class HealthMonitorTests(unittest.TestCase):
    def test_start_and_stop_monitor(self):
        logs: list[str] = []
        monitor = HealthMonitor(DummyCheck(), logs.append, interval_seconds=0.05)

        first_start = monitor.start()
        second_start = monitor.start()
        time.sleep(0.12)
        stopped = monitor.stop(timeout=1)

        self.assertTrue(first_start)
        self.assertFalse(second_start)
        self.assertTrue(stopped)
        self.assertGreaterEqual(len(logs), 1)
        self.assertTrue(any(msg.startswith("Hintergrund-Monitor") for msg in logs))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

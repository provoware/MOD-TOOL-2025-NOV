import logging
import unittest

from mod_tool.diagnostics import guarded_action


class GuardedActionTests(unittest.TestCase):
    def test_guarded_action_logs_duration(self):
        logger = logging.getLogger("test_guard")
        handler = logging.StreamHandler()
        log_output = []

        def capture(message):
            log_output.append(message)

        handler.emit = lambda record: capture(handler.format(record))  # type: ignore
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        @guarded_action("Probe", logger)
        def _fake_task():
            return "ok"

        result = _fake_task()
        logger.removeHandler(handler)

        self.assertEqual(result, "ok")
        self.assertTrue(any("Probe – erfolgreich" in line for line in log_output))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

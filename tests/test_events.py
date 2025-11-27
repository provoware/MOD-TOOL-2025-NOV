import unittest

from mod_tool.events import EventTrace, render_event_digest


class EventTraceTests(unittest.TestCase):
    def test_records_and_renders_events(self):
        trace = EventTrace(max_events=3)
        first = trace.record("Start", "Bootstrap läuft", severity="info")
        self.assertEqual(first.name, "Start")
        trace.record("Warnung", "Kontrast prüfen", severity="warn")
        lines = trace.as_lines()
        self.assertEqual(len(lines), 2)
        self.assertIn("[WARN] Warnung", lines[-1])
        digest = render_event_digest(trace.snapshot())
        self.assertIn("Start (info)", digest)
        self.assertIn("Warnung (warn)", digest)

    def test_rejects_invalid_data(self):
        trace = EventTrace()
        with self.assertRaises(ValueError):
            trace.record("", "ohne Namen")
        with self.assertRaises(ValueError):
            trace.record("Fehler", "", severity="info")
        with self.assertRaises(ValueError):
            trace.record("Fehler", "ungültig", severity="fatal")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

import logging
import tkinter as tk
import unittest

from mod_tool.logging_dashboard import LoggingManager


class LoggingManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("Tk nicht verfügbar")

    def tearDown(self) -> None:
        if hasattr(self, "root"):
            self.root.destroy()

    def test_level_threshold_filters_records(self) -> None:
        manager = LoggingManager(self.root)
        manager.set_level_threshold("WARNING")

        info_record = logging.LogRecord("test", logging.INFO, __file__, 1, "info", args=(), exc_info=None)
        warn_record = logging.LogRecord("test", logging.WARNING, __file__, 2, "warn", args=(), exc_info=None)

        self.assertFalse(manager.should_display_record(info_record))
        self.assertTrue(manager.should_display_record(warn_record))

    def test_level_threshold_validation(self) -> None:
        manager = LoggingManager(self.root)
        with self.assertRaises(ValueError):
            manager.set_level_threshold("")
        label = manager.set_level_threshold("ERROR")
        self.assertEqual(label, "ERROR")


if __name__ == "__main__":
    unittest.main()

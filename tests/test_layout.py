import tkinter as tk
import tkinter as tk
import unittest

from mod_tool.layout import DashboardLayout
from mod_tool.logging_dashboard import LoggingManager
from mod_tool.themes import ThemeManager


class LayoutTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("Tk nicht verfügbar")

    def tearDown(self):  # pragma: no cover - cleanup
        if hasattr(self, "root"):
            self.root.destroy()

    def test_layout_builds_grid(self):
        themes = ThemeManager(self.root)
        logging_manager = LoggingManager(self.root)
        layout = DashboardLayout(self.root, themes, logging_manager)
        layout.build(on_start=lambda: None, on_health_check=lambda: None, on_toggle_debug=lambda _=False: None, on_show_index=lambda: None)
        self.assertEqual(self.root.grid_size(), (1, 3))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

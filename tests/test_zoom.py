import tkinter as tk
import unittest

from mod_tool.themes import ThemeManager
from mod_tool.zoom import ZoomManager


class ZoomManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("Tk nicht verfügbar")

    def tearDown(self) -> None:  # pragma: no cover - cleanup
        if hasattr(self, "root"):
            self.root.destroy()

    def test_zoom_scales_fonts_and_clamps(self) -> None:
        theme_manager = ThemeManager(self.root)
        zoom = ZoomManager(self.root, theme_manager.fonts, min_scale=0.9, max_scale=1.2)
        base_size = theme_manager.fonts["default"].cget("size")

        zoom.set_scale(1.1)
        increased_size = theme_manager.fonts["default"].cget("size")
        self.assertGreaterEqual(increased_size, round(base_size * 1.1))

        zoom.set_scale(2.5)
        clamped_size = theme_manager.fonts["default"].cget("size")
        self.assertEqual(zoom.scale, 1.2)
        self.assertEqual(clamped_size, max(6, round(base_size * 1.2)))

        zoom.reset()
        self.assertEqual(theme_manager.fonts["default"].cget("size"), base_size)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

import tkinter as tk
import unittest

from mod_tool.themes import ThemeManager


class ThemeAccessibilityTests(unittest.TestCase):
    def test_accessibility_report_ok(self):
        report = ThemeManager.accessibility_report()
        self.assertEqual(report["status"], "ok", msg=report["details"])
        self.assertIn("details", report)

    def test_theme_palettes_are_unique_and_readable(self):
        names = list(ThemeManager.THEMES.keys())
        self.assertEqual(len(names), len(set(names)))

        for theme, palette in ThemeManager.THEMES.items():
            fg_ratio = ThemeManager._contrast_ratio(palette["background"], palette["foreground"])
            accent_ratio = ThemeManager._contrast_ratio(palette["background"], palette["accent"])
            self.assertGreaterEqual(
                fg_ratio, 4.5, msg=f"Lesekontrast zu niedrig für {theme} ({fg_ratio:.2f})"
            )
            self.assertGreaterEqual(
                accent_ratio, 4.5,
                msg=f"Akzentkontrast zu niedrig für {theme} ({accent_ratio:.2f})",
            )

    def test_accessibility_report_rejects_invalid_ratio(self):
        with self.assertRaises(ValueError):
            ThemeManager.accessibility_report(0)

    def test_invert_theme_switches_text_colors(self):
        try:
            root = tk.Tk()
            root.withdraw()
        except tk.TclError:
            self.skipTest("Tk nicht verfügbar")
        manager = ThemeManager(root)
        manager.apply_theme("Invertiert")
        text_widget = tk.Text(root)
        manager.apply_text_theme(text_widget)
        palette = manager.palette
        self.assertEqual(text_widget.cget("foreground"), palette["background"])
        self.assertEqual(text_widget.cget("background"), palette["foreground"])
        root.destroy()

    def test_invert_only_active_field(self):
        try:
            root = tk.Tk()
            root.withdraw()
        except tk.TclError:
            self.skipTest("Tk nicht verfügbar")
        manager = ThemeManager(root)
        manager.apply_theme("Hell")
        text_widget = tk.Text(root)
        manager.apply_text_theme(text_widget, invert=True)
        self.assertEqual(text_widget.cget("foreground"), manager.palette["background"])
        manager.apply_text_theme(text_widget, invert=False)
        self.assertEqual(text_widget.cget("foreground"), manager.palette["foreground"])
        root.destroy()

    def test_aurora_theme_exposes_card_palette(self):
        try:
            root = tk.Tk()
            root.withdraw()
        except tk.TclError:
            self.skipTest("Tk nicht verfügbar")
        manager = ThemeManager(root)
        manager.apply_theme("Aurora")
        palette = manager.module_palette
        self.assertGreaterEqual(len(palette), 4)
        for primary, secondary in palette:
            self.assertTrue(primary.startswith("#"))
            self.assertTrue(secondary.startswith("#"))
            self.assertGreater(
                ThemeManager._contrast_ratio(primary, secondary),
                1.1,
                msg="Palettenfarben sollen sich voneinander abheben",
            )
        root.destroy()

    def test_theme_guard_falls_back_on_low_contrast(self):
        try:
            root = tk.Tk()
            root.withdraw()
        except tk.TclError:
            self.skipTest("Tk nicht verfügbar")
        manager = ThemeManager(root)
        manager.THEMES["Low"] = {"background": "#ffffff", "foreground": "#ffffff", "accent": "#ffffff"}
        try:
            report = manager.apply_theme("Low")
            self.assertEqual(report["status"], "warnung")
            self.assertEqual(manager.current_theme, "Kontrast")
        finally:
            manager.THEMES.pop("Low", None)
            root.destroy()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

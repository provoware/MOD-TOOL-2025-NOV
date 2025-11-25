import unittest

from mod_tool.themes import ThemeManager


class ThemeAccessibilityTests(unittest.TestCase):
    def test_accessibility_report_ok(self):
        report = ThemeManager.accessibility_report()
        self.assertIn(report["status"], {"ok", "warnung"})
        self.assertIn("details", report)
        # Ensure contrast calculation returns numeric values
        for theme, palette in ThemeManager.THEMES.items():
            ratio = ThemeManager._contrast_ratio(palette["background"], palette["foreground"])
            self.assertGreater(ratio, 0.0, msg=f"Kontrast für {theme} sollte > 0 sein")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

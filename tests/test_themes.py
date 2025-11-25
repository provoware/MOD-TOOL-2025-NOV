import unittest

from mod_tool.themes import ThemeManager


class ThemeAccessibilityTests(unittest.TestCase):
    def test_accessibility_report_ok(self):
        report = ThemeManager.accessibility_report()
        self.assertEqual(report["status"], "ok", msg=report["details"])
        self.assertIn("details", report)
        # Ensure contrast calculation stays above WCAG AA guidance
        for theme, palette in ThemeManager.THEMES.items():
            fg_ratio = ThemeManager._contrast_ratio(palette["background"], palette["foreground"])
            accent_ratio = ThemeManager._contrast_ratio(
                palette["background"], palette["accent"]
            )
            self.assertGreaterEqual(
                fg_ratio, 4.5, msg=f"Text-Kontrast für {theme} zu gering"
            )
            self.assertGreaterEqual(
                accent_ratio, 4.5, msg=f"Akzent-Kontrast für {theme} zu gering"
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

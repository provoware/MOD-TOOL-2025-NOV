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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

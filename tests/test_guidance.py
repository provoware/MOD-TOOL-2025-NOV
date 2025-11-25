import os
import unittest

from mod_tool.guidance import GuidanceItem, StartupGuide


class GuidanceItemTests(unittest.TestCase):
    def test_render_contains_command_and_title(self):
        item = GuidanceItem(
            title="Testtitel",
            description="Einfache Beschreibung",
            command="python -m unittest",
        )
        rendered = item.render()
        self.assertIn("Testtitel", rendered)
        self.assertIn("python -m unittest", rendered)

    def test_validate_blocks_empty_values(self):
        with self.assertRaises(ValueError):
            GuidanceItem(title="", description="ok", command="cmd").validate()
        with self.assertRaises(ValueError):
            GuidanceItem(title="t", description="", command="cmd").validate()
        with self.assertRaises(ValueError):
            GuidanceItem(title="t", description="d", command=" ").validate()


class StartupGuideTests(unittest.TestCase):
    def test_activation_command_matches_platform(self):
        guide = StartupGuide(".venv")
        command = guide._activation_command()
        if os.name == "nt":
            self.assertIn("\\Scripts\\", command)
            self.assertTrue(command.endswith("activate.bat"))
        else:
            self.assertIn("/bin/", command)
            self.assertTrue(command.endswith("activate"))

    def test_render_for_logging_produces_hints(self):
        guide = StartupGuide(".venv")
        messages = guide.render_for_logging()
        self.assertGreaterEqual(len(messages), 3)
        self.assertTrue(any("Tests" in msg for msg in messages))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

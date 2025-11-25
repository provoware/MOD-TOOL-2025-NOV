import json
import tempfile
from pathlib import Path
import unittest

from mod_tool.dashboard_state import DashboardState


class DashboardStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.state = DashboardState(self.base)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ensure_project_structure_creates_paths(self):
        report = self.state.ensure_project_structure()
        self.assertIn(str(self.base / "logs"), report)
        self.assertEqual(report[str(self.base / "plugins")], "automatisch erstellt")

    def test_save_and_autosave_snapshot(self):
        target = self.state.save_notes("Hallo Welt")
        self.assertTrue(target.exists())
        autosave_path = self.state.autosave_snapshot("Hallo Welt", status={"ok": "ja"})
        data = json.loads(autosave_path.read_text(encoding="utf-8"))
        self.assertEqual(data["notes"], "Hallo Welt")
        self.assertEqual(data["status"].get("ok"), "ja")

    def test_import_export_roundtrip(self):
        sample_text = "Einfacher Export"
        export_target = self.base / "export.json"
        self.state.export_notes(export_target, sample_text)
        imported = self.state.import_notes(export_target)
        self.assertIn(sample_text, imported)

    def test_random_hint_creates_default_list(self):
        hints = self.state.load_hints()
        self.assertGreaterEqual(len(hints), 1)
        hint = self.state.random_hint()
        self.assertIsInstance(hint, str)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

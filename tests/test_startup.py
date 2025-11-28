import pathlib
import tempfile
import unittest

from mod_tool.bootstrap import Bootstrapper
from mod_tool.startup import AutonomousStarter, StartupStatusBoard, StartupStep


class StartupBoardTests(unittest.TestCase):
    def test_progress_and_lines(self):
        board = StartupStatusBoard()
        board.record(StartupStep(key="a", title="Schritt A", status="ok", detail="fertig"))
        board.record(StartupStep(key="b", title="Schritt B", status="warnung", detail="Info"))

        percent, label = board.progress()

        self.assertEqual(percent, 50)
        self.assertIn("Fortschritt", label)
        lines = board.status_lines()
        self.assertEqual(len(lines), 2)
        self.assertIn("Schritt A", lines[0])


class AutonomousStarterTests(unittest.TestCase):
    def test_run_returns_status_payload(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            module_dir = root / "mod_tool"
            module_dir.mkdir()
            (module_dir / "__init__.py").write_text("# dummy module\n", encoding="utf-8")

            starter = AutonomousStarter(
                bootstrapper=Bootstrapper(project_root=root, auto_relaunch=False, feedback=lambda _: None),
                feedback=lambda _: None,
            )
            status = starter.run()

            self.assertIn("virtualenv", status)
            self.assertIn("dependencies", status)
            self.assertIn("self_check", status)
            self.assertIn("progress", status)
            self.assertIn("progress_info", status)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

import pathlib
import tempfile
import unittest

from mod_tool.bootstrap import Bootstrapper


class BootstrapperTests(unittest.TestCase):
    def test_creates_env_and_runs_self_check(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = pathlib.Path(tmp_dir)
            module_dir = root / "mod_tool"
            module_dir.mkdir()
            (module_dir / "__init__.py").write_text("# dummy module for compile check\n")

            bootstrapper = Bootstrapper(
                project_root=root, auto_relaunch=False, feedback=lambda _: None
            )
            status = bootstrapper.run()

            self.assertTrue((root / ".venv").exists())
            self.assertIn(status["virtualenv"], {"vorhanden", "erstellt"})
            self.assertIn(status["dependencies"], {"übersprungen", "ok", "fehlend", "warnung"})
            self.assertIn(status["self_check"], {"ok", "warnung"})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

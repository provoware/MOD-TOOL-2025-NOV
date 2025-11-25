import os
import pathlib
import tempfile
import unittest

from mod_tool.self_check import SelfCheck


class SelfCheckTests(unittest.TestCase):
    def test_self_check_creates_missing_paths(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing = pathlib.Path(tmp_dir) / "plugins"
            check = SelfCheck([missing])
            result = check.ensure_required_paths()
            self.assertEqual(result[str(missing)], "automatisch erstellt")
            self.assertTrue(missing.exists())

    def test_full_check_runs_compile(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dummy_root = pathlib.Path(tmp_dir)
            module_dir = dummy_root / "mod_tool"
            module_dir.mkdir()
            (module_dir / "__init__.py").write_text("# dummy")
            old_cwd = os.getcwd()
            try:
                os.chdir(dummy_root)
                check = SelfCheck([dummy_root / "logs"])
                result = check.full_check()
            finally:
                os.chdir(old_cwd)
            self.assertIn(result["code_format"], {"ok", "kompilierungswarnung"})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

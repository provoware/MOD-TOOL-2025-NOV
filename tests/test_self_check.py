import os
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from mod_tool.self_check import SelfCheck


class SelfCheckTests(unittest.TestCase):
    def test_self_check_creates_missing_paths(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing = pathlib.Path(tmp_dir) / "plugins"
            check = SelfCheck([missing], base_path=pathlib.Path(tmp_dir))
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
                check = SelfCheck([dummy_root / "logs"], base_path=dummy_root)
                with mock.patch.object(
                    SelfCheck, "run_dependency_probe", return_value=("ok", "pip check stub")
                ):
                    result = check.full_check()
            finally:
                os.chdir(old_cwd)
            self.assertIn(result["code_format"], {"ok", "kompilierungswarnung"})
            self.assertIn(result["tests"], {"ok", "fehlgeschlagen", "übersprungen"})
            self.assertIn(result["manifest"], {"vorhanden", "erstellt"})
            self.assertIn(result["accessibility"], {"ok", "warnung"})
            self.assertIn("accessibility_notes", result)
            self.assertIn("tests_info", result)
            self.assertIn(result["abhängigkeiten"], {"ok", "warnung", "übersprungen"})
            manifest_file = dummy_root / "manifest.json"
            self.assertTrue(manifest_file.exists())

    def test_quick_tests_timeout_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = pathlib.Path(tmp_dir)
            tests_dir = base / "tests"
            tests_dir.mkdir()
            (tests_dir / "test_sleep.py").write_text(
                (
                    "import time\nimport unittest\n"
                    "class Slow(unittest.TestCase):\n"
                    "    def test_wait(self):\n        time.sleep(5)\n"
                )
            )

            check = SelfCheck([base / "logs"], base_path=base, test_timeout_seconds=1)
            status, info = check.run_quick_tests()

            self.assertEqual(status, "abgebrochen")
            self.assertIn("Timeout", info)

    def test_classify_overall_warn_and_error(self):
        check = SelfCheck([pathlib.Path("logs")])
        warning_status = check.classify_overall({"tests": "warnung", "linting": "ok"})
        error_status = check.classify_overall({"tests": "fehlgeschlagen", "linting": "ok"})

        self.assertEqual(warning_status, "warnung")
        self.assertEqual(error_status, "fehler")

    def test_dependency_probe_reports_status(self):
        check = SelfCheck([pathlib.Path("logs")])
        ok_result = subprocess.CompletedProcess(args=["pip"], returncode=0, stdout="", stderr="")
        warn_result = subprocess.CompletedProcess(args=["pip"], returncode=1, stdout="", stderr="Konflikt")

        with mock.patch("mod_tool.self_check.subprocess.run", return_value=ok_result):
            status, info = check.run_dependency_probe()
            self.assertEqual(status, "ok")
            self.assertIn("konsistent", info)

        with mock.patch("mod_tool.self_check.subprocess.run", return_value=warn_result):
            status, info = check.run_dependency_probe()
            self.assertEqual(status, "warnung")
            self.assertIn("Konflikt", info)

    def test_manifest_versions_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = pathlib.Path(tmp_dir)
            manifest_path = base / "manifest.json"
            manifest_path.write_text(
                '{"structure_manifest": {"version": "2.0"}, "layout_manifest": {"version": "2.1"}}',
                encoding="utf-8",
            )
            check = SelfCheck([base / "logs"], base_path=base, manifest_path=manifest_path)
            status, info = check.ensure_manifest_file()
            self.assertEqual(status, "vorhanden")
            self.assertIn("Struktur v2.0", info)
            human = check.read_manifest_versions()
            self.assertIn("Layout v2.1", human)

    def test_manifest_repair_rewrites_invalid_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = pathlib.Path(tmp_dir)
            manifest_path = base / "manifest.json"
            manifest_path.write_text("{defekt}", encoding="utf-8")
            check = SelfCheck([base / "logs"], base_path=base, manifest_path=manifest_path)
            status, info = check.ensure_manifest_file()
            self.assertEqual(status, "erstellt")
            self.assertIn("Version", info)
            self.assertIn("Struktur v", check.read_manifest_versions())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

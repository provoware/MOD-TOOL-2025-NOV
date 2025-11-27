import pathlib
import tempfile
import unittest

from mod_tool.plugins import PluginManager


class PluginManagerTests(unittest.TestCase):
    def test_load_plugins_returns_names(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            plugin_dir = pathlib.Path(tmp_dir)
            plugin_file = plugin_dir / "demo.py"
            plugin_file.write_text("""\
loaded = True
""")
            manager = PluginManager(str(plugin_dir))
            loaded = manager.load_plugins()
            self.assertIn("demo", loaded)

    def test_load_report_records_outcome(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            plugin_dir = pathlib.Path(tmp_dir)
            bad_plugin = plugin_dir / "broken.py"
            bad_plugin.write_text("raise RuntimeError('kaputt')\n")

            manager = PluginManager(str(plugin_dir))
            loaded = manager.load_plugins()

            self.assertEqual([], loaded)
            self.assertTrue(any("broken.py" in entry for entry in manager.load_report))

    def test_load_plugins_handles_errors(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            plugin_dir = pathlib.Path(tmp_dir)
            bad_plugin = plugin_dir / "broken.py"
            bad_plugin.write_text("raise RuntimeError('kaputt')\n")
            manager = PluginManager(str(plugin_dir))
            loaded = manager.load_plugins()
            self.assertNotIn("broken", loaded)
            self.assertEqual(loaded, manager.loaded_plugins)

    def test_invalid_schema_blocks_plugin(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            plugin_dir = pathlib.Path(tmp_dir)
            bad_plugin = plugin_dir / "invalid.py"
            bad_plugin.write_text(
                """
def on_load(required):
    return required
PLUGIN_META = {"name": "Bad", "version": 1}
                """
            )
            manager = PluginManager(str(plugin_dir))
            loaded = manager.load_plugins()

            self.assertEqual([], loaded)
            report = " | ".join(manager.load_report)
            self.assertIn("invalid.py", report)
            self.assertIn("blockiert", report)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

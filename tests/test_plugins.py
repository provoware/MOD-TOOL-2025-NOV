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

    def test_load_plugins_handles_errors(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            plugin_dir = pathlib.Path(tmp_dir)
            bad_plugin = plugin_dir / "broken.py"
            bad_plugin.write_text("raise RuntimeError('kaputt')\n")
            manager = PluginManager(str(plugin_dir))
            loaded = manager.load_plugins()
            self.assertNotIn("broken", loaded)
            self.assertEqual(loaded, manager.loaded_plugins)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

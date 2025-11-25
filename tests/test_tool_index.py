import pathlib
import unittest

from mod_tool.tool_index import ToolIndex


class ToolIndexTests(unittest.TestCase):
    def test_collects_core_modules(self):
        index = ToolIndex(base_path=pathlib.Path(__file__).resolve().parent.parent / "mod_tool")
        entries = index.collect_index()
        modules = {entry.module for entry in entries}
        self.assertIn("mod_tool.app", modules)
        self.assertTrue(all(entry.functions is not None for entry in entries))

    def test_invalid_base_path_raises(self):
        with self.assertRaises(ValueError):
            ToolIndex(base_path=pathlib.Path("/pfad/gibt/es/nicht"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

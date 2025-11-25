import tempfile
from pathlib import Path
import unittest

from mod_tool.snippet_library import SnippetStore


class SnippetStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tempdir.name)
        self.store = SnippetStore(self.base_path)

    def tearDown(self):  # pragma: no cover - cleanup
        self.tempdir.cleanup()

    def test_add_update_delete_snippet(self):
        created = self.store.add_snippet("Test", "Inhalt")
        self.assertEqual(len(self.store.list_snippets()), 1)
        updated = self.store.update_snippet(created.id, "Neu", "Mehr Inhalt")
        self.assertEqual(updated.name, "Neu")
        self.store.delete_snippet(updated.id)
        self.assertEqual(len(self.store.list_snippets()), 0)

    def test_import_export_roundtrip(self):
        self.store.add_snippet("Alpha", "Beta")
        export_path = self.store.export_archive(self.base_path / "export.json")
        self.assertTrue(export_path.exists())
        self.store.delete_snippet(self.store.list_snippets()[0].id)
        self.assertEqual(len(self.store.list_snippets()), 0)
        imported_count = self.store.import_archive(export_path)
        self.assertEqual(imported_count, 1)
        self.assertEqual(len(self.store.list_snippets()), 1)

    def test_validation_rejects_empty(self):
        with self.assertRaises(ValueError):
            self.store.add_snippet(" ", "")
        with self.assertRaises(ValueError):
            self.store.update_snippet("missing", "", "content")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from mod_tool.todo import TodoManager


class TodoManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.manager = TodoManager(Path(self.tmp.name))

    def tearDown(self) -> None:  # pragma: no cover - cleanup helper
        self.tmp.cleanup()

    def test_add_and_list_upcoming(self):
        item = self.manager.add_item("Test", "2025-01-01", "Info", False)
        todos = self.manager.list_upcoming(limit=5)
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0].title, item.title)
        self.assertEqual(todos[0].due_date, "2025-01-01")

    def test_toggle_done_updates_state(self):
        item = self.manager.add_item("Check", None, "", False)
        updated = self.manager.set_done(item.id, True)
        self.assertTrue(updated.done)
        todos = self.manager.list_upcoming()
        self.assertTrue(any(t.done for t in todos))

    def test_invalid_date_raises(self):
        with self.assertRaises(ValueError):
            self.manager.add_item("Fehler", "2025-13-01", "", False)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

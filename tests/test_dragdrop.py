import tkinter as tk
import unittest

from mod_tool.dragdrop import DragDropManager


class DummyEvent:
    def __init__(self, widget: tk.Text):
        self.widget = widget


class DragDropTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("Tk nicht verfügbar")

    def tearDown(self):  # pragma: no cover - cleanup
        if hasattr(self, "root"):
            self.root.destroy()

    def test_bindings_are_registered(self):
        widget = tk.Text(self.root)
        manager = DragDropManager()
        manager.enable_for_text(widget, "Test")
        self.assertIsNotNone(widget.bind("<ButtonPress-1>"))
        self.assertIsNotNone(widget.bind("<ButtonRelease-1>"))

    def test_drag_and_drop_transfers_text(self):
        messages: list[str] = []
        manager = DragDropManager(messages.append)
        source = tk.Text(self.root)
        target = tk.Text(self.root)
        source.insert("1.0", "Hallo Welt")
        source.tag_add("sel", "1.0", "1.5")

        manager._start_drag(DummyEvent(source), "Quelle")
        manager._maybe_activate_drag(DummyEvent(source))
        manager._drop(DummyEvent(target), "Ziel")

        self.assertIn("Hallo", target.get("1.0", tk.END))
        self.assertEqual((), source.tag_ranges("sel"))
        self.assertTrue(any("Drop abgeschlossen" in msg for msg in messages))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

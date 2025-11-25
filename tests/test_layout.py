import tkinter as tk
import unittest

from mod_tool.layout import DashboardLayout, WorkspacePane
from mod_tool.logging_dashboard import LoggingManager
from mod_tool.themes import ThemeManager


class LayoutTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("Tk nicht verfügbar")

    def tearDown(self):  # pragma: no cover - cleanup
        if hasattr(self, "root"):
            self.root.destroy()

    def test_layout_builds_grid(self):
        themes = ThemeManager(self.root)
        logging_manager = LoggingManager(self.root)
        layout = DashboardLayout(self.root, themes, logging_manager)
        layout.build(
            on_start=lambda: None,
            on_health_check=lambda: None,
            on_toggle_debug=lambda _=False: None,
            on_show_index=lambda: None,
        )
        self.assertEqual(self.root.grid_size(), (1, 3))
        self.assertGreaterEqual(len(layout.tile_cards), 9)
        self.assertFalse(layout._details_visible.get())

    def test_core_widgets_have_scrollbars(self):
        themes = ThemeManager(self.root)
        logging_manager = LoggingManager(self.root)
        layout = DashboardLayout(self.root, themes, logging_manager)
        layout.build(
            on_start=lambda: None,
            on_health_check=lambda: None,
            on_toggle_debug=lambda _=False: None,
            on_show_index=lambda: None,
        )
        self.assertNotEqual(layout.note_panel.text.cget("yscrollcommand"), "")
        self.assertNotEqual(layout.todo_panel.tree.cget("yscrollcommand"), "")

        pane = WorkspacePane(
            self.root,
            title="Test",
            description="Scroll-Test",
            logging_manager=logging_manager,
            status_color_provider=layout.state.rotate_status_colors,
            theme_manager=themes,
        )
        self.assertNotEqual(pane.text.cget("yscrollcommand"), "")

    def test_workspace_panes_start_collapsed_and_can_expand(self):
        themes = ThemeManager(self.root)
        logging_manager = LoggingManager(self.root)
        layout = DashboardLayout(self.root, themes, logging_manager)
        layout.build(
            on_start=lambda: None,
            on_health_check=lambda: None,
            on_toggle_debug=lambda _=False: None,
            on_show_index=lambda: None,
        )
        pane = layout._workspace_panes[0]
        self.assertTrue(pane._collapsed.get())
        pane.toggle_body()
        self.assertFalse(pane._collapsed.get())

    def test_workspace_rows_rotate(self):
        themes = ThemeManager(self.root)
        logging_manager = LoggingManager(self.root)
        layout = DashboardLayout(self.root, themes, logging_manager)
        layout.build(
            on_start=lambda: None,
            on_health_check=lambda: None,
            on_toggle_debug=lambda _=False: None,
            on_show_index=lambda: None,
        )
        before = list(layout.pane_grid.panes())
        layout.rotate_workspace_rows()
        after = list(layout.pane_grid.panes())
        self.assertNotEqual(before, after)

    def test_details_toggle_brings_helpers_back(self):
        themes = ThemeManager(self.root)
        logging_manager = LoggingManager(self.root)
        layout = DashboardLayout(self.root, themes, logging_manager)
        layout.build(
            on_start=lambda: None,
            on_health_check=lambda: None,
            on_toggle_debug=lambda _=False: None,
            on_show_index=lambda: None,
        )
        layout._toggle_details(True, focus="notes")
        self.assertTrue(layout._details_visible.get())
        self.assertTrue(layout.detail_frame.winfo_ismapped())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

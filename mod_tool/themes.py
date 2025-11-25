"""Theme definitions and utilities."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ThemeManager:
    """Handles five accessible themes and style registration."""

    THEMES = {
        "Hell": {
            "background": "#f7f7f7",
            "foreground": "#1f2933",
            "accent": "#2b6cb0",
        },
        "Dunkel": {"background": "#1f2933", "foreground": "#f7f7f7", "accent": "#63b3ed"},
        "Kontrast": {"background": "#000000", "foreground": "#ffffff", "accent": "#ffd166"},
        "Blau": {"background": "#e6f0ff", "foreground": "#102a43", "accent": "#2c5282"},
        "Wald": {"background": "#0b3d2e", "foreground": "#e5f4ec", "accent": "#28a745"},
    }

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.style = ttk.Style(root)
        self.current_theme = "Hell"

    @property
    def theme_names(self) -> list[str]:
        return list(self.THEMES.keys())

    def configure_styles(self) -> None:
        self.style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        self.style.configure("TLabel", wraplength=400)

    def apply_theme(self, name: str) -> None:
        theme = self.THEMES.get(name, self.THEMES["Hell"])
        self.current_theme = name if name in self.THEMES else "Hell"
        bg = theme["background"]
        fg = theme["foreground"]
        accent = theme["accent"]

        self.root.configure(bg=bg)
        for element in ["TFrame", "TLabel", "TLabelFrame", "TButton", "TCombobox", "Treeview"]:
            self.style.configure(element, background=bg, foreground=fg)
        self.style.configure("TButton", padding=6, relief="raised")
        self.style.configure("TCombobox", fieldbackground="white")
        self.style.configure("Treeview", fieldbackground=bg, bordercolor=accent)
        self.style.map("TButton", background=[("active", accent)])

        for child in self.root.winfo_children():
            self._propagate_bg(child, bg)

    def _propagate_bg(self, widget: tk.Widget, bg: str) -> None:
        try:
            widget.configure(background=bg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._propagate_bg(child, bg)

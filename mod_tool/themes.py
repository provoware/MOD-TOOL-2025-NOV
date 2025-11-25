"""Theme definitions and utilities with contrast validation."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, Tuple


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
        "Wald": {"background": "#0b3d2e", "foreground": "#e5f4ec", "accent": "#40e0d0"},
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
        self.style.configure("Helper.TLabel", foreground="#1f2933", wraplength=520)
        self.style.configure("Status.TLabel", font=("Arial", 11, "bold"))

    def apply_theme(self, name: str) -> None:
        theme = self.THEMES.get(name, self.THEMES["Hell"])
        self.current_theme = name if name in self.THEMES else "Hell"
        bg = theme["background"]
        fg = theme["foreground"]
        accent = theme["accent"]

        self.root.configure(bg=bg)
        for element in ["TFrame", "TLabel", "TLabelFrame", "TButton", "TCombobox", "Treeview"]:
            self.style.configure(element, background=bg, foreground=fg)
        self.style.configure("TButton", padding=8, relief="raised")
        self.style.configure("TCombobox", fieldbackground="white")
        self.style.configure("Treeview", fieldbackground=bg, bordercolor=accent)
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.map("TButton", background=[("active", accent)], foreground=[("active", fg)])
        self.style.map("TCheckbutton", focuscolor=[("active", accent)])

        for child in self.root.winfo_children():
            self._propagate_bg(child, bg)

    def _propagate_bg(self, widget: tk.Widget, bg: str) -> None:
        try:
            widget.configure(background=bg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._propagate_bg(child, bg)

    @staticmethod
    def _hex_to_rgb(color: str) -> Tuple[int, int, int]:
        color = color.lstrip("#")
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))

    @classmethod
    def _relative_luminance(cls, color: str) -> float:
        r, g, b = [channel / 255 for channel in cls._hex_to_rgb(color)]
        channels = []
        for c in (r, g, b):
            channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    @classmethod
    def _contrast_ratio(cls, color_a: str, color_b: str) -> float:
        lum_a = cls._relative_luminance(color_a)
        lum_b = cls._relative_luminance(color_b)
        lighter, darker = (lum_a, lum_b) if lum_a > lum_b else (lum_b, lum_a)
        return (lighter + 0.05) / (darker + 0.05)

    @classmethod
    def accessibility_report(cls, minimum_ratio: float = 4.5) -> Dict[str, str]:
        """Validate all palettes against WCAG contrast guidance."""

        warnings: list[str] = []
        for name, palette in cls.THEMES.items():
            fg_ratio = cls._contrast_ratio(palette["background"], palette["foreground"])
            accent_ratio = cls._contrast_ratio(palette["background"], palette["accent"])
            if fg_ratio < minimum_ratio:
                warnings.append(f"{name}: Text-Kontrast {fg_ratio:.2f} unter {minimum_ratio}")
            if accent_ratio < minimum_ratio:
                warnings.append(f"{name}: Akzent-Kontrast {accent_ratio:.2f} unter {minimum_ratio}")

        status = "ok" if not warnings else "warnung"
        detail = "Alle Themes kontraststark" if not warnings else "; ".join(warnings)
        return {"status": status, "details": detail}

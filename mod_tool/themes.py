"""Theme definitions and utilities with contrast validation."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from typing import Dict, Tuple


class ThemeManager:
    """Handles accessible themes, font scaling, and style registration."""

    THEMES = {
        "Aurora": {
            "background": "#0b1f2f",
            "foreground": "#eaf1ff",
            "accent": "#ff9f0c",
            "nav_bg": "#d4550f",
            "nav_fg": "#fffaf2",
            "nav_accent": "#ffb347",
            "settings_bg": "#102840",
            "settings_fg": "#eaf1ff",
            "card_base": "#0f2c44",
            "card_title": "#fef08a",
            "card_palette": [
                ("#168cf5", "#0c273d"),
                ("#d97706", "#2f1a06"),
                ("#16a34a", "#0f3022"),
                ("#ef4444", "#301014"),
                ("#8b5cf6", "#25183a"),
                ("#0ea5e9", "#0a2435"),
            ],
        },
        "Hell": {
            "background": "#f7f9fb",
            "foreground": "#0f172a",
            "accent": "#1d4ed8",
        },
        "Dunkel": {
            "background": "#0f172a",
            "foreground": "#e5e7eb",
            "accent": "#22d3ee",
        },
        "Kontrast": {
            "background": "#000000",
            "foreground": "#ffffff",
            "accent": "#fbbf24",
        },
        "Marine": {
            "background": "#0b1b2b",
            "foreground": "#e0f2fe",
            "accent": "#38bdf8",
        },
        "Wald": {
            "background": "#0b3d2e",
            "foreground": "#e8fff5",
            "accent": "#34d399",
        },
        "Pastell": {
            "background": "#eef2ff",
            "foreground": "#1f2937",
            "accent": "#7c3aed",
        },
        "Neon": {
            "background": "#0a0f1f",
            "foreground": "#e5e7ff",
            "accent": "#16f2b8",
        },
        "Invertiert": {
            "background": "#0b0f16",
            "foreground": "#f8fafc",
            "accent": "#fb923c",
            "invert_text": True,
        },
        "Sand": {
            "background": "#f5f0e8",
            "foreground": "#1f2937",
            "accent": "#7c2d12",
        },
        "Graphit": {
            "background": "#1c1c1e",
            "foreground": "#f5f5f7",
            "accent": "#64d2ff",
        },
        "Solar": {
            "background": "#112b3c",
            "foreground": "#f1f5f9",
            "accent": "#f59e0b",
        },
    }

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.style = ttk.Style(root)
        self.current_theme = "Aurora"
        self.invert_text = False
        self.current_surfaces: dict[str, object] = {}
        default_font = tkfont.nametofont("TkDefaultFont")
        text_font = tkfont.nametofont("TkTextFont")
        fixed_font = tkfont.nametofont("TkFixedFont")
        for named_font in (default_font, text_font, fixed_font):
            named_font.configure(size=max(12, int(named_font.cget("size"))))
        self.fonts = {
            "default": default_font,
            "text": text_font,
            "fixed": fixed_font,
            "header": tkfont.Font(root=root, family="Arial", size=18, weight="bold"),
            "status": tkfont.Font(root=root, family="Arial", size=12, weight="bold"),
            "helper": tkfont.Font(
                root=root,
                family=default_font.cget("family"),
                size=max(12, int(default_font.cget("size"))),
            ),
            "button": tkfont.Font(root=root, family="Arial", size=12, weight="bold"),
        }

    @property
    def theme_names(self) -> list[str]:
        return list(self.THEMES.keys())

    @property
    def palette(self) -> dict[str, str]:
        return self.THEMES.get(self.current_theme, self.THEMES["Hell"])

    def _resolve_surfaces(self, theme: dict[str, object]) -> dict[str, object]:
        defaults = {
            "nav_bg": theme.get("nav_bg", theme["background"]),
            "nav_fg": theme.get("nav_fg", theme["foreground"]),
            "nav_accent": theme.get("nav_accent", theme["accent"]),
            "settings_bg": theme.get("settings_bg", theme["background"]),
            "settings_fg": theme.get("settings_fg", theme["foreground"]),
            "card_base": theme.get("card_base", theme["background"]),
            "card_title": theme.get("card_title", theme["accent"]),
        }
        card_palette = theme.get("card_palette")
        if isinstance(card_palette, list) and all(
            isinstance(pair, (list, tuple)) and len(pair) == 2 and all(isinstance(color, str) for color in pair)
            for pair in card_palette
        ):
            defaults["card_palette"] = card_palette
        else:
            defaults["card_palette"] = [
                ("#1fb6ff", "#e0f7ff"),
                ("#7c3aed", "#f3e8ff"),
                ("#16a34a", "#e6ffed"),
                ("#f97316", "#fff3e6"),
            ]
        return defaults

    @property
    def module_palette(self) -> list[tuple[str, str]]:
        palette = self.current_surfaces.get("card_palette")
        if isinstance(palette, list) and all(isinstance(pair, (list, tuple)) and len(pair) == 2 for pair in palette):
            return [(str(primary), str(secondary)) for primary, secondary in palette]
        return [
            ("#1fb6ff", "#e0f7ff"),
            ("#7c3aed", "#f3e8ff"),
            ("#16a34a", "#e6ffed"),
            ("#f97316", "#fff3e6"),
        ]

    def configure_styles(self) -> None:
        self.style.configure("Header.TLabel", font=self.fonts["header"])
        self.style.configure("TLabel", wraplength=440, font=self.fonts["default"])
        self.style.configure(
            "Helper.TLabel",
            foreground="#1f2933",
            wraplength=540,
            font=self.fonts["helper"],
        )
        self.style.configure("Status.TLabel", font=self.fonts["status"])
        self.style.configure("Pane.TLabelframe", padding=8)
        self.style.configure("Pane.TLabelframe.Label", font=self.fonts["header"])
        self.style.configure("Note.TLabelframe", padding=8)
        self.style.configure("Note.TLabelframe.Label", font=self.fonts["header"])
        self.style.configure("Sidebar.TLabelframe", padding=8)
        self.style.configure("Sidebar.TLabelframe.Label", font=self.fonts["status"])

    def apply_theme(self, name: str) -> None:
        theme = self.THEMES.get(name, self.THEMES["Hell"])
        self.current_theme = name if name in self.THEMES else "Hell"
        self.invert_text = bool(theme.get("invert_text", False))
        bg = theme["background"]
        fg = theme["foreground"]
        accent = theme["accent"]
        self.current_surfaces = self._resolve_surfaces(theme)

        self.root.configure(bg=bg)
        for element in ["TFrame", "TLabel", "TLabelFrame", "TButton", "TCombobox", "Treeview"]:
            self.style.configure(element, background=bg, foreground=fg, font=self.fonts["default"])
        self.style.configure(
            "TButton",
            padding=(14, 12),
            relief="raised",
            borderwidth=2,
            focusthickness=2,
            focuscolor=accent,
            font=self.fonts["button"],
        )
        self.style.configure("TCombobox", fieldbackground="white", padding=(10, 8))
        self.style.configure("Treeview", fieldbackground=bg, bordercolor=accent)
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.map(
            "TButton",
            background=[("active", accent)],
            foreground=[("active", fg)],
            focuscolor=[("focus", accent)],
        )
        self.style.map("TCheckbutton", focuscolor=[("active", accent)])
        self.style.map("TEntry", highlightcolor=[("focus", accent)], bordercolor=[("focus", accent)])
        for style_name in ("Pane.TLabelframe", "Note.TLabelframe", "Sidebar.TLabelframe"):
            self.style.configure(style_name, background=bg, foreground=fg, bordercolor=accent)
            self.style.configure(f"{style_name}.Label", background=bg, foreground=accent)
        self.style.configure("Status.TLabel", foreground=accent)

        progress_style = {
            "troughcolor": bg,
            "background": accent,
            "bordercolor": accent,
            "lightcolor": accent,
            "darkcolor": accent,
        }
        self.style.configure("TProgressbar", **progress_style)

        nav_bg = self.current_surfaces["nav_bg"]
        nav_fg = self.current_surfaces["nav_fg"]
        nav_accent = self.current_surfaces["nav_accent"]
        settings_bg = self.current_surfaces["settings_bg"]
        settings_fg = self.current_surfaces["settings_fg"]
        card_base = self.current_surfaces["card_base"]
        card_title = self.current_surfaces["card_title"]

        self.style.configure("Nav.TFrame", background=nav_bg)
        self.style.configure("Nav.TLabel", background=nav_bg, foreground=nav_fg, font=self.fonts["status"])
        self.style.configure(
            "Nav.TButton",
            background=nav_bg,
            foreground=nav_fg,
            font=self.fonts["button"],
            bordercolor=nav_accent,
            focusthickness=2,
            focuscolor=nav_accent,
        )
        self.style.map(
            "Nav.TButton",
            background=[("active", nav_accent)],
            foreground=[("active", nav_fg)],
        )
        self.style.configure(
            "Nav.TLabelframe",
            background=nav_bg,
            foreground=nav_fg,
            bordercolor=nav_accent,
            padding=8,
        )
        self.style.configure("Nav.TLabelframe.Label", background=nav_bg, foreground=nav_fg)

        self.style.configure(
            "Settings.TLabelframe",
            background=settings_bg,
            foreground=settings_fg,
            bordercolor=accent,
            padding=10,
        )
        self.style.configure("Settings.TLabelframe.Label", background=settings_bg, foreground=accent)

        self.style.configure(
            "Card.TLabelframe",
            background=card_base,
            foreground=fg,
            bordercolor=accent,
            padding=10,
        )
        self.style.configure("Card.TLabelframe.Label", background=card_base, foreground=card_title)
        self.style.configure("Main.TFrame", background=bg)

        for child in self.root.winfo_children():
            self._propagate_bg(child, bg)

    def status_colors(self, ok: bool) -> tuple[str, str]:
        palette = self.palette
        accent = palette["accent"]
        background = palette["background"]
        return (accent, background) if ok else ("#c0392b", background)

    def apply_text_theme(self, widget: tk.Widget, invert: bool | None = None) -> None:
        """Apply readable text settings to plain Tk widgets.

        The optional ``invert`` flag allows callers to invert only the active
        text field without switching the full dashboard theme. If ``invert`` is
        omitted, the current theme preference is respected.
        """

        if not isinstance(widget, tk.Text):
            raise TypeError("apply_text_theme erwartet ein tk.Text-Widget")
        palette = self.palette
        invert_flag = self.invert_text or bool(palette.get("invert_text", False))
        if invert is not None:
            invert_flag = bool(invert)
        fg = palette["background"] if invert_flag else palette["foreground"]
        bg = palette["foreground"] if invert_flag else palette["background"]
        widget.configure(
            font=self.fonts["text"],
            foreground=fg,
            background=bg,
            insertbackground=palette["accent"],
            highlightthickness=1,
            highlightbackground=palette["accent"],
        )

    def _propagate_bg(self, widget: tk.Widget, bg: str) -> None:
        if isinstance(widget, ttk.Widget):
            for child in widget.winfo_children():
                self._propagate_bg(child, bg)
            return
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

        if minimum_ratio <= 0:
            raise ValueError("minimum_ratio muss größer als 0 sein")

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

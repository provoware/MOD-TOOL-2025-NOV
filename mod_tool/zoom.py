"""Zoom and scaling utilities for accessible font resizing."""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Mapping


class ZoomManager:
    """Centralises zoom handling for the GUI via Ctrl + Scroll.

    The manager scales both the Tk DPI setting and the registered fonts so
    all elements adapt fluidly. Input values are clamped to protect
    readability and to keep the layout stable.
    """

    def __init__(
        self,
        root: tk.Tk,
        fonts: Mapping[str, tkfont.Font],
        min_scale: float = 0.8,
        max_scale: float = 1.6,
    ) -> None:
        if not isinstance(min_scale, (int, float)) or not isinstance(max_scale, (int, float)):
            raise ValueError("min_scale und max_scale müssen Zahlen sein")
        if min_scale <= 0 or max_scale <= 0:
            raise ValueError("Skalierungswerte müssen positiv sein")
        if min_scale >= max_scale:
            raise ValueError("min_scale muss kleiner als max_scale sein")

        self.root = root
        self.fonts = dict(fonts)
        self.min_scale = float(min_scale)
        self.max_scale = float(max_scale)
        self.scale = 1.0
        self._base_sizes: dict[str, int] = {name: font.cget("size") for name, font in self.fonts.items()}
        self._status_callback: Callable[[str], None] | None = None

    def bind_shortcuts(self, status_callback: Callable[[str], None] | None = None) -> None:
        """Activate Ctrl + Scroll handling for zooming the interface."""

        self._status_callback = status_callback
        self.root.bind_all("<Control-MouseWheel>", self._on_mouse_wheel)  # Windows/Mac
        self.root.bind_all("<Control-Button-4>", self._on_scroll_up)  # Linux
        self.root.bind_all("<Control-Button-5>", self._on_scroll_down)  # Linux

    def set_scale(self, new_scale: float) -> float:
        """Apply a specific scale value with clamping and reporting."""

        if not isinstance(new_scale, (int, float)):
            raise ValueError("Skalierungsfaktor muss eine Zahl sein")
        return self._apply_scale(float(new_scale))

    def zoom_in(self) -> float:
        """Increase zoom by 10% and return the active factor."""

        return self._apply_scale(self.scale + 0.1)

    def zoom_out(self) -> float:
        """Decrease zoom by 10% and return the active factor."""

        return self._apply_scale(self.scale - 0.1)

    def reset(self) -> float:
        """Reset zoom to 100% and return the active factor."""

        return self._apply_scale(1.0)

    def _apply_scale(self, requested: float) -> float:
        clamped = max(self.min_scale, min(self.max_scale, requested))
        if abs(clamped - self.scale) < 0.001:
            return self.scale

        self.scale = clamped
        self.root.tk.call("tk", "scaling", self.scale)

        for name, font in self.fonts.items():
            base_size = self._base_sizes.get(name, font.cget("size"))
            target = max(6, round(base_size * self.scale))
            font.configure(size=target)

        self._notify(f"Zoom gesetzt auf {int(self.scale * 100)}% – Ansicht passt sich automatisch an.")
        return self.scale

    def _on_mouse_wheel(self, event: tk.Event[tk.Misc]) -> None:  # pragma: no cover - UI binding
        direction = 1 if event.delta > 0 else -1
        self._apply_scale(self.scale + 0.1 * direction)

    def _on_scroll_up(self, _: tk.Event[tk.Misc]) -> None:  # pragma: no cover - UI binding
        self._apply_scale(self.scale + 0.1)

    def _on_scroll_down(self, _: tk.Event[tk.Misc]) -> None:  # pragma: no cover - UI binding
        self._apply_scale(self.scale - 0.1)

    def _notify(self, message: str) -> None:
        if self._status_callback:
            self._status_callback(message)

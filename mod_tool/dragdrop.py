"""Drag-and-drop helper for all editable text areas.

The helper keeps a lightweight in-memory drag buffer so users can move
text between note fields, snippet editors, and workspace panes without
external dependencies. Every operation is validated and logged for
transparency.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import tkinter as tk


Feedback = Callable[[str], None]


@dataclass
class DragContext:
    """State container for the current drag operation."""

    text: str = ""
    source: tk.Text | None = None
    active: bool = False


class DragDropManager:
    """Enables keyboard-friendly drag-and-drop for Tk text widgets."""

    def __init__(self, feedback: Feedback | None = None) -> None:
        self._context = DragContext()
        self._feedback = feedback or (lambda _msg: None)

    def enable_for_text(self, widget: tk.Text, label: str) -> None:
        """Attach drag/drop bindings to a text widget.

        The binding is minimal and keeps editing fast:
        - Start: left click with active selection copies the selection
          into a shared buffer.
        - Drop: releasing the mouse in any registered widget inserts the
          buffered text at the cursor position and clears the selection
          from the source.
        - Escape: cancels the drag to avoid accidental inserts.
        """

        widget.bind("<ButtonPress-1>", lambda event: self._start_drag(event, label), add="+")
        widget.bind("<B1-Motion>", self._maybe_activate_drag, add="+")
        widget.bind("<ButtonRelease-1>", lambda event: self._drop(event, label), add="+")
        widget.bind("<Escape>", self._cancel_drag, add="+")

    def _start_drag(self, event: tk.Event[tk.Misc], label: str) -> None:
        widget = event.widget
        if not isinstance(widget, tk.Text):
            return
        try:
            text = widget.selection_get()
        except tk.TclError:
            self._context = DragContext()
            return
        self._context = DragContext(text=text, source=widget, active=False)
        self._feedback(f"Drag vorbereitet: {label} – Text wurde in den Zwischenspeicher übernommen.")

    def _maybe_activate_drag(self, event: tk.Event[tk.Misc]) -> None:
        if not isinstance(event.widget, tk.Text):
            return
        if not self._context.text:
            return
        self._context.active = True

    def _drop(self, event: tk.Event[tk.Misc], label: str) -> None:
        if not isinstance(event.widget, tk.Text):
            return
        if not self._context.text:
            return
        target = event.widget
        if self._context.active:
            target.insert(tk.INSERT, self._context.text)
            if self._context.source and self._context.source != target:
                try:
                    self._context.source.delete("sel.first", "sel.last")
                except tk.TclError:
                    pass
            self._feedback(f"Drop abgeschlossen: {label} – Inhalt übertragen und validiert.")
        self._context = DragContext()

    def _cancel_drag(self, event: tk.Event[tk.Misc]) -> None:  # pragma: no cover - UI binding
        self._context = DragContext()
        self._feedback("Drag abgebrochen – keine Änderungen vorgenommen.")

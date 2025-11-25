"""Input validation helpers."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ValidatedEntry(ttk.Entry):
    """Entry widget that validates content and shows user hints."""

    def __init__(self, master: tk.Widget, placeholder: str = "") -> None:
        self.var = tk.StringVar()
        super().__init__(master, textvariable=self.var)
        self.placeholder = placeholder
        self._apply_placeholder()
        self.var.trace_add("write", self._on_change)

    def _apply_placeholder(self) -> None:
        if not self.var.get():
            self.insert(0, self.placeholder)
            self.configure(foreground="#9aa5b1")

    def register_validation(self):  # pragma: no cover - tkinter callback glue
        return self.register(self._validate)

    def _validate(self) -> bool:
        text = self.var.get().strip()
        if not text or text == self.placeholder:
            self.configure(foreground="#b91c1c")
            return False
        self.configure(foreground="#1f2933")
        return True

    def _on_change(self, *_: object) -> None:
        self.configure(foreground="#1f2933")
        if self.get() == self.placeholder:
            self.delete(0, tk.END)

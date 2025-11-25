"""Dashboard layout builder."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .logging_dashboard import LoggingManager
from .themes import ThemeManager
from .validator import ValidatedEntry


class HeaderControls:
    """Header widgets providing stats, theme selection, and quick inputs."""

    def __init__(self, parent: tk.Widget, theme_manager: ThemeManager) -> None:
        self.frame = ttk.Frame(parent, padding=8)
        self.theme_manager = theme_manager
        self.theme_choice = tk.StringVar(value="Hell")
        self.status_var = tk.StringVar(value="Bereit – Auto-Checks aktiv")
        self.stat_var = tk.StringVar(value="System gesund")
        self.input_fields: list[ValidatedEntry] = []

    def build(self) -> None:
        ttk.Label(self.frame, text="Steuerzentrale", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(self.frame, textvariable=self.status_var).grid(row=1, column=0, sticky="w")
        ttk.Label(self.frame, textvariable=self.stat_var).grid(row=2, column=0, sticky="w")

        ttk.Label(self.frame, text="Theme").grid(row=0, column=1, sticky="e")
        theme_box = ttk.Combobox(self.frame, textvariable=self.theme_choice, values=self.theme_manager.theme_names)
        theme_box.grid(row=0, column=2, sticky="ew", padx=(8, 0))
        theme_box.bind("<<ComboboxSelected>>", self._on_theme_change)

        input_field = ValidatedEntry(self.frame, placeholder="Eingabe (z. B. Pfad)")
        input_field.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(8, 0))
        self.input_fields.append(input_field)

        ttk.Button(self.frame, text="Hilfe & Tipps", command=self._show_help).grid(
            row=2, column=1, columnspan=2, sticky="ew", padx=(8, 0)
        )

        self.frame.columnconfigure(2, weight=1)

    def _on_theme_change(self, event: object) -> None:  # pragma: no cover - UI binding
        self.theme_manager.apply_theme(self.theme_choice.get())

    def _show_help(self) -> None:  # pragma: no cover - UI binding
        self.status_var.set("Hilfe: Wähle ein Theme, nutze die Felder und überwache das Logging.")


class DashboardLayout:
    """Constructs the dashboard grid: header, workspace panes, and footer."""

    def __init__(self, root: tk.Tk, theme_manager: ThemeManager, logging_manager: LoggingManager) -> None:
        self.root = root
        self.theme_manager = theme_manager
        self.logging_manager = logging_manager
        self.header_controls = HeaderControls(root, theme_manager)

    def build(self) -> None:
        self.theme_manager.configure_styles()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.header_controls.build()
        self.header_controls.frame.grid(row=0, column=0, sticky="nsew")

        workspace = ttk.Frame(self.root, padding=8)
        workspace.grid(row=1, column=0, sticky="nsew")
        for i in range(2):
            workspace.columnconfigure(i, weight=1, uniform="pane")
            workspace.rowconfigure(i, weight=1, uniform="pane")

        for row in range(2):
            for col in range(2):
                pane = ttk.LabelFrame(
                    workspace,
                    text=f"Bereich {row * 2 + col + 1}",
                    labelanchor="n",
                    padding=8,
                )
                pane.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
                ttk.Label(pane, text="Modularer Inhalt / Plugin-Fläche", wraplength=220).pack(
                    anchor="w"
                )

        footer = ttk.Frame(self.root, padding=8)
        footer.grid(row=2, column=0, sticky="nsew")
        for i in range(3):
            footer.columnconfigure(i, weight=1, uniform="footer")

        debug_block = ttk.LabelFrame(footer, text="Debug", padding=6)
        debug_block.grid(row=0, column=0, padx=6, sticky="nsew")
        log_block = ttk.LabelFrame(footer, text="Logging", padding=6)
        log_block.grid(row=0, column=1, padx=6, sticky="nsew")
        info_block = ttk.LabelFrame(footer, text="Infos", padding=6)
        info_block.grid(row=0, column=2, padx=6, sticky="nsew")

        self.logging_manager.attach(log_block)
        ttk.Label(debug_block, text="Debugger-Modus bereit – Eingriffe protokolliert.").pack(anchor="w")
        ttk.Label(info_block, text="Tipps: Eingaben prüfen, automatische Selbstheilung aktiv.").pack(
            anchor="w"
        )

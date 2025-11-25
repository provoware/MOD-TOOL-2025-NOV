"""Dashboard layout builder."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from .logging_dashboard import LoggingManager
from .manifest import LayoutSection
from .themes import ThemeManager
from .validator import ValidatedEntry


class HeaderControls:
    """Header widgets providing stats, theme selection, and quick inputs."""

    def __init__(
        self,
        parent: tk.Widget,
        theme_manager: ThemeManager,
        on_start: Callable[[], None],
        on_health_check: Callable[[], None],
        on_toggle_debug: Callable[[bool], None],
        on_show_index: Callable[[], None],
    ) -> None:
        self.frame = ttk.Frame(parent, padding=8)
        self.theme_manager = theme_manager
        self.on_start = on_start
        self.on_health_check = on_health_check
        self.on_toggle_debug = on_toggle_debug
        self.on_show_index = on_show_index
        self.theme_choice = tk.StringVar(value="Hell")
        self.status_var = tk.StringVar(value="Bereit – Auto-Checks aktiv")
        self.stat_var = tk.StringVar(value="System gesund")
        self.debug_enabled = tk.BooleanVar(value=False)
        self.input_fields: list[ValidatedEntry] = []

    def build(self) -> None:
        ttk.Label(self.frame, text="Steuerzentrale", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(self.frame, textvariable=self.status_var).grid(row=1, column=0, sticky="w")
        ttk.Label(self.frame, textvariable=self.stat_var).grid(row=2, column=0, sticky="w")

        ttk.Button(
            self.frame,
            text="Klick & Start (Autopilot)",
            command=self.on_start,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(
            self.frame,
            text="Schnell-Check (Gesundheit)",
            command=self.on_health_check,
        ).grid(row=1, column=1, sticky="ew", padx=(8, 0))
        ttk.Checkbutton(
            self.frame,
            text="Debug/Logging-Modus",
            variable=self.debug_enabled,
            command=lambda: self.on_toggle_debug(self.debug_enabled.get()),
        ).grid(row=2, column=1, sticky="w", padx=(8, 0))

        ttk.Button(
            self.frame,
            text="Index (Module & Funktionen)",
            command=self.on_show_index,
        ).grid(row=0, column=2, sticky="ew", padx=(8, 0))

        ttk.Label(self.frame, text="Theme").grid(row=0, column=3, sticky="e")
        theme_box = ttk.Combobox(
            self.frame, textvariable=self.theme_choice, values=self.theme_manager.theme_names
        )
        theme_box.grid(row=0, column=4, sticky="ew", padx=(8, 0))
        theme_box.bind("<<ComboboxSelected>>", self._on_theme_change)

        input_field = ValidatedEntry(
            self.frame,
            placeholder="Eingabe (z. B. Pfad, Name) – rot = fehlt, dunkel = ok",
        )
        input_field.grid(row=1, column=2, columnspan=3, sticky="ew", padx=(8, 0))
        self.input_fields.append(input_field)

        ttk.Button(self.frame, text="Hilfe & Tipps", command=self._show_help).grid(
            row=2, column=2, columnspan=3, sticky="ew", padx=(8, 0)
        )

        self.frame.columnconfigure(4, weight=1)

    def _on_theme_change(self, event: object) -> None:  # pragma: no cover - UI binding
        self.theme_manager.apply_theme(self.theme_choice.get())

    def _show_help(self) -> None:  # pragma: no cover - UI binding
        self.status_var.set(
            "Hilfe: Klicke auf 'Klick & Start' – die Routine prüft alles, Plugins und Tests inklusive."
        )


class DashboardLayout:
    """Constructs the dashboard grid: header, workspace panes, and footer."""

    def __init__(
        self,
        root: tk.Tk,
        theme_manager: ThemeManager,
        logging_manager: LoggingManager,
    ) -> None:
        self.root = root
        self.theme_manager = theme_manager
        self.logging_manager = logging_manager
        self.header_controls: HeaderControls | None = None
        self._workspace_sections: list[LayoutSection] = [
            LayoutSection(
                identifier="pane-1",
                title="Bereich 1",
                purpose="Freier Slot für Plugins oder Statuskarten",
                accessibility_label="Linkes oberes Panel",
            ),
            LayoutSection(
                identifier="pane-2",
                title="Bereich 2",
                purpose="Freier Slot für Plugins oder Statuskarten",
                accessibility_label="Rechtes oberes Panel",
            ),
            LayoutSection(
                identifier="pane-3",
                title="Bereich 3",
                purpose="Freier Slot für Plugins oder Statuskarten",
                accessibility_label="Linkes unteres Panel",
            ),
            LayoutSection(
                identifier="pane-4",
                title="Bereich 4",
                purpose="Freier Slot für Plugins oder Statuskarten",
                accessibility_label="Rechtes unteres Panel",
            ),
        ]

    def build(
        self,
        on_start: Callable[[], None],
        on_health_check: Callable[[], None],
        on_toggle_debug: Callable[[bool], None],
        on_show_index: Callable[[], None],
    ) -> None:
        self.theme_manager.configure_styles()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.header_controls = HeaderControls(
            self.root, self.theme_manager, on_start, on_health_check, on_toggle_debug, on_show_index
        )
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

    def describe_sections(self) -> list[LayoutSection]:
        """Expose layout sections for manifest creation and accessibility docs."""

        return [
            LayoutSection(
                identifier="header",
                title="Steuerzentrale",
                purpose="Start, Prüfungen, Theme-Auswahl",
                accessibility_label="Obere Leiste mit Status- und Kontroll-Buttons",
            ),
            *self._workspace_sections,
            LayoutSection(
                identifier="footer",
                title="Fußleiste",
                purpose="Debug, Log-Ansicht, Hinweise",
                accessibility_label="Unterer Bereich mit Debug-Status und Tipps",
            ),
        ]

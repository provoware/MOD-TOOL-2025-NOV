"""Dashboard layout builder with accessible, editable workspaces."""
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
        self.progress_var = tk.IntVar(value=10)
        self.progress_label = tk.StringVar(value="Startroutine: bereit")
        self.debug_enabled = tk.BooleanVar(value=False)
        self.input_fields: list[ValidatedEntry] = []

    def build(self) -> None:
        ttk.Label(self.frame, text="Steuerzentrale", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            self.frame,
            text="Alles im Blick: Starte Autopilot, prüfe Gesundheit oder wechsle das Theme.",
            style="Helper.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Label(self.frame, textvariable=self.status_var, style="Status.TLabel").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(self.frame, textvariable=self.stat_var).grid(row=3, column=0, sticky="w")

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
            self.frame,
            textvariable=self.theme_choice,
            values=self.theme_manager.theme_names,
            state="readonly",
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

        ttk.Progressbar(
            self.frame,
            maximum=100,
            variable=self.progress_var,
        ).grid(row=3, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=(4, 0))
        ttk.Label(self.frame, textvariable=self.progress_label).grid(
            row=3, column=4, sticky="w", padx=(8, 0)
        )

        self.frame.columnconfigure(4, weight=1)

    def _on_theme_change(self, event: object) -> None:  # pragma: no cover - UI binding
        self.theme_manager.apply_theme(self.theme_choice.get())

    def _show_help(self) -> None:  # pragma: no cover - UI binding
        self.status_var.set(
            "Hilfe: Klicke auf 'Klick & Start' – die Routine prüft alles, Plugins und Tests inklusive."
        )

    def set_progress(self, percent: int, label: str) -> None:
        safe_value = max(0, min(100, percent))
        self.progress_var.set(safe_value)
        self.progress_label.set(label)


class WorkspacePane(ttk.LabelFrame):
    """Editable workspace pane with context menu and validation."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        description: str,
        logging_manager: LoggingManager | None = None,
    ) -> None:
        super().__init__(parent, text=title, padding=10, labelanchor="n")
        self.logging_manager = logging_manager
        self.status_var = tk.StringVar(
            value="Bereit: Einfach Text eintragen. Rechtsklick öffnet das Kontextmenü."
        )
        self.description = description
        self._menu = tk.Menu(self, tearoff=False)
        self._menu.add_command(label="Kopieren", command=self.copy_selection)
        self._menu.add_command(label="Einfügen", command=self.paste_clipboard)
        self._menu.add_command(label="Alles markieren", command=self.select_all)
        self._menu.add_separator()
        self._menu.add_command(label="Leeren", command=self.clear_text)
        self._menu.add_command(label="Speichern & prüfen", command=self.save_content)

        ttk.Label(self, text=self.description, wraplength=240).pack(anchor="w")
        self.text = tk.Text(self, height=6, wrap="word")
        self.text.insert(
            "1.0",
            "Freier Bereich für Notizen, Modul-Befehle oder To-dos."
            " Tastatur: Strg+Enter speichert den Inhalt.",
        )
        self.text.bind("<Button-3>", self._show_menu)
        self.text.bind("<Control-Return>", lambda event: self.save_content())
        self.text.pack(fill=tk.BOTH, expand=True, pady=4)

        button_bar = ttk.Frame(self)
        ttk.Button(button_bar, text="Speichern & prüfen", command=self.save_content).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(button_bar, text="Kontextmenü öffnen", command=self.open_menu_now).pack(
            side=tk.LEFT
        )
        ttk.Button(button_bar, text="Leeren", command=self.clear_text).pack(side=tk.LEFT, padx=(6, 0))
        button_bar.pack(anchor="w", pady=(2, 0))

        ttk.Label(self, textvariable=self.status_var, style="Status.TLabel").pack(
            anchor="w", pady=(4, 0)
        )

    def _show_menu(self, event: tk.Event[tk.Misc]) -> None:  # pragma: no cover - UI binding
        self._menu.tk_popup(event.x_root, event.y_root)

    def open_menu_now(self) -> None:
        self._menu.tk_popup(self.winfo_rootx() + 20, self.winfo_rooty() + 20)

    def copy_selection(self) -> None:
        try:
            selection = self.text.selection_get()
        except tk.TclError:
            self.status_var.set("Nichts markiert – bitte Text auswählen.")
            return
        self.clipboard_clear()
        self.clipboard_append(selection)
        self.status_var.set("Kopiert – Inhalt liegt in der Zwischenablage.")

    def paste_clipboard(self) -> None:
        try:
            data = self.clipboard_get()
        except tk.TclError:
            self.status_var.set("Zwischenablage leer – nichts zum Einfügen.")
            return
        self.text.insert(tk.INSERT, data)
        self.status_var.set("Eingefügt – bitte kurz prüfen.")

    def select_all(self) -> None:
        self.text.tag_add("sel", "1.0", tk.END)
        self.status_var.set("Alles markiert – bereit zum Kopieren oder Löschen.")

    def clear_text(self) -> None:
        self.text.delete("1.0", tk.END)
        self.status_var.set("Feld geleert – neu starten und speichern nicht vergessen.")

    def save_content(self) -> bool:
        content = self.text.get("1.0", tk.END).strip()
        if not content:
            self.status_var.set("Bitte Text eingeben – leer kann nicht gespeichert werden.")
            return False
        preview = content[:60].replace("\n", " ")
        self.status_var.set("Gespeichert: Inhalt geprüft und angenommen.")
        if self.logging_manager:
            self.logging_manager.log_system(f"Pane aktualisiert: {preview}")
        return True


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

        pane_descriptions = [
            "Hier kannst du To-dos sammeln oder einfache Schritte notieren.",
            "Platz für Plugin-Notizen und schnelle Ergebnisse.",
            "Sammel Hinweise für Fehler, Logs oder Screenshots.",
            "Freie Zone für eigene Ideen oder Checklisten.",
        ]

        index = 0
        for row in range(2):
            for col in range(2):
                pane = WorkspacePane(
                    workspace,
                    title=f"Bereich {row * 2 + col + 1}",
                    description=pane_descriptions[index],
                    logging_manager=self.logging_manager,
                )
                pane.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
                index += 1

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
        ttk.Label(
            info_block,
            text=(
                "Tipps: Eingaben prüfen, automatische Selbstheilung aktiv."
                " Kontextmenü über Rechtsklick öffnet Bearbeitungsoptionen."
            ),
        ).pack(anchor="w")

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

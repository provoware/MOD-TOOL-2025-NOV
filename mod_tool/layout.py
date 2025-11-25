"""Dashboard layout builder with accessible, editable workspaces."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Iterable, Sequence

from .dashboard_state import DashboardState

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
        on_toggle_sidebar: Callable[[], None],
    ) -> None:
        self.frame = ttk.Frame(parent, padding=8)
        self.theme_manager = theme_manager
        self.on_start = on_start
        self.on_health_check = on_health_check
        self.on_toggle_debug = on_toggle_debug
        self.on_show_index = on_show_index
        self.on_toggle_sidebar = on_toggle_sidebar
        self.theme_choice = tk.StringVar(value="Hell")
        self.status_var = tk.StringVar(value="Bereit – Auto-Checks aktiv")
        self.stat_var = tk.StringVar(value="System gesund")
        self.progress_var = tk.IntVar(value=10)
        self.progress_label = tk.StringVar(value="Startroutine: bereit")
        self.debug_enabled = tk.BooleanVar(value=False)
        self.clock_var = tk.StringVar(value="Zeit wird geladen…")
        self.input_fields: list[ValidatedEntry] = []

    def build(self) -> None:
        ttk.Label(self.frame, text="Steuerzentrale", style="Header.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            self.frame,
            text=(
                "Alles im Blick: Starte Autopilot, prüfe Gesundheit oder wechsle das Theme. "
                "Daten bleiben lokal, Eingaben werden geprüft."
            ),
            style="Helper.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Label(self.frame, textvariable=self.status_var, style="Status.TLabel").grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(self.frame, textvariable=self.stat_var).grid(row=3, column=0, sticky="w")
        ttk.Label(self.frame, textvariable=self.clock_var, style="Helper.TLabel").grid(
            row=4, column=0, sticky="w"
        )

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
        ttk.Button(
            self.frame,
            text="Sidebar ein/aus",
            command=self.on_toggle_sidebar,
        ).grid(row=1, column=2, sticky="ew", padx=(8, 0))

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
        self.frame.rowconfigure(5, weight=0)

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
        status_color_provider: Callable[[bool], tuple[str, str]] | None = None,
    ) -> None:
        super().__init__(parent, text=title, padding=10, labelanchor="n", style="Pane.TLabelframe")
        self.logging_manager = logging_manager
        self.status_var = tk.StringVar(
            value="Bereit: Einfach Text eintragen. Rechtsklick öffnet das Kontextmenü."
        )
        self.status_color_provider = status_color_provider
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

        self.status_label = ttk.Label(self, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(anchor="w", pady=(4, 0))

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
            self._set_status("Bitte Text eingeben – leer kann nicht gespeichert werden.", ok=False)
            return False
        preview = content[:60].replace("\n", " ")
        self._set_status("Gespeichert: Inhalt geprüft und angenommen.")
        if self.logging_manager:
            self.logging_manager.log_system(f"Pane aktualisiert: {preview}")
        return True

    def _set_status(self, message: str, ok: bool = True) -> None:
        self.status_var.set(message)
        if self.status_color_provider and self.status_label:
            fg, bg = self.status_color_provider(ok)
            self.status_label.configure(foreground=fg, background=bg)


class NotePanel(ttk.LabelFrame):
    """Dedicated note area with autosave, undo, and status coloring."""

    def __init__(
        self,
        parent: tk.Widget,
        on_save: Callable[[str], bool],
        on_autosave: Callable[[str], None],
        status_color_provider: Callable[[bool], tuple[str, str]],
    ) -> None:
        super().__init__(parent, text="Notizbereich – speichert automatisch", padding=10, style="Note.TLabelframe")
        self.on_save = on_save
        self.on_autosave = on_autosave
        self.status_color_provider = status_color_provider
        self.status_var = tk.StringVar(value="Tippe Notizen. Verlassen = Autosave. Rückgängig jederzeit möglich.")
        self.text = tk.Text(self, height=5, wrap="word", undo=True)
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.bind("<FocusOut>", self._auto_save_event)

        button_bar = ttk.Frame(self)
        ttk.Button(button_bar, text="Speichern", command=self._save).pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Rückgängig", command=self._undo).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(button_bar, text="Wiederholen", command=self._redo).pack(side=tk.LEFT, padx=(6, 0))
        button_bar.pack(anchor="w", pady=(4, 0))

        self.status_label = ttk.Label(self, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(anchor="w", pady=(4, 0))

    def set_content(self, text: str) -> None:
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", text)

    def get_content(self) -> str:
        return self.text.get("1.0", tk.END).strip()

    def _save(self) -> None:
        success = self.on_save(self.get_content())
        self._update_status(success, "Notiz gespeichert" if success else "Speichern fehlgeschlagen")

    def _auto_save_event(self, event: tk.Event[tk.Misc]) -> None:  # pragma: no cover - UI binding
        self.on_autosave(self.get_content())
        self._update_status(True, "Autosave durchgeführt")

    def _undo(self) -> None:  # pragma: no cover - UI binding
        try:
            self.text.edit_undo()
            self._update_status(True, "Rückgängig ausgeführt")
        except tk.TclError:
            self._update_status(False, "Nichts zum Zurücknehmen")

    def _redo(self) -> None:  # pragma: no cover - UI binding
        try:
            self.text.edit_redo()
            self._update_status(True, "Wiederholen ausgeführt")
        except tk.TclError:
            self._update_status(False, "Nichts zu wiederholen")

    def _update_status(self, ok: bool, message: str) -> None:
        fg, bg = self.status_color_provider(ok)
        self.status_label.configure(foreground=fg, background=bg)
        self.status_var.set(message)


class Sidebar(ttk.LabelFrame):
    """Collapsible sidebar for quick actions and transparency info."""

    def __init__(
        self,
        parent: tk.Widget,
        actions: dict[str, Callable[[], None]],
        info_provider: Callable[[], Iterable[str]],
    ) -> None:
        super().__init__(parent, text="Schnellzugriff & Sicherheit", padding=10, labelanchor="n", style="Sidebar.TLabelframe")
        self.actions = actions
        self.info_provider = info_provider
        self.visible = True
        for idx, (label, action) in enumerate(self.actions.items()):
            ttk.Button(self, text=label, command=action).grid(row=idx, column=0, sticky="ew", pady=2)
        ttk.Label(self, text="Best Practices & Barrierefreiheit:", style="Helper.TLabel").grid(
            row=len(self.actions), column=0, sticky="w", pady=(8, 0)
        )
        self.info_label = ttk.Label(self, text="", wraplength=180, justify=tk.LEFT)
        self.info_label.grid(row=len(self.actions) + 1, column=0, sticky="w")
        self.columnconfigure(0, weight=1)

    def refresh_info(self) -> None:
        tips = list(self.info_provider())
        if not tips:
            self.info_label.configure(text="Keine Hinweise verfügbar")
            return
        self.info_label.configure(text="\n".join(f"- {tip}" for tip in tips))

    def toggle(self) -> None:
        self.visible = not self.visible
        if self.visible:
            self.grid()
        else:
            self.grid_remove()


class DashboardLayout:
    """Constructs the dashboard grid: header, workspace panes, and footer."""

    def __init__(
        self,
        root: tk.Tk,
        theme_manager: ThemeManager,
        logging_manager: LoggingManager,
        state: DashboardState | None = None,
    ) -> None:
        self.root = root
        self.theme_manager = theme_manager
        self.logging_manager = logging_manager
        self.state = state or DashboardState(base_path=Path("logs"))
        self.header_controls: HeaderControls | None = None
        self.sidebar: Sidebar | None = None
        self.note_panel: NotePanel | None = None
        self.info_label: ttk.Label | None = None
        self.module_palette: Sequence[tuple[str, str]] = (
            ("#1fb6ff", "#e0f7ff"),  # Modul 1: Blau/Türkis
            ("#7c3aed", "#f3e8ff"),  # Modul 2: Violett
            ("#16a34a", "#e6ffed"),  # Modul 3: Grün
            ("#f97316", "#fff3e6"),  # Modul 4: Orange
        )
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
        on_toggle_sidebar: Callable[[], None] | None = None,
        on_choose_project: Callable[[], None] | None = None,
        on_save_note: Callable[[str], bool] | None = None,
        on_autosave_note: Callable[[str], None] | None = None,
        on_backup: Callable[[], None] | None = None,
        on_import_notes: Callable[[], None] | None = None,
        on_export_notes: Callable[[], None] | None = None,
        on_edit_hints: Callable[[], None] | None = None,
        info_provider: Callable[[], Iterable[str]] | None = None,
    ) -> None:
        self.theme_manager.configure_styles()
        self.root.columnconfigure(0, weight=1)
        # Accessibility sizing: clear header/footer heights and generous sidebar width
        self.root.rowconfigure(0, weight=0, minsize=72)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0, minsize=48)

        on_toggle_sidebar = on_toggle_sidebar or (lambda: None)
        on_choose_project = on_choose_project or (lambda: None)
        on_save_note = on_save_note or (lambda _text: True)
        on_autosave_note = on_autosave_note or (lambda _text: None)
        on_backup = on_backup or (lambda: None)
        on_import_notes = on_import_notes or (lambda: None)
        on_export_notes = on_export_notes or (lambda: None)
        on_edit_hints = on_edit_hints or (lambda: None)
        info_provider = info_provider or (lambda: ("Best Practices folgen noch",))

        self.header_controls = HeaderControls(
            self.root,
            self.theme_manager,
            on_start,
            on_health_check,
            on_toggle_debug,
            on_show_index,
            on_toggle_sidebar,
        )
        self.header_controls.build()
        self.header_controls.frame.grid(row=0, column=0, sticky="nsew")

        workspace_container = ttk.Frame(self.root, padding=8)
        workspace_container.grid(row=1, column=0, sticky="nsew")
        workspace_container.columnconfigure(0, weight=0, minsize=220)
        workspace_container.columnconfigure(1, weight=1)
        workspace_container.rowconfigure(0, weight=1)

        actions = {
            "Projekt wählen": on_choose_project,
            "Projekt prüfen": on_health_check,
            "Backup erstellen": on_backup,
            "Notizen importieren": on_import_notes,
            "Notizen exportieren": on_export_notes,
            "Hints bearbeiten": on_edit_hints,
        }
        self.sidebar = Sidebar(workspace_container, actions=actions, info_provider=info_provider)
        self.sidebar.grid(row=0, column=0, sticky="nsw", padx=(0, 8))

        workspace = ttk.Frame(workspace_container)
        workspace.grid(row=0, column=1, sticky="nsew")
        workspace.columnconfigure(0, weight=1)
        workspace.rowconfigure(1, weight=1)

        self.note_panel = NotePanel(
            workspace,
            on_save=on_save_note,
            on_autosave=on_autosave_note,
            status_color_provider=self.state.rotate_status_colors,
        )
        self.note_panel.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        pane_grid = ttk.Frame(workspace)
        pane_grid.grid(row=1, column=0, sticky="nsew")
        for i in range(2):
            pane_grid.columnconfigure(i, weight=1, uniform="pane")
            pane_grid.rowconfigure(i, weight=1, uniform="pane")

        pane_descriptions = [
            "Hier kannst du To-dos sammeln oder einfache Schritte notieren.",
            "Platz für Plugin-Notizen und schnelle Ergebnisse.",
            "Sammel Hinweise für Fehler, Logs oder Screenshots.",
            "Freie Zone für eigene Ideen oder Checklisten.",
        ]

        index = 0
        for row in range(2):
            for col in range(2):
                color_primary, color_bg = self.module_palette[index % len(self.module_palette)]
                pane = WorkspacePane(
                    pane_grid,
                    title=f"Bereich {row * 2 + col + 1}",
                    description=pane_descriptions[index],
                    logging_manager=self.logging_manager,
                    status_color_provider=self.state.rotate_status_colors,
                )
                color_band = tk.Frame(
                    pane, height=8, background=color_primary, highlightthickness=0
                )
                color_band.pack(fill=tk.X, padx=6, pady=(0, 6))
                color_band = tk.Frame(pane, height=8, background=color_primary, highlightthickness=0)
                color_band.pack(fill=tk.X, padx=-4, pady=(0, 6))
                pane.configure(style="Pane.TLabelframe")
                pane.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
                pane.configure(labelanchor="n")
                pane.text.configure(highlightthickness=2, highlightbackground=color_bg)
                pane.status_label.configure(background=color_bg)
                index += 1

        footer = ttk.Frame(self.root, padding=8)
        footer.grid(row=2, column=0, sticky="nsew")
        for i in range(3):
            footer.columnconfigure(i, weight=1, uniform="footer")

        debug_block = ttk.LabelFrame(footer, text="Debug", padding=6)
        debug_block.grid(row=0, column=0, padx=6, sticky="nsew")
        log_block = ttk.LabelFrame(footer, text="Logging", padding=6)
        log_block.grid(row=0, column=1, padx=6, sticky="nsew")
        info_block = ttk.LabelFrame(footer, text="Infos", padding=6, style="Note.TLabelframe")
        info_block.grid(row=0, column=2, padx=6, sticky="nsew")

        self.logging_manager.attach(log_block)
        ttk.Label(debug_block, text="Debugger-Modus bereit – Eingriffe protokolliert.").pack(anchor="w")
        self.info_label = ttk.Label(
            info_block,
            text=(
                "Tipps: Eingaben prüfen, automatische Selbstheilung aktiv."
                " Kontextmenü über Rechtsklick öffnet Bearbeitungsoptionen."
            ),
            wraplength=360,
            style="Helper.TLabel",
        )
        self.info_label.pack(anchor="w")

        self.status_var = tk.StringVar(value="Ampel: alles ok – Klick für Details")
        self.status_indicator = tk.Label(
            info_block,
            textvariable=self.status_var,
            background="#16a34a",
            foreground="#ffffff",
            padx=10,
            pady=6,
            relief=tk.GROOVE,
            cursor="hand2",
        )
        self.status_indicator.pack(fill=tk.X, pady=(6, 0))

    def set_status_light(self, level: str, message: str) -> None:
        """Update the footer status light with warning/error levels."""

        palette = {
            "ok": "#16a34a",
            "warnung": "#f59e0b",
            "fehler": "#dc2626",
        }
        color = palette.get(level, "#2563eb")
        self.status_var.set(message)
        self.status_indicator.configure(background=color)

    def describe_sections(self) -> list[LayoutSection]:
        """Expose layout sections for manifest creation and accessibility docs."""

        return [
            LayoutSection(
                identifier="header",
                title="Steuerzentrale",
                purpose="Start, Prüfungen, Theme-Auswahl",
                accessibility_label="Obere Leiste mit Status- und Kontroll-Buttons",
            ),
            LayoutSection(
                identifier="sidebar",
                title="Schnellzugriff",
                purpose="Projektwahl, Backup, Import/Export, Hinweise",
                accessibility_label="Ein- und ausklappbarer Bereich mit Buttons",
            ),
            LayoutSection(
                identifier="notes",
                title="Notizbereich",
                purpose="Autosave-Notizen mit Undo/Redo",
                accessibility_label="Eingabefeld speichert automatisch beim Verlassen",
            ),
            *self._workspace_sections,
            LayoutSection(
                identifier="footer",
                title="Fußleiste",
                purpose="Debug, Log-Ansicht, Hinweise",
                accessibility_label="Unterer Bereich mit Debug-Status und Tipps",
            ),
        ]

"""Dashboard layout builder with accessible, editable workspaces."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Iterable, Sequence

from .todo import TodoItem

from .dashboard_state import DashboardState

from .logging_dashboard import LoggingManager
from .manifest import LayoutSection
from .snippet_library import SnippetLibraryPanel, SnippetStore
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
        on_toggle_large_text: Callable[[bool], None],
        on_toggle_sidebar: Callable[[], None],
        on_validate_links: Callable[[], None],
        on_reflow_workspaces: Callable[[], None],
        on_toggle_invert: Callable[[], None],
    ) -> None:
        self.frame = ttk.Frame(parent, padding=8)
        self.theme_manager = theme_manager
        self.on_start = on_start
        self.on_health_check = on_health_check
        self.on_toggle_debug = on_toggle_debug
        self.on_show_index = on_show_index
        self.on_toggle_large_text = on_toggle_large_text
        self.on_toggle_sidebar = on_toggle_sidebar
        self.on_validate_links = on_validate_links
        self.on_reflow_workspaces = on_reflow_workspaces
        self.on_toggle_invert = on_toggle_invert
        self.theme_choice = tk.StringVar(value="Hell")
        self.status_var = tk.StringVar(value="Bereit – Auto-Checks aktiv")
        self.stat_var = tk.StringVar(value="System gesund")
        self.progress_var = tk.IntVar(value=10)
        self.progress_label = tk.StringVar(value="Startroutine: bereit")
        self.debug_enabled = tk.BooleanVar(value=False)
        self.clock_var = tk.StringVar(value="Zeit wird geladen…")
        self.accessibility_var = tk.StringVar(value="Kontrast-Check lädt…")
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
            row=5, column=0, sticky="w"
        )
        ttk.Label(self.frame, textvariable=self.accessibility_var, style="Helper.TLabel").grid(
            row=6, column=0, sticky="w", pady=(2, 0)
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

        self.large_text_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.frame,
            text="Großtext (150%)",
            variable=self.large_text_enabled,
            command=lambda: self.on_toggle_large_text(self.large_text_enabled.get()),
        ).grid(row=3, column=1, sticky="w", padx=(8, 0))

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
        ttk.Button(
            self.frame,
            text="Verknüpfungen prüfen",
            command=self.on_validate_links,
        ).grid(row=2, column=2, sticky="ew", padx=(8, 0))
        ttk.Button(
            self.frame,
            text="Fenster neu anordnen",
            command=self.on_reflow_workspaces,
        ).grid(row=3, column=2, sticky="ew", padx=(8, 0))
        ttk.Button(
            self.frame,
            text="Invertierter Text (aktiv)",
            command=self.on_toggle_invert,
        ).grid(row=4, column=2, sticky="ew", padx=(8, 0))

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
        ).grid(row=4, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=(4, 0))
        ttk.Label(self.frame, textvariable=self.progress_label).grid(
            row=4, column=4, sticky="w", padx=(8, 0)
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

    def set_accessibility_status(self, report: dict[str, str]) -> None:
        if not isinstance(report, dict) or "status" not in report or "details" not in report:
            raise ValueError("Ungültiger Kontrast-Report übergeben")
        status = report.get("status", "warnung")
        detail = report.get("details", "Keine Details")
        prefix = "Kontrast ok" if status == "ok" else "Kontrast prüfen"
        self.accessibility_var.set(f"{prefix}: {detail}")


class WorkspacePane(ttk.LabelFrame):
    """Editable workspace pane with context menu, validation, and collapsing."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        description: str,
        logging_manager: LoggingManager | None = None,
        status_color_provider: Callable[[bool], tuple[str, str]] | None = None,
        theme_manager: ThemeManager | None = None,
        start_collapsed: bool = True,
    ) -> None:
        super().__init__(parent, text=title, padding=10, labelanchor="n", style="Pane.TLabelframe")
        self.logging_manager = logging_manager
        self.status_var = tk.StringVar(
            value="Bereit: Einfach Text eintragen. Rechtsklick öffnet das Kontextmenü."
        )
        self.status_color_provider = status_color_provider
        self.theme_manager = theme_manager
        self.description = description
        self._menu = tk.Menu(self, tearoff=False)
        self._menu.add_command(label="Kopieren", command=self.copy_selection)
        self._menu.add_command(label="Einfügen", command=self.paste_clipboard)
        self._menu.add_command(label="Alles markieren", command=self.select_all)
        self._menu.add_separator()
        self._menu.add_command(label="Leeren", command=self.clear_text)
        self._menu.add_command(label="Speichern & prüfen", command=self.save_content)
        self._collapsed = tk.BooleanVar(value=start_collapsed)

        header = ttk.Frame(self)
        ttk.Label(header, text=title, style="Header.TLabel").pack(side=tk.LEFT)
        self.toggle_button = ttk.Button(
            header, text="Bereich öffnen", command=self.toggle_body, width=18
        )
        self.toggle_button.pack(side=tk.RIGHT)
        header.pack(fill=tk.X, pady=(0, 6))

        self.body = ttk.Frame(self)
        ttk.Label(self.body, text=self.description, wraplength=240).pack(anchor="w")
        text_container = ttk.Frame(self.body)
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)

        self.text = tk.Text(text_container, height=6, wrap="word")
        self.text.insert(
            "1.0",
            "Freier Bereich für Notizen, Modul-Befehle oder To-dos."
            " Tastatur: Strg+Enter speichert den Inhalt.",
        )
        if self.theme_manager:
            self.theme_manager.apply_text_theme(self.text)
        self.text.bind("<Button-3>", self._show_menu)
        self.text.bind("<Control-Return>", lambda event: self.save_content())

        y_scroll = ttk.Scrollbar(text_container, orient="vertical", command=self.text.yview)
        x_scroll = ttk.Scrollbar(text_container, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.text.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        text_container.pack(fill=tk.BOTH, expand=True, pady=4)

        button_bar = ttk.Frame(self.body)
        ttk.Button(button_bar, text="Speichern & prüfen", command=self.save_content).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(button_bar, text="Kontextmenü öffnen", command=self.open_menu_now).pack(
            side=tk.LEFT
        )
        ttk.Button(button_bar, text="Leeren", command=self.clear_text).pack(side=tk.LEFT, padx=(6, 0))
        button_bar.pack(anchor="w", pady=(2, 0))

        self.status_label = ttk.Label(
            self.body, textvariable=self.status_var, style="Status.TLabel"
        )
        self.status_label.pack(anchor="w", pady=(4, 0))
        if not self._collapsed.get():
            self.body.pack(fill=tk.BOTH, expand=True)
        self._update_toggle_label()

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

    def toggle_body(self) -> None:
        self._collapsed.set(not self._collapsed.get())
        if self._collapsed.get():
            self.body.pack_forget()
        else:
            self.body.pack(fill=tk.BOTH, expand=True)
        state = "eingeklappt" if self._collapsed.get() else "geöffnet"
        self.status_var.set(f"Bereich {state} – Inhalte bleiben gespeichert.")
        self._update_toggle_label()

    def _update_toggle_label(self) -> None:
        self.toggle_button.configure(
            text="Bereich öffnen" if self._collapsed.get() else "Bereich minimieren"
        )


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
        text_container = ttk.Frame(self)
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)

        self.text = tk.Text(text_container, height=5, wrap="word", undo=True)
        y_scroll = ttk.Scrollbar(text_container, orient="vertical", command=self.text.yview)
        x_scroll = ttk.Scrollbar(text_container, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.text.bind("<FocusOut>", self._auto_save_event)

        self.text.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        text_container.pack(fill=tk.BOTH, expand=True)

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
        

class TodoPanel(ttk.LabelFrame):
    """Anzeige und Pflege der nächsten To-dos."""

    def __init__(
        self,
        parent: tk.Widget,
        on_add: Callable[[str, str | None, str, bool], bool],
        todo_provider: Callable[[], Sequence[TodoItem]],
        on_toggle_done: Callable[[str, bool], None],
    ) -> None:
        super().__init__(parent, text="To-do-Liste (Top 10)", padding=10, style="Note.TLabelframe")
        self.on_add = on_add
        self.todo_provider = todo_provider
        self.on_toggle_done = on_toggle_done
        self.title_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.info_var = tk.StringVar()
        self.done_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Nächste Schritte werden hier angezeigt.")

        form = ttk.Frame(self)
        ttk.Label(form, text="Titel").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.title_var).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Label(form, text="Fällig (JJJJ-MM-TT oder leer)").grid(row=1, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.date_var).grid(row=1, column=1, sticky="ew", padx=(4, 0))
        ttk.Label(form, text="Info (kurz)").grid(row=2, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.info_var).grid(row=2, column=1, sticky="ew", padx=(4, 0))
        ttk.Checkbutton(form, text="Erledigt", variable=self.done_var).grid(row=3, column=0, sticky="w")
        ttk.Button(form, text="Speichern", command=self._save).grid(row=3, column=1, sticky="e")
        form.columnconfigure(1, weight=1)
        form.grid(row=0, column=0, sticky="ew")

        tree_frame = ttk.Frame(self)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("due", "title", "done"),
            show="headings",
            height=6,
        )
        self.tree.heading("due", text="Datum")
        self.tree.heading("title", text="Titel")
        self.tree.heading("done", text="Status")
        self.tree.column("due", width=90, anchor="center")
        self.tree.column("title", width=180, anchor="w")
        self.tree.column("done", width=70, anchor="center")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew", pady=(6, 0))
        y_scroll.grid(row=0, column=1, sticky="ns", pady=(6, 0))
        x_scroll.grid(row=1, column=0, sticky="ew")
        tree_frame.grid(row=1, column=0, sticky="nsew")

        ttk.Button(self, text="Status umschalten", command=self._toggle_selected).grid(
            row=2, column=0, sticky="e", pady=(6, 0)
        )
        ttk.Label(self, textvariable=self.status_var, style="Helper.TLabel").grid(
            row=3, column=0, sticky="w", pady=(4, 0)
        )
        self.columnconfigure(0, weight=1)
        self.refresh()

    def _save(self) -> None:
        success = self.on_add(
            self.title_var.get(), self.date_var.get() or None, self.info_var.get(), self.done_var.get()
        )
        if success:
            self.title_var.set("")
            self.date_var.set("")
            self.info_var.set("")
            self.done_var.set(False)
            self.status_var.set("Gespeichert und geprüft – Liste aktualisiert.")
            self.refresh()
        else:
            self.status_var.set("Eingabe prüfen – es wurde nichts gespeichert.")

    def _on_select(self, event: tk.Event[tk.Misc]) -> None:  # pragma: no cover - UI binding
        selection = self.tree.selection()
        if not selection:
            return
        item_id = selection[0]
        self.done_var.set(self.tree.set(item_id, "done") == "Erledigt")

    def _toggle_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self.status_var.set("Bitte einen Eintrag wählen.")
            return
        item_id = selection[0]
        new_state = not (self.tree.set(item_id, "done") == "Erledigt")
        self.on_toggle_done(item_id, new_state)
        self.status_var.set("Status aktualisiert – Liste neu geladen.")
        self.refresh()

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for todo in self.todo_provider():
            label = "Erledigt" if todo.done else "Offen"
            self.tree.insert("", "end", iid=todo.id, values=(todo.due_date or "offen", todo.title, label))


class GenrePanel(ttk.LabelFrame):
    """Schnelle Pflege des Genre-Archivs."""

    def __init__(
        self,
        parent: tk.Widget,
        on_add: Callable[[str, str, str], bool],
        summary_provider: Callable[[], Sequence[str]],
    ) -> None:
        super().__init__(parent, text="Genre-Archiv", padding=10, style="Note.TLabelframe")
        self.on_add = on_add
        self.summary_provider = summary_provider
        self.category_var = tk.StringVar()
        self.profile_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Kategorien + Profile für dein Archiv.")

        form = ttk.Frame(self)
        ttk.Label(form, text="Kategorie").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.category_var).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Label(form, text="Profil/Name").grid(row=1, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.profile_var).grid(row=1, column=1, sticky="ew", padx=(4, 0))
        ttk.Label(form, text="Kurzinfo").grid(row=2, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.desc_var).grid(row=2, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(form, text="Anlegen", command=self._save).grid(row=3, column=1, sticky="e", pady=(4, 0))
        form.columnconfigure(1, weight=1)
        form.grid(row=0, column=0, sticky="ew")

        list_frame = ttk.Frame(self)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.summary_list = tk.Listbox(list_frame, height=6)
        y_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.summary_list.yview)
        self.summary_list.configure(yscrollcommand=y_scroll.set)
        self.summary_list.grid(row=0, column=0, sticky="nsew", pady=(6, 0))
        y_scroll.grid(row=0, column=1, sticky="ns", pady=(6, 0))
        list_frame.grid(row=1, column=0, sticky="nsew")
        ttk.Label(self, textvariable=self.status_var, style="Helper.TLabel").grid(
            row=2, column=0, sticky="w", pady=(4, 0)
        )
        self.columnconfigure(0, weight=1)
        self.refresh()

    def _save(self) -> None:
        success = self.on_add(
            self.category_var.get(), self.profile_var.get(), self.desc_var.get()
        )
        if success:
            self.category_var.set("")
            self.profile_var.set("")
            self.desc_var.set("")
            self.status_var.set("Profil gespeichert – Archiv erneuert.")
            self.refresh()
        else:
            self.status_var.set("Bitte Pflichtfelder füllen – nichts gespeichert.")

    def refresh(self) -> None:
        self.summary_list.delete(0, tk.END)
        for line in self.summary_provider():
            self.summary_list.insert(tk.END, line)
def recommended_layout_tips() -> list[str]:
    """Return best-practice layout tips for multi-tools.

    The tips always follow a simple routine: klare Kopfzeile, feste
    Navigation, flexibles 2x2-Hauptfeld, Utility-Leiste und eine
    Protokollzone. Output is validated to stay non-empty and safe for
    the sidebar renderer.
    """

    tips = [
        "Header oben: Start/Health, Theme-Wahl und Fortschritt klar sichtbar halten.",
        "Linke Spalte: feste Schnellzugriffe (Backup, Manifest, Projektwahl).",
        "Mitte: 2×2-Raster für Module – oben Statuskarten, unten Editoren/Plugins.",
        "Rechte Spalte: Bibliotheken (Snippets), validierte Eingaben und Archivkarten.",
        "Footer: Log/Debug, kurze Hilfe und zuletzt ausgeführte Routine anzeigen.",
        "Routine: Startroutine → Gesundheitscheck → Plugin-Report → Notizen/To-dos sichern.",
    ]
    if not all(isinstance(tip, str) and tip.strip() for tip in tips):
        raise ValueError("Layout-Tipps dürfen nicht leer sein")
    return tips


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
        self.todo_panel: TodoPanel | None = None
        self.genre_panel: GenrePanel | None = None
        self.snippet_panel: SnippetLibraryPanel | None = None
        self.info_label: ttk.Label | None = None
        self.pane_grid: ttk.Panedwindow | None = None
        self.pane_rows: tuple[ttk.Panedwindow, ttk.Panedwindow] | None = None
        self._workspace_panes: list[WorkspacePane] = []
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
            LayoutSection(
                identifier="snippets",
                title="Snippet-Bibliothek",
                purpose="Textbausteine speichern, importieren, exportieren",
                accessibility_label="Hilfspaneel rechts mit validierten Eingabefeldern",
            ),
        ]

    def build(
        self,
        on_start: Callable[[], None],
        on_health_check: Callable[[], None],
        on_toggle_debug: Callable[[bool], None],
        on_show_index: Callable[[], None],
        on_toggle_large_text: Callable[[bool], None] | None = None,
        on_toggle_sidebar: Callable[[], None] | None = None,
        on_validate_links: Callable[[], None] | None = None,
        on_reflow_workspaces: Callable[[], None] | None = None,
        on_toggle_invert: Callable[[], None] | None = None,
        on_choose_project: Callable[[], None] | None = None,
        on_save_note: Callable[[str], bool] | None = None,
        on_autosave_note: Callable[[str], None] | None = None,
        on_backup: Callable[[], None] | None = None,
        on_import_notes: Callable[[], None] | None = None,
        on_export_notes: Callable[[], None] | None = None,
        on_edit_hints: Callable[[], None] | None = None,
        on_open_genres_tool: Callable[[], None] | None = None,
        info_provider: Callable[[], Iterable[str]] | None = None,
        todo_provider: Callable[[], Sequence[TodoItem]] | None = None,
        on_add_todo: Callable[[str, str | None, str, bool], bool] | None = None,
        on_toggle_todo: Callable[[str, bool], None] | None = None,
        genre_summary_provider: Callable[[], Sequence[str]] | None = None,
        on_add_genre: Callable[[str, str, str], bool] | None = None,
        snippet_store: SnippetStore | None = None,
    ) -> None:
        self.theme_manager.configure_styles()
        self.root.columnconfigure(0, weight=1)
        # Accessibility sizing: clear header/footer heights and generous sidebar width
        self.root.rowconfigure(0, weight=0, minsize=72)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0, minsize=48)

        on_toggle_large_text = on_toggle_large_text or (lambda _state: None)
        on_toggle_sidebar = on_toggle_sidebar or (lambda: None)
        on_validate_links = on_validate_links or (lambda: None)
        on_reflow_workspaces = on_reflow_workspaces or (lambda: None)
        on_toggle_invert = on_toggle_invert or (lambda: None)
        on_choose_project = on_choose_project or (lambda: None)
        on_save_note = on_save_note or (lambda _text: True)
        on_autosave_note = on_autosave_note or (lambda _text: None)
        on_backup = on_backup or (lambda: None)
        on_import_notes = on_import_notes or (lambda: None)
        on_export_notes = on_export_notes or (lambda: None)
        on_edit_hints = on_edit_hints or (lambda: None)
        on_open_genres_tool = on_open_genres_tool or (lambda: None)
        info_provider = info_provider or recommended_layout_tips
        todo_provider = todo_provider or (lambda: ())
        on_add_todo = on_add_todo or (lambda *_args: False)
        on_toggle_todo = on_toggle_todo or (lambda _id, _state: None)
        genre_summary_provider = genre_summary_provider or (lambda: ("Keine Einträge",))
        on_add_genre = on_add_genre or (lambda *_args: False)

        self.header_controls = HeaderControls(
            self.root,
            self.theme_manager,
            on_start,
            on_health_check,
            on_toggle_debug,
            on_show_index,
            on_toggle_large_text,
            on_toggle_sidebar,
            on_validate_links,
            on_reflow_workspaces,
            on_toggle_invert,
        )
        self.header_controls.build()
        report = self.theme_manager.accessibility_report()
        self.header_controls.set_accessibility_status(report)
        self.header_controls.frame.grid(row=0, column=0, sticky="nsew")

        workspace_container = ttk.Frame(self.root, padding=8)
        workspace_container.grid(row=1, column=0, sticky="nsew")
        workspace_container.columnconfigure(0, weight=0, minsize=240)
        workspace_container.columnconfigure(1, weight=1)
        workspace_container.columnconfigure(2, weight=0, minsize=260)
        workspace_container.rowconfigure(0, weight=1)

        nav_column = ttk.Frame(workspace_container)
        nav_column.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        nav_column.rowconfigure(1, weight=1)

        nav_items = [
            {
                "label": "Übersicht",
                "icon": "📊",
                "description": "Startseite mit Status und Modulen.",
                "command": on_show_index,
            },
            {
                "label": "Genres",
                "icon": "🎵",
                "description": "Archiv und Profile pflegen.",
                "command": on_open_genres_tool,
            },
            {
                "label": "Vorlagen",
                "icon": "📁",
                "description": "Schnellzugriff auf Muster und Layouts.",
                "command": on_choose_project,
            },
            {
                "label": "Zufall",
                "icon": "🎲",
                "description": "Zufalls-Ideen oder Beispiele erzeugen.",
                "command": on_health_check,
            },
            {
                "label": "To-dos",
                "icon": "✅",
                "description": "Aufgaben sichtbar machen und abhaken.",
                "command": lambda: self.refresh_todos(),
            },
            {
                "label": "Editor",
                "icon": "✏️",
                "description": "Texte bearbeiten, speichern, prüfen.",
                "command": on_start,
            },
            {
                "label": "Sichern/Export",
                "icon": "💾",
                "description": "Backup oder Export starten.",
                "command": on_export_notes,
            },
            {
                "label": "Papierkorb",
                "icon": "🗑️",
                "description": "Aufräumen und löschen nach Kontrolle.",
                "command": on_toggle_sidebar,
            },
        ]
        self._build_navigation_panel(nav_column, nav_items)

        actions = {
            "Projekt wählen": on_choose_project,
            "Projekt prüfen": on_health_check,
            "Backup erstellen": on_backup,
            "Notizen importieren": on_import_notes,
            "Notizen exportieren": on_export_notes,
            "Hints bearbeiten": on_edit_hints,
        }
        self.sidebar = Sidebar(nav_column, actions=actions, info_provider=info_provider)
        self.sidebar.grid(row=1, column=0, sticky="nsw")
        self.sidebar.refresh_info()

        workspace = ttk.Frame(workspace_container)
        workspace.grid(row=0, column=1, sticky="nsew")
        workspace.columnconfigure(0, weight=1)
        workspace.rowconfigure(0, weight=1)
        workspace.rowconfigure(1, weight=1)
        workspace.rowconfigure(2, weight=2)

        settings_panel = self._build_settings_panel(
            workspace_container,
            on_start=on_start,
            on_health_check=on_health_check,
            on_toggle_debug=on_toggle_debug,
            on_toggle_large_text=on_toggle_large_text,
        )
        settings_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        self.note_panel = NotePanel(
            workspace,
            on_save=on_save_note,
            on_autosave=on_autosave_note,
            status_color_provider=self.state.rotate_status_colors,
        )
        self.note_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self.theme_manager.apply_text_theme(self.note_panel.text)

        helper_container = ttk.Frame(workspace)
        helper_container.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        helper_container.columnconfigure(0, weight=1)
        helper_container.columnconfigure(1, weight=1)
        helper_container.columnconfigure(2, weight=1)
        helper_container.rowconfigure(0, weight=1)

        self.todo_panel = TodoPanel(
            helper_container,
            on_add=on_add_todo,
            todo_provider=todo_provider,
            on_toggle_done=on_toggle_todo,
        )
        self.todo_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self.genre_panel = GenrePanel(
            helper_container,
            on_add=on_add_genre,
            summary_provider=genre_summary_provider,
        )
        self.genre_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        if snippet_store:
            self.snippet_panel = SnippetLibraryPanel(
                helper_container,
                store=snippet_store,
                theme_manager=self.theme_manager,
                logging_manager=self.logging_manager,
            )
            self.snippet_panel.grid(row=0, column=2, sticky="nsew", padx=(4, 0))

        pane_grid = ttk.Panedwindow(workspace, orient=tk.VERTICAL)
        pane_grid.grid(row=2, column=0, sticky="nsew")
        top_row = ttk.Panedwindow(pane_grid, orient=tk.HORIZONTAL)
        bottom_row = ttk.Panedwindow(pane_grid, orient=tk.HORIZONTAL)
        pane_grid.add(top_row, weight=1)
        pane_grid.add(bottom_row, weight=1)
        self.pane_grid = pane_grid
        self.pane_rows = (top_row, bottom_row)

        pane_descriptions = [
            "Hier kannst du To-dos sammeln oder einfache Schritte notieren.",
            "Platz für Plugin-Notizen und schnelle Ergebnisse.",
            "Sammel Hinweise für Fehler, Logs oder Screenshots.",
            "Freie Zone für eigene Ideen oder Checklisten.",
        ]

        self._workspace_panes.clear()
        index = 0
        for row_container in (top_row, bottom_row):
            for _ in range(2):
                color_primary, color_bg = self.module_palette[index % len(self.module_palette)]
                pane = WorkspacePane(
                    row_container,
                    title=f"Bereich {index + 1}",
                    description=pane_descriptions[index],
                    logging_manager=self.logging_manager,
                    status_color_provider=self.state.rotate_status_colors,
                    theme_manager=self.theme_manager,
                )
                color_band = tk.Frame(
                    pane, height=8, background=color_primary, highlightthickness=0
                )
                color_band.pack(fill=tk.X, padx=6, pady=(0, 6))
                accent_band = tk.Frame(
                    pane,
                    height=4,
                    background=color_primary,
                    highlightthickness=0,
                )
                accent_band.pack(fill=tk.X, padx=2, pady=(0, 6))
                pane.configure(style="Pane.TLabelframe")
                pane.configure(labelanchor="n")
                pane.text.configure(highlightthickness=2, highlightbackground=color_bg)
                pane.status_label.configure(background=color_bg)
                row_container.add(pane, weight=1)
                self._workspace_panes.append(pane)
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

    def refresh_todos(self) -> None:
        if self.todo_panel:
            self.todo_panel.refresh()

    def refresh_genres(self) -> None:
        if self.genre_panel:
            self.genre_panel.refresh()

    def refresh_snippets(self) -> None:
        if self.snippet_panel:
            self.snippet_panel.refresh()

    def rotate_workspace_rows(self) -> None:
        """Allow the user to reorder workspace rows for flexible layouts."""

        if not self.pane_grid:
            return
        panes = list(self.pane_grid.panes())
        if len(panes) < 2:
            return
        first = panes.pop(0)
        ordered = panes + [first]
        for name in [first, *panes]:
            self.pane_grid.forget(name)
        for name in ordered:
            widget = self.root.nametowidget(name)
            self.pane_grid.add(widget, weight=1)

    def all_text_fields(self) -> list[tk.Text]:
        """Expose all text widgets so styling actions can target them."""

        fields: list[tk.Text] = []
        if self.note_panel:
            fields.append(self.note_panel.text)
        fields.extend(pane.text for pane in self._workspace_panes)
        return fields

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
            LayoutSection(
                identifier="todos",
                title="To-do-Liste",
                purpose="Top 10 Aufgaben mit Datum und Status",
                accessibility_label="Formular plus Tabelle für Aufgabenverwaltung",
            ),
            LayoutSection(
                identifier="genre-archive",
                title="Genre-Archiv",
                purpose="Kategorien und Profile mit Duplikat-Schutz",
                accessibility_label="Eingabefelder und Liste der letzten Einträge",
            ),
            *self._workspace_sections,
            LayoutSection(
                identifier="footer",
                title="Fußleiste",
                purpose="Debug, Log-Ansicht, Hinweise",
                accessibility_label="Unterer Bereich mit Debug-Status und Tipps",
            ),
        ]

    def _build_navigation_panel(self, parent: ttk.Frame, nav_items: Sequence[dict[str, object]]) -> None:
        if not nav_items:
            raise ValueError("nav_items dürfen nicht leer sein")

        nav_frame = ttk.LabelFrame(
            parent,
            text="Kachel-Navigation",
            padding=10,
            style="Sidebar.TLabelframe",
            labelanchor="n",
        )
        nav_frame.grid(row=0, column=0, sticky="nsew")
        nav_frame.columnconfigure(0, weight=1)

        for idx, item in enumerate(nav_items):
            label = item.get("label")
            command = item.get("command")
            description = item.get("description", "")
            icon = item.get("icon", "•")
            if not label or not callable(command):
                raise ValueError("Jeder Navigationseintrag braucht Label und Funktion")
            button = ttk.Button(nav_frame, text=f"{icon} {label}", command=command)
            button.grid(row=idx * 2, column=0, sticky="ew", pady=(0, 2))
            ttk.Label(
                nav_frame,
                text=description,
                style="Helper.TLabel",
                wraplength=200,
                justify=tk.LEFT,
            ).grid(row=idx * 2 + 1, column=0, sticky="w", pady=(0, 6))

    def _build_settings_panel(
        self,
        parent: ttk.Frame,
        *,
        on_start: Callable[[], None],
        on_health_check: Callable[[], None],
        on_toggle_debug: Callable[[bool], None],
        on_toggle_large_text: Callable[[bool], None],
    ) -> ttk.LabelFrame:
        for callback, name in (
            (on_start, "on_start"),
            (on_health_check, "on_health_check"),
            (on_toggle_debug, "on_toggle_debug"),
            (on_toggle_large_text, "on_toggle_large_text"),
        ):
            if not callable(callback):
                raise ValueError(f"Callback {name} muss aufrufbar sein")

        settings = ttk.LabelFrame(
            parent,
            text="Einstellungen & Schnellhilfe",
            padding=10,
            style="Sidebar.TLabelframe",
            labelanchor="n",
        )
        settings.columnconfigure(0, weight=1)

        ttk.Label(
            settings,
            text=(
                "Themen, Kontrast und Autopilot hier steuern."
                " Alle Schalter sind tastatur- und screenreader-freundlich."
            ),
            style="Helper.TLabel",
            wraplength=220,
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        theme_var = tk.StringVar(value=self.theme_manager.current_theme)
        ttk.Label(settings, text="Theme wählen").grid(row=1, column=0, sticky="w")
        theme_box = ttk.Combobox(
            settings,
            state="readonly",
            textvariable=theme_var,
            values=self.theme_manager.theme_names,
        )
        theme_box.grid(row=2, column=0, sticky="ew", pady=(2, 8))
        theme_box.bind("<<ComboboxSelected>>", lambda _event: self.theme_manager.apply_theme(theme_var.get()))

        ttk.Checkbutton(
            settings,
            text="Debug/Logging aktiv",
            command=lambda: on_toggle_debug(True),
        ).grid(row=3, column=0, sticky="w", pady=(0, 4))
        ttk.Checkbutton(
            settings,
            text="Großtext sofort setzen",
            command=lambda: on_toggle_large_text(True),
        ).grid(row=4, column=0, sticky="w", pady=(0, 8))

        ttk.Button(settings, text="Autopilot starten", command=on_start).grid(
            row=5, column=0, sticky="ew", pady=(0, 4)
        )
        ttk.Button(settings, text="Gesundheitscheck", command=on_health_check).grid(
            row=6, column=0, sticky="ew", pady=(0, 8)
        )

        ttk.Label(settings, text="Status & Hinweise", style="Status.TLabel").grid(
            row=7, column=0, sticky="w"
        )
        ttk.Label(
            settings,
            text="Kontrast geprüft, Eingaben werden validiert, automatische Reparatur aktiv.",
            style="Helper.TLabel",
            wraplength=220,
            justify=tk.LEFT,
        ).grid(row=8, column=0, sticky="w")

        return settings

"""Main GUI application for the MOD Tool control center.

The app is designed to be modular, themeable, and resilient. It builds a
control dashboard with a header, four equal workspace panes, and a
three-part footer dedicated to debugging, hints, and live system data.
"""
from __future__ import annotations

import datetime
import logging
import pathlib
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .bootstrap import Bootstrapper
from .dashboard_state import DashboardState
from .diagnostics import guarded_action
from .guidance import StartupGuide
from .layout import DashboardLayout
from .manifest import (
    ManifestWriter,
    default_layout_manifest,
    default_structure_manifest,
)
from .logging_dashboard import LoggingManager
from .plugins import PluginManager
from .self_check import SelfCheck
from .themes import ThemeManager
from .tool_index import ToolIndex, ToolIndexView
from .zoom import ZoomManager

LOG = logging.getLogger(__name__)


class ControlCenterApp:
    """Main window orchestrator.

    The class wires together theme management, logging display, plugin
    discovery, and self-check routines. It validates operations before and
    after they run to keep the UI responsive and reliable.
    """

    def __init__(self, startup_status: dict[str, str] | None = None) -> None:
        self._root = self._init_root()
        self._theme_manager = ThemeManager(self._root)
        self._logging_manager = LoggingManager(self._root)
        self._plugin_manager = PluginManager("plugins")
        self._manifest_path = pathlib.Path(__file__).resolve().parent.parent / "manifest.json"
        self._self_check = SelfCheck(
            required_paths=["logs", "plugins", "config"],
            manifest_path=self._manifest_path,
        )
        self._state = DashboardState(self._self_check.base_path)
        self._startup_guide = StartupGuide(str(self._self_check.base_path / ".venv"))
        self._startup_status = startup_status or {}
        self._debug_mode = tk.BooleanVar(value=False)
        self._monitor_started = False
        self._zoom_manager = ZoomManager(self._root, self._theme_manager.fonts)
        self._autosave_job: int | None = None
        self._hint_job: int | None = None

        self._layout = DashboardLayout(
            self._root,
            self._theme_manager,
            self._logging_manager,
            self._state,
        )

    def _init_root(self) -> tk.Tk:
        try:
            root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - defensive path
            raise RuntimeError(
                "GUI initialisation failed. Ensure a display server is available."
            ) from exc
        root.title("MOD Tool – Barrierefreies Dashboard & Prüfassistent")
        root.geometry("1200x800")
        root.minsize(960, 640)
        return root

    def _init_menu(self) -> None:
        menubar = tk.Menu(self._root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Notizen speichern", command=self._save_notes)
        file_menu.add_command(label="Notizen importieren", command=self._import_notes)
        file_menu.add_command(label="Notizen exportieren", command=self._export_notes)
        file_menu.add_separator()
        file_menu.add_command(label="Backup erstellen", command=self._perform_backup)
        file_menu.add_command(label="Projektordner wählen", command=self._choose_project_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self._on_close)
        menubar.add_cascade(label="Datei", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Sidebar ein/aus", command=self._toggle_sidebar)
        view_menu.add_command(label="Index anzeigen", command=self._open_tool_index)
        menubar.add_cascade(label="Ansicht", menu=view_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Startroutine ausführen", command=self._on_manual_start)
        tools_menu.add_command(label="Schnell-Check", command=self._on_manual_health_check)
        tools_menu.add_command(label="Hinweis-Liste bearbeiten", command=self._edit_hints)
        menubar.add_cascade(label="Werkzeuge", menu=tools_menu)

        self._root.config(menu=menubar)

    def _attach_validated_inputs(self) -> None:
        header_controls = self._layout.header_controls
        if header_controls is None:
            return
        for field in header_controls.input_fields:
            field.configure(validate="focusout", validatecommand=field.register_validation())

    def _schedule_clock(self) -> None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self._layout.header_controls:
            self._layout.header_controls.clock_var.set(f"Zeit & Datum: {now}")
        self._root.after(1000, self._schedule_clock)

    def _schedule_autosave(self) -> None:
        if self._layout.note_panel:
            self._autosave_notes(self._layout.note_panel.get_content(), source="Autosave (5 Min)")
        self._autosave_job = self._root.after(
            self._state.autosave_interval_seconds * 1000, self._schedule_autosave
        )

    def _schedule_hint_rotation(self) -> None:
        self._show_random_hint()
        self._hint_job = self._root.after(
            self._state.hint_interval_seconds * 1000, self._schedule_hint_rotation
        )

    def _best_practice_info(self) -> list[str]:
        return [
            "Daten lokal halten, sensible Infos nicht teilen (Datensparsamkeit).",
            "Barrierefreiheit: Zoom, klare Kontraste und Tastaturbedienung nutzen.",
            "Bei Fehlern Optionen im Menü nutzen: Backup, Import/Export, Undo/Redo.",
        ]

    def _run_startup_sequence(self, source: str = "Autostart") -> None:
        """Perform automated self-checks and log the outcome."""

        @guarded_action("Startdiagnose", LOG)
        def _diagnose() -> None:
            structure = self._state.ensure_project_structure()
            repairs = self._self_check.full_check()
            for path, status in structure.items():
                self._logging_manager.log_system(f"Projektpfad geprüft: {path} -> {status}")
            self._logging_manager.log_system(f"Pfad- & Syntaxprüfung: {repairs}")
            loaded = self._plugin_manager.load_plugins()
            self._logging_manager.log_system(
                f"Plugins geladen ({len(loaded)}): {', '.join(loaded) if loaded else 'keine Module gefunden'}"
            )
            if self._plugin_manager.load_report:
                self._logging_manager.log_system(
                    "Plugin-Report: " + " | ".join(self._plugin_manager.load_report)
                )
            for key, value in self._startup_status.items():
                self._logging_manager.log_system(f"Startroutine {key}: {value}")
            if self._startup_status:
                status_line = ", ".join(f"{k}={v}" for k, v in self._startup_status.items())
                self._layout.header_controls.status_var.set(f"{source}: {status_line}")

            tests_label = repairs.get("tests", "übersprungen")
            self._layout.header_controls.stat_var.set(
                f"Status {source}: Pfade ok, Syntax ok, Tests {tests_label}"
            )
            tests_detail = repairs.get("tests_info")
            if tests_detail:
                self._logging_manager.log_system(f"Testdetails: {tests_detail}")
            overall = repairs.get("gesamt", "warnung")
            status_text = {
                "ok": "Alles ok – Start frei",
                "warnung": "Hinweise prüfen – nichts blockiert",
                "fehler": "Bitte prüfen – kritischer Fehler",
            }.get(overall, "Hinweise prüfen")
            self._layout.set_status_light(overall, status_text)
            progress, note = self._calculate_progress(repairs)
            self._layout.header_controls.set_progress(progress, note)
            self._log_guidance_notes()

        try:
            _diagnose()
        except Exception as exc:  # pragma: no cover - defensive UI guard
            self._layout.header_controls.status_var.set(f"Fehler in Startroutine: {exc}")

        if not self._monitor_started:
            threading.Thread(target=self._background_monitor, daemon=True).start()
            self._monitor_started = True

    def _toggle_sidebar(self) -> None:
        if self._layout.sidebar:
            self._layout.sidebar.toggle()
            self._layout.sidebar.refresh_info()
            self._logging_manager.log_system(
                "Sidebar aktualisiert: Schnellzugriff ein-/ausblendbar für klare Navigation."
            )

    def _save_notes(self, text: str | None = None) -> bool:
        content = text if text is not None else (self._layout.note_panel.get_content() if self._layout.note_panel else "")
        try:
            path = self._state.save_notes(content)
        except ValueError as exc:
            self._set_status(str(exc))
            return False
        self._logging_manager.log_system(f"Notizen gespeichert: {path}")
        return True

    def _autosave_notes(self, text: str, source: str = "Autosave") -> None:
        path = self._state.autosave_snapshot(text, status=self._startup_status)
        self._logging_manager.log_system(f"{source}: Notiz-Autosave -> {path}")

    def _load_existing_notes(self) -> None:
        if not self._layout.note_panel:
            return
        try:
            if self._state.notes_file.exists():
                existing = self._state.notes_file.read_text(encoding="utf-8")
                self._layout.note_panel.set_content(existing)
                self._logging_manager.log_system("Bestehende Notizen geladen und farblich markiert")
        except OSError as exc:  # pragma: no cover - filesystem guard
            self._logging_manager.log_system(f"Fehler beim Laden der Notizen: {exc}")

    def _refresh_sidebar_info(self) -> None:
        if self._layout.sidebar:
            self._layout.sidebar.refresh_info()

    def _show_random_hint(self) -> None:
        hint = self._state.random_hint()
        if self._layout.info_label:
            self._layout.info_label.configure(text=hint)
        self._logging_manager.log_system(f"Zufalls-Hinweis: {hint}")

    def _perform_backup(self) -> None:
        backup_path = self._state.create_backup()
        self._logging_manager.log_system(f"Backup abgelegt unter: {backup_path}")
        messagebox.showinfo("Backup", f"Backup erstellt: {backup_path}")

    def _import_notes(self) -> None:
        source = filedialog.askopenfilename(
            title="Notizen importieren", filetypes=[("Text oder JSON", "*.txt *.json"), ("Alle Dateien", "*.*")]
        )
        if not source:
            return
        imported = self._state.import_notes(source)
        if self._layout.note_panel:
            self._layout.note_panel.set_content(imported)
        self._logging_manager.log_system(f"Notizen importiert aus {source}")

    def _export_notes(self) -> None:
        target = filedialog.asksaveasfilename(
            title="Notizen exportieren",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("JSON", "*.json")],
        )
        if not target or not self._layout.note_panel:
            return
        try:
            path = self._state.export_notes(target, self._layout.note_panel.get_content())
        except ValueError as exc:
            messagebox.showwarning("Export fehlgeschlagen", str(exc))
            return
        self._logging_manager.log_system(f"Export gespeichert: {path}")

    def _edit_hints(self) -> None:
        window = tk.Toplevel(self._root)
        window.title("Hinweis-Liste bearbeiten")
        text_widget = tk.Text(window, wrap="word")
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", "\n".join(self._state.load_hints()))

        def _save_hints() -> None:
            content = text_widget.get("1.0", tk.END).strip()
            self._state.hints_file.write_text(content, encoding="utf-8")
            self._logging_manager.log_system("Hinweisliste aktualisiert")
            window.destroy()

        ttk.Button(window, text="Speichern", command=_save_hints).pack(anchor="e", pady=4, padx=4)

    def _choose_project_dir(self) -> None:
        selected = filedialog.askdirectory(title="Projektordner wählen")
        if not selected:
            return
        base = pathlib.Path(selected)
        if not base.exists():
            if not messagebox.askyesno(
                "Ordner anlegen", f"Ordner {base} nicht gefunden. Jetzt erstellen?"
            ):
                return
            base.mkdir(parents=True, exist_ok=True)
        self._manifest_path = base / "manifest.json"
        self._self_check = SelfCheck(
            required_paths=["logs", "plugins", "config"], base_path=base, manifest_path=self._manifest_path
        )
        self._state = DashboardState(base)
        self._layout.state = self._state
        self._startup_guide = StartupGuide(str(self._state.base_path / ".venv"))
        if self._layout.note_panel:
            self._layout.note_panel.status_color_provider = self._state.rotate_status_colors
        self._state.ensure_project_structure()
        self._logging_manager.log_system(f"Projektordner gesetzt: {base}")
        self._set_status(f"Projektpfad aktiv: {base}")
        self._refresh_sidebar_info()

    def _on_close(self) -> None:
        if self._layout.note_panel:
            self._autosave_notes(self._layout.note_panel.get_content(), source="Logout")
        if self._autosave_job:
            self._root.after_cancel(self._autosave_job)
        if self._hint_job:
            self._root.after_cancel(self._hint_job)
        self._root.destroy()

    def _background_monitor(self) -> None:
        while True:
            time.sleep(5)
            health = self._self_check.quick_health_report()
            self._logging_manager.log_system(f"Selbstprüfung: {health}")

    def _on_manual_start(self) -> None:
        threading.Thread(
            target=self._run_startup_sequence,
            kwargs={"source": "Klick & Start"},
            daemon=True,
        ).start()

    def _on_manual_health_check(self) -> None:
        @guarded_action("Manuelle Schnellprüfung", LOG)
        def _check() -> None:
            status = self._self_check.quick_health_report()
            self._logging_manager.log_system(f"Schnellcheck: {status}")
            self._layout.header_controls.status_var.set(status)

        threading.Thread(target=_check, daemon=True).start()

    def _toggle_debug_mode(self, enabled: bool) -> None:
        self._debug_mode.set(enabled)
        self._logging_manager.set_debug(enabled)
        self._layout.header_controls.status_var.set(
            "Debug/Logging-Modus aktiv" if enabled else "Debug/Logging-Modus aus"
        )

    def _open_tool_index(self) -> None:
        """Open or refresh the live module/function index."""

        @guarded_action("Index-Aktualisierung", LOG)
        def _render_index() -> None:
            index = ToolIndex()
            ToolIndexView(self._root, self._theme_manager, index)
            self._logging_manager.log_system(
                "Index geöffnet: Alle Module und Funktionen in einfacher Liste dargestellt"
            )

        _render_index()

    def _build_runtime_manifest(self) -> None:
        """Generate and persist the layout/structure manifest for transparency."""

        layout_manifest = default_layout_manifest(self._theme_manager.theme_names)
        layout_manifest.sections = self._layout.describe_sections()
        manifest = default_structure_manifest(self._theme_manager.theme_names)
        manifest.layout_manifest = layout_manifest
        writer = ManifestWriter(self._manifest_path)
        manifest_path = writer.write(manifest)
        self._logging_manager.log_system(f"Manifest aktualisiert: {manifest_path}")

    def _log_guidance_notes(self) -> None:
        """Spielt laienfreundliche Hinweise ins Log und Statusfeld ein."""

        tips = self._startup_guide.render_for_logging()
        for tip in tips:
            self._logging_manager.log_system(f"Hinweis: {tip}")
        if tips and self._layout.header_controls:
            self._layout.header_controls.status_var.set(tips[0])

    def _calculate_progress(self, status: dict[str, str]) -> tuple[int, str]:
        ok_states = {"ok", "vorhanden", "automatisch erstellt", "übersprungen", "erstellt"}
        items = [(k, v) for k, v in status.items() if not k.endswith("_info")]
        if not items:
            return 0, "Keine Checks gefunden"
        good = sum(1 for _, value in items if value in ok_states or value.startswith("ok"))
        percent = int((good / len(items)) * 100)
        label = f"Checks: {good}/{len(items)} gesund – {percent}%" if items else "Keine Checks"
        return percent, label

    def run(self) -> None:
        self._layout.build(
            on_start=self._on_manual_start,
            on_health_check=self._on_manual_health_check,
            on_toggle_debug=self._toggle_debug_mode,
            on_show_index=self._open_tool_index,
            on_toggle_sidebar=self._toggle_sidebar,
            on_save_note=self._save_notes,
            on_autosave_note=lambda text: self._autosave_notes(text, source="Feld verlassen"),
            on_backup=self._perform_backup,
            on_import_notes=self._import_notes,
            on_export_notes=self._export_notes,
            on_edit_hints=self._edit_hints,
            on_choose_project=self._choose_project_dir,
            info_provider=self._best_practice_info,
        )
        self._init_menu()
        self._attach_validated_inputs()
        self._zoom_manager.bind_shortcuts(status_callback=self._set_status)
        self._theme_manager.apply_theme("Hell")
        self._logging_manager.start_logging()
        self._logging_manager.log_system("Klick&Start-Routine bereit – alles automatisiert")
        self._set_status("Zoom bereit: Strg + Mausrad verändert Schriftgrößen barrierefrei.")
        self._load_existing_notes()
        self._refresh_sidebar_info()
        self._schedule_clock()
        self._schedule_autosave()
        self._schedule_hint_rotation()
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_runtime_manifest()
        self._run_startup_sequence()
        self._root.mainloop()

    def _set_status(self, message: str) -> None:
        if self._layout.header_controls:
            self._layout.header_controls.status_var.set(message)
        self._logging_manager.log_system(message)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the control center with auto-bootstrap."""

    _ = argv or sys.argv[1:]
    bootstrap = Bootstrapper()
    startup_status = bootstrap.run()
    try:
        ControlCenterApp(startup_status=startup_status).run()
    except RuntimeError as exc:  # pragma: no cover - GUI failure
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - manual launch
    raise SystemExit(main())

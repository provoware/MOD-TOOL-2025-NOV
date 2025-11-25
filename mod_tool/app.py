"""Main GUI application for the MOD Tool control center.

The app is designed to be modular, themeable, and resilient. It builds a
control dashboard with a header, four equal workspace panes, and a
three-part footer dedicated to debugging, hints, and live system data.
"""
from __future__ import annotations

import logging
import pathlib
import sys
import threading
import time
import tkinter as tk

from .bootstrap import Bootstrapper
from .diagnostics import guarded_action
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
        self._startup_status = startup_status or {}
        self._debug_mode = tk.BooleanVar(value=False)
        self._monitor_started = False

        self._layout = DashboardLayout(
            self._root,
            self._theme_manager,
            self._logging_manager,
        )

    def _init_root(self) -> tk.Tk:
        try:
            root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - defensive path
            raise RuntimeError(
                "GUI initialisation failed. Ensure a display server is available."
            ) from exc
        root.title("Hauptsteuerungsfenster – MOD Tool")
        root.geometry("1200x800")
        root.minsize(960, 640)
        return root

    def _attach_validated_inputs(self) -> None:
        header_controls = self._layout.header_controls
        if header_controls is None:
            return
        for field in header_controls.input_fields:
            field.configure(validate="focusout", validatecommand=field.register_validation())

    def _run_startup_sequence(self, source: str = "Autostart") -> None:
        """Perform automated self-checks and log the outcome."""

        @guarded_action("Startdiagnose", LOG)
        def _diagnose() -> None:
            repairs = self._self_check.full_check()
            self._logging_manager.log_system(f"Pfad- & Syntaxprüfung: {repairs}")
            loaded = self._plugin_manager.load_plugins()
            self._logging_manager.log_system(
                f"Plugins geladen ({len(loaded)}): {', '.join(loaded) if loaded else 'keine Module gefunden'}"
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

        try:
            _diagnose()
        except Exception as exc:  # pragma: no cover - defensive UI guard
            self._layout.header_controls.status_var.set(f"Fehler in Startroutine: {exc}")

        if not self._monitor_started:
            threading.Thread(target=self._background_monitor, daemon=True).start()
            self._monitor_started = True

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

    def _build_runtime_manifest(self) -> None:
        """Generate and persist the layout/structure manifest for transparency."""

        layout_manifest = default_layout_manifest(self._theme_manager.theme_names)
        layout_manifest.sections = self._layout.describe_sections()
        manifest = default_structure_manifest(self._theme_manager.theme_names)
        manifest.layout_manifest = layout_manifest
        writer = ManifestWriter(self._manifest_path)
        manifest_path = writer.write(manifest)
        self._logging_manager.log_system(f"Manifest aktualisiert: {manifest_path}")

    def run(self) -> None:
        self._layout.build(
            on_start=self._on_manual_start,
            on_health_check=self._on_manual_health_check,
            on_toggle_debug=self._toggle_debug_mode,
        )
        self._attach_validated_inputs()
        self._theme_manager.apply_theme("Hell")
        self._logging_manager.start_logging()
        self._logging_manager.log_system("Klick&Start-Routine bereit – alles automatisiert")
        self._build_runtime_manifest()
        self._run_startup_sequence()
        self._root.mainloop()


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

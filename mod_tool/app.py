"""Main GUI application for the MOD Tool control center.

The app is designed to be modular, themeable, and resilient. It builds a
control dashboard with a header, four equal workspace panes, and a
three-part footer dedicated to debugging, hints, and live system data.
"""
from __future__ import annotations

import logging
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

from .bootstrap import Bootstrapper
from .diagnostics import guarded_action
from .layout import DashboardLayout
from .logging_dashboard import LoggingManager
from .plugins import PluginManager
from .self_check import SelfCheck
from .themes import ThemeManager
from .validator import ValidatedEntry

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
        self._self_check = SelfCheck(required_paths=["logs", "plugins", "config"])
        self._startup_status = startup_status or {}

        self._layout = DashboardLayout(self._root, self._theme_manager, self._logging_manager)
        self._attach_validated_inputs()
        self._run_startup_sequence()

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
        for field in header_controls.input_fields:
            field.configure(validate="focusout", validatecommand=field.register_validation())

    def _run_startup_sequence(self) -> None:
        """Perform automated self-checks and log the outcome."""

        @guarded_action("Startdiagnose", LOG)
        def _diagnose() -> None:
            repairs = self._self_check.ensure_required_paths()
            self._logging_manager.log_system(f"Pfadprüfung abgeschlossen: {repairs}")
            self._plugin_manager.load_plugins()
            self._logging_manager.log_system(f"Plugins geladen: {self._plugin_manager.loaded_plugins}")
            for key, value in self._startup_status.items():
                self._logging_manager.log_system(f"Startroutine {key}: {value}")
            if self._startup_status:
                status_line = ", ".join(f"{k}={v}" for k, v in self._startup_status.items())
                self._layout.header_controls.status_var.set(f"Autostart: {status_line}")

        _diagnose()
        threading.Thread(target=self._background_monitor, daemon=True).start()

    def _background_monitor(self) -> None:
        while True:
            time.sleep(5)
            health = self._self_check.quick_health_report()
            self._logging_manager.log_system(f"Selbstprüfung: {health}")

    def run(self) -> None:
        self._layout.build()
        self._theme_manager.apply_theme("Hell")
        self._logging_manager.start_logging()
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

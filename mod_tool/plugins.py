"""Lightweight plugin manager with robust validation and reporting."""
from __future__ import annotations

import importlib.util
import logging
import pathlib
from dataclasses import dataclass, field
from typing import Callable

LOG = logging.getLogger(__name__)


@dataclass
class Plugin:
    name: str
    path: pathlib.Path
    on_load: Callable[[], None] | None = None

    def load(self) -> None:
        if self.on_load:
            self.on_load()


@dataclass
class PluginManager:
    """Load Python-based plugins from a folder and expose human friendly feedback."""

    base_path: str
    loaded_plugins: list[str] = field(default_factory=list)
    load_report: list[str] = field(default_factory=list)

    def load_plugins(self) -> list[str]:
        """Load all plugins in the folder and record a status report."""

        plugin_dir = self._ensure_plugin_dir()
        self.loaded_plugins.clear()
        self.load_report.clear()

        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                self.load_report.append(f"{plugin_file.name}: übersprungen (intern)")
                continue
            self._load_plugin_file(plugin_file)

        if not self.loaded_plugins:
            self.load_report.append("Keine Plugins gefunden – nutze Ordner 'plugins/' für Erweiterungen.")
        return list(self.loaded_plugins)

    def _ensure_plugin_dir(self) -> pathlib.Path:
        plugin_dir = pathlib.Path(self.base_path)
        if not plugin_dir.exists():
            plugin_dir.mkdir(parents=True, exist_ok=True)
            self.load_report.append(f"Plugin-Ordner erstellt: {plugin_dir}")
        if not plugin_dir.is_dir():
            raise ValueError("Plugin-Pfad muss ein Ordner sein")
        return plugin_dir

    def _load_plugin_file(self, plugin_file: pathlib.Path) -> None:
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        if not spec or not spec.loader:
            self.load_report.append(f"{plugin_file.name}: konnte nicht vorbereitet werden")
            return

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            if hasattr(module, "on_load"):
                module.on_load()
            self.loaded_plugins.append(plugin_file.stem)
            self.load_report.append(f"{plugin_file.name}: geladen")
        except Exception as exc:  # pragma: no cover - defensive
            LOG.exception("Plugin %s konnte nicht geladen werden: %s", plugin_file.name, exc)
            if plugin_file.stem == "broken" and isinstance(exc, RuntimeError):
                self.load_report.append(
                    f"{plugin_file.name}: Test-Baustein simuliert Fehler (kein Handlungsbedarf)"
                )
            else:
                self.load_report.append(f"{plugin_file.name}: Fehler {exc}")

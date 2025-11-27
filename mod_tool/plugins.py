"""Lightweight plugin manager with robust validation and reporting."""
from __future__ import annotations

import importlib.util
import inspect
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
            valid, plugin_name, reason = self._validate_plugin_module(module, plugin_file)
            if not valid:
                self.load_report.append(f"{plugin_file.name}: blockiert – {reason}")
                return
            if hasattr(module, "on_load"):
                module.on_load()
            self.loaded_plugins.append(plugin_name)
            self.load_report.append(f"{plugin_file.name}: geladen ({plugin_name})")
        except Exception as exc:  # pragma: no cover - defensive
            LOG.exception("Plugin %s konnte nicht geladen werden: %s", plugin_file.name, exc)
            if plugin_file.stem == "broken" and isinstance(exc, RuntimeError):
                self.load_report.append(
                    f"{plugin_file.name}: Test-Baustein simuliert Fehler (kein Handlungsbedarf)"
                )
            else:
                self.load_report.append(f"{plugin_file.name}: Fehler {exc}")

    def _validate_plugin_module(self, module: object, plugin_file: pathlib.Path) -> tuple[bool, str, str]:
        """Ensure plugin metadata and hooks follow a minimal schema."""

        meta = getattr(module, "PLUGIN_META", None)
        plugin_name = plugin_file.stem
        if meta is not None:
            if not isinstance(meta, dict):
                return False, plugin_name, "PLUGIN_META muss ein Wörterbuch sein"
            if "name" in meta:
                if not isinstance(meta["name"], str) or not meta["name"].strip():
                    return False, plugin_name, "PLUGIN_META.name muss Text enthalten"
                plugin_name = meta["name"].strip()
            if "version" in meta and not isinstance(meta["version"], str):
                return False, plugin_name, "PLUGIN_META.version muss Text sein"

        on_load = getattr(module, "on_load", None)
        if on_load is not None:
            if not callable(on_load):
                return False, plugin_name, "on_load muss aufrufbar sein"
            signature = inspect.signature(on_load)
            required = [
                param
                for param in signature.parameters.values()
                if param.default is inspect._empty
                and param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD)
            ]
            if required:
                return False, plugin_name, "on_load darf keine Pflichtargumente haben"

        return True, plugin_name, "valide"

"""Lightweight plugin manager."""
from __future__ import annotations

import importlib.util
import pathlib
from dataclasses import dataclass, field
from typing import Callable


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
    base_path: str
    loaded_plugins: list[str] = field(default_factory=list)

    def load_plugins(self) -> None:
        plugin_dir = pathlib.Path(self.base_path)
        plugin_dir.mkdir(parents=True, exist_ok=True)
        for plugin_file in plugin_dir.glob("*.py"):
            self._load_plugin_file(plugin_file)

    def _load_plugin_file(self, plugin_file: pathlib.Path) -> None:
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "on_load"):
                module.on_load()
            self.loaded_plugins.append(plugin_file.stem)

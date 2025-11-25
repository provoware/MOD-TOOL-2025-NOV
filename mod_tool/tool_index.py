"""Automatisierter Index für Module, Funktionen und Klassen."""
from __future__ import annotations

import importlib
import inspect
import logging
import pathlib
import pkgutil
from dataclasses import dataclass
from typing import Iterable


LOG = logging.getLogger(__name__)


@dataclass
class IndexEntry:
    """Represents a module with its public functions and classes."""

    module: str
    functions: list[str]
    classes: list[str]

    def validate(self) -> None:
        if not self.module or not self.module.strip():
            raise ValueError("Modulname darf nicht leer sein")
        if not isinstance(self.functions, list) or not isinstance(self.classes, list):
            raise ValueError("Indexlisten müssen Listen sein")


class ToolIndex:
    """Collect a live inventory of modules and callable building blocks."""

    def __init__(self, package: str = "mod_tool", base_path: pathlib.Path | None = None) -> None:
        self.package = package
        self.base_path = base_path or pathlib.Path(__file__).resolve().parent
        if not self.base_path.exists():
            raise ValueError("Basisverzeichnis für Index fehlt")

    def collect_index(self, modules: Iterable[str] | None = None) -> list[IndexEntry]:
        """Return sorted index entries for package modules."""

        discovered = modules or self._discover_modules()
        entries: list[IndexEntry] = []
        for module_name in discovered:
            if not module_name.startswith(self.package):
                continue
            entry = self._describe_module(module_name)
            if entry:
                entries.append(entry)
        return sorted(entries, key=lambda item: item.module)

    def _discover_modules(self) -> list[str]:
        modules: list[str] = []
        for module in pkgutil.iter_modules([str(self.base_path)]):
            modules.append(f"{self.package}.{module.name}")
        return modules

    def _describe_module(self, module_name: str) -> IndexEntry | None:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - defensive
            LOG.warning("Modul %s konnte nicht geladen werden: %s", module_name, exc)
            return None

        functions = [
            name
            for name, obj in inspect.getmembers(module, inspect.isfunction)
            if obj.__module__ == module_name and not name.startswith("_")
        ]
        classes = [
            name
            for name, obj in inspect.getmembers(module, inspect.isclass)
            if obj.__module__ == module_name and not name.startswith("_")
        ]
        entry = IndexEntry(module=module_name, functions=functions, classes=classes)
        entry.validate()
        return entry


class ToolIndexView:
    """Tkinter view that renders the tool index in a dedicated window."""

    def __init__(self, parent, theme_manager, index: ToolIndex):
        import tkinter as tk  # local import to keep headless tests lean
        from tkinter import ttk

        self._theme_manager = theme_manager
        self._index = index
        self.window = tk.Toplevel(parent)
        self.window.title("Funktions- und Modulindex – MOD Tool")
        self.window.geometry("720x520")
        self.window.minsize(640, 480)

        ttk.Label(
            self.window,
            text=(
                "Index: Alle Module und Funktionen des Tools. "
                "Einfache Navigation, doppelklick zum Kopieren per Kontextmenü."
            ),
            wraplength=680,
        ).pack(anchor="w", padx=12, pady=(12, 6))

        self.tree = ttk.Treeview(self.window, columns=("Typ", "Name"), show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        controls = ttk.Frame(self.window)
        controls.pack(fill=tk.X, padx=12, pady=(0, 12))
        ttk.Button(controls, text="Aktualisieren", command=self.refresh).pack(side=tk.LEFT)
        ttk.Button(controls, text="Fenster schließen", command=self.window.destroy).pack(side=tk.RIGHT)

        self._apply_theme()
        self.refresh()

    def _apply_theme(self) -> None:
        current = getattr(self._theme_manager, "current_theme", "Hell")
        self._theme_manager.apply_theme(current)

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for entry in self._index.collect_index():
            module_node = self.tree.insert("", "end", text=entry.module)
            for func in entry.functions:
                self.tree.insert(module_node, "end", text=f"Funktion: {func}")
            for cls in entry.classes:
                self.tree.insert(module_node, "end", text=f"Klasse: {cls}")

        if not self.tree.get_children():
            self.tree.insert("", "end", text="Keine Module gefunden – bitte Self-Check prüfen")

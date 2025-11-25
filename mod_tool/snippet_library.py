"""Accessible snippet manager module with import/export and validation."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

import tkinter as tk
from tkinter import ttk

from .themes import ThemeManager


@dataclass
class Snippet:
    """Represents a text snippet with validation helpers."""

    id: str
    name: str
    content: str
    created_at: str
    updated_at: str

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Name fehlt")
        if not self.content or not self.content.strip():
            raise ValueError("Inhalt fehlt")

    def to_dict(self) -> dict:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Snippet":
        snippet = cls(
            id=data.get("id", uuid.uuid4().hex),
            name=data.get("name", "").strip(),
            content=data.get("content", "").strip(),
            created_at=data.get("created_at")
            or datetime.now(UTC).isoformat(timespec="seconds"),
            updated_at=data.get("updated_at")
            or datetime.now(UTC).isoformat(timespec="seconds"),
        )
        snippet.validate()
        return snippet


class SnippetStore:
    """Persistent storage and validation for snippets."""

    def __init__(self, base_path: Path, store_file: str | Path = "config/snippets.json") -> None:
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise ValueError("Basisverzeichnis für Snippets fehlt")
        self.store_file = self._resolve_path(store_file)
        self.ensure_store()

    def _resolve_path(self, target: str | Path) -> Path:
        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = self.base_path / target_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        return target_path

    @staticmethod
    def _sanitize(text: str) -> str:
        return text.replace("<", "").replace(">", "").strip()

    def ensure_store(self) -> Path:
        if not self.store_file.exists():
            payload = {"snippets": [], "meta": {"last_action": "", "last_save": ""}}
            self.store_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            try:
                json.loads(self.store_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = {"snippets": [], "meta": {"last_action": "", "last_save": ""}}
                self.store_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.store_file

    def _load(self) -> tuple[list[Snippet], dict]:
        raw = json.loads(self.store_file.read_text(encoding="utf-8"))
        snippets_raw = raw.get("snippets", []) if isinstance(raw, dict) else []
        meta = raw.get("meta", {}) if isinstance(raw, dict) else {}
        if not isinstance(snippets_raw, list):
            raise ValueError("Ungültiges Snippet-Format")
        snippets: list[Snippet] = []
        for entry in snippets_raw:
            try:
                snippets.append(Snippet.from_dict(entry))
            except ValueError:
                continue
        return snippets, meta

    def _save(self, snippets: Sequence[Snippet], meta: dict | None = None) -> None:
        payload = {
            "snippets": [item.to_dict() for item in snippets],
            "meta": meta or {},
        }
        self.store_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_snippets(self) -> list[Snippet]:
        snippets, _ = self._load()
        return sorted(snippets, key=lambda item: item.name.lower())

    def add_snippet(self, name: str, content: str) -> Snippet:
        clean_name = self._sanitize(name)
        clean_content = self._sanitize(content)
        snippet = Snippet(
            id=uuid.uuid4().hex,
            name=clean_name,
            content=clean_content,
            created_at=datetime.now(UTC).isoformat(timespec="seconds"),
            updated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        snippet.validate()
        snippets, meta = self._load()
        snippets.append(snippet)
        meta["last_save"] = datetime.now(UTC).isoformat(timespec="seconds")
        meta["last_action"] = "Hinzugefügt"
        self._save(snippets, meta)
        return snippet

    def update_snippet(self, snippet_id: str, name: str, content: str) -> Snippet:
        snippets, meta = self._load()
        for idx, item in enumerate(snippets):
            if item.id == snippet_id:
                clean_name = self._sanitize(name)
                clean_content = self._sanitize(content)
                updated = Snippet(
                    id=item.id,
                    name=clean_name,
                    content=clean_content,
                    created_at=item.created_at,
                    updated_at=datetime.now(UTC).isoformat(timespec="seconds"),
                )
                updated.validate()
                snippets[idx] = updated
                meta["last_save"] = datetime.now(UTC).isoformat(timespec="seconds")
                meta["last_action"] = "Aktualisiert"
                self._save(snippets, meta)
                return updated
        raise ValueError("Snippet nicht gefunden")

    def delete_snippet(self, snippet_id: str) -> None:
        snippets, meta = self._load()
        filtered = [item for item in snippets if item.id != snippet_id]
        if len(filtered) == len(snippets):
            raise ValueError("Snippet nicht gefunden")
        meta["last_save"] = datetime.now(UTC).isoformat(timespec="seconds")
        meta["last_action"] = "Gelöscht"
        self._save(filtered, meta)

    def export_archive(self, target: str | Path) -> Path:
        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = self.base_path / target_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        snippets, meta = self._load()
        payload = {"snippets": [item.to_dict() for item in snippets], "meta": meta}
        target_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return target_path

    def import_archive(self, source: str | Path) -> int:
        source_path = Path(source)
        if not source_path.exists():
            raise ValueError("Archiv nicht gefunden")
        raw = json.loads(source_path.read_text(encoding="utf-8"))
        if "snippets" not in raw:
            raise ValueError("Archiv enthält keine Snippets")
        snippets_raw = raw.get("snippets", [])
        if not isinstance(snippets_raw, list):
            raise ValueError("Ungültiges Archiv-Format")
        imported: list[Snippet] = []
        for entry in snippets_raw:
            imported.append(Snippet.from_dict(entry))
        meta = raw.get("meta", {}) if isinstance(raw, dict) else {}
        meta["last_action"] = "Import"
        meta["last_save"] = datetime.now(UTC).isoformat(timespec="seconds")
        self._save(imported, meta)
        return len(imported)

    def stats(self) -> dict[str, str]:
        snippets, meta = self._load()
        return {
            "count": str(len(snippets)),
            "last_action": meta.get("last_action", "–") or "–",
            "last_save": meta.get("last_save", "–") or "–",
        }


class SnippetLibraryPanel(ttk.LabelFrame):
    """Tkinter panel to manage snippets with validation and logging."""

    def __init__(
        self,
        parent: tk.Widget,
        store: SnippetStore,
        theme_manager: ThemeManager,
        logging_manager,
        frame_style: str = "Note.TLabelframe",
    ) -> None:
        super().__init__(
            parent,
            text="Snippet-Bibliothek (Vorlagen & Textbausteine)",
            padding=10,
            style=frame_style,
        )
        self.store = store
        self.theme_manager = theme_manager
        self.logging_manager = logging_manager

        self.status_var = tk.StringVar(
            value="Schnipsel (Snippets) speichern, importieren/exportieren und per Klick kopieren."
        )
        self.count_var = tk.StringVar()
        self.last_action_var = tk.StringVar()
        self.last_save_var = tk.StringVar()
        self.selected_id: str | None = None

        self._build_header()
        self._build_creator()
        self._build_list()
        self._build_detail()
        self.refresh()

    def _build_header(self) -> None:
        stats_frame = ttk.Frame(self)
        ttk.Label(stats_frame, text="Gesamt").grid(row=0, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.count_var, style="Status.TLabel").grid(
            row=0, column=1, sticky="w", padx=(4, 8)
        )
        ttk.Label(stats_frame, text="Letzte Aktion").grid(row=1, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.last_action_var).grid(row=1, column=1, sticky="w")
        ttk.Label(stats_frame, text="Letzte Sicherung").grid(row=2, column=0, sticky="w")
        ttk.Label(stats_frame, textvariable=self.last_save_var).grid(row=2, column=1, sticky="w")

        action_bar = ttk.Frame(stats_frame)
        ttk.Button(action_bar, text="Archiv exportieren", command=self._export).pack(side=tk.LEFT)
        ttk.Button(action_bar, text="Archiv importieren", command=self._import).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        action_bar.grid(row=0, column=2, rowspan=3, sticky="e")

        self.status_label = ttk.Label(self, textvariable=self.status_var, style="Helper.TLabel")
        self.status_label.pack(anchor="w", pady=(0, 6))
        stats_frame.pack(fill=tk.X, pady=(0, 8))

    def _build_creator(self) -> None:
        frame = ttk.LabelFrame(self, text="Neu anlegen", padding=6, style="Sidebar.TLabelframe")
        self.new_name = tk.StringVar()
        content_frame = ttk.Frame(frame)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        self.new_content = tk.Text(content_frame, height=4, wrap="word")
        y_scroll = ttk.Scrollbar(content_frame, orient="vertical", command=self.new_content.yview)
        x_scroll = ttk.Scrollbar(content_frame, orient="horizontal", command=self.new_content.xview)
        self.new_content.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        ttk.Label(frame, text="Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.new_name).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Label(frame, text="Inhalt").grid(row=1, column=0, sticky="nw", pady=(4, 0))
        self.new_content.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        content_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 0), pady=(4, 0))
        self.theme_manager.apply_text_theme(self.new_content)
        frame.columnconfigure(1, weight=1)

        button_bar = ttk.Frame(frame)
        ttk.Button(button_bar, text="Hinzufügen", command=self._add).pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Zurücksetzen", command=self._reset_creator).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Button(button_bar, text="Zwischenablage einfügen", command=self._paste_clipboard).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        button_bar.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        frame.pack(fill=tk.X, pady=(0, 8))

    def _build_list(self) -> None:
        list_frame = ttk.LabelFrame(self, text="Schnipsel", padding=6)
        tree_container = ttk.Frame(list_frame)
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(tree_container, columns=("name", "aktualisiert"), show="headings")
        self.tree.heading("name", text="Name")
        self.tree.heading("aktualisiert", text="Geändert")
        self.tree.column("name", width=160)
        self.tree.column("aktualisiert", width=120)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        y_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        tree_container.pack(fill=tk.BOTH, expand=True)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

    def _build_detail(self) -> None:
        frame = ttk.LabelFrame(self, text="Details & Bearbeitung", padding=6)
        self.detail_name = tk.StringVar()
        content_frame = ttk.Frame(frame)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        self.detail_content = tk.Text(content_frame, height=6, wrap="word")
        y_scroll = ttk.Scrollbar(content_frame, orient="vertical", command=self.detail_content.yview)
        x_scroll = ttk.Scrollbar(content_frame, orient="horizontal", command=self.detail_content.xview)
        self.detail_content.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        ttk.Label(frame, text="Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.detail_name).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Label(frame, text="Inhalt").grid(row=1, column=0, sticky="nw", pady=(4, 0))
        self.detail_content.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        content_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 0), pady=(4, 0))
        self.theme_manager.apply_text_theme(self.detail_content)
        frame.columnconfigure(1, weight=1)

        button_bar = ttk.Frame(frame)
        ttk.Button(button_bar, text="Speichern", command=self._save_detail).pack(side=tk.LEFT)
        ttk.Button(button_bar, text="Löschen", command=self._delete).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(button_bar, text="In Zwischenablage", command=self._copy_detail).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        button_bar.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        ttk.Label(frame, text="Tipp: Auswahl kopiert automatisch (Clipboard).", style="Helper.TLabel").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        frame.pack(fill=tk.X)

    def refresh(self) -> None:
        stats = self.store.stats()
        self.count_var.set(stats.get("count", "0"))
        self.last_action_var.set(stats.get("last_action", "–"))
        self.last_save_var.set(stats.get("last_save", "–"))

        for item in self.tree.get_children():
            self.tree.delete(item)
        for snippet in self.store.list_snippets():
            self.tree.insert("", "end", iid=snippet.id, values=(snippet.name, snippet.updated_at))
        self._set_status("Bibliothek synchronisiert", ok=True)

    def _add(self) -> None:
        name = self.new_name.get()
        content = self.new_content.get("1.0", tk.END)
        try:
            snippet = self.store.add_snippet(name, content)
        except ValueError as exc:
            self._set_status(str(exc), ok=False)
            return
        self._reset_creator()
        self.refresh()
        self._log(f"Snippet angelegt: {snippet.name}")
        self._set_status("Snippet gespeichert und geprüft", ok=True)

    def _reset_creator(self) -> None:
        self.new_name.set("")
        self.new_content.delete("1.0", tk.END)

    def _paste_clipboard(self) -> None:  # pragma: no cover - UI binding
        try:
            text = self.clipboard_get()
            self.new_content.delete("1.0", tk.END)
            self.new_content.insert("1.0", text)
            self._set_status("Zwischenablage eingefügt", ok=True)
        except tk.TclError:
            self._set_status("Zwischenablage nicht lesbar", ok=False)

    def _on_select(self, event: tk.Event[tk.Misc]) -> None:  # pragma: no cover - UI binding
        selection = self.tree.selection()
        if not selection:
            return
        snippet_id = selection[0]
        snippets = {item.id: item for item in self.store.list_snippets()}
        snippet = snippets.get(snippet_id)
        if not snippet:
            return
        self.selected_id = snippet.id
        self.detail_name.set(snippet.name)
        self.detail_content.delete("1.0", tk.END)
        self.detail_content.insert("1.0", snippet.content)
        self._copy_to_clipboard(snippet.content)
        self._set_status("Snippet geladen und kopiert", ok=True)

    def _save_detail(self) -> None:
        if not self.selected_id:
            self._set_status("Bitte zuerst ein Snippet wählen", ok=False)
            return
        name = self.detail_name.get()
        content = self.detail_content.get("1.0", tk.END)
        try:
            updated = self.store.update_snippet(self.selected_id, name, content)
        except ValueError as exc:
            self._set_status(str(exc), ok=False)
            return
        self.refresh()
        self._set_status("Änderungen gespeichert", ok=True)
        self._log(f"Snippet aktualisiert: {updated.name}")

    def _delete(self) -> None:
        if not self.selected_id:
            self._set_status("Keine Auswahl zum Löschen", ok=False)
            return
        try:
            self.store.delete_snippet(self.selected_id)
        except ValueError as exc:
            self._set_status(str(exc), ok=False)
            return
        self.selected_id = None
        self.detail_name.set("")
        self.detail_content.delete("1.0", tk.END)
        self.refresh()
        self._set_status("Snippet entfernt", ok=True)
        self._log("Snippet gelöscht")

    def _copy_detail(self) -> None:  # pragma: no cover - UI binding
        text = self.detail_content.get("1.0", tk.END)
        self._copy_to_clipboard(text)
        self._set_status("In Zwischenablage übertragen", ok=True)

    def _copy_to_clipboard(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)

    def _export(self) -> None:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        target = self.base_path / f"snippet_export_{timestamp}.json"
        path = self.store.export_archive(target)
        self._set_status(f"Export erstellt: {path}", ok=True)
        self._log(f"Export gesichert: {path}")

    def _import(self) -> None:
        source = self.base_path / "snippet_import.json"
        if not source.exists():
            self._set_status("Import-Datei 'snippet_import.json' fehlt im Projektordner", ok=False)
            return
        try:
            count = self.store.import_archive(source)
        except ValueError as exc:
            self._set_status(f"Import fehlgeschlagen: {exc}", ok=False)
            return
        self.refresh()
        self._set_status(f"Import abgeschlossen ({count} Einträge)", ok=True)
        self._log(f"Archiv importiert ({count} Snippets)")

    @property
    def base_path(self) -> Path:
        return self.store.base_path

    def _set_status(self, message: str, ok: bool) -> None:
        fg, bg = self.theme_manager.status_colors(ok)
        self.status_var.set(message)
        try:
            self.status_label.configure(foreground=fg, background=bg)
        except tk.TclError:
            self.status_label.configure(foreground=fg)
        if self.logging_manager:
            self.logging_manager.log_system(message)

    def _log(self, message: str) -> None:
        if self.logging_manager:
            self.logging_manager.log_system(message)

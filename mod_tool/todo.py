"""Einfache To-do-Verwaltung mit Validierung und Dauer-Speicher."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import List


@dataclass
class TodoItem:
    """Repräsentiert einen einzelnen To-do-Eintrag."""

    id: str
    title: str
    due_date: str | None
    info: str
    done: bool
    created_at: str

    def validate(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("Titel fehlt")
        if self.due_date:
            try:
                date.fromisoformat(self.due_date)
            except ValueError as exc:  # pragma: no cover - defensive
                raise ValueError("Datum bitte als JJJJ-MM-TT eintragen") from exc

    def to_dict(self) -> dict:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TodoItem":
        item = cls(
            id=data.get("id", uuid.uuid4().hex),
            title=data.get("title", ""),
            due_date=data.get("due_date"),
            info=data.get("info", ""),
            done=bool(data.get("done", False)),
            created_at=data.get("created_at", date.today().isoformat()),
        )
        item.validate()
        return item


class TodoManager:
    """Persistente Verwaltung der To-do-Liste."""

    def __init__(self, base_path: Path, store_file: str | Path = "todos.json") -> None:
        if not isinstance(base_path, Path):
            base_path = Path(base_path)
        self.base_path = base_path
        self.store_file = self._resolve_path(store_file)
        self.ensure_store()

    def _resolve_path(self, target: str | Path) -> Path:
        target_path = target if isinstance(target, Path) else Path(target)
        if not target_path.is_absolute():
            target_path = self.base_path / target_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        return target_path

    def ensure_store(self) -> Path:
        if not self.store_file.exists():
            self.store_file.write_text(json.dumps({"todos": []}, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            try:
                data = json.loads(self.store_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {"todos": []}
            if "todos" not in data or not isinstance(data.get("todos"), list):
                data = {"todos": []}
            self.store_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.store_file

    def _load(self) -> list[TodoItem]:
        raw = json.loads(self.store_file.read_text(encoding="utf-8"))
        todos = raw.get("todos", []) if isinstance(raw, dict) else []
        if not isinstance(todos, list):
            raise ValueError("Ungültiges Todo-Format")
        result: list[TodoItem] = []
        for entry in todos:
            try:
                result.append(TodoItem.from_dict(entry))
            except ValueError:
                continue
        return result

    def _save(self, items: List[TodoItem]) -> None:
        payload = {"todos": [item.to_dict() for item in items]}
        self.store_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_item(self, title: str, due_date: str | None, info: str = "", done: bool = False) -> TodoItem:
        item = TodoItem(
            id=uuid.uuid4().hex,
            title=title.strip(),
            due_date=due_date.strip() if due_date else None,
            info=info.strip(),
            done=done,
            created_at=date.today().isoformat(),
        )
        item.validate()
        todos = self._load()
        todos.append(item)
        self._save(todos)
        return item

    def list_upcoming(self, limit: int = 10) -> list[TodoItem]:
        todos = self._load()
        todos.sort(key=lambda x: (x.done, x.due_date or "9999-12-31", x.title.lower()))
        return todos[:limit]

    def set_done(self, item_id: str, done: bool) -> TodoItem:
        todos = self._load()
        for item in todos:
            if item.id == item_id:
                item.done = done
                item.validate()
                self._save(todos)
                return item
        raise ValueError("To-do nicht gefunden")

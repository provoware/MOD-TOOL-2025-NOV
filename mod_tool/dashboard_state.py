"""State management for dashboard data, autosave, hints, and backups."""
from __future__ import annotations

import json
import random
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List


@dataclass
class DashboardState:
    """Handle persistence, autosave, and hint rotation in a user-friendly way."""

    base_path: Path
    notes_file: Path | str = "notes.txt"
    autosave_file: Path | str = "autosave.json"
    hints_file: Path | str = "hints.txt"
    backups_dir: Path | str = "backups"
    autosave_interval_seconds: int = 300
    hint_interval_seconds: int = 1200
    _last_hint_timestamp: float = field(default_factory=lambda: 0.0, init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.base_path, Path):
            self.base_path = Path(self.base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.notes_file = self._ensure_path(self.notes_file)
        self.autosave_file = self._ensure_path(self.autosave_file)
        self.hints_file = self._ensure_path(self.hints_file)
        self.backups_dir = self._ensure_path(self.backups_dir, is_dir=True)

    def _ensure_path(self, path: Path | str, is_dir: bool = False) -> Path:
        target = path if isinstance(path, Path) else Path(path)
        if not target.is_absolute():
            target = self.base_path / target
        if is_dir:
            target.mkdir(parents=True, exist_ok=True)
        return target

    def ensure_project_structure(self, extra_paths: Iterable[str | Path] | None = None) -> dict[str, str]:
        """Ensure that key project paths exist and describe actions taken."""

        extra_paths = list(extra_paths or [])
        paths = [self.base_path, self.base_path / "logs", self.base_path / "config", self.base_path / "plugins", *extra_paths]
        report: dict[str, str] = {}
        for path in paths:
            resolved = path if isinstance(path, Path) else Path(path)
            if not resolved.is_absolute():
                resolved = self.base_path / resolved
            if resolved.exists():
                report[str(resolved)] = "vorhanden"
            else:
                resolved.mkdir(parents=True, exist_ok=True)
                report[str(resolved)] = "automatisch erstellt"
        return report

    def save_notes(self, text: str) -> Path:
        """Persist notes to a text file; empty strings raise a validation error."""

        if text is None:
            raise ValueError("Notiztext fehlt")
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Leere Notizen werden nicht gespeichert")
        self.notes_file.write_text(cleaned, encoding="utf-8")
        return self.notes_file

    def autosave_snapshot(self, note_text: str, status: dict[str, str] | None = None) -> Path:
        """Persist a JSON snapshot with timestamp, notes, and status values."""

        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "notes": note_text or "",
            "status": status or {},
        }
        self.autosave_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.autosave_file

    def load_hints(self) -> List[str]:
        """Return hints list, creating a default file if missing."""

        if not self.hints_file.exists():
            default_hints = [
                "Kurze Eingaben halten – klare Schritte erleichtern die Automatik.",
                "Bei Fehlermeldungen: roten Text anklicken und Hinweise lesen.",
                "Regelmäßig sichern: Menü > Backup legt Kopie im Backup-Ordner an.",
            ]
            self.hints_file.write_text("\n".join(default_hints), encoding="utf-8")
        lines = [line.strip() for line in self.hints_file.read_text(encoding="utf-8").splitlines()]
        return [line for line in lines if line]

    def random_hint(self) -> str:
        """Pick a random hint, respecting the hint rotation interval."""

        hints = self.load_hints()
        if not hints:
            return "Keine Hinweise verfügbar. Hints-Datei im Dashboard bearbeiten."
        now = time.time()
        if now - self._last_hint_timestamp < self.hint_interval_seconds:
            return "Hinweise aktuell – nächste Rotation folgt automatisch."
        self._last_hint_timestamp = now
        return random.choice(hints)

    def import_notes(self, source: Path | str) -> str:
        """Load notes from a txt or json file and return the content."""

        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {source_path}")
        suffix = source_path.suffix.lower()
        if suffix == ".json":
            data = json.loads(source_path.read_text(encoding="utf-8"))
            return str(data.get("notes", ""))
        return source_path.read_text(encoding="utf-8")

    def export_notes(self, target: Path | str, note_text: str) -> Path:
        """Export notes to txt or json depending on file extension."""

        target_path = Path(target)
        cleaned = (note_text or "").strip()
        if not cleaned:
            raise ValueError("Leerer Text kann nicht exportiert werden")
        if target_path.suffix.lower() == ".json":
            payload = {"notes": cleaned, "exported_at": time.time()}
            target_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            target_path.write_text(cleaned, encoding="utf-8")
        return target_path

    def create_backup(self) -> Path:
        """Create a timestamped backup of the notes and autosave files."""

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        bundle_dir = self.backups_dir / f"backup-{timestamp}"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        for file_path in (self.notes_file, self.autosave_file):
            if Path(file_path).exists():
                shutil.copy(file_path, bundle_dir / Path(file_path).name)
        return bundle_dir

    def rotate_status_colors(self, ok: bool) -> tuple[str, str]:
        """Return contrasting colors for status labels depending on success."""

        return ("#0f9d58", "#0b3d2e") if ok else ("#c0392b", "#3b0b0b")


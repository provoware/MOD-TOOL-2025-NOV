"""Genre-Archiv mit validierten Profilen und Duplikat-Schutz."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class GenreProfile:
    """Ein einzelnes Profil innerhalb einer Kategorie."""

    category: str
    name: str
    description: str
    created_at: str

    def validate(self) -> None:
        if not self.category or not self.category.strip():
            raise ValueError("Kategorie fehlt")
        if not self.name or not self.name.strip():
            raise ValueError("Profilname fehlt")

    def to_dict(self) -> dict[str, str]:
        self.validate()
        return asdict(self)


class GenreArchive:
    """Verwaltet ein dauerhaftes Genre-Archiv mit Auto-Anlage."""

    def __init__(self, base_path: Path, archive_file: str | Path = "genre_archive.json") -> None:
        if not isinstance(base_path, Path):
            base_path = Path(base_path)
        self.base_path = base_path
        self.archive_file = self._resolve_path(archive_file)
        self.ensure_archive()

    def _resolve_path(self, target: str | Path) -> Path:
        target_path = target if isinstance(target, Path) else Path(target)
        if not target_path.is_absolute():
            target_path = self.base_path / target_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        return target_path

    def ensure_archive(self) -> Path:
        """Legt die Archivdatei an, falls sie fehlt, und validiert die Struktur."""

        if not self.archive_file.exists():
            payload = {"profiles": [], "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
            self.archive_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            try:
                data = json.loads(self.archive_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {"profiles": []}
            if "profiles" not in data or not isinstance(data.get("profiles"), list):
                data = {"profiles": []}
            data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            self.archive_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.archive_file

    def _load(self) -> dict:
        raw = json.loads(self.archive_file.read_text(encoding="utf-8"))
        profiles = raw.get("profiles", [])
        if not isinstance(profiles, list):
            raise ValueError("Archiv-Datei fehlerhaft: profiles muss eine Liste sein")
        return raw

    def _save(self, data: dict) -> None:
        data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.archive_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_profile(self, category: str, name: str, description: str = "") -> GenreProfile:
        """Fügt ein Profil hinzu und prüft Duplikate je Kategorie/Name."""

        profile = GenreProfile(
            category=category.strip(),
            name=name.strip(),
            description=description.strip(),
            created_at=time.strftime("%Y-%m-%d"),
        )
        profile.validate()
        data = self._load()
        existing = [
            p
            for p in data.get("profiles", [])
            if p.get("category", "").lower() == profile.category.lower()
            and p.get("name", "").lower() == profile.name.lower()
        ]
        if existing:
            raise ValueError("Profil existiert bereits in dieser Kategorie")
        data.setdefault("profiles", []).append(profile.to_dict())
        self._save(data)
        return profile

    def list_profiles(self, category: str | None = None, limit: int | None = None) -> List[GenreProfile]:
        data = self._load()
        profiles: Iterable[dict] = data.get("profiles", [])
        result: List[GenreProfile] = []
        for item in profiles:
            try:
                candidate = GenreProfile(
                    category=item.get("category", ""),
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    created_at=item.get("created_at", ""),
                )
                candidate.validate()
            except ValueError:
                continue
            if category and candidate.category.lower() != category.strip().lower():
                continue
            result.append(candidate)
        result.sort(key=lambda p: (p.category.lower(), p.name.lower()))
        if limit is not None:
            return result[:limit]
        return result

    def categories(self) -> list[str]:
        return sorted({profile.category for profile in self.list_profiles()})

    def summary_lines(self, limit: int = 5) -> list[str]:
        profiles = self.list_profiles(limit=limit)
        if not profiles:
            return ["Keine Einträge – lege Kategorien und Profile an."]
        lines = [f"{p.category}: {p.name} – {p.description or 'ohne Beschreibung'}" for p in profiles]
        return lines

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from mod_tool.genres_tool import GenresToolStore


def test_store_creates_default_profile(tmp_path: Path) -> None:
    store = GenresToolStore(tmp_path)
    assert store.store_path.exists()
    assert store.active_profile() == "Profil 1"
    assert store.counts() == {"Genres": 0, "Moods": 0, "Styles": 0}


def test_add_profile_and_entries_unique(tmp_path: Path) -> None:
    store = GenresToolStore(tmp_path)
    store.add_profile("Test")
    added = store.add_entries("Genres", ["Rock", "rock", "Pop"])
    assert added == ["Rock", "Pop"]
    counts = store.counts()
    assert counts["Genres"] == 2


def test_random_pick_logs_and_uniqueness(tmp_path: Path) -> None:
    store = GenresToolStore(tmp_path)
    store.add_entries("Genres", ["Rock", "Jazz"])
    store.add_entries("Moods", ["Happy", "Calm"])
    result = store.generate_random(categories=["Genres", "Moods"], max_per_category=2)
    assert len(result) >= 2
    assert len(store.logs()) == 1


def test_export_import_roundtrip(tmp_path: Path) -> None:
    store = GenresToolStore(tmp_path)
    store.add_entries("Genres", ["Electro"])
    payload = store.export_json()
    new_dir = Path(tempfile.mkdtemp())
    new_store = GenresToolStore(new_dir)
    new_store.import_json(payload)
    assert "Electro" in new_store.list_entries("Genres")


def test_duplicate_and_delete_rules(tmp_path: Path) -> None:
    store = GenresToolStore(tmp_path)
    clone = store.duplicate_profile(store.active_profile(), "Copy")
    assert clone in store.profiles()
    store.delete_profile(clone)
    assert store.active_profile() == "Profil 1"
    # Deleting last profile should raise
    try:
        store.delete_profile("Profil 1")
    except ValueError:
        pass
    else:
        raise AssertionError("Deleting last profile must fail")

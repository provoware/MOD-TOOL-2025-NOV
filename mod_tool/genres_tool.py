"""GenresTool: Portiertes Zufallstool mit Profilverwaltung und Barrierefreiheit.

Dieses Modul überführt die im HTML-Prototyp enthaltene Logik in eine
strukturierte, getestete Python-Implementierung. Die Logik ist klar von
UI-Komponenten getrennt, damit Tests ohne GUI laufen können.
"""
from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from .themes import ThemeManager

LOG = logging.getLogger(__name__)


ALLOWED_CATEGORIES = ("Genres", "Moods", "Styles")


@dataclass
class ProfileData:
    """Sammlung pro Profil mit Validierung und Standardwerten."""

    Genres: list[str] = field(default_factory=list)
    Moods: list[str] = field(default_factory=list)
    Styles: list[str] = field(default_factory=list)
    Logs: list[str] = field(default_factory=list)

    def validate(self) -> None:
        for category in ALLOWED_CATEGORIES:
            values = getattr(self, category, None)
            if values is None or not isinstance(values, list):
                raise ValueError(f"Kategorie {category} fehlt oder ist ungültig")

    def to_dict(self) -> dict[str, list[str]]:
        self.validate()
        return {
            "Genres": list(self.Genres),
            "Moods": list(self.Moods),
            "Styles": list(self.Styles),
            "Logs": list(self.Logs),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "ProfileData":
        profile = cls(
            Genres=list(payload.get("Genres", [])),
            Moods=list(payload.get("Moods", [])),
            Styles=list(payload.get("Styles", [])),
            Logs=list(payload.get("Logs", [])),
        )
        profile.validate()
        return profile


class GenresToolStore:
    """Speichert Profile, prüft Eingaben und bietet Zufallsauswahl."""

    def __init__(self, base_path: Path, store_file: str | Path = "config/genres_tool.json", logger: logging.Logger | None = None) -> None:
        if not isinstance(base_path, Path):
            base_path = Path(base_path)
        self.base_path = base_path
        self.store_path = self._resolve_store(store_file)
        self.logger = logger or LOG
        self.data: dict[str, object] = {}
        self.ensure_store()
        self._load()

    def _resolve_store(self, target: str | Path) -> Path:
        path = target if isinstance(target, Path) else Path(target)
        if not path.is_absolute():
            path = self.base_path / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _default_payload(self) -> dict[str, object]:
        return {
            "profiles": {"Profil 1": ProfileData().to_dict()},
            "active": "Profil 1",
            "settings": {"dark_mode": False, "debug_mode": False},
        }

    def ensure_store(self) -> Path:
        if not self.store_path.exists():
            self.store_path.write_text(json.dumps(self._default_payload(), indent=2, ensure_ascii=False), encoding="utf-8")
        return self.store_path

    def _load(self) -> None:
        try:
            payload = json.loads(self.store_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = self._default_payload()
        profiles_raw = payload.get("profiles", {})
        if not isinstance(profiles_raw, dict) or not profiles_raw:
            profiles_raw = {"Profil 1": ProfileData().to_dict()}
        profiles = {}
        for name, data in profiles_raw.items():
            try:
                profiles[name] = ProfileData.from_dict(data).to_dict()
            except ValueError:
                continue
        if not profiles:
            profiles = {"Profil 1": ProfileData().to_dict()}
        active = payload.get("active") if payload.get("active") in profiles else list(profiles)[0]
        settings = payload.get("settings") if isinstance(payload.get("settings"), dict) else {}
        settings.setdefault("dark_mode", False)
        settings.setdefault("debug_mode", False)
        self.data = {"profiles": profiles, "active": active, "settings": settings}
        self._save()

    def _save(self) -> None:
        self.store_path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Profile Verwaltung ---
    def profiles(self) -> list[str]:
        names = list(self.data.get("profiles", {}).keys())
        if not names:
            raise ValueError("Keine Profile verfügbar")
        return sorted(names)

    def active_profile(self) -> str:
        active = self.data.get("active")
        if not active or active not in self.data.get("profiles", {}):
            raise ValueError("Aktives Profil fehlt")
        return str(active)

    def set_active(self, name: str) -> str:
        if not name or name not in self.data.get("profiles", {}):
            raise ValueError("Profil nicht gefunden")
        self.data["active"] = name
        self._save()
        return name

    def add_profile(self, name: str) -> str:
        cleaned = (name or "").strip()
        if not cleaned:
            raise ValueError("Profilname darf nicht leer sein")
        profiles = self.data.get("profiles", {})
        if cleaned in profiles:
            raise ValueError("Profil existiert bereits")
        profiles[cleaned] = ProfileData().to_dict()
        self.data["profiles"] = profiles
        self.data["active"] = cleaned
        self._save()
        self.logger.info("Profil %s angelegt", cleaned)
        return cleaned

    def delete_profile(self, name: str) -> None:
        profiles = self.data.get("profiles", {})
        if name not in profiles:
            raise ValueError("Profil nicht gefunden")
        if len(profiles) == 1:
            raise ValueError("Letztes Profil kann nicht gelöscht werden")
        profiles.pop(name)
        if self.data.get("active") == name:
            self.data["active"] = list(profiles)[0]
        self._save()
        self.logger.info("Profil %s gelöscht", name)

    def duplicate_profile(self, source: str, target: str) -> str:
        profiles = self.data.get("profiles", {})
        if source not in profiles:
            raise ValueError("Quellprofil fehlt")
        cleaned = (target or "").strip()
        if not cleaned:
            raise ValueError("Name für Duplikat fehlt")
        if cleaned in profiles:
            raise ValueError("Zielname existiert bereits")
        profiles[cleaned] = json.loads(json.dumps(profiles[source]))
        self.data["active"] = cleaned
        self._save()
        return cleaned

    # --- Kategorien & Inhalte ---
    def _require_category(self, category: str) -> str:
        if category not in ALLOWED_CATEGORIES:
            raise ValueError("Unbekannte Kategorie")
        return category

    def add_entries(self, category: str, values: Iterable[str]) -> list[str]:
        category = self._require_category(category)
        if not isinstance(values, Iterable):
            raise ValueError("Werte-Liste fehlt")
        profile = self.data.get("profiles", {}).get(self.active_profile())
        if profile is None:
            raise ValueError("Aktives Profil fehlt")
        target_list: list[str] = profile.get(category, [])
        existing_lower = {item.lower() for item in target_list}
        added: list[str] = []
        for raw in values:
            cleaned = (raw or "").strip()
            if not cleaned:
                continue
            if cleaned.lower() in existing_lower:
                continue
            target_list.append(cleaned)
            existing_lower.add(cleaned.lower())
            added.append(cleaned)
        profile[category] = target_list
        self._save()
        return added

    def list_entries(self, category: str) -> list[str]:
        category = self._require_category(category)
        profile = self.data.get("profiles", {}).get(self.active_profile(), {})
        return list(profile.get(category, []))

    def counts(self) -> dict[str, int]:
        profile = self.data.get("profiles", {}).get(self.active_profile(), {})
        return {cat: len(profile.get(cat, [])) for cat in ALLOWED_CATEGORIES}

    # --- Zufallslogik & Logs ---
    def generate_random(
        self,
        *,
        categories: Sequence[str] | None = None,
        max_per_category: int = 1,
    ) -> list[str]:
        if max_per_category <= 0:
            raise ValueError("Anzahl muss größer 0 sein")
        chosen_categories = list(categories or ALLOWED_CATEGORIES)
        for cat in chosen_categories:
            self._require_category(cat)
        profile = self.data.get("profiles", {}).get(self.active_profile())
        if profile is None:
            raise ValueError("Aktives Profil fehlt")
        selection: list[str] = []
        for cat in chosen_categories:
            pool = list(profile.get(cat, []))
            random.shuffle(pool)
            selection.extend(pool[:max_per_category])
        unique = []
        seen = set()
        for item in selection:
            key = item.lower()
            if key in seen:
                continue
            unique.append(item)
            seen.add(key)
        self._append_log(unique)
        self._save()
        return unique

    def _append_log(self, values: Sequence[str]) -> None:
        profile = self.data.get("profiles", {}).get(self.active_profile())
        if profile is None:
            return
        timestamp = time.strftime("%H:%M:%S")
        line = f"{timestamp}: {', '.join(values) if values else 'Keine Auswahl'}"
        logs: list[str] = profile.get("Logs", [])
        logs.insert(0, line)
        self.data["profiles"][self.active_profile()]["Logs"] = logs[:30]

    def logs(self) -> list[str]:
        profile = self.data.get("profiles", {}).get(self.active_profile(), {})
        return list(profile.get("Logs", []))

    def clear_logs(self) -> None:
        profile = self.data.get("profiles", {}).get(self.active_profile())
        if profile is None:
            raise ValueError("Aktives Profil fehlt")
        profile["Logs"] = []
        self._save()

    # --- Export/Import ---
    def export_archive_text(self) -> str:
        profile_name = self.active_profile()
        profile = ProfileData.from_dict(self.data.get("profiles", {}).get(profile_name, {}))
        lines = [f"Profil: {profile_name}", "", "Genres:"]
        lines.extend(profile.Genres or ["(leer)"])
        lines.extend(["", "Stimmungen:"])
        lines.extend(profile.Moods or ["(leer)"])
        lines.extend(["", "Stile:"])
        lines.extend(profile.Styles or ["(leer)"])
        return "\n".join(lines)

    def export_logs_text(self) -> str:
        return "\n".join(self.logs())

    def export_json(self) -> str:
        return json.dumps(self.data, indent=2, ensure_ascii=False)

    def import_json(self, payload: str) -> None:
        if not payload:
            raise ValueError("Importdaten fehlen")
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("Ungültiges JSON") from exc
        if "profiles" not in data:
            raise ValueError("profiles-Schlüssel fehlt")
        # Validierung erzwingen
        validated = {name: ProfileData.from_dict(item).to_dict() for name, item in data.get("profiles", {}).items()}
        active = data.get("active") if data.get("active") in validated else list(validated)[0]
        settings = data.get("settings") if isinstance(data.get("settings"), dict) else {}
        settings.setdefault("dark_mode", False)
        settings.setdefault("debug_mode", False)
        self.data = {"profiles": validated, "active": active, "settings": settings}
        self._save()

    # --- Settings ---
    def toggle_dark_mode(self) -> bool:
        settings = self.data.get("settings", {})
        settings["dark_mode"] = not bool(settings.get("dark_mode", False))
        self.data["settings"] = settings
        self._save()
        return settings["dark_mode"]

    def toggle_debug_mode(self) -> bool:
        settings = self.data.get("settings", {})
        settings["debug_mode"] = not bool(settings.get("debug_mode", False))
        self.data["settings"] = settings
        self._save()
        return settings["debug_mode"]


class GenresToolWindow:
    """Barrierefreie Oberfläche für das Genre-Zufallstool."""

    def __init__(
        self,
        root,
        store: GenresToolStore,
        theme_manager: ThemeManager,
        logging_manager=None,
    ) -> None:
        import tkinter as tk  # lokale Importe für headless Tests
        from tkinter import ttk

        self._root = root
        self._store = store
        self._theme_manager = theme_manager
        self._logging_manager = logging_manager
        self._window: tk.Toplevel | None = None
        self._tk = tk
        self._ttk = ttk
        self._random_result_var = tk.StringVar(value="Noch keine Zufallsauswahl.")
        self._profile_var = tk.StringVar(value=self._store.active_profile())
        self._count_var = tk.StringVar(value="1")
        self._inc_genres = tk.BooleanVar(value=True)
        self._inc_moods = tk.BooleanVar(value=True)
        self._inc_styles = tk.BooleanVar(value=True)
        self._message_var = tk.StringVar(value="Bereit: Alles lokal, Eingaben werden geprüft.")

    def show(self) -> None:
        if self._window is not None and self._window.winfo_exists():  # pragma: no cover - UI binding
            self._window.lift()
            return
        self._build_window()

    # --- UI Aufbau ---
    def _build_window(self) -> None:
        tk, ttk = self._tk, self._ttk
        self._window = tk.Toplevel(self._root)
        self._window.title("Genres & Ideen – Zufallstool")
        self._window.geometry("1100x780")
        self._window.minsize(900, 640)
        self._window.columnconfigure(1, weight=1)
        self._window.rowconfigure(1, weight=1)

        header = ttk.Frame(self._window, padding=12)
        header.grid(row=0, column=0, columnspan=2, sticky="nsew")
        ttk.Label(header, text="🎵 Genres & Ideen", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self._message_var, style="Helper.TLabel").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Label(header, text="Aktives Profil:").grid(row=0, column=1, sticky="e", padx=(8, 0))
        self._profile_box = ttk.Combobox(
            header, textvariable=self._profile_var, values=self._store.profiles(), state="readonly"
        )
        self._profile_box.grid(row=0, column=2, sticky="ew")
        self._profile_box.bind("<<ComboboxSelected>>", lambda _event: self._on_profile_change())
        header.columnconfigure(2, weight=1)

        sidebar = ttk.LabelFrame(
            self._window,
            text="Profile & Daten",
            padding=10,
            style="Sidebar.TLabelframe",
            labelanchor="n",
        )
        sidebar.grid(row=1, column=0, sticky="nsw", padx=(12, 6), pady=(0, 12))
        sidebar.columnconfigure(0, weight=1)
        self._build_sidebar(sidebar)

        content = ttk.Frame(self._window, padding=8)
        content.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(0, 12))
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)
        self._build_panels(content)
        self._theme_manager.apply_theme(self._theme_manager.current_theme)

    def _build_sidebar(self, parent) -> None:
        tk, ttk = self._tk, self._ttk
        ttk.Button(parent, text="+ Profil", command=self._create_profile).grid(row=0, column=0, sticky="ew", pady=2)
        ttk.Button(parent, text="– Profil", command=self._delete_profile).grid(row=1, column=0, sticky="ew", pady=2)
        ttk.Button(parent, text="Profil duplizieren", command=self._duplicate_profile).grid(row=2, column=0, sticky="ew", pady=2)
        ttk.Separator(parent).grid(row=3, column=0, sticky="ew", pady=6)
        ttk.Button(parent, text="Export (JSON)", command=self._export_json).grid(row=4, column=0, sticky="ew", pady=2)
        ttk.Button(parent, text="Import (JSON)", command=self._import_json).grid(row=5, column=0, sticky="ew", pady=2)
        ttk.Button(parent, text="Archiv als Text", command=self._export_archive).grid(row=6, column=0, sticky="ew", pady=2)
        ttk.Button(parent, text="Logs exportieren", command=self._export_logs).grid(row=7, column=0, sticky="ew", pady=2)
        ttk.Separator(parent).grid(row=8, column=0, sticky="ew", pady=6)
        ttk.Button(parent, text="Dark Mode umschalten", command=self._toggle_dark).grid(row=9, column=0, sticky="ew", pady=2)
        ttk.Button(parent, text="Debug-Logging umschalten", command=self._toggle_debug).grid(row=10, column=0, sticky="ew", pady=2)
        ttk.Label(parent, text="Theme wählen", style="Helper.TLabel").grid(row=11, column=0, sticky="w", pady=(6, 0))
        theme_box = ttk.Combobox(parent, values=self._theme_manager.theme_names, state="readonly")
        theme_box.set(self._theme_manager.current_theme)
        theme_box.grid(row=12, column=0, sticky="ew", pady=(0, 4))
        theme_box.bind("<<ComboboxSelected>>", lambda _event: self._theme_manager.apply_theme(theme_box.get()))
        ttk.Label(parent, text="Tipps: Einfach starten – alle Eingaben werden geprüft und gespeichert.", style="Helper.TLabel", wraplength=200).grid(row=13, column=0, sticky="w", pady=(6, 0))

    def _build_panels(self, parent) -> None:
        tk, ttk = self._tk, self._ttk
        grid = ttk.Frame(parent)
        grid.grid(row=0, column=0, sticky="nsew")
        for i in range(2):
            grid.columnconfigure(i, weight=1, uniform="panel")
            grid.rowconfigure(i, weight=1, uniform="panel")

        self._build_random_panel(grid, row=0, column=0)
        self._build_input_panel(grid, row=0, column=1)
        self._build_archive_panel(grid, row=1, column=0)
        self._build_logs_panel(grid, row=1, column=1)

    def _build_random_panel(self, parent, *, row: int, column: int) -> None:
        tk, ttk = self._tk, self._ttk
        panel = ttk.LabelFrame(parent, text="Zufall", padding=10)
        panel.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
        panel.columnconfigure(1, weight=1)
        ttk.Label(panel, text="Welche Bereiche sollen gezogen werden?").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(panel, text="Genres", variable=self._inc_genres).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(panel, text="Stimmungen", variable=self._inc_moods).grid(row=1, column=1, sticky="w")
        ttk.Checkbutton(panel, text="Stile", variable=self._inc_styles).grid(row=1, column=2, sticky="w")

        ttk.Label(panel, text="Anzahl je Kategorie").grid(row=2, column=0, sticky="w", pady=(6, 0))
        button_frame = ttk.Frame(panel)
        button_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 4))
        for value in (1, 3, 5):
            ttk.Button(button_frame, text=str(value), command=lambda v=value: self._count_var.set(str(v))).pack(side=tk.LEFT, padx=2)
        ttk.Entry(button_frame, textvariable=self._count_var, width=4).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(panel, text="Los", command=self._generate_random).grid(row=4, column=0, sticky="w", pady=(4, 0))
        result_box = ttk.Label(panel, textvariable=self._random_result_var, wraplength=320, style="Status.TLabel")
        result_box.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(6, 0))

    def _build_input_panel(self, parent, *, row: int, column: int) -> None:
        tk, ttk = self._tk, self._ttk
        panel = ttk.LabelFrame(parent, text="Eingabe", padding=10)
        panel.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
        panel.columnconfigure(1, weight=1)
        ttk.Label(panel, text="Mehrere Werte mit Komma trennen (Duplikate werden ignoriert)").grid(row=0, column=0, columnspan=2, sticky="w")
        self._input_genres = ttk.Entry(panel)
        self._input_genres.grid(row=1, column=0, columnspan=2, sticky="ew", pady=2)
        self._input_genres.bind("<Return>", lambda _event: self._save_inputs("Genres"))
        self._input_genres.insert(0, "Genres…")
        self._input_moods = ttk.Entry(panel)
        self._input_moods.grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)
        self._input_moods.bind("<Return>", lambda _event: self._save_inputs("Moods"))
        self._input_moods.insert(0, "Stimmungen…")
        self._input_styles = ttk.Entry(panel)
        self._input_styles.grid(row=3, column=0, columnspan=2, sticky="ew", pady=2)
        self._input_styles.bind("<Return>", lambda _event: self._save_inputs("Styles"))
        self._input_styles.insert(0, "Stile…")
        ttk.Button(panel, text="Speichern", command=lambda: self._save_inputs("all")).grid(
            row=4, column=0, sticky="w", pady=(4, 0)
        )
        ttk.Label(panel, text="Enter speichert sofort", style="Helper.TLabel").grid(row=5, column=0, sticky="w", pady=(4, 0))

    def _build_archive_panel(self, parent, *, row: int, column: int) -> None:
        tk, ttk = self._tk, self._ttk
        panel = ttk.LabelFrame(parent, text="Archiv", padding=10)
        panel.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
        panel.columnconfigure(0, weight=1)
        counts = self._store.counts()
        self._counts_var = tk.StringVar(value=self._counts_text(counts))
        ttk.Label(panel, textvariable=self._counts_var).grid(row=0, column=0, sticky="w")
        self._archive_list = tk.Text(panel, height=8, wrap="word", state=tk.DISABLED)
        self._archive_list.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        ttk.Button(panel, text="Archiv aktualisieren", command=self._refresh_archive).grid(row=2, column=0, sticky="e", pady=(4, 0))
        panel.rowconfigure(1, weight=1)
        self._theme_manager.apply_text_theme(self._archive_list)
        self._refresh_archive()

    def _build_logs_panel(self, parent, *, row: int, column: int) -> None:
        tk, ttk = self._tk, self._ttk
        panel = ttk.LabelFrame(parent, text="Logs", padding=10)
        panel.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
        panel.columnconfigure(0, weight=1)
        self._logs_box = tk.Listbox(panel, height=8)
        self._logs_box.grid(row=0, column=0, sticky="nsew")
        ttk.Button(panel, text="Alle löschen", command=self._clear_logs).grid(row=1, column=0, sticky="w", pady=(4, 0))
        panel.rowconfigure(0, weight=1)
        self._refresh_logs()

    # --- UI Aktionen ---
    def _on_profile_change(self) -> None:
        selected = self._profile_var.get()
        try:
            self._store.set_active(selected)
            self._message_var.set(f"Profil {selected} aktiv.")
            self._refresh_archive()
            self._refresh_logs()
        except ValueError as exc:
            self._message_var.set(str(exc))

    def _create_profile(self) -> None:
        tk = self._tk
        name = tk.simpledialog.askstring("Neues Profil", "Profilname")
        if not name:
            self._message_var.set("Abgebrochen – kein Name eingegeben.")
            return
        try:
            self._store.add_profile(name)
            self._profile_var.set(name)
            self._refresh_profiles()
            self._message_var.set(f"Profil {name} angelegt.")
        except ValueError as exc:
            self._message_var.set(str(exc))

    def _delete_profile(self) -> None:
        tk = self._tk
        name = self._profile_var.get()
        if not tk.messagebox.askyesno("Profil löschen", f"Profil {name} wirklich löschen?"):
            return
        try:
            self._store.delete_profile(name)
            self._profile_var.set(self._store.active_profile())
            self._refresh_profiles()
            self._message_var.set(f"Profil {name} gelöscht.")
        except ValueError as exc:
            self._message_var.set(str(exc))

    def _duplicate_profile(self) -> None:
        tk = self._tk
        source = self._profile_var.get()
        target = tk.simpledialog.askstring("Duplikat", "Neuer Name für das Duplikat")
        if not target:
            self._message_var.set("Abgebrochen – kein Name eingegeben.")
            return
        try:
            name = self._store.duplicate_profile(source, target)
            self._profile_var.set(name)
            self._refresh_profiles()
            self._message_var.set(f"Profil {name} erstellt.")
        except ValueError as exc:
            self._message_var.set(str(exc))

    def _export_json(self) -> None:
        tk = self._tk
        payload = self._store.export_json()
        path = tk.filedialog.asksaveasfilename(title="Export speichern", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        Path(path).write_text(payload, encoding="utf-8")
        self._message_var.set(f"Export gespeichert: {path}")

    def _import_json(self) -> None:
        tk = self._tk
        path = tk.filedialog.askopenfilename(title="JSON importieren", filetypes=[("JSON", "*.json")])
        if not path:
            return
        payload = Path(path).read_text(encoding="utf-8")
        try:
            self._store.import_json(payload)
            self._refresh_profiles()
            self._profile_var.set(self._store.active_profile())
            self._refresh_archive()
            self._refresh_logs()
            self._message_var.set("Import abgeschlossen.")
        except ValueError as exc:
            tk.messagebox.showerror("Import fehlgeschlagen", str(exc))

    def _export_archive(self) -> None:
        tk = self._tk
        content = self._store.export_archive_text()
        path = tk.filedialog.asksaveasfilename(title="Archiv exportieren", defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not path:
            return
        Path(path).write_text(content, encoding="utf-8")
        self._message_var.set(f"Archiv gespeichert: {path}")

    def _export_logs(self) -> None:
        tk = self._tk
        content = self._store.export_logs_text()
        path = tk.filedialog.asksaveasfilename(title="Logs exportieren", defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not path:
            return
        Path(path).write_text(content, encoding="utf-8")
        self._message_var.set(f"Logs gespeichert: {path}")

    def _toggle_dark(self) -> None:
        enabled = self._store.toggle_dark_mode()
        self._theme_manager.apply_theme("Dunkel" if enabled else self._theme_manager.current_theme)
        self._message_var.set("Dark Mode aktiviert" if enabled else "Hellere Ansicht aktiv")

    def _toggle_debug(self) -> None:
        enabled = self._store.toggle_debug_mode()
        if self._logging_manager:
            self._logging_manager.log_system("Debug-Logging aktiviert" if enabled else "Debug-Logging ausgeschaltet")
        self._message_var.set("Debug an" if enabled else "Debug aus")

    def _generate_random(self) -> None:
        try:
            count = int(self._count_var.get())
        except ValueError:
            self._message_var.set("Bitte eine gültige Zahl eingeben.")
            return
        categories: list[str] = []
        if self._inc_genres.get():
            categories.append("Genres")
        if self._inc_moods.get():
            categories.append("Moods")
        if self._inc_styles.get():
            categories.append("Styles")
        if not categories:
            self._message_var.set("Mindestens eine Kategorie wählen.")
            return
        try:
            results = self._store.generate_random(categories=categories, max_per_category=count)
            text = ", ".join(results) if results else "Keine Werte hinterlegt"
            self._random_result_var.set(text)
            if self._logging_manager:
                self._logging_manager.log_system(f"Zufallsauswahl: {text}")
            self._refresh_logs()
            self._message_var.set("Auswahl kopiert & geloggt.")
            self._window.clipboard_clear()
            self._window.clipboard_append(text)
        except ValueError as exc:
            self._message_var.set(str(exc))

    def _save_inputs(self, category: str) -> None:
        def _split_values(raw: str, placeholder: str) -> list[str]:
            cleaned = (raw or "").strip()
            if not cleaned or cleaned == placeholder:
                return []
            return [part.strip() for part in cleaned.split(",") if part.strip()]

        mapping = {
            "Genres": _split_values(self._input_genres.get(), "Genres…"),
            "Moods": _split_values(self._input_moods.get(), "Stimmungen…"),
            "Styles": _split_values(self._input_styles.get(), "Stile…"),
        }
        if category == "all":
            for cat, raw in mapping.items():
                self._store.add_entries(cat, raw)
        else:
            raw = mapping.get(category, [])
            self._store.add_entries(category, raw)
        self._input_genres.delete(0, self._tk.END)
        self._input_moods.delete(0, self._tk.END)
        self._input_styles.delete(0, self._tk.END)
        self._message_var.set("Gespeichert – Duplikate wurden übersprungen.")
        self._refresh_archive()
        self._refresh_profiles()

    def _refresh_profiles(self) -> None:
        profiles = self._store.profiles()
        self._profile_var.set(self._store.active_profile())
        if hasattr(self, "_profile_box"):
            self._profile_box.configure(values=profiles)
            self._profile_box.set(self._profile_var.get())

    def _refresh_archive(self) -> None:
        counts = self._store.counts()
        self._counts_var.set(self._counts_text(counts))
        lines = []
        for cat in ALLOWED_CATEGORIES:
            lines.append(f"{cat} ({counts.get(cat, 0)}):")
            entries = self._store.list_entries(cat)
            if entries:
                lines.extend(f"• {item}" for item in entries)
            else:
                lines.append("(leer)")
            lines.append("")
        self._archive_list.configure(state=self._tk.NORMAL)
        self._archive_list.delete("1.0", self._tk.END)
        self._archive_list.insert("1.0", "\n".join(lines))
        self._archive_list.configure(state=self._tk.DISABLED)

    def _refresh_logs(self) -> None:
        self._logs_box.delete(0, self._tk.END)
        for line in self._store.logs():
            self._logs_box.insert(self._tk.END, line)

    def _clear_logs(self) -> None:
        try:
            self._store.clear_logs()
            self._refresh_logs()
            self._message_var.set("Logs gelöscht.")
        except ValueError as exc:
            self._message_var.set(str(exc))

    # --- Helper ---
    def _counts_text(self, counts: dict[str, int]) -> str:
        return ", ".join(f"{cat}: {counts.get(cat, 0)}" for cat in ALLOWED_CATEGORIES)

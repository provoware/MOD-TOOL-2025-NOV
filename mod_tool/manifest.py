"""Manifest definitions for layout and automation structure."""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class LayoutSection:
    """Describe a UI section for accessibility and layout docs."""

    identifier: str
    title: str
    purpose: str
    accessibility_label: str

    def validate(self) -> None:
        for value, name in [
            (self.identifier, "identifier"),
            (self.title, "title"),
            (self.purpose, "purpose"),
            (self.accessibility_label, "accessibility_label"),
        ]:
            if not value or not str(value).strip():
                raise ValueError(f"LayoutSection {name} darf nicht leer sein")


@dataclass
class LayoutManifest:
    """Manifest describing the visible layout and theming."""

    version: str
    sections: List[LayoutSection] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.version.strip():
            raise ValueError("LayoutManifest version darf nicht leer sein")
        if not self.sections:
            raise ValueError("LayoutManifest benötigt mindestens einen Abschnitt")
        for section in self.sections:
            section.validate()
        if not self.themes:
            raise ValueError("LayoutManifest benötigt mindestens ein Theme")

    def to_dict(self) -> dict:
        self.validate()
        return {
            "version": self.version,
            "sections": [
                {
                    "id": section.identifier,
                    "title": section.title,
                    "purpose": section.purpose,
                    "accessibility_label": section.accessibility_label,
                }
                for section in self.sections
            ],
            "themes": self.themes,
        }


@dataclass
class StructureManifest:
    """Overall structure manifest including automation and layout."""

    version: str
    project: str
    automation_steps: list[str] = field(default_factory=list)
    health_checks: list[str] = field(default_factory=list)
    accessibility: dict[str, str] = field(default_factory=dict)
    layout_manifest: LayoutManifest | None = None

    def validate(self) -> None:
        if not self.version.strip():
            raise ValueError("StructureManifest version darf nicht leer sein")
        if not self.project.strip():
            raise ValueError("StructureManifest project darf nicht leer sein")
        if not self.automation_steps:
            raise ValueError("Automation-Schritte dürfen nicht leer sein")
        if not self.health_checks:
            raise ValueError("Gesundheitsprüfungen dürfen nicht leer sein")
        if self.layout_manifest is None:
            raise ValueError("LayoutManifest muss gesetzt sein")
        self.layout_manifest.validate()

    def to_serialized(self) -> dict:
        self.validate()
        return {
            "structure_manifest": {
                "version": self.version,
                "project": self.project,
                "automation_steps": self.automation_steps,
                "health_checks": self.health_checks,
                "accessibility": self.accessibility,
            },
            "layout_manifest": self.layout_manifest.to_dict(),
        }


class ManifestWriter:
    """Utility that writes validated manifests to JSON."""

    def __init__(self, target_path: pathlib.Path | str) -> None:
        target = pathlib.Path(target_path)
        if target.is_dir():
            raise ValueError("Manifest-Ziel muss eine Datei sein")
        self.target_path = target

    def write(self, manifest: StructureManifest) -> pathlib.Path:
        manifest.validate()
        payload = manifest.to_serialized()
        self.target_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return self.target_path


def default_layout_manifest(theme_names: Iterable[str] | None = None) -> LayoutManifest:
    """Provide a default layout manifest for the dashboard grid."""

    sections = [
        LayoutSection(
            identifier="header",
            title="Steuerzentrale",
            purpose="Klick & Start, Schnell-Check, Theme-Wahl",
            accessibility_label="Obere Leiste mit Statusanzeigen und Startknöpfen",
        ),
        LayoutSection(
            identifier="workspace",
            title="Arbeitsbereich",
            purpose="Vier flexibel belegbare Quadranten",
            accessibility_label="Hauptbereich mit vier Panels für Module",
        ),
        LayoutSection(
            identifier="footer",
            title="Fußleiste",
            purpose="Debugging, Logging, Hinweise",
            accessibility_label="Unterer Bereich mit Protokoll- und Hilfetexten",
        ),
    ]
    themes = list(theme_names) if theme_names else ["Hell", "Dunkel", "Kontrast", "Blau", "Wald"]
    return LayoutManifest(version="1.0", sections=sections, themes=themes)


def default_structure_manifest(theme_names: Iterable[str] | None = None) -> StructureManifest:
    """Provide a baseline structure manifest for the project."""

    layout = default_layout_manifest(theme_names)
    return StructureManifest(
        version="1.0",
        project="MOD Tool Control Center",
        automation_steps=[
            "Virtuelle Umgebung prüfen",
            "Abhängigkeiten automatisch installieren",
            "Pflichtordner reparieren",
            "Syntax- und Format-Checks anstoßen",
            "Schnelltests ausführen",
            "Plugins laden",
        ],
        health_checks=[
            "Ordner vorhanden",
            "Code kompilierbar",
            "Tests grün oder übersprungen",
            "Manifest vorhanden",
        ],
        accessibility={
            "screenreader": "Klare Beschriftungen und Status-Labels für jede Zone",
            "kontrast": "Mehrere Farb-Themes inklusive Hochkontrast",
            "tastatur": "Steuerung per Tab-Reihenfolge von oben nach unten",
        },
        layout_manifest=layout,
    )

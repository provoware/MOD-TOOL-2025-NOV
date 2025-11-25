"""Nutzerfreundliche Schritt-für-Schritt-Hinweise mit Klartext-Begriffen."""
from __future__ import annotations

"""Geführte Tipps für Einsteiger mit verständlichen Befehlen."""

import os
from dataclasses import dataclass
from typing import Iterable


@dataclass
class GuidanceItem:
    """Kurze Anleitung mit Begriffserklärung und direkt ausführbarem Befehl."""

    title: str
    description: str
    command: str

    def validate(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("Titel für Hinweis fehlt")
        if not self.description or not self.description.strip():
            raise ValueError("Beschreibung darf nicht leer sein")
        if not self.command or not self.command.strip():
            raise ValueError("Befehl fehlt – bitte vollständigen Konsolenaufruf angeben")

    def render(self) -> str:
        """Formatiere den Hinweis für Log-Ausgaben in einfacher Sprache."""

        self.validate()
        return f"{self.title}: {self.description} (Befehl: {self.command})"


class StartupGuide:
    """Stellt laienfreundliche Tipps für Start, Tests und Debug bereit."""

    def __init__(self, venv_dir: str = ".venv") -> None:
        if not venv_dir or not venv_dir.strip():
            raise ValueError("Pfad zur virtuellen Umgebung darf nicht leer sein")
        self.venv_dir = venv_dir

    def tips(self) -> list[GuidanceItem]:
        """Gibt strukturierte Hinweise für häufige Aufgaben zurück."""

        return [
            GuidanceItem(
                title="Startroutine starten",
                description=(
                    "Autostart prüft Pfade und Abhängigkeiten selbständig. "
                    "Virtuelle Umgebung (geschützter Arbeitsraum) wird automatisch genutzt."
                ),
                command="python main.py",
            ),
            GuidanceItem(
                title="Umgebung manuell aktivieren",
                description=(
                    "Aktivierung sorgt dafür, dass alle Befehle die abgeschottete Umgebung nutzen "
                    "(isolierte Paketinstallation)."
                ),
                command=self._activation_command(),
            ),
            GuidanceItem(
                title="Tests ausführen",
                description=(
                    "Unit-Tests (kleine Selbstprüfungen) stellen Codequalität sicher."\
                    " Ergebnis erscheint direkt im Log."
                ),
                command="python -m unittest discover -s tests",
            ),
            GuidanceItem(
                title="Codeformat prüfen",
                description=(
                    "Optionale Formatter (Formatierer) wie 'black' laufen ohne Risiko."\
                    " So bleibt die Darstellung einheitlich."
                ),
                command="python -m black --check mod_tool",
            ),
            GuidanceItem(
                title="Debugmodus aktivieren",
                description=(
                    "Debugmodus (Fehlersuche mit Detailausgaben) liefert mehr Kontext."\
                    " Praktisch bei Plugin-Entwicklung."
                ),
                command="MOD_TOOL_DEBUG=1 python main.py",
            ),
        ]

    def render_for_logging(self) -> list[str]:
        """Bereitet alle Hinweise textuell auf."""

        return [item.render() for item in self._validated_tips()]

    def _validated_tips(self) -> Iterable[GuidanceItem]:
        for tip in self.tips():
            tip.validate()
            yield tip

    def _activation_command(self) -> str:
        bin_dir = "Scripts" if os.name == "nt" else "bin"
        activate = "activate.bat" if os.name == "nt" else "activate"
        return os.path.join(self.venv_dir, bin_dir, activate)

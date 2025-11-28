"""Autonome Startroutine mit Statusanzeige und Konfliktbehebung.

Die Routine führt alle notwendigen Schritte (virtuelle Umgebung, Pakete,
Selbstprüfung) automatisch aus und gibt laienfreundliche Rückmeldungen.
Jeder Schritt besitzt eine kleine Statuszeile (Statusanzeige), damit
Nutzende sofort sehen, was passiert und ob etwas repariert wurde.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .bootstrap import Bootstrapper, _default_feedback


@dataclass
class StartupStep:
    """Repräsentiert einen einzelnen Schritt der Startroutine."""

    key: str
    title: str
    status: str
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("Schritt benötigt einen Schlüssel")
        if not self.title:
            raise ValueError("Schritt benötigt einen Titel")
        self.status = self.status or "unbekannt"


class StartupStatusBoard:
    """Sammelt Schrittstände und berechnet einen Fortschritt."""

    def __init__(self) -> None:
        self.steps: list[StartupStep] = []

    def record(self, step: StartupStep) -> None:
        self.steps.append(step)

    def progress(self) -> tuple[int, str]:
        """Liefert Fortschritts-Prozentwert und kurze Lesefassung."""

        if not self.steps:
            return 0, "Keine Schritte gestartet"
        good_states = {"ok", "vorhanden", "erstellt", "automatisch erstellt", "übersprungen"}
        good = sum(1 for step in self.steps if step.status in good_states)
        percent = int((good / len(self.steps)) * 100)
        label = f"Fortschritt: {percent}% – {good}/{len(self.steps)} Schritte stabil"
        return percent, label

    def status_lines(self) -> list[str]:
        """Textzeilen für Log/Statusanzeige."""

        lines: list[str] = []
        for step in self.steps:
            detail = f" – {step.detail}" if step.detail else ""
            lines.append(f"{step.title}: {step.status}{detail}")
        return lines

    def as_dict(self) -> dict[str, str]:
        """Einfaches Mapping für UI/Logs."""

        return {step.key: step.status for step in self.steps}


class AutonomousStarter:
    """Vollautomatischer Starter mit Konfliktlösung und Statusanzeige."""

    def __init__(
        self,
        bootstrapper: Bootstrapper | None = None,
        feedback: Callable[[str], None] = _default_feedback,
    ) -> None:
        self.bootstrapper = bootstrapper or Bootstrapper(feedback=feedback)
        self.feedback = feedback
        self.status_board = StartupStatusBoard()

    def run(self) -> dict[str, str]:
        """Führt alle Schritte aus und liefert ein kompaktes Statuspaket."""

        self.feedback("Startroutine: vollautomatischer Ablauf gestartet.")
        self._record_step(
            key="virtualenv",
            title="Virtuelle Umgebung",
            status=self.bootstrapper.ensure_virtualenv(),
            detail="Eigener Arbeitsraum wurde geprüft oder erstellt.",
        )

        dep_status, dep_detail = self._install_with_healing()
        self._record_step(
            key="dependencies",
            title="Abhängigkeiten",
            status=dep_status,
            detail=dep_detail,
        )

        full_report = self.bootstrapper.self_check.full_check()
        friendly_summary = self.bootstrapper.self_check.human_summary(full_report)
        overall = full_report.get("gesamt", "warnung")
        detail = friendly_summary[0] if friendly_summary else "Selbstprüfung abgeschlossen"
        self._record_step("self_check", "Selbstprüfung", overall, detail)

        percent, label = self.status_board.progress()
        self._record_step("progress", "Fortschritt", f"{percent}%", label)

        for line in self.status_board.status_lines():
            self.feedback(line)

        summary = self.status_board.as_dict()
        summary["progress_info"] = label
        summary["statusanzeige"] = " | ".join(self.status_board.status_lines())
        return summary

    def _record_step(self, key: str, title: str, status: str, detail: str) -> None:
        step = StartupStep(key=key, title=title, status=status, detail=detail)
        self.status_board.record(step)

    def _install_with_healing(self) -> tuple[str, str]:
        status = self.bootstrapper.install_dependencies()
        detail = {
            "ok": "Alle Pakete bereit (automatisch installiert).",
            "übersprungen": "Keine requirements gefunden – Standardbibliothek reicht.",
            "fehlend": "Python in der Umgebung nicht gefunden.",
        }.get(status, "Pakete überprüft.")
        if status in {"warnung", "fehlend", "fehler"}:
            repair_status, repair_detail = self.bootstrapper.repair_dependencies(
                force_reinstall=True
            )
            detail = f"Konfliktbehebung: {repair_detail}"
            status = repair_status
        return status, detail


def render_status_lines(board: StartupStatusBoard) -> Iterable[str]:
    """Erlaubt externen Tools, nur die Textzeilen zu nutzen."""

    return board.status_lines()

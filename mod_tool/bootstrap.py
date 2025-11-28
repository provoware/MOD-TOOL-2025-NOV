"""Automated bootstrapper for a friendly, self-healing start routine.

The bootstrapper creates a virtual environment (eigener Python-Arbeitsraum),
installs dependencies, and re-launches the tool inside the environment so
users do not have to manage any setup details manually.
"""
from __future__ import annotations

import logging
import os
import pathlib
import subprocess
import sys
import venv
from dataclasses import dataclass, field
from typing import Callable

from .self_check import SelfCheck

LOG = logging.getLogger(__name__)


def _default_feedback(message: str) -> None:
    """Print and log status messages in simple language."""

    print(message)
    LOG.info(message)


@dataclass
class Bootstrapper:
    """Handle automatic environment creation and validation.

    Attributes:
        project_root: Root directory of the project repository.
        venv_dir: Target directory for the virtual environment.
        requirements_file: Path to `requirements.txt` if present.
        feedback: Callback to surface status messages to users.
        auto_relaunch: If true, restart the process inside the virtual env.
    """

    project_root: pathlib.Path = field(
        default_factory=lambda: pathlib.Path(__file__).resolve().parent.parent
    )
    venv_dir: pathlib.Path | None = None
    requirements_file: pathlib.Path | None = None
    feedback: Callable[[str], None] = _default_feedback
    auto_relaunch: bool = True

    def __post_init__(self) -> None:
        if not self.project_root.is_dir():
            raise ValueError("project_root muss ein existierender Ordner sein")
        self.venv_dir = self.venv_dir or self.project_root / ".venv"
        self.requirements_file = self.requirements_file or self.project_root / "requirements.txt"
        self.messages: list[str] = []
        self.self_check = SelfCheck(
            required_paths=[
                self.project_root / "logs",
                self.project_root / "plugins",
                self.project_root / "config",
            ],
            base_path=self.project_root,
        )

    def run(self) -> dict[str, str]:
        """Execute the full bootstrap sequence and return a status summary."""

        summary = {
            "virtualenv": self.ensure_virtualenv(),
            "dependencies": self.install_dependencies(),
            "self_check": self.self_check_report(),
        }
        if self.auto_relaunch:
            self.maybe_relaunch_in_venv()
        return summary

    def ensure_virtualenv(self) -> str:
        """Create the virtual environment if missing."""

        assert self.venv_dir is not None  # typing guard
        if self.venv_dir.exists():
            self._feedback("Virtuelle Umgebung gefunden – wird genutzt.")
            return "vorhanden"

        self._feedback("Erstelle virtuelle Umgebung (eigener Arbeitsraum)...")
        try:
            venv.create(self.venv_dir, with_pip=True, clear=False)
        except Exception as exc:  # pragma: no cover - defensive
            self._feedback(f"Fehler beim Erstellen der Umgebung: {exc}")
            raise
        self._feedback("Virtuelle Umgebung bereit.")
        return "erstellt"

    def install_dependencies(self) -> str:
        """Install dependencies from requirements.txt inside the venv."""

        assert self.venv_dir is not None
        assert self.requirements_file is not None
        python_bin = self._python_executable()

        if not python_bin.exists():
            self._feedback("Kein Python in der Umgebung gefunden – Installation übersprungen.")
            return "fehlend"

        if not self.requirements_file.exists():
            self._feedback("Keine requirements.txt gefunden – Standardbibliothek reicht aus.")
            return "übersprungen"

        lines = [line.strip() for line in self.requirements_file.read_text(encoding="utf-8").splitlines()]
        if not any(line and not line.startswith("#") for line in lines):
            self._feedback("Requirements-Datei ist leer – Installation nicht nötig.")
            return "übersprungen"

        pip_ready = self._run_command([str(python_bin), "-m", "pip", "--version"], "pip bereit")
        if not pip_ready:
            self._run_command([str(python_bin), "-m", "ensurepip", "--upgrade"], "pip nachinstalliert")
        cmd = [
            str(python_bin),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "-r",
            str(self.requirements_file),
        ]
        installed = self._run_command(cmd, "Abhängigkeiten installiert")
        if not installed:
            self._feedback(
                "Installationskonflikt erkannt – starte automatische Reparatur (Neuinstallation)."
            )
            repaired_status, repaired_info = self.repair_dependencies(force_reinstall=True)
            self._feedback(f"Konfliktlösung: {repaired_info}")
            return repaired_status

        dep_status, dep_info = self.self_check.run_dependency_probe()
        self._feedback(f"Abhängigkeitsprüfung: {dep_info}")
        if dep_status != "ok":
            self._feedback(
                "Abhängigkeitswarnung erkannt – starte automatische Neuinstallation zur Konfliktbehebung."
            )
            repaired_status, repaired_info = self.repair_dependencies(force_reinstall=True)
            self._feedback(f"Konfliktlösung: {repaired_info}")
            return repaired_status
        return "ok"

    def repair_dependencies(self, *, force_reinstall: bool = False) -> tuple[str, str]:
        """Attempt to heal dependency conflicts in a transparent way."""

        assert self.requirements_file is not None
        python_bin = self._python_executable()
        if not python_bin.exists():
            return "warnung", "Python in virtueller Umgebung fehlt – Reparatur übersprungen"
        if not self.requirements_file.exists():
            return "übersprungen", "Keine requirements.txt – nichts zu reparieren"

        reinstall_cmd = [str(python_bin), "-m", "pip", "install", "--upgrade"]
        if force_reinstall:
            reinstall_cmd.append("--force-reinstall")
        reinstall_cmd += ["-r", str(self.requirements_file)]
        reinstall = self._run_command(
            reinstall_cmd, "Abhängigkeiten wurden automatisch neu aufgebaut"
        )
        if not reinstall:
            return "warnung", "Neuinstallation nicht erfolgreich – bitte Log prüfen"

        dep_status, dep_info = self.self_check.run_dependency_probe()
        final_status = dep_status if dep_status in {"ok", "warnung"} else "warnung"
        return final_status, dep_info

    def self_check_report(self) -> str:
        """Run self-healing checks for folders and code format."""

        status = self.self_check.full_check()
        for line in self.self_check.human_summary(status):
            self._feedback(f"Selbstprüfung: {line}")
        for key, value in status.items():
            if key.endswith("_info"):
                readable_key = key.replace("_info", " (Details)")
            else:
                readable_key = key
            self._feedback(f"Selbstprüfung {readable_key}: {value}")
        return status.get("gesamt", "warnung")

    def maybe_relaunch_in_venv(self) -> None:
        """Restart the process inside the venv for a seamless user flow."""

        assert self.venv_dir is not None
        venv_python = self.venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python"
        if not venv_python.exists():
            self._feedback("Neustart nicht möglich – Python in Umgebung fehlt.")
            return
        if os.environ.get("MOD_TOOL_BOOTSTRAPPED") == "1":
            return
        current = pathlib.Path(sys.executable).resolve()
        if current == venv_python.resolve():
            return
        self._feedback("Starte automatisch in der virtuellen Umgebung neu...")
        env = os.environ.copy()
        env["MOD_TOOL_BOOTSTRAPPED"] = "1"
        os.execv(venv_python, [str(venv_python), *sys.argv])

    def _python_executable(self) -> pathlib.Path:
        """Return the Python interpreter path inside the virtual environment."""

        assert self.venv_dir is not None
        if os.name == "nt":  # pragma: no cover - Windows path
            return self.venv_dir / "Scripts" / "python.exe"
        return self.venv_dir / "bin" / "python"

    def _run_command(self, cmd: list[str], success_message: str) -> bool:
        """Run a subprocess command and return success state."""

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError:  # pragma: no cover - defensive
            self._feedback("Kommando nicht gefunden – bitte Python prüfen.")
            return False
        if result.returncode == 0:
            self._feedback(success_message)
            return True
        self._feedback(f"Befehl fehlgeschlagen: {result.stderr.strip()}")
        return False

    def _feedback(self, message: str) -> None:
        self.messages.append(message)
        self.feedback(message)

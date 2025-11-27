"""Automated self-check and self-repair routines."""
from __future__ import annotations

import datetime
import json
import compileall
import pathlib
import subprocess
import sys
from typing import Iterable

from .manifest import ManifestWriter, default_structure_manifest
from .themes import ThemeManager


class SelfCheck:
    """Ensures required paths exist and performs lightweight validation."""

    def __init__(
        self,
        required_paths: Iterable[pathlib.Path | str],
        base_path: pathlib.Path | None = None,
        manifest_path: pathlib.Path | str | None = None,
        test_timeout_seconds: int = 30,
    ) -> None:
        base = pathlib.Path(base_path) if base_path else pathlib.Path.cwd()
        if not base.exists():  # pragma: no cover - defensive guard
            raise ValueError("Basisverzeichnis fehlt oder ist ungültig")
        self.base_path = base
        self.required_paths = []
        for path in required_paths:
            target = pathlib.Path(path)
            if not target.is_absolute():
                target = base / target
            self.required_paths.append(target)
        self.manifest_path = pathlib.Path(manifest_path) if manifest_path else self.base_path / "manifest.json"
        self.test_timeout_seconds = int(test_timeout_seconds)

    def ensure_required_paths(self) -> dict[str, str]:
        """Create missing folders and confirm availability."""

        results: dict[str, str] = {}
        for path in self.required_paths:
            if path.exists():
                results[str(path)] = "vorhanden"
            else:
                path.mkdir(parents=True, exist_ok=True)
                results[str(path)] = "automatisch erstellt"
        return results

    def quick_health_report(self) -> str:
        """Return a short status summary and self-heal if required."""

        missing = [str(p) for p in self.required_paths if not p.exists()]
        if missing:
            self.ensure_required_paths()
            return f"Fehlende Pfade repariert: {', '.join(missing)}"
        return "Alle Pflichtpfade verfügbar"

    def manifest_version_stamp(self) -> str:
        """Return a time-based version stamp for manifest updates."""

        return datetime.datetime.now().strftime("%Y.%m.%d-%H%M")

    def run_code_format_check(self) -> bool:
        """Run a syntax-only compile check for the code base."""

        target = self.base_path / "mod_tool"
        if not target.exists():
            return False
        return bool(compileall.compile_dir(str(target), quiet=1))

    def run_optional_linters(self) -> str:
        """Run optional formatters/linters when available without breaking flow."""

        available_tools: list[str] = []
        for tool in ("ruff", "black"):
            try:
                result = subprocess.run(
                    [sys.executable, "-m", tool, "--version"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except FileNotFoundError:
                continue
            if result.returncode == 0:
                available_tools.append(tool)

        if not available_tools:
            return "keine optionalen Lint-Tools gefunden"

        reports: list[str] = []
        for tool in available_tools:
            cmd = [sys.executable, "-m", tool]
            if tool == "ruff":
                cmd += ["check", str(self.base_path / "mod_tool")]
            elif tool == "black":
                cmd += ["--check", str(self.base_path / "mod_tool")]

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            status = "ok" if result.returncode == 0 else "warnung"
            reports.append(f"{tool}: {status}")
        return ", ".join(reports)

    def run_dependency_probe(self) -> tuple[str, str]:
        """Validate installed dependencies with a time-bounded ``pip check`` run."""

        timeout = max(self.test_timeout_seconds // 2, 5)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
        except FileNotFoundError:
            return "übersprungen", "pip nicht verfügbar – Abhängigkeitsprüfung ausgelassen"
        except subprocess.TimeoutExpired:
            return "warnung", f"Abhängigkeitsprüfung nach {timeout}s gestoppt (Timeout)"

        if result.returncode == 0:
            return "ok", "Abhängigkeiten laut pip check konsistent"

        detail = (result.stderr.strip() or result.stdout.strip() or "pip check meldete Hinweise").splitlines()[0]
        return "warnung", f"pip check meldet Hinweise: {detail}"

    def run_quick_tests(self) -> tuple[str, str]:
        """Execute lightweight unit tests if available and time-bound for responsiveness."""

        tests_dir = self.base_path / "tests"
        if not tests_dir.exists():
            return "übersprungen", "Keine Tests gefunden"

        try:
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir)],
                capture_output=True,
                text=True,
                check=False,
                timeout=max(self.test_timeout_seconds, 1),
            )
        except subprocess.TimeoutExpired:
            return "abgebrochen", f"Tests nach {self.test_timeout_seconds}s automatisch gestoppt (Timeout)"

        status = "ok" if result.returncode == 0 else "warnung"
        raw_output = result.stdout.strip() or result.stderr.strip() or "Keine Testausgabe vorhanden"
        first_line = raw_output.splitlines()[0] if raw_output else ""
        output = (
            "Tests erfolgreich (Kurzlauf)"
            if status == "ok"
            else f"Tests mit Hinweisen: {first_line}"
        )
        return status, output

    def run_quality_suite(self) -> tuple[str, str]:
        """Run the full quality suite (pytest) with friendly messaging."""

        tests_dir = self.base_path / "tests"
        if not tests_dir.exists():
            return "übersprungen", "Kein Tests-Ordner – Qualitätssuite entfällt"

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", str(tests_dir)],
                capture_output=True,
                text=True,
                check=False,
                timeout=max(self.test_timeout_seconds, 10),
            )
        except FileNotFoundError:
            return "übersprungen", "pytest nicht installiert – Qualitätssuite ausgelassen"
        except subprocess.TimeoutExpired:
            return "warnung", f"Qualitätssuite nach {self.test_timeout_seconds}s gestoppt (Timeout)"

        summary_line = (result.stdout or result.stderr).splitlines()[:2]
        headline = summary_line[0] if summary_line else "Keine Ausgabe"
        status = "ok" if result.returncode == 0 else "warnung"
        return status, headline

    def full_check(self) -> dict[str, str]:
        """Perform folder repair, syntax validation, and smoke tests."""

        path_status = self.ensure_required_paths()
        code_ok = self.run_code_format_check()
        path_status["code_format"] = "ok" if code_ok else "kompilierungswarnung"

        tests_status, tests_info = self.run_quick_tests()
        path_status["tests"] = tests_status
        path_status["tests_info"] = tests_info
        quality_status, quality_info = self.run_quality_suite()
        path_status["qualität"] = quality_status
        path_status["qualität_info"] = quality_info
        path_status["linting"] = self.run_optional_linters()
        dep_status, dep_info = self.run_dependency_probe()
        path_status["abhängigkeiten"] = dep_status
        path_status["abhängigkeiten_info"] = dep_info
        manifest_status, manifest_msg = self.ensure_manifest_file()
        path_status["manifest"] = manifest_status
        if manifest_msg:
            path_status["manifest_info"] = manifest_msg
        accessibility = ThemeManager.accessibility_report()
        path_status["accessibility"] = accessibility["status"]
        path_status["accessibility_notes"] = accessibility["details"]
        path_status["gesamt"] = self.classify_overall(path_status)
        return path_status

    def classify_overall(self, status: dict[str, str]) -> str:
        """Return ok/warnung/fehler based on the collected results."""

        warn_states = {"warnung", "kompilierungswarnung", "abgebrochen", "teilweise"}
        error_states = {"fehlgeschlagen", "fehler"}
        overall = "ok"
        for key, value in status.items():
            if key.endswith("_info"):
                continue
            if value in error_states:
                return "fehler"
            if value in warn_states:
                overall = "warnung"
        return overall

    def ensure_manifest_file(self) -> tuple[str, str]:
        """Create or validate the JSON manifest for transparency."""

        if not self.manifest_path:
            return "übersprungen", "Kein Manifestpfad konfiguriert"

        content = ""
        try:
            content = self.manifest_path.read_text(encoding="utf-8")
            if content.strip():
                versions = self._extract_manifest_versions(json.loads(content))
                return "vorhanden", f"Manifest geprüft ({versions})"
        except FileNotFoundError:
            content = ""
        except (json.JSONDecodeError, ValueError):
            pass

        manifest = default_structure_manifest()
        stamp = self.manifest_version_stamp()
        manifest.version = stamp
        manifest.layout_manifest.version = stamp
        writer = ManifestWriter(self.manifest_path)
        writer.write(manifest)
        return "erstellt", f"Manifest neu erstellt (Version {stamp})"

    def read_manifest_versions(self) -> str:
        """Return human-friendly manifest versions or a fallback text."""

        if not self.manifest_path or not self.manifest_path.exists():
            return "Manifest fehlt – wird beim Start erzeugt"
        try:
            content = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return self._extract_manifest_versions(content)
        except (json.JSONDecodeError, ValueError):
            return "Manifest unlesbar – Autoreparatur aktiv"
        except OSError:
            return "Manifest nicht lesbar"

    def human_summary(self, status: dict[str, str]) -> list[str]:
        """Translate raw status values into laienfreundliche Sätze."""

        messages: list[str] = []
        for key, value in status.items():
            if key.endswith("_info"):
                continue
            headline = self._friendly_headline(key, value, status)
            messages.append(headline)
        return messages

    def _friendly_headline(self, key: str, value: str, status: dict[str, str]) -> str:
        readable = key.replace("_", " ")
        severity = {
            "ok": "OK",
            "vorhanden": "OK",
            "automatisch erstellt": "OK",
            "erstellt": "OK",
            "übersprungen": "Hinweis",
            "warnung": "Warnung",
            "kompilierungswarnung": "Warnung",
            "abgebrochen": "Warnung",
            "fehlgeschlagen": "Fehler",
            "fehler": "Fehler",
        }.get(value, value.capitalize())

        detail_key = f"{key}_info"
        detail = status.get(detail_key, "")
        if key == "tests" and value == "übersprungen":
            detail = detail or "Keine Tests gefunden – weiter mit den anderen Checks"
        if key == "qualität" and value == "warnung":
            detail = detail or "Qualitätssuite hat Hinweise ausgegeben"
        if key == "linting" and value.startswith("keine"):
            detail = detail or "Linting ist optional – kein Handlungsbedarf"
        if key == "abhängigkeiten" and value == "übersprungen":
            detail = detail or "pip check ist optional – kann später nachinstalliert werden"
        if key == "abhängigkeiten" and value == "warnung":
            detail = detail or "Bitte Fehlermeldung aus pip check prüfen"
        detail_text = f" – {detail}" if detail else ""
        return f"{severity}: {readable}{detail_text}"

    def _extract_manifest_versions(self, manifest_data: dict) -> str:
        """Return a combined version string for structure and layout sections."""

        if not isinstance(manifest_data, dict):
            raise ValueError("Manifestdaten fehlen oder sind ungültig")
        structure = manifest_data.get("structure_manifest", {})
        layout = manifest_data.get("layout_manifest", {})
        structure_version = structure.get("version", "unbekannt")
        layout_version = layout.get("version", "unbekannt")
        if not structure_version or not layout_version:
            raise ValueError("Manifest-Versionen fehlen – Neuaufbau nötig")
        return f"Struktur v{structure_version}, Layout v{layout_version}"

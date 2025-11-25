"""Automated self-check and self-repair routines."""
from __future__ import annotations

import compileall
import pathlib
import subprocess
import sys
from typing import Iterable


class SelfCheck:
    """Ensures required paths exist and performs lightweight validation."""

    def __init__(self, required_paths: Iterable[pathlib.Path | str], base_path: pathlib.Path | None = None) -> None:
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

    def run_code_format_check(self) -> bool:
        """Run a syntax-only compile check for the code base."""

        target = self.base_path / "mod_tool"
        if not target.exists():
            return False
        return bool(compileall.compile_dir(str(target), quiet=1))

    def run_quick_tests(self) -> tuple[str, str]:
        """Execute lightweight unit tests if available."""

        tests_dir = self.base_path / "tests"
        if not tests_dir.exists():
            return "übersprungen", "Keine Tests gefunden"

        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        status = "ok" if result.returncode == 0 else "fehlgeschlagen"
        output = result.stdout.strip() or result.stderr.strip()
        return status, output

    def full_check(self) -> dict[str, str]:
        """Perform folder repair, syntax validation, and smoke tests."""

        path_status = self.ensure_required_paths()
        code_ok = self.run_code_format_check()
        path_status["code_format"] = "ok" if code_ok else "kompilierungswarnung"

        tests_status, _ = self.run_quick_tests()
        path_status["tests"] = tests_status
        return path_status

"""Automated self-check and self-repair routines."""
from __future__ import annotations

import compileall
import pathlib
from typing import Iterable


class SelfCheck:
    """Ensures required paths exist and performs lightweight validation."""

    def __init__(self, required_paths: Iterable[pathlib.Path | str], base_path: pathlib.Path | None = None) -> None:
        base = pathlib.Path(base_path) if base_path else pathlib.Path.cwd()
        if not base.exists():  # pragma: no cover - defensive guard
            raise ValueError("Basisverzeichnis fehlt oder ist ungültig")
        self.base_path = base
        self.required_paths = [base / pathlib.Path(path) for path in required_paths]
    def __init__(self, required_paths: Iterable[str]) -> None:
        self.required_paths = [pathlib.Path(path) for path in required_paths]

    def ensure_required_paths(self) -> dict[str, str]:
        results: dict[str, str] = {}
        for path in self.required_paths:
            if path.exists():
                results[str(path)] = "vorhanden"
            else:
                path.mkdir(parents=True, exist_ok=True)
                results[str(path)] = "automatisch erstellt"
        return results

    def quick_health_report(self) -> str:
        missing = [str(p) for p in self.required_paths if not p.exists()]
        if missing:
            self.ensure_required_paths()
            return f"Fehlende Pfade repariert: {', '.join(missing)}"
        return "Alle Pflichtpfade verfügbar"

    def run_code_format_check(self) -> bool:
        """Runs a syntax-only compile check to keep code consistent."""

        target = self.base_path / "mod_tool"
        return compileall.compile_dir(str(target), quiet=1)
        return compileall.compile_dir("mod_tool", quiet=1)

    def full_check(self) -> dict[str, str]:
        path_status = self.ensure_required_paths()
        code_ok = self.run_code_format_check()
        path_status["code_format"] = "ok" if code_ok else "kompilierungswarnung"
        return path_status

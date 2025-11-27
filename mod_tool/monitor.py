"""Background health monitor with start/stop controls."""
from __future__ import annotations

import threading
from typing import Callable

from .self_check import SelfCheck


class HealthMonitor:
    """Periodically call ``SelfCheck.quick_health_report`` and log the outcome."""

    def __init__(
        self,
        self_check: SelfCheck,
        logger: Callable[[str], None],
        *,
        interval_seconds: int = 5,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds muss größer als 0 sein")
        if not callable(logger):
            raise ValueError("Logger muss aufrufbar sein")
        self.self_check = self_check
        self.logger = logger
        self.interval_seconds = float(interval_seconds)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        """Start the monitor if not already active."""

        if self._thread and self._thread.is_alive():
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def stop(self, *, timeout: float = 1.0) -> bool:
        """Request stop and wait for the background thread to finish."""

        if not self._thread:
            return False
        self._stop_event.set()
        self._thread.join(timeout)
        stopped = not self._thread.is_alive()
        if stopped:
            self._thread = None
        return stopped

    def _run(self) -> None:
        while not self._stop_event.wait(self.interval_seconds):
            status = self.self_check.quick_health_report()
            self.logger(f"Hintergrund-Monitor: {status}")

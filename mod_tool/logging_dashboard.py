"""Logging utilities and on-screen console."""
from __future__ import annotations

import logging
import queue
import tkinter as tk
from tkinter import ttk
from typing import Callable


class QueueHandler(logging.Handler):
    """A logging handler that sends records to a queue."""

    def __init__(self, log_queue: queue.Queue[logging.LogRecord]):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put(record)


class LoggingPanel(ttk.Frame):
    """Simple text area that consumes logging records."""

    def __init__(
        self,
        parent: tk.Widget,
        log_queue: queue.Queue[logging.LogRecord],
        record_filter: Callable[[logging.LogRecord], bool] | None = None,
    ) -> None:
        super().__init__(parent)
        self.log_queue = log_queue
        self.text = tk.Text(self, height=6, state="disabled", wrap="word")
        self.text.pack(fill=tk.BOTH, expand=True)
        self._running = False
        self._record_filter = record_filter

    def start(self) -> None:
        self._running = True
        self._poll_queue()

    def stop(self) -> None:
                self._running = False

    def _poll_queue(self) -> None:
        if not self._running:
            return
        try:
            while True:
                record = self.log_queue.get_nowait()
                if self._record_filter and not self._record_filter(record):
                    continue
                message = f"{record.levelname}: {record.getMessage()}\n"
                self._append(message)
        except queue.Empty:
            pass
        self.after(200, self._poll_queue)

    def _append(self, message: str) -> None:
        if not self.winfo_exists():
            return
        # ensure UI updates run on the main thread to avoid TclError
        self.after(0, self._insert_message, message)

    def _insert_message(self, message: str) -> None:
        if not self.winfo_exists():
            return
        self.text.configure(state="normal")
        self.text.insert(tk.END, message)
        self.text.configure(state="disabled")
        self.text.see(tk.END)


class LoggingManager:
    """Coordinates application logging and dashboard output."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.log_queue: queue.Queue[logging.LogRecord] = queue.Queue()
        self.panel: LoggingPanel | None = None
        self.handler = QueueHandler(self.log_queue)
        self._debug_enabled = False
        self._level_threshold = logging.INFO

    def attach(self, parent: tk.Widget) -> None:
        self.panel = LoggingPanel(parent, self.log_queue, record_filter=self.should_display_record)
        self.panel.pack(fill=tk.BOTH, expand=True)

    def start_logging(self) -> None:
        logging.basicConfig(level=logging.DEBUG, handlers=[self.handler])
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        self._apply_logging_level()
        logging.info("Live-Logging aktiviert")
        if self.panel:
            self.panel.start()

    def set_debug(self, enabled: bool) -> None:
        self._debug_enabled = enabled
        self._apply_logging_level()
        logging.getLogger(__name__).info(
            "Debugmodus %s", "aktiv" if enabled else "deaktiviert"
        )

    def set_level_threshold(self, level_name: str) -> str:
        if not level_name or not isinstance(level_name, str):
            raise ValueError("Log-Level fehlt")
        resolved = getattr(logging, level_name.upper(), None)
        if not isinstance(resolved, int):
            raise ValueError(f"Unbekannter Log-Level: {level_name}")
        self._level_threshold = resolved
        self._apply_logging_level()
        level_label = logging.getLevelName(resolved)
        self.log_system(f"Log-Filter: ab {level_label}")
        return level_label

    def should_display_record(self, record: logging.LogRecord | None) -> bool:
        if not isinstance(record, logging.LogRecord):
            return False
        return record.levelno >= self._level_threshold

    def _apply_logging_level(self) -> None:
        target = logging.DEBUG if self._debug_enabled else logging.INFO
        logging.getLogger().setLevel(target)

    def log_system(self, message: str) -> None:
        logging.getLogger(__name__).info(message)

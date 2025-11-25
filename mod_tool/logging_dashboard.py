"""Logging utilities and on-screen console."""
from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
from tkinter import ttk


class QueueHandler(logging.Handler):
    """A logging handler that sends records to a queue."""

    def __init__(self, log_queue: queue.Queue[logging.LogRecord]):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put(record)


class LoggingPanel(ttk.Frame):
    """Simple text area that consumes logging records."""

    def __init__(self, parent: tk.Widget, log_queue: queue.Queue[logging.LogRecord]):
        super().__init__(parent)
        self.log_queue = log_queue
        self.text = tk.Text(self, height=6, state="disabled", wrap="word")
        self.text.pack(fill=tk.BOTH, expand=True)
        self._running = False

    def start(self) -> None:
        self._running = True
        threading.Thread(target=self._poll_queue, daemon=True).start()

    def stop(self) -> None:
        self._running = False

    def _poll_queue(self) -> None:
        while self._running:
            try:
                record = self.log_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            message = f"{record.levelname}: {record.getMessage()}\n"
            self._append(message)

    def _append(self, message: str) -> None:
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

    def attach(self, parent: tk.Widget) -> None:
        self.panel = LoggingPanel(parent, self.log_queue)
        self.panel.pack(fill=tk.BOTH, expand=True)

    def start_logging(self) -> None:
        logging.basicConfig(level=logging.INFO, handlers=[self.handler])
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.info("Live-Logging aktiviert")
        if self.panel:
            self.panel.start()

    def set_debug(self, enabled: bool) -> None:
        self._debug_enabled = enabled
        level = logging.DEBUG if enabled else logging.INFO
        logging.getLogger().setLevel(level)
        logging.getLogger(__name__).info(
            "Debugmodus %s", "aktiv" if enabled else "deaktiviert"
        )

    def log_system(self, message: str) -> None:
        logging.getLogger(__name__).info(message)

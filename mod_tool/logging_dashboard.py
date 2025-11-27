"""Logging utilities and on-screen console."""
from __future__ import annotations

import logging
import queue
from collections import deque
import tkinter as tk
from tkinter import ttk
from typing import Callable


class QueueHandler(logging.Handler):
    """A logging handler that sends records to a queue and observers."""

    def __init__(
        self,
        log_queue: queue.Queue[logging.LogRecord],
        on_record: Callable[[logging.LogRecord], None] | None = None,
    ) -> None:
        super().__init__()
        self.log_queue = log_queue
        self._on_record = on_record

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put(record)
        if self._on_record:
            try:
                self._on_record(record)
            except Exception:
                # Beobachter müssen die Anzeige nicht blockieren
                pass


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


class RecentLogPanel(ttk.Frame):
    """Shows the latest log entries with colour-coded levels."""

    def __init__(self, parent: tk.Widget, *, max_rows: int = 10) -> None:
        super().__init__(parent)
        self.max_rows = max_rows
        self.tree = ttk.Treeview(self, columns=("level", "message"), show="headings", height=max_rows)
        self.tree.heading("level", text="Level")
        self.tree.heading("message", text="Nachricht")
        self.tree.column("level", width=80, anchor="center")
        self.tree.column("message", anchor="w")

        y_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.tag_configure("positive", foreground="#15803d")
        self.tree.tag_configure("warning", foreground="#b45309")
        self.tree.tag_configure("negative", foreground="#b91c1c")

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def render(self, records: list[logging.LogRecord]) -> None:
        self.tree.delete(*self.tree.get_children())
        for record in records[-self.max_rows :]:
            tag = self._tag_for_level(record.levelno)
            self.tree.insert(
                "",
                "end",
                values=(record.levelname, record.getMessage()),
                tags=(tag,),
            )

    @staticmethod
    def _tag_for_level(level: int) -> str:
        if level >= logging.ERROR:
            return "negative"
        if level >= logging.WARNING:
            return "warning"
        return "positive"


class LoggingManager:
    """Coordinates application logging and dashboard output."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.log_queue: queue.Queue[logging.LogRecord] = queue.Queue()
        self.panel: LoggingPanel | None = None
        self.recent_panel: RecentLogPanel | None = None
        self._recent_records: deque[logging.LogRecord] = deque(maxlen=10)
        self.handler = QueueHandler(self.log_queue, on_record=self._remember_record)
        self._debug_enabled = False
        self._level_threshold = logging.INFO

    def attach(self, parent: tk.Widget) -> None:
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Letzte 10 Log-Einträge (live)", style="Helper.TLabel").pack(
            anchor="w"
        )

        self.recent_panel = RecentLogPanel(container)
        self.recent_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        ttk.Separator(container, orient="horizontal").pack(fill=tk.X, pady=4)

        ttk.Label(container, text="Volle Log-Ansicht", style="Helper.TLabel").pack(anchor="w")
        self.panel = LoggingPanel(container, self.log_queue, record_filter=self.should_display_record)
        self.panel.pack(fill=tk.BOTH, expand=True)

        self._render_recent()

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

    def _remember_record(self, record: logging.LogRecord) -> None:
        self._recent_records.append(record)
        self._render_recent()

    def _render_recent(self) -> None:
        if not self.recent_panel:
            return
        self.recent_panel.render(list(self._recent_records))

    @property
    def recent_messages(self) -> list[str]:
        """Expose last messages for tests and status panels."""

        return [record.getMessage() for record in self._recent_records]

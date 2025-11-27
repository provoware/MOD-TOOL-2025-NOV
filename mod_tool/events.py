"""Event tracing utilities for transparent, validated status reporting."""
from __future__ import annotations

import dataclasses
import datetime as _dt
from collections import deque
from typing import Deque, Iterable, List

_ALLOWED_SEVERITIES = {"debug", "info", "warn", "error"}


@dataclasses.dataclass(frozen=True)
class Event:
    """Simple event record with validation-friendly fields."""

    name: str
    message: str
    severity: str = "info"
    source: str = "system"
    timestamp: _dt.datetime = dataclasses.field(
        default_factory=lambda: _dt.datetime.now(_dt.timezone.utc)
    )

    def __post_init__(self) -> None:
        if not str(self.name).strip():
            raise ValueError("Event name darf nicht leer sein")
        if not str(self.message).strip():
            raise ValueError("Event message darf nicht leer sein")
        severity = self.severity.lower()
        if severity not in _ALLOWED_SEVERITIES:
            raise ValueError(f"Unbekannte Severity '{self.severity}'")
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "source", str(self.source or "system"))

    @property
    def iso_time(self) -> str:
        """Return the timestamp in ISO format without milliseconds."""

        return self.timestamp.replace(microsecond=0).isoformat()

    def to_line(self) -> str:
        """Human friendly, screenreader-ready line for dashboards and logs."""

        return f"{self.iso_time} [{self.severity.upper()}] {self.name}: {self.message}"


class EventTrace:
    """Circular buffer of events for dashboards, tests, and audits."""

    def __init__(self, *, max_events: int = 50) -> None:
        if max_events <= 0:
            raise ValueError("max_events muss größer als 0 sein")
        self._events: Deque[Event] = deque(maxlen=max_events)
        self._max_events = max_events

    @property
    def max_events(self) -> int:
        return self._max_events

    def record(self, name: str, message: str, *, severity: str = "info", source: str = "system") -> Event:
        """Add a validated event and return it for further processing."""

        event = Event(name=name, message=message, severity=severity, source=source)
        self._events.append(event)
        return event

    def extend(self, events: Iterable[Event]) -> None:
        for event in events:
            if not isinstance(event, Event):
                raise ValueError("Nur Event-Objekte können hinzugefügt werden")
            self._events.append(event)

    def snapshot(self) -> List[Event]:
        """Return a copy of all buffered events in chronological order."""

        return list(self._events)

    def as_lines(self) -> list[str]:
        """Render buffered events as screenreader-friendly lines."""

        return [event.to_line() for event in self._events]

    def latest(self) -> Event | None:
        """Return the newest event or None if the buffer is empty."""

        return self._events[-1] if self._events else None


def render_event_digest(events: Iterable[Event]) -> str:
    """Create a condensed summary (name + severity) for status labels."""

    parts = [f"{event.name} ({event.severity})" for event in events]
    return ", ".join(parts) if parts else "Keine Ereignisse protokolliert"

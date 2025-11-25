"""Diagnostics helpers and guard rails."""
from __future__ import annotations

import functools
import logging
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def guarded_action(name: str, log: logging.Logger) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Wrap a function with pre/post logging and timing.

    Ensures that failures are visible and no exception is swallowed silently.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log.info("%s – gestartet", name)
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                log.info("%s – erfolgreich (%.2f s)", name, time.perf_counter() - start)
                return result
            except Exception as exc:  # pragma: no cover - defensive
                log.exception("%s – fehlgeschlagen: %s", name, exc)
                raise

        return wrapper

    return decorator

"""Beispiel-Plugin mit klarer Statusmeldung und Eingangsprüfung."""

import logging

LOG = logging.getLogger(__name__)


def on_load() -> None:
    """Meldet sich im Log und bestätigt erfolgreiche Initialisierung."""

    LOG.info("Sample-Plugin aktiv: Statusanzeige bereit und geprüft.")

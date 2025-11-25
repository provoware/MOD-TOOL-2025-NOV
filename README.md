# MOD-TOOL-2025-NOV – Steuerzentrale

Modulare, barrierearme Steuerzentrale mit Live-Logging, automatischer Selbstprüfung und Plugin-Unterstützung.

## Starten (mit Autopilot)
- `python main.py` reicht: Das Tool legt automatisch eine virtuelle Umgebung
  (eigener Python-Arbeitsraum) an, springt hinein und installiert die
  Abhängigkeiten aus `requirements.txt`. Fortschritt wird im Terminal angezeigt.
- Pflichtordner (`logs/`, `plugins/`, `config/`) werden repariert oder erstellt.
- Ein Syntax-Check (`compileall`, prüft Quelltext) läuft vor dem GUI-Start.
- Hintergrundüberwachung liefert Live-Status im Logging-Panel.
## Starten
```bash
python main.py
```

## Automatische Prüfungen
- Beim Start werden Pflichtordner (`logs/`, `plugins/`, `config/`) angelegt.
- Syntax-Check via `compileall` sichert Konsistenz.
- Hintergrundüberwachung protokolliert Gesundheitsmeldungen im Logging-Panel.

## Tests
```bash
python -m unittest discover
```

## Hinweise für Einsteiger
- Themes im Kopfbereich wechseln, um bestes Farb- und Kontrastverhalten zu finden.
- Rote Eingaben bedeuten: Feld ausfüllen; dunkle Schrift bedeutet gültig.
- Log-Bereich zeigt alle Schritte klar und transparent, ideal zum Debuggen.

Weitere Details siehe `docs/DEVELOPER_GUIDE.md`.

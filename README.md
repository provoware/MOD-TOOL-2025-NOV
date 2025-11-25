# MOD-TOOL-2025-NOV – Steuerzentrale

Modulare, barrierearme Steuerzentrale mit Live-Logging, automatischer Selbstprüfung und Plugin-Unterstützung.

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

Weitere Details siehe `docs/DEVELOPER_GUIDE.md`.

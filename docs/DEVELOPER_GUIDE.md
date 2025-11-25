# Entwicklerhandbuch – MOD Tool Steuerzentrale

## Ziele
- Maximale Barrierefreiheit mit klarer Sprache und wählbaren Themes (fünf Varianten mit hohem Kontrast).
- Modularer Aufbau: Header, vier gleich große Arbeitsbereiche, dreigeteilte Fußzeile (Debug, Logging, Infos).
- Live-Logging über eine Queue, sichere Guard-Funktionen (`guarded_action`) und Selbstheilung (`SelfCheck`).
- Plugin-fähigkeit über den `plugins/`-Ordner (Python-Module mit optionaler `on_load`-Funktion).
- Vollautomatische Prüfungen beim Start: Verzeichnis-Existenz, Syntax-Check via `compileall`.

## Projektstruktur
- `main.py`: Startet die GUI über `ControlCenterApp` und ruft die Startroutine auf.
- `mod_tool/bootstrap.py`: Autostart (virtuelle Umgebung, Abhängigkeits-Installation,
  Selbstprüfung) mit laienfreundlichem Feedback.
- `main.py`: Startet die GUI über `ControlCenterApp`.
- `mod_tool/app.py`: Orchestriert Themes, Logging, Layout, Plugins und Selbstprüfungen.
- `mod_tool/layout.py`: Baut Header, 2x2-Arbeitsbereich und Fußleiste auf.
- `mod_tool/themes.py`: Enthält die fünf barrierefreien Themes.
- `mod_tool/logging_dashboard.py`: Realzeit-Logging mit Queue-Handler und Panel.
- `mod_tool/self_check.py`: Selbstheilung (Ordner anlegen) und Syntax-Check.
- `mod_tool/plugins.py`: Minimaler Plugin-Loader für `plugins/*.py`.
- `mod_tool/diagnostics.py`: Dekorator `guarded_action` für Vor/Nach-Logging und Timing.
- `mod_tool/validator.py`: Validierende Eingabefelder mit Platzhaltern und Fehlermarkierung.
- `tests/`: Unittests für Layout, Guard-Checks und Selbstheilung.
- `docs/DEVELOPER_GUIDE.md`: Dieses Dokument.
- `todo.txt`: Laufende Aufgabenliste, nach jedem Change aktualisieren.

## Best Practices
- **Einfache Sprache:** Nutzertexte in Klartext, Fachbegriffe in Klammern mit kurzem Hinweis.
- **Validierung:** Jede Funktion prüft Eingaben; Eingabefelder wechseln Farbe bei Fehlern.
- **Logging:** Nutze `LoggingManager.log_system` für Statusmeldungen; echte Aktionen über `guarded_action` schützen.
- **Layout-Standards:** Nur `ttk`-Widgets verwenden; Grid-Layout mit `uniform` sorgt für gleich große Paneels.
- **Themes:** Neue Themes in `ThemeManager.THEMES` ergänzen; `apply_theme` ruft automatische Hintergrund-Propagation.
- **Plugins:** Python-Dateien in `plugins/` ablegen; optional `on_load()` implementieren. Fehler werden geloggt.
- **Selbstprüfungen:** `SelfCheck.full_check()` in automatischen Routinen nutzen; erzeugt fehlende Ordner.
- **Tests:** `python -m unittest discover` ausführen. Tests skippen sich selbst, wenn Tk nicht initialisiert werden kann.

## Automatische Prüfungen & Codequalität
- `SelfCheck.run_code_format_check()` ruft `compileall` auf, um Syntaxfehler früh zu melden.
- `Bootstrapper.run()` erstellt `.venv`, installiert Abhängigkeiten und startet bei Bedarf
  automatisch in der Umgebung neu.
- Ergänzende Tools können in einem `Makefile` oder CI angebunden werden (z. B. `ruff`, `black`).
- Logging-Ausgaben dienen als Live-Debug- und Compliance-Protokoll.

## Layout-Responsivität
- Fenster minimal 960x640, nutzt Grid-Weights für dynamisches Skalieren.
- Texte besitzen `wraplength`, damit Hinweise auch auf kleineren Bildschirmen lesbar bleiben.

## Erweiterbarkeit
- Neue Module im `mod_tool/`-Namespace hinzufügen und über den Header/Arbeitsbereich andocken.
- Fußzeile ist bewusst dreigeteilt; neue Widgets dort platzieren, um Diagnose/Hilfe/Monitoring getrennt zu halten.

## Tests starten
```bash
python -m unittest discover
```

## Tipps für Laien
- Ändere Themes im Header-Dropdown für bestes Kontrastgefühl.
- Nutze das Eingabefeld im Header: rote Schrift = Eingabe fehlt, dunkle Schrift = gültig.
- Log-Bereich zeigt alle Aktionen in Echtzeit; bei Fehlern erscheinen klare Meldungen.
- Startroutine zeigt jeden Schritt im Terminal (virtuelle Umgebung, Installation, Checks).

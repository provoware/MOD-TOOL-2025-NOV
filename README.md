# MOD-TOOL-2025-NOV – Steuerzentrale

Modulare, barrierearme Steuerzentrale mit Live-Logging, automatischer Selbstprüfung und Plugin-Unterstützung.
Jetzt mit "Klick & Start"-Routine, Debug/Logging-Umschalter und Schnellcheck-Schaltfläche für sofortige Sichtbarkeit.

## Starten (mit Autopilot)
- `python main.py` reicht: Das Tool legt automatisch eine virtuelle Umgebung
  (eigener Python-Arbeitsraum) an, springt hinein und installiert die
  Abhängigkeiten aus `requirements.txt`. Fortschritt wird im Terminal angezeigt.
- Pflichtordner (`logs/`, `plugins/`, `config/`) werden repariert oder erstellt.
- Ein Syntax-Check (`compileall`, prüft Quelltext) läuft vor dem GUI-Start.
- Neu: Eine vollautomatische Startroutine mit Statusanzeige zeigt Schritt für
  Schritt an, was gerade passiert (virtuelle Umgebung, Pakete, Selbstprüfung).
  Konflikte in Abhängigkeiten werden automatisch behoben (`--force-reinstall`),
  der Fortschritt wird laienfreundlich zusammengefasst.
- Die Klick-&-Start-Schaltfläche im Header triggert alle Prüfungen erneut (inkl. Plugins & Tests)
  und protokolliert verständlich.
- Hintergrundüberwachung liefert Live-Status im Logging-Panel.

## Statusanzeige & Laienhinweise (einfache Sprache)
- Jede Startroutine meldet eine kompakte Statusanzeige (Statusboard) mit
  Klartext: "OK" oder "Warnung" plus kurzer Erklärung in Klammern
  (z. B. "Abhängigkeiten: OK – alles neu installiert").
- Begriffe werden direkt erklärt: virtuelle Umgebung = isolierter Arbeitsraum,
  Pip-Check = Konfliktprüfer, Manifest = Fahrplan für Layout und Struktur.
- Drei Farb-Themes mit geprüften Kontrasten stehen bereit (Aurora, Neon,
  Invertiert); die Kontrastprüfung läuft beim Start und beim Theme-Wechsel.
- Debug-/Logging-Modus lässt sich im Header umschalten, damit Fehler transparent
  bleiben. Alle Schritte landen im Log (Protokollbereich) und sind rückverfolgbar.

## Manifest & Layout-Doku
- Die aktuelle Struktur (Automationsschritte, Health-Checks) und das Layout (Header, vier Panels, Fußleiste)
  stehen in `manifest.json` im Projektordner.
- Der Inhalt wird bei jedem Start automatisch aktualisiert. Manuell aktualisieren geht in einem Schritt:
  ```bash
  python - <<'PY'
  from mod_tool.manifest import ManifestWriter, default_structure_manifest
  ManifestWriter("manifest.json").write(default_structure_manifest())
  print("Manifest erneuert.")
  PY
  ```

## Zusätzliche Prüfungen für Codequalität
- Syntax-Check (`compileall`) läuft automatisch über `mod_tool/`.
- Unittests decken Self-Check, Plugins und das Manifest ab: `python -m unittest discover`.
  Ein Timeout stoppt blockierende Tests automatisch und schreibt den Hinweis ins Log.
- Format-Hinweis: Für optionale Formatierung können `ruff` oder `black` in `.venv` installiert und ausgeführt werden.

## Plugins
- Beispiel-Plugin liegt unter `plugins/sample_status.py` und meldet sich beim Laden im Log.
- Eigene Plugins: Neue `.py`-Datei in `plugins/` ablegen und optional eine `on_load()`-Funktion definieren.
- Der Plugin-Report im Logging zeigt für jedes Plugin den Status (geladen/übersprungen/Fehler) und erstellt den Ordner bei Bedarf automatisch.

## Starten
```bash
python main.py
```

## Automatische Prüfungen
- Beim Start werden Pflichtordner (`logs/`, `plugins/`, `config/`) angelegt.
- Syntax-Check via `compileall` sichert Konsistenz.
- Hintergrundüberwachung protokolliert Gesundheitsmeldungen im Logging-Panel.

## Genres-Tool (Zufalls-Ideen)
- Über `Werkzeuge > Genres-Tool öffnen` oder die Sidebar-Kachel `Genres` starten.
- Profile mit Genres, Stimmungen und Stilen anlegen, Duplikate werden automatisch abgefangen.
- Zufallsauswahl mit Kopierfunktion, Log-Export und Dark-Mode-Schalter inklusive.

## Tests
```bash
python -m unittest discover
```

## Hinweise für Einsteiger
- Themes im Kopfbereich wechseln, um bestes Farb- und Kontrastverhalten zu finden.
- Rote Eingaben bedeuten: Feld ausfüllen; dunkle Schrift bedeutet gültig.
- Log-Bereich zeigt alle Schritte klar und transparent, ideal zum Debuggen.
- Tipp: Wenn etwas hakt, einfach `python main.py` erneut starten – die Startroutine repariert Ordner,
  installiert fehlende Pakete und schreibt das Manifest neu.
- Schnellbefehle (einfach nach Tippfehler kopieren und einfügen):
  - `python main.py` – startet die Oberfläche, richtet fehlende Ordner/Manifest automatisch.
  - `python -m unittest discover` – führt die kurzen Selbsttests aus (Stoppt automatisch bei Timeout).
  - `python -m pytest -q tests` – ausführlichere Qualitätssuite (falls `pytest` installiert ist).
  - `python -m pip check` – prüft Abhängigkeiten, meldet Konflikte im Klartext.
  - `python -m black --check mod_tool` / `python -m ruff check mod_tool` – optionale Format-/Stilkontrolle.

Weitere Details siehe `docs/DEVELOPER_GUIDE.md`.

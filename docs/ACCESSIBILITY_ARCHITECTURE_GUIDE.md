# Leitfaden: Barrierefreie Offline-Werkbank (MOD Tool)

Dieser Leitfaden beschreibt, wie du ein laienfreundliches, vollständig offline
nutzbares Tool mit Header-Dashboard, vier gleich großen Arbeitsflächen und
klarer Fußzeile aufbaust. Er ergänzt das Entwicklerhandbuch mit konkreten
Best-Practices, klaren Begriffserklärungen und Prüfschritten, damit das Tool auf
allen gängigen Systemen stabil läuft.

## Zielbild
- **Offline & ohne Cloud/KI:** Alle Funktionen laufen lokal, keine Telemetrie.
- **Ein-Nutzer-Betrieb:** Keine Mehrbenutzer- oder Netzwerkabhängigkeiten.
- **Modularer Kern:** Hauptmodul mit Header (Dashboard), 2x2-Arbeitsbereich und
  dreigeteilter Fußbereich (Debug, Hinweise, Systeminfos).
- **Erweiterbar:** Module für Archiv, Vorlagen, Genre-Generator, Editor,
  ToDo-Liste, Links-Archiv, Vorschau, Konsole, Suche, Backup, Import/Export
  und Logs lassen sich später andocken.
- **Barrierefrei:** Hoher Kontrast, Tastaturbedienung, klare Fokus-Reihenfolge,
  selbsterklärende Texte (Fachbegriffe in Klammern), skalierbare Schrift.
- **Robust & fehlertolerant:** Automatisches Speichern, Selbstheilung bei
  Fehlern, nie hartes Abbrechen.

## Empfohlene Struktur
- `main.py`: Startdatei, ruft das Hauptfenster auf.
- `setup.py` oder `setup.sh`: Setup-Datei, prüft Abhängigkeiten offline, fragt
  nach Bestätigung (z. B. "Ja, fehlendes Paket installieren?").
- `mod_tool/app.py`: Orchestrator, der Header, Layout, Themes, Logging und
  Selbstprüfungen verbindet.
- `mod_tool/layout.py`: Baut Header + 4 Arbeitsbereiche + Fußleiste; nutzt
  `grid` mit `uniform`-Werten, damit alle Bereiche gleich groß sind.
- `mod_tool/themes.py`: Gemeinsame Farb- und Kontrastregeln; jede Farbe prüft
  den AA/AAA-Kontrast.
- `mod_tool/plugins.py`: Lädt Module aus `plugins/` (Archiv, Genre-Generator,
  Editor, etc.). Jedes Plugin validiert Eingaben und liefert klares Ergebnis.
- `mod_tool/self_check.py`: Prüft Ordner, Manifest, Syntax und Tests; kann
  fehlende Abhängigkeiten reparieren (Selbstheilung).
- `mod_tool/tool_index.py`: Zeigt alle Module/Funktionen als Index im Header-
  Menü.
- `tests/`: Automatisierte Tests für Layout, Validierung, Plugins und CLI.
- `logs/` und `backups/`: Lokale Datenhaltung; keine Cloud.

## Dashboard-Aufbau (Header)
- **Statuszeile:** Klartext, z. B. "Autostart fertig – Pfade ok, Tests ok".
- **Bedienelemente (Controls):** Start (Startroutine), Gesundheitstest,
  Debug/Logging-Schalter, Theme-Auswahl, Index-Button.
- **Eingabefelder:** Validierung beim Verlassen ("focusout"), Farbumschlag bei
  Fehlern, klare Fehlermeldung in einfacher Sprache.

## Arbeitsbereiche (4 gleich große Panels)
- **Links oben:** Schnellaktionen (z. B. Vorlagen, Genre-Zufalls-Generator mit
  Profilwahl wie "HardTechno", "Chill").
- **Rechts oben:** Editor/Notizen, Songtext-Entwurf mit Profil-Auswahl.
- **Links unten:** Archiv/Datei-Organisation mit Vorschau (Bild/Audio) und
  Umbenennen-Funktion.
- **Rechts unten:** Backup/Import/Export, Größenübersicht, Konsole (Befehl-
  Anzeige, keine Remote-Befehle), Links-Archiv.

## Fußbereich (dreiteilig)
1. **Debug/Logs:** Live-Logging, Filter für Fehler/Warnungen, Log-Export
   (Datei speichern).
2. **Hinweise/Hilfe:** Tooltips (Kurzinfo), Status in Klartext, Tipp des Tages.
3. **Systemdaten:** Speicherbedarf, Dateimengen, letzte Sicherung, Auto-Save-
   Countdown (z. B. alle 5 Minuten).

## Automatische Startroutine
- Prüft: Python-Version, Tk-Installation, Schreibrechte für Projektordner,
  vorhandene Unterordner (`logs`, `plugins`, `config`, `backups`).
- Repariert: Legt fehlende Ordner an, erneuert Manifest, räumt kaputte
  Plugin-Caches auf.
- Tests: Führt Syntax-Check (`compileall`), optionale Format-/Lint-Checks
  (`ruff`, `black`) und Unittests aus. Ergebnisse in Klartext loggen.
- Nutzerfeedback: Jeder Schritt meldet sich im Log und im Header-Status; fragt
  nur dann nach Bestätigung, wenn wirklich etwas installiert werden muss.

## Bedienkonzept & Barrierefreiheit
- **Fokus-Reihenfolge (Tab):** Header-Steuerung -> Panels (im Uhrzeigersinn) ->
  Fußzeile. Keine versteckten Elemente.
- **Kontraste:** Mindestens WCAG AA, besser AAA. Themes: Hell, Dunkel,
  Kontrastreich, Blautöne, Sepia.
- **Schrift & Größen:** Mindestschriftgröße 12pt, skalierbar; Buttons mit
  Mindesthöhe 32px.
- **Tastaturkürzel:** F1 = Hilfe, F5 = Schnellcheck, F9 = Debug an/aus, Ctrl+S
  = Speichern.
- **Sprache:** Fachbegriffe erklären (z. B. "Manifest (Strukturplan der
  Oberfläche)").

## Selbstheilung & Fehlertoleranz
- **Guarded Actions:** Jede kritische Aktion über einen Schutz-Wrapper
  ausführen, der Ausnahmen abfängt und Lösungsvorschläge loggt.
- **Automatisches Speichern:** Alle 5 Minuten, beim Verlassen eines Feldes und
  beim Schließen des Fensters.
- **Fallbacks:** Bei fehlenden Plugins Dummy-Funktionen anzeigen (mit Hinweis
  "Modul nicht installiert – bitte über Setup hinzufügen").
- **Debug-Modus:** Umschaltbar; zeigt Stacktraces und Schritt-für-Schritt-
  Aktionen im Log.

## Modulrichtlinien (für Archiv, Vorlagen, Genre-Profile)
- **Eingangsvalidierung:** Prüfe Dateipfade, Profilnamen und Auswahlfelder; bei
  Fehlern klare Meldung + markiertes Feld.
- **Ergebnisprüfung:** Bestätige erfolgreiche Aktionen ("Datei umbenannt"),
  zeige Alternativen bei Fehlschlag.
- **Profil-Archiv:** JSON/YAML-Datei lokal speichern (z. B. `config/genres.json`
  mit Profilen wie "HardTechno", "Chill", "Hörspiel", "Favoriten").
- **Vorlagen:** Ablage in `templates/`; Bearbeitung nur lokal.
- **Konvertierung:** Nutze plattformunabhängige Bibliotheken (reine Python oder
  portable Wheels), keine System-Tools erzwingen.

## Test-Strategie (vollautomatisch, offline)
- **Unit-Tests:** Layout-Beschreibung, Eingabevalidierung, Plugin-Laden,
  Selbstcheck, Manifest-Erzeugung.
- **Format/Lint:** `python -m compileall`, `python -m ruff check`,
  `python -m black --check` (nur wenn installiert).
- **End-to-End-Light:** Startroutine im "Dry-Run" ausführen, Log-Ausgaben
  prüfen (kein echtes Netz, keine Cloud).
- **Akustik/Screenreader:** Kurze Texte, sinnvolle `title`/`aria`-Labels an
  Widgets (sofern Toolkit es unterstützt).

## Backups, Import/Export & Datenlage
- **Ablageorte wählbar:** Pfade in `config/settings.json` speichern; immer
  absolute Pfade loggen.
- **Backups:** Zeitstempel-Ordner unter `backups/`; keine Überschreibung ohne
  Nachfrage.
- **Logs:** Tagesbasierte Log-Dateien (`logs/YYYY-MM-DD.log`) plus Export-Button
  im UI.

## Benutzerfreundliche Befehle
- Start (GUI): `python main.py`
- Setup (Abhängigkeitsprüfung): `python setup.py --check` oder `./setup.sh`
- Tests: `python -m unittest discover`
- Format optional: `python -m ruff check` / `python -m black --check`

## Laien-Tipps
- Themes über den Header wechseln, bis der Kontrast angenehm ist.
- Fehlertexte genau lesen: sie bieten immer eine Lösung, nie nur einen Abbruch.
- Vor dem Schließen kurz warten, bis "Auto-Save fertig" im Log steht.
- Bei Fragen: Hilfe-Panel öffnen (F1) – dort stehen alle Schritte in Klartext.

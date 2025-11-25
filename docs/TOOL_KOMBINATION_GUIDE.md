# Kombinationsleitfaden: System-Layer, Module, UI & A11y

Kurzübersicht in einfacher Sprache (Fachbegriffe in Klammern): Alle Vorgaben lassen sich sauber schichten: unten die Startroutine mit Auto-Prüfungen, in der Mitte ein stabiles Daten- und Plugin-Layer, oben ein barrierefreies UI mit einheitlichem Designsystem.

## 1) Schichtenmodell
- **System- & Start-Layer**: `mod_tool/bootstrap.py` erstellt/aktiviert automatisch die virtuelle Umgebung (venv) und installiert Abhängigkeiten. `SelfCheck` prüft Pfade, Manifest und Syntax. Ergebnisse werden als Klartextstatus im Dashboard gezeigt.
- **Daten-Layer**: `DashboardState`, `TodoManager` und `GenreArchive` teilen sich dieselbe Basis (`logs/`, `config/`, Profilordner). Jede Schreibaktion sollte einen Schema-Check (Strukturprüfung) und ein Backup des letzten Stands auslösen.
- **Modul-/Plugin-Layer**: `PluginManager` lädt Module aus `plugins/`, prüft und meldet sie. Kernmodule (Dashboard, Genres & Archiv, Zufall) folgen derselben API (`load`, `save_state`, `on_load`). Fehler werden protokolliert, Module können sicher deaktiviert werden.
- **UI- & A11y-Layer (Barrierefreiheit)**: `DashboardLayout` + `ThemeManager` setzen das einheitliche Layout um (Header, 2x2/3x3-Panels per `QSplitter`-Äquivalent via `ttk`-`PanedWindow`), Tabs (Dashboard • Genres & Archiv • Zufall), Fokusrahmen, große Klickflächen. `ZoomManager` liefert Strg+Mausrad-Zoom (9–28 pt) und einen 150%-Großtextmodus.

## 2) Start- & Self-Check-Routine (vollautomatisch)
1. **Auto-venv & Auto-Install**: `python main.py` reicht. Bootstrap prüft die Umgebung, legt bei Bedarf `.venv` an und installiert `requirements.txt` (sicherer Offline-Modus, keine Telemetrie).
2. **Vorprüfung**: Ordner (`logs`, `plugins`, `config`, Profilordner) werden angelegt. `manifest.json` wird mit `ManifestWriter` erstellt/verglichen.
3. **Self-Check & Tests**: Syntax-Check (`compileall`), optionale Format/Lint-Checks, dann `python -m unittest discover` als Kurzprüfung. Status im Header: OK/Warnung/Fehler + Kurztext.
4. **Plugin-Scan**: Module laden, Version/Abhängigkeit prüfen, fehlerhafte Module isolieren („deaktiviert, Details im Debug-Tab“).
5. **UI-Feedback**: Ampel im Header, Klartextmeldung, Log-Panel protokolliert jeden Schritt. Laien sehen: „System ok / Problem automatisch behoben“.

## 3) Daten- & Backup-Strategie (datensicher)
- **Profile**: Eigene Datenräume (`profile_<name>/config.json`, `data/`, `backups/`). Beim Profilwechsel den Speicherpfad im `DashboardState` umschalten.
- **Schreibwege**: Vor jedem Speichern Schema prüfen; nach jedem Speichern Integritäts-Check + Backup-Rotation (z. B. letzte 5 Stände). Beschädigte Dateien automatisch aus Backup wiederherstellen (klare Meldung im Log).
- **Validierung**: Jede Funktion validiert Eingaben und Erfolgsausgabe (Rückgabe prüfen, klare Fehlermeldungen). `Validator`-Felder färben sich bei Fehlern.

## 4) Modul- & Plugin-Handbuch
- **Referenz-Module**: Dashboard, Genres & Archiv, Zufall nutzen die gleiche Struktur: `init_module(app_context)`, `save_state()`, `load_state()`, Fehler → Log + Hinweistext.
- **Auto-Handling**: Beim Start Plugins scannen, signalisieren (OK/Warnung/Fehler). Toggles im UI („aktiv/inaktiv“). Keine Erweiterung kann das Haupttool blockieren, weil Fehler abgefangen und geloggt werden.
- **Erweiterung**: Neue Module in `plugins/` ablegen, optional `on_load()` für Initialprüfungen. Konsistentes Styling über `ThemeManager.apply_theme` sicherstellen.

## 5) UI, Themes & Barrierefreiheit (moderne Optik)
- **Grundlayout**: Header mit Profilwahl, Status-LED, Schnellzugriff (Einstellungen, Debug, Hilfe). Mitte: flexible Paneels mit `ttk.PanedWindow` + ScrollAreas; Footer dreigeteilt (Log, Hinweise, Systemstatus). Tabs: Dashboard • Genres & Archiv • Zufall.
- **Designsystem**: Dunkles Standard-Theme + High-Contrast + Light + Neon/Trash-Style. Hohe Kontraste (≥ 4.5:1), klare Typografie, große Klickziele. Fokusrahmen deutlich sichtbar; Tastaturbedienung vollständig möglich.
- **A11y-Extras**: Strg+Mausrad-Zoom, 150%-Großtext, Farbsimulator (Protan/Deutan/Tritan) im Debug-Tab, Tastaturnavigation dokumentiert. Alle Meldungen in Klartext, Fachbegriffe erklärt.

## 6) Vollautomatische Sicherheit & Monitoring
- **Autosave**: Intervall 2–5 Minuten + manuelles Speichern mit Zeitstempel. Undo/Redo bleibt erhalten. Statusleiste zeigt letzten Speichervorgang.
- **Monitoring**: Fehlerzähler, langsame Module, Speicherwarnungen im Debug-Tab. Beim Beenden: letzter Autosave, temporäre Dateien aufräumen, Sitzungsprotokoll schreiben.
- **Logging/Debugging**: `LoggingManager` für UI-Logs, `guarded_action` für sichere Aktionen (Vor/Nach-Logging, Timing). Debug-Modus im Menü schaltet ausführlichere Protokolle frei.

## 7) Tests & Codequalität (vollautomatisch)
- **Schnellbefehl** (Laien-tauglich):
  ```bash
  python -m unittest discover
  ```
- **Optional (falls installiert)**: `ruff .` (Linting), `black .` (Format), `python -m compileall .` (Syntax). In CI oder Startroutine einbinden, Ergebnisse im Dashboard anzeigen.
- **Eingabe-Checks**: Jede neue Funktion erhält einen kurzen Vorher/Nachher-Test (z. B. für Profile, Backups, Plugins).

## 8) Laienfreundliche Tipps & Kommandos
- Starten reicht mit `python main.py` – das Tool richtet alles ein (venv, Install, Checks).
- Themes bei Blendung wechseln; Zoom per Strg+Mausrad. Großtext-Knopf oben rechts für schnelle 150%-Ansicht.
- Bei Fehlermeldung zuerst den Debug-Tab öffnen: Klartext-Hinweis + Lösungsschritt. Backups lassen sich im Datei-Menü direkt anstoßen.
- Profile nutzen, um getrennte Arbeitsumgebungen zu halten (z. B. „Lyrics“, „Video“, „Archiv“). Jedes Profil hat eigene Daten & Backups.
- Plugins nur aus vertrauenswürdigen Quellen nutzen; fehlerhafte Plugins werden blockiert, ohne das Haupttool zu stoppen.

## 9) Empfohlene Implementierungsreihenfolge (stabil & wartbar)
1. Architekturdiagramm aktualisieren (System/Daten/Modul/UI-Schicht). 
2. Startdiagnose festziehen: Auto-venv, Auto-Install, Self-Check, Tests → Status ins Dashboard. 
3. Datensicherheit erhärten: Schema-Checks, Backup-Rotation, automatische Recovery. 
4. UI/Themes verfeinern: High-Contrast als Default, Neon/Trash als Optionen; Fokusrahmen & Tastaturpfade prüfen. 
5. Referenz-Module vereinheitlichen: gleiche API, gleiche Fehlertexte, A11y-Prüfung. 
6. Plugin-Toggles & Statusanzeigen abschließen; Debug-Tab um Farbsimulator und A11y-Checkliste erweitern. 
7. Tests automatisieren (unittest + optional ruff/black) und Ergebnisse im Header spiegeln.

## 10) Standards zur Wartbarkeit
- Trenne Tool-Logik klar: Bootstrap (Start), Self-Check (Prüfen/Heilen), Daten-Manager (Profile/Backups), Plugins (Erweiterungen), UI (Layout/Themes/A11y).
- Keine Netzwerkpflicht, keine Telemetrie. Alles offline-fähig halten.
- Jede neue Funktion validiert Eingaben und prüft Erfolgsausgabe, Log bei Fehlversuch.
- Einheitliche Fehlermeldungen: „Was ist passiert?“, „Was wurde automatisch behoben?“, „Was kann ich tun?“

So bleibt das Tool maximal flexibel, datensicher, vollautomatisch und optisch modern – ohne Laien zu überfordern.

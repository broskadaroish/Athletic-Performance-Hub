# Windows-Installer bauen — Schritt-für-Schritt

## Voraussetzungen (einmalig installieren)

| Software | Version | Download |
|---|---|---|
| **Python** | 3.10 oder neuer | https://python.org → „Add Python to PATH" aktivieren |
| **Inno Setup 6** | 6.x | https://jrsoftware.org/isdl.php |

> **Wichtig:** Python muss in der PATH-Variable des Systems eingetragen sein.
> Beim Python-Installer das Häkchen „Add Python to PATH" setzen.

---

## Build starten

1. Diesen Ordner (`installer\`) öffnen
2. **`build.bat`** doppelklicken
3. Warten — beim ersten Mal dauert der Build 5–15 Minuten
4. Nach dem Build öffnet sich automatisch der `dist\`-Ordner

### Ergebnis

```
artifacts\athletik\dist\
└── BruceFootball_Setup_v1.0.0.exe   ← fertige Setup-Datei
```

---

## Was der Build-Prozess macht

```
build.bat
  │
  ├── 1. Python & pip prüfen
  ├── 2. Python-Pakete installieren (requirements.txt + PyInstaller)
  ├── 3. PyInstaller → dist\BruceFootballDiagnostics\  (alle Dateien)
  ├── 4. Inno Setup prüfen
  ├── 5. Inno Setup → dist\BruceFootball_Setup_v1.0.0.exe
  └── 6. dist\-Ordner öffnen
```

---

## Installation auf dem Ziel-PC

1. `BruceFootball_Setup_v1.0.0.exe` starten
2. Installationsassistenten folgen
3. Fertig — die App öffnet sich im Browser unter `http://localhost:85xx`

### Was installiert wird

| Pfad | Inhalt |
|---|---|
| `C:\Program Files\Bruce Football Performance Diagnostics\` | Programmdateien |
| `%APPDATA%\BruceFootballDiagnostics\` | Benutzerdaten |

### Benutzerdaten-Ordner (`%APPDATA%\BruceFootballDiagnostics\`)

```
BruceFootballDiagnostics\
├── athletik.db          ← SQLite-Datenbank (alle Spieler, Tests, Pläne)
├── Berichte\            ← exportierte PDF-Berichte
├── Trainingspläne\      ← exportierte Trainingspläne
├── Backups\             ← manuelle Datenbank-Backups
└── Logs\                ← Anwendungsprotokolle
```

> **Diese Daten werden bei Updates und Deinstallationen nicht gelöscht.**

---

## Update auf neue Version

1. Neue `BruceFootball_Setup_vX.X.X.exe` starten
2. Installer überschreibt die Programmdateien
3. Alle Benutzerdaten in `%APPDATA%\BruceFootballDiagnostics\` bleiben erhalten

---

## Fehlersuche

### Python nicht gefunden
```
FEHLER: Python wurde nicht gefunden.
```
→ Python neu installieren, dabei „Add Python to PATH" aktivieren.
→ Danach Eingabeaufforderung neu starten.

### Inno Setup nicht gefunden
```
FEHLER: Inno Setup wurde nicht gefunden.
```
→ Inno Setup 6 von https://jrsoftware.org/isdl.php installieren.
→ Der PyInstaller-Build liegt trotzdem in `dist\BruceFootballDiagnostics\` und kann manuell gestartet werden.

### PyInstaller-Fehler (fehlende Module)
Falls Module fehlen: in `athletik.spec` unter `hiddenimports` das fehlende Paket eintragen.

### App startet nicht / Browser öffnet sich nicht
1. `BruceFootballDiagnostics.exe` direkt aus dem Installationsordner starten
2. Konsolenausgabe auf Fehlermeldungen prüfen
3. Port-Konflikt: Die App sucht automatisch einen freien Port (8501–8600)

---

## Icon austauschen

Das App-Icon liegt unter:
```
artifacts\athletik\assets\icon.ico
```
Einfach die Datei ersetzen (gleiches Format: `.ico`, 256×256 px empfohlen)
und den Build erneut starten.

---

## Dateien in diesem Ordner

| Datei | Zweck |
|---|---|
| `build.bat` | Einziger Startpunkt — alles in einem Doppelklick |
| `athletik.spec` | PyInstaller-Konfiguration |
| `setup.iss` | Inno Setup-Skript |
| `launcher.py` | Windows-Startprogramm (startet Streamlit, öffnet Browser) |
| `README_BUILD.md` | Diese Anleitung |

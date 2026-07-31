# Bruce Football Performance Diagnostics — Windows Build-Anleitung

## Voraussetzungen (auf einem Windows-PC)

1. **Python 3.11+** — https://www.python.org/downloads/
2. **PyInstaller** — `pip install pyinstaller`
3. **Inno Setup 6** — https://jrsoftware.org/isinfo.php

## Schritte

### 1. Abhängigkeiten installieren
```cmd
pip install -r requirements.txt
pip install pyinstaller
```

### 2. Executable erstellen (PyInstaller)
```cmd
cd artifacts\athletik
pyinstaller build\bruce_football.spec
```
→ Ergebnis: `dist\BruceFootball\BruceFootballPerformanceDiagnostics.exe`

### 3. Icon bereitstellen
Lege das Icon als `assets\icon.ico` ab (256×256 px, .ico-Format).

### 4. Installer erstellen (Inno Setup)
- Öffne `build\setup.iss` in Inno Setup
- Klicke **Build → Compile**
→ Ergebnis: `build\Output\BruceFootballPerformanceDiagnostics_Setup_v1.0.exe`

## Release-Struktur

```
Bruce Football Performance Diagnostics\
├── Release\
│   └── BruceFootballPerformanceDiagnostics.exe
├── Setup\
│   └── BruceFootballPerformanceDiagnostics_Setup_v1.0.exe
├── Dokumentation\
│   ├── Installationsanleitung.pdf
│   └── Aenderungsprotokoll.pdf
├── Icons\
│   └── icon.ico  ← hier ablegen
└── Backup\
```

## Copyright
© 2026 Broska Daroish. Alle Rechte vorbehalten.

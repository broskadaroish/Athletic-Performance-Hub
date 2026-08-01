# Windows-Installer erstellen

## Voraussetzungen (auf Windows)

| Programm | Download |
|---|---|
| **Inno Setup 6** | https://jrsoftware.org/isdl.php |
| Internetverbindung | Python + Pakete werden automatisch geladen |

---

## Schritte

### 1. Ordner auf Windows kopieren
Kopiere den **kompletten `athletik/`-Ordner** vom Replit-Projekt auf deinen Windows-PC.  
(Download über Replit → drei Punkte → „Download as zip")

### 2. Installer-Build starten
Öffne den Ordner `athletik\installer\` und doppelklicke:

```
build_installer.bat
```

> Das Script läuft **5–10 Minuten** (je nach Internetgeschwindigkeit).  
> Ein Konsolenfenster zeigt den Fortschritt.

### 3. Setup.exe finden
Nach Abschluss öffnet sich automatisch der Ordner:
```
athletik\installer\Output\
    BruceFootball_Setup_v1.0.0.exe   ← Das ist die fertige Setup.exe
```

---

## Was der Installer macht

- Installiert in `C:\Users\<Name>\AppData\Local\Programs\BruceFootballDiagnostics\`
- Kopiert Python (embedded, ca. 80 MB) + alle Pakete + die App
- Erstellt Startmenü-Eintrag mit App-Icon
- Erstellt optional Desktop-Verknüpfung
- Erstellt optional Autostart-Eintrag
- Daten (Datenbank, Vereinslogo) werden in `%APPDATA%\BruceFootballDiagnostics\` gespeichert

## App starten (nach Installation)

- Doppelklick auf Desktop-Verknüpfung **oder**
- Startmenü → „Bruce Football Performance Diagnostics"
- Browser öffnet sich automatisch auf `http://localhost:8501`

## App beenden

- Startmenü → „Bruce Football Performance Diagnostics beenden"

---

## Häufige Probleme

| Problem | Lösung |
|---|---|
| VBScript wird blockiert | `launcher.bat` direkt starten oder per Doppelklick |
| Port 8501 belegt | Anderen Prozess beenden oder Port in `launcher.vbs` ändern |
| Inno Setup nicht gefunden | Pfad in `build_installer.bat` Zeile ~22 anpassen |
| Python-Download schlägt fehl | Firewall/Proxy prüfen oder Python manuell herunterladen |

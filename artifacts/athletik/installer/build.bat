@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Bruce Football — Build

echo.
echo ============================================================
echo   Bruce Football Performance Diagnostics — Installer Build
echo ============================================================
echo.

:: ── Verzeichnis: Installer-Ordner als Ausgangspunkt ──────────────────────────
cd /d "%~dp0"
set "INSTALLER_DIR=%~dp0"
set "APP_DIR=%~dp0.."
set "DIST_DIR=%APP_DIR%\dist\BruceFootballDiagnostics"
set "ICON=%APP_DIR%\assets\icon.ico"

:: ── 1. Python prüfen ──────────────────────────────────────────────────────────
echo [1/6] Python prüfen...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  FEHLER: Python wurde nicht gefunden.
    echo  Bitte Python 3.10 oder neuer installieren: https://python.org
    echo  Wichtig: "Add Python to PATH" beim Setup aktivieren!
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('python --version') do echo  Gefunden: %%V

:: ── 2. Abhängigkeiten installieren ───────────────────────────────────────────
echo.
echo [2/6] Python-Pakete installieren...
python -m pip install --upgrade pip --quiet
python -m pip install -r "%APP_DIR%\requirements.txt" --quiet
if errorlevel 1 (
    echo  FEHLER beim Installieren der Abhängigkeiten.
    pause
    exit /b 1
)

:: Zusätzliche Pakete die im requirements.txt fehlen könnten
python -m pip install pyinstaller pillow matplotlib --quiet
echo  Pakete installiert.

:: ── 3. PyInstaller ausführen ─────────────────────────────────────────────────
echo.
echo [3/6] PyInstaller — App bündeln...
echo  (Dieser Schritt dauert 5–15 Minuten beim ersten Mal)
echo.

:: Alten Build entfernen
if exist "%APP_DIR%\dist\BruceFootballDiagnostics" (
    rmdir /s /q "%APP_DIR%\dist\BruceFootballDiagnostics"
)
if exist "%APP_DIR%\build\BruceFootballDiagnostics" (
    rmdir /s /q "%APP_DIR%\build\BruceFootballDiagnostics"
)

python -m PyInstaller "%INSTALLER_DIR%\athletik.spec" --distpath "%APP_DIR%\dist" --workpath "%APP_DIR%\build" --noconfirm

if errorlevel 1 (
    echo.
    echo  FEHLER: PyInstaller ist fehlgeschlagen.
    echo  Bitte die Ausgabe oben auf Fehlermeldungen prüfen.
    pause
    exit /b 1
)

:: Prüfen ob die EXE erstellt wurde
if not exist "%DIST_DIR%\BruceFootballDiagnostics.exe" (
    echo  FEHLER: BruceFootballDiagnostics.exe wurde nicht erstellt.
    pause
    exit /b 1
)
echo  PyInstaller erfolgreich abgeschlossen.

:: ── 4. Inno Setup prüfen ─────────────────────────────────────────────────────
echo.
echo [4/6] Inno Setup prüfen...

set "ISCC="
for %%P in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
) do (
    if exist %%P set "ISCC=%%P"
)

if not defined ISCC (
    echo.
    echo  FEHLER: Inno Setup wurde nicht gefunden.
    echo  Bitte Inno Setup 6 installieren: https://jrsoftware.org/isdl.php
    echo.
    echo  Der PyInstaller-Build liegt bereits fertig in:
    echo  %DIST_DIR%
    echo.
    pause
    exit /b 1
)
echo  Gefunden: %ISCC%

:: ── 5. Inno Setup — Setup.exe erstellen ──────────────────────────────────────
echo.
echo [5/6] Inno Setup — Setup.exe erstellen...

:: Output-Verzeichnis für Setup.exe
if not exist "%APP_DIR%\dist" mkdir "%APP_DIR%\dist"

%ISCC% /Q "%INSTALLER_DIR%\setup.iss" /O"%APP_DIR%\dist" /DAppVersion=1.0.0

if errorlevel 1 (
    echo.
    echo  FEHLER: Inno Setup ist fehlgeschlagen.
    pause
    exit /b 1
)

:: Prüfen ob Setup.exe erstellt wurde
if not exist "%APP_DIR%\dist\BruceFootball_Setup_v1.0.0.exe" (
    echo  FEHLER: Setup.exe wurde nicht erstellt.
    pause
    exit /b 1
)

:: ── 6. Ergebnis ───────────────────────────────────────────────────────────────
echo.
echo [6/6] Build abgeschlossen.
echo.
echo ============================================================
echo   FERTIG!
echo.
echo   Setup.exe:
echo   %APP_DIR%\dist\BruceFootball_Setup_v1.0.0.exe
echo ============================================================
echo.

:: dist\-Ordner öffnen
explorer "%APP_DIR%\dist"

endlocal
pause

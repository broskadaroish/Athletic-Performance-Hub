@echo off
REM ============================================================
REM Bruce Football Performance Diagnostics — Windows Build-Script
REM Dieses Skript muss auf einem Windows-PC mit Python + PyInstaller
REM und Inno Setup ausgeführt werden.
REM ============================================================

echo.
echo ============================================================
echo  Bruce Football Performance Diagnostics — Build v1.0.0
echo  Copyright (c) 2026 Broska Daroish
echo ============================================================
echo.

REM Ins Projektverzeichnis wechseln (artifacts\athletik)
cd /d "%~dp0.."

REM Abhängigkeiten prüfen
echo [1/4] Pruefe Abhaengigkeiten...
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet
echo     OK.

REM PyInstaller ausführen
echo [2/4] Erstelle Executable (PyInstaller)...
pyinstaller build\bruce_football.spec --clean --noconfirm
if errorlevel 1 (
    echo FEHLER: PyInstaller fehlgeschlagen.
    pause
    exit /b 1
)
echo     OK — dist\BruceFootball\BruceFootballPerformanceDiagnostics.exe erstellt.

REM Inno Setup ausführen (ISCC muss im PATH sein)
echo [3/4] Erstelle Installer (Inno Setup)...
where ISCC >nul 2>&1
if errorlevel 1 (
    echo WARNUNG: Inno Setup (ISCC.exe) nicht gefunden.
    echo Bitte manuell: Oeffne build\setup.iss in Inno Setup und kompiliere.
) else (
    ISCC build\setup.iss
    if errorlevel 1 (
        echo FEHLER: Inno Setup fehlgeschlagen.
        pause
        exit /b 1
    )
    echo     OK — build\Output\BruceFootballPerformanceDiagnostics_Setup_v1.0.exe erstellt.
)

REM Release-Struktur erstellen
echo [4/4] Erstelle Release-Struktur...
if not exist "Release"       mkdir Release
if not exist "Setup"         mkdir Setup
if not exist "Dokumentation" mkdir Dokumentation
if not exist "Icons"         mkdir Icons
if not exist "Backup"        mkdir Backup

copy "dist\BruceFootball\BruceFootballPerformanceDiagnostics.exe" "Release\" >nul
if exist "build\Output\BruceFootballPerformanceDiagnostics_Setup_v1.0.exe" (
    copy "build\Output\BruceFootballPerformanceDiagnostics_Setup_v1.0.exe" "Setup\" >nul
)
echo     OK.

echo.
echo ============================================================
echo  Build abgeschlossen!
echo  Executable : Release\BruceFootballPerformanceDiagnostics.exe
echo  Installer  : Setup\BruceFootballPerformanceDiagnostics_Setup_v1.0.exe
echo ============================================================
pause

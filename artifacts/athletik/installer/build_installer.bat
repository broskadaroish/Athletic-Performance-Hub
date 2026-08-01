@echo off
setlocal enabledelayedexpansion
title Bruce Football Diagnostics — Installer Builder
chcp 65001 >nul

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   Bruce Football Performance Diagnostics                ║
echo  ║   Windows-Installer Builder                             ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: ── Konfiguration ─────────────────────────────────────────────────────────────
set APP_VERSION=1.0.0
set PYTHON_VERSION=3.12.10
set PYTHON_EMBED_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py

set SCRIPT_DIR=%~dp0
set BUILD_DIR=%SCRIPT_DIR%_build
set DIST_DIR=%SCRIPT_DIR%Output
set PYTHON_DIR=%BUILD_DIR%\python
set APP_DEST=%BUILD_DIR%\app
set APP_SRC=%SCRIPT_DIR%..

:: ── Inno Setup suchen ─────────────────────────────────────────────────────────
set ISCC=
for %%p in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
    "C:\Program Files\Inno Setup 5\ISCC.exe"
) do if exist %%p if "!ISCC!"=="" set ISCC=%%~p

if "%ISCC%"=="" (
    echo [FEHLER] Inno Setup nicht gefunden!
    echo Bitte installieren: https://jrsoftware.org/isdl.php
    pause & exit /b 1
)
echo [OK] Inno Setup: %ISCC%

:: ── Build-Verzeichnisse ────────────────────────────────────────────────────────
echo [INFO] Bereinige alten Build...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"
mkdir "%PYTHON_DIR%"
mkdir "%APP_DEST%"

:: ── Python Embeddable herunterladen ───────────────────────────────────────────
echo.
echo [1/5] Lade Python %PYTHON_VERSION% (embedded)...
powershell -NoProfile -Command ^
  "Invoke-WebRequest -Uri '%PYTHON_EMBED_URL%' -OutFile '%BUILD_DIR%\python_embed.zip' -UseBasicParsing"
if errorlevel 1 (
    echo [FEHLER] Python-Download fehlgeschlagen. Internet-Verbindung prüfen.
    pause & exit /b 1
)
echo [OK] Python heruntergeladen.

:: ── Python entpacken ──────────────────────────────────────────────────────────
echo [2/5] Entpacke Python...
powershell -NoProfile -Command ^
  "Expand-Archive -Path '%BUILD_DIR%\python_embed.zip' -DestinationPath '%PYTHON_DIR%' -Force"
echo [OK] Python entpackt.

:: ── pip aktivieren (._pth anpassen) ──────────────────────────────────────────
for %%f in ("%PYTHON_DIR%\python*._pth") do (
    echo. >> "%%f"
    echo import site >> "%%f"
)
echo [OK] pip-Unterstützung in ._pth aktiviert.

:: ── pip installieren ──────────────────────────────────────────────────────────
echo [3/5] Installiere pip...
powershell -NoProfile -Command ^
  "Invoke-WebRequest -Uri '%GET_PIP_URL%' -OutFile '%BUILD_DIR%\get-pip.py' -UseBasicParsing"
"%PYTHON_DIR%\python.exe" "%BUILD_DIR%\get-pip.py" --no-warn-script-location --quiet
if errorlevel 1 (
    echo [FEHLER] pip-Installation fehlgeschlagen.
    pause & exit /b 1
)
echo [OK] pip installiert.

:: ── Pakete installieren ───────────────────────────────────────────────────────
echo [4/5] Installiere Pakete (3-5 Minuten)...
"%PYTHON_DIR%\python.exe" -m pip install ^
    "streamlit==1.60.0" ^
    "fpdf2==2.8.3" ^
    "pandas==3.0.5" ^
    "plotly==6.9.0" ^
    "numpy>=1.26" ^
    "openpyxl>=3.1" ^
    "Pillow>=10.0" ^
    --no-warn-script-location --quiet
if errorlevel 1 (
    echo [FEHLER] Paket-Installation fehlgeschlagen.
    pause & exit /b 1
)
echo [OK] Pakete installiert.

:: ── App-Dateien kopieren ──────────────────────────────────────────────────────
echo [5/5] Kopiere App-Dateien...
for %%f in (
    app.py database.py pdf_report.py testprotokoll_pdf.py pdf_anleitung.py
    age_norms.py agilitaet.py analytics.py anthropometrie.py ausdauer.py
    export.py field_eval.py fms.py help_ui.py i18n.py kraft.py
    periodisierung.py safety_texts.py spiro.py sprint.py sprung.py
    test_help.py test_observations.py theme.py training.py
    ui_components.py y_balance.py requirements.txt
) do (
    if exist "%APP_SRC%\%%f" (
        copy /y "%APP_SRC%\%%f" "%APP_DEST%\%%f" >nul
    )
)
xcopy /s /q /y "%APP_SRC%\assets" "%APP_DEST%\assets\" >nul 2>&1
echo [OK] App-Dateien kopiert.

:: ── Launcher + Streamlit-Config kopieren ─────────────────────────────────────
copy /y "%SCRIPT_DIR%launcher.vbs"  "%BUILD_DIR%\launcher.vbs"  >nul
copy /y "%SCRIPT_DIR%launcher.bat"  "%BUILD_DIR%\launcher.bat"  >nul
copy /y "%SCRIPT_DIR%stop.vbs"      "%BUILD_DIR%\stop.vbs"      >nul 2>&1

:: Streamlit config
mkdir "%BUILD_DIR%\streamlit_config"
(
    echo [server]
    echo headless = true
    echo port = 8501
    echo [browser]
    echo serverAddress = "localhost"
    echo gatherUsageStats = false
) > "%BUILD_DIR%\streamlit_config\config.toml"

echo [OK] Launcher erstellt.

:: ── Inno Setup kompilieren ────────────────────────────────────────────────────
echo.
echo [ISCC] Erstelle Setup.exe...
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"

"%ISCC%" "%SCRIPT_DIR%setup.iss" /DMyBuildDir="%BUILD_DIR%" /DMyOutputDir="%DIST_DIR%"
if errorlevel 1 (
    echo [FEHLER] Inno Setup Kompilierung fehlgeschlagen!
    pause & exit /b 1
)

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   FERTIG!                                               ║
echo  ║   Setup.exe liegt in:                                   ║
echo  ║   %DIST_DIR%
echo  ╚══════════════════════════════════════════════════════════╝
echo.
explorer "%DIST_DIR%"
pause

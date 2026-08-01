@echo off
:: Fallback-Launcher falls VBScript blockiert wird (z.B. Gruppenrichtlinie)
cd /d "%APPDATA%\BruceFootballDiagnostics"
set PYTHONPATH=
set STREAMLIT_SERVER_HEADLESS=true
set STREAMLIT_SERVER_PORT=8501
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

start /b "" "%~dp0python\python.exe" -m streamlit run "%~dp0app\app.py" ^
    --server.headless=true ^
    --server.port=8501 ^
    --server.address=localhost ^
    --browser.gatherUsageStats=false

echo Starte Bruce Football Performance Diagnostics...
echo Browser öffnet sich in wenigen Sekunden.
timeout /t 4 /nobreak >nul
start http://localhost:8501

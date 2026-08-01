# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller-Spec für Bruce Football Performance Diagnostics
Ausführen mit:  pyinstaller installer\athletik.spec
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Verzeichnis der App (Elternordner von installer/)
APP_DIR = Path(SPECPATH).parent

# ── Paket-Daten einsammeln ────────────────────────────────────────────────────
st_datas,      st_bins,      st_hidden      = collect_all("streamlit")
plotly_datas,  plotly_bins,  plotly_hidden  = collect_all("plotly")
fpdf_datas,    fpdf_bins,    fpdf_hidden    = collect_all("fpdf2")
altair_datas,  altair_bins,  altair_hidden  = collect_all("altair")
pydeck_datas,  pydeck_bins,  pydeck_hidden  = collect_all("pydeck")

# ── Daten: App-Quelldateien + Assets ─────────────────────────────────────────
app_py_files = [
    (str(f), ".")
    for f in APP_DIR.glob("*.py")
    if not f.name.startswith("backup_")          # Backup-Dateien weglassen
]

app_datas = (
    app_py_files
    + [(str(APP_DIR / "assets"), "assets")]       # SVGs, Icons, PDFs …
    + st_datas
    + plotly_datas
    + fpdf_datas
    + altair_datas
    + pydeck_datas
)

# ── Lokale Module als Hidden Imports (app.py wird von Streamlit geladen) ──────
local_modules = [
    "age_norms", "agilitaet", "analytics", "anthropometrie", "ausdauer",
    "database", "export", "field_eval", "fms", "help_ui", "i18n", "kraft",
    "pdf_anleitung", "pdf_report", "periodisierung", "safety_texts", "spiro",
    "sprint", "sprung", "test_help", "test_observations", "testprotokoll_pdf",
    "theme", "training", "ui_components", "y_balance",
]

extra_hidden = [
    "pandas", "pandas._libs.tslibs.np_datetime",
    "pandas._libs.tslibs.nattype",
    "pandas._libs.tslibs.timedeltas",
    "numpy", "numpy.core._methods",
    "openpyxl", "openpyxl.styles", "openpyxl.utils",
    "PIL", "PIL.Image", "PIL.ImageDraw", "PIL.ImageFont",
    "matplotlib", "matplotlib.pyplot", "matplotlib.backends.backend_agg",
    "sqlite3", "_sqlite3",
    "streamlit.web.cli", "streamlit.web.bootstrap",
    "streamlit.runtime.scriptrunner",
    "pkg_resources", "pkg_resources._vendor",
    "google.protobuf",
    "tzdata",
]

all_hidden = local_modules + extra_hidden + st_hidden + plotly_hidden + fpdf_hidden + altair_hidden + pydeck_hidden

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(APP_DIR / "installer" / "launcher.py")],
    pathex=[str(APP_DIR)],
    binaries=st_bins + plotly_bins + fpdf_bins + altair_bins + pydeck_bins,
    datas=app_datas,
    hiddenimports=all_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest", "_pytest"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,        # --onedir (stabiler als --onefile für Streamlit)
    name="BruceFootballDiagnostics",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,                 # Konsolenfenster: beim ersten Rollout nützlich für Debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(APP_DIR / "assets" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BruceFootballDiagnostics",
)

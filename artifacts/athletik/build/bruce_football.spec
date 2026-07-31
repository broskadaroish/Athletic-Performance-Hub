# -*- mode: python ; coding: utf-8 -*-
# PyInstaller Spec — Bruce Football Performance Diagnostics
# Ausführen: pyinstaller build/bruce_football.spec

import os, sys
from pathlib import Path

# Basisverzeichnis: artifacts/athletik/
BASE = Path(SPECPATH).parent

block_cipher = None

a = Analysis(
    [str(BASE / 'app.py')],
    pathex=[str(BASE)],
    binaries=[],
    datas=[
        # Alle Python-Module einbinden
        (str(BASE / '*.py'),       '.'),
        # Assets (SVGs, Icons, etc.)
        (str(BASE / 'assets'),     'assets'),
        # Tests-Unterordner
        (str(BASE / 'tests'),      'tests'),
    ],
    hiddenimports=[
        'streamlit',
        'streamlit.web.cli',
        'streamlit.runtime.scriptrunner.magic_funcs',
        'fpdf',
        'fpdf2',
        'plotly',
        'plotly.graph_objects',
        'plotly.express',
        'pandas',
        'numpy',
        'sqlite3',
        'PIL',
        'altair',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(BASE / 'build' / 'runtime_hook.py')],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BruceFootballPerformanceDiagnostics',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                    # Kein Konsolenfenster
    icon=str(BASE / 'assets' / 'icon.ico'),  # Icon hier ablegen
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BruceFootball',
)

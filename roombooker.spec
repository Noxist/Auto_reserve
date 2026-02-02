# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

datas = []
binaries = []
hiddenimports = ['nest_asyncio', 'streamlit', 'playwright', 'pandas']

# Sammle Bibliotheken
for lib in ['streamlit', 'playwright', 'pandas', 'nest_asyncio']:
    tmp = collect_all(lib)
    datas += tmp[0]; binaries += tmp[1]; hiddenimports += tmp[2]

# Icon Pfad prüfen (Windows only handling im Build Script besser, hier generisch)
icon_path = 'assets/icons/app.ico' if os.path.exists('assets/icons/app.ico') else None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas + [('app.py', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RoomBookerPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # KEIN SCHWARZES FENSTER
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=icon_path, 
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RoomBookerPro',
)

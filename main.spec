# -*- mode: python ; coding: utf-8 -*-

import os

# Function to read requirements.txt and extract package names
def read_requirements():
    with open('requirements.txt', 'r') as f:
        lines = f.readlines()
    packages = [line.split("==")[0].strip() for line in lines if line and not line.startswith("#")]
    return packages

# Generate hidden imports dynamically
hidden_imports = read_requirements()

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('tmp', 'tmp'), ('assets/icon.ico', 'assets')],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
    env={'PATH': os.environ['PATH']}  # Include the current PATH
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
app = BUNDLE(
    exe,
    name='main.app',
    icon='assets/icon.ico',
    bundle_identifier=None,
)

# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('preview/assets', 'preview/assets'), ('assets', 'assets')]
binaries = []
hiddenimports = ['fitz', 'pymupdf']
tmp_ret = collect_all('pymupdf')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# System libraries that must NOT be bundled to prevent GLIBC version mismatch (Fix for Issue #9)
EXCLUDED_HOST_LIBS = {
    'libglib-2.0.so.0',
    'libgobject-2.0.so.0',
    'libgio-2.0.so.0',
    'libgmodule-2.0.so.0',
    'libgthread-2.0.so.0',
}
safe_binaries = [
    item for item in a.binaries
    if not any(excluded in item[0] for excluded in EXCLUDED_HOST_LIBS)
]

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='preview-app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    safe_binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='preview-app',
)

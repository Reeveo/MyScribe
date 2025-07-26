# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['c:/Users/Luke/OneDrive/Documents/Coding/MyScribe'],
    binaries=[],
    datas=[('resources', 'resources'), ('myscribe.db', '.')],
    hiddenimports=[
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'sounddevice',
        'pygame',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MyScribe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/Myscribe_icon.ico',
)

# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

project_dir = Path.cwd()

datas = [
    (str(project_dir / 'templates'), 'templates'),
    (str(project_dir / 'static'), 'static'),
    (str(project_dir / 'app_icon.ico'), '.'),
    (str(project_dir / 'app_icon.png'), '.'),
]

hiddenimports = [
    'fitz',
    'pymupdf',
    'flask',
    'jinja2',
    'werkzeug',
    'werkzeug.serving',
    'win32com',
    'win32com.client',
    'pythoncom',
    'win32process',
    'win32api',
    'tkinter',
    'tkinter.ttk',
]

a = Analysis(
    ['launcher.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['test_app', 'test_launcher', 'test_sign_documents', 'test_word_conversion'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LocalDocumentSigner',
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
    icon=str(project_dir / 'app_icon.ico'),
)

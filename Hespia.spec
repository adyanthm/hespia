# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collecting all required files
added_files = [
    ('media', 'media'),    # Include the media folder
    ('ui', 'ui'),          # Include the UI package
    ('core', 'core'),      # Include the Core package
]
added_files += collect_data_files('mitmproxy')
added_files += collect_data_files('cryptography')
added_files += collect_data_files('pyOpenSSL')

a = Analysis(
    ['proxy.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'mitmproxy',
        'mitmproxy.tools.main',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets'
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
    name='Hespia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['media/logo.png'], # Use the logo as exe icon
)

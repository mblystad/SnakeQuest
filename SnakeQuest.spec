# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('menubg.png', '.'), ('menubg2.png', '.'), ('banner.png', '.'), ('button1.png', '.'), ('gate.png', '.'), ('heart.png', '.'), ('head.png', '.'), ('segment.png', '.'), ('tail.png', '.'), ('throat.png', '.'), ('corner.png', '.'), ('snakebug.png', '.'), ('f1.png', '.'), ('IDMGlogo.png', '.'), ('theme.wav', '.'), ('jump.mp3', '.'), ('eat.mp3', '.'), ('click.mp3', '.'), ('death.mp3', '.'), ('Vipnagorgialla_Bd.otf', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='SnakeQuest',
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
    icon=['head.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SnakeQuest',
    distpath='dist',
)

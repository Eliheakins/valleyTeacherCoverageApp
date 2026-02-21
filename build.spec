# PyInstaller build script for Valley Teacher Coverage App
# Usage: pyinstaller build.spec

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Add the project root to the path
project_root = os.path.abspath('.')
sys.path.insert(0, project_root)

# Collect data files (if any)
datas = []
# Add any additional data files here if needed
# datas += collect_data_files('data_folder')

# Collect hidden imports
hiddenimports = []
hiddenimports += collect_submodules('dearpygui')
hiddenimports += collect_submodules('pandas')
hiddenimports += collect_submodules('openpyxl')

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ValleyTeacherCoverage',
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
    icon=None,  # You can add an icon file here if you have one
)

app = BUNDLE(
    exe,
    name='ValleyTeacherCoverage.app',
    icon=None,  # You can add an icon file here if you have one
    bundle_identifier='com.valley.teachercoverage',
    info_plist={
        'CFBundleName': 'Valley Teacher Coverage',
        'CFBundleDisplayName': 'Valley Teacher Coverage',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIdentifier': 'com.valley.teachercoverage',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    }
)

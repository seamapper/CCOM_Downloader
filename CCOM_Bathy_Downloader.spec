# -*- mode: python ; coding: utf-8 -*-
# Executable name: CCOM_Bathy_Downloader_v<version>.exe (version read from main.py)


import os
import re
import pyproj

# Read uncommented __version__ from main.py (single source of truth)
# SPEC is set by PyInstaller when executing the spec file
_spec_dir = os.path.dirname(os.path.abspath(SPEC))
with open(os.path.join(_spec_dir, 'main.py'), encoding='utf-8') as f:
    for line in f:
        stripped = line.strip()
        if stripped.startswith('__version__') and not stripped.startswith('# __version__'):
            match = re.search(r'["\']([^"\']+)["\']', line)
            if match:
                __version__ = match.group(1)
                break
    else:
        __version__ = '0.0.0'
EXE_NAME = f'CCOM_Bathy_Downloader_v{__version__}'

# Get PROJ data directory
proj_data_dir = pyproj.datadir.get_data_dir()
proj_share_dir = os.path.dirname(proj_data_dir)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (proj_data_dir, 'proj'),  # Include PROJ data files
    ],
    hiddenimports=[
        'rasterio',
        'rasterio.sample',
        'rasterio._io',
        'rasterio._base',
        'rasterio._env',
        'rasterio._err',
        'rasterio._example',
        'rasterio._features',
        'rasterio._fill',
        'rasterio._transform',
        'rasterio._warp',
        'rasterio.control',
        'rasterio.coords',
        'rasterio.crs',
        'rasterio.drivers',
        'rasterio.dtypes',
        'rasterio.enums',
        'rasterio.env',
        'rasterio.errors',
        'rasterio.features',
        'rasterio.fill',
        'rasterio.io',
        'rasterio.mask',
        'rasterio.merge',
        'rasterio.plot',
        'rasterio.profiles',
        'rasterio.rio',
        'rasterio.session',
        'rasterio.shutil',
        'rasterio.transform',
        'rasterio.vrt',
        'rasterio.warp',
        'rasterio.windows',
    ],
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
    a.binaries,
    a.datas,
    [],
    name=EXE_NAME,
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
    icon=['media\\CCOM.ico'],
)

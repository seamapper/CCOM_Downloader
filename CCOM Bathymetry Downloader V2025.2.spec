# -*- mode: python ; coding: utf-8 -*-


import os
import pyproj

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
    name='CCOM Bathymetry Downloader V2025.2',
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

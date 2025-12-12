#!/usr/bin/env python3
"""
Mac App Builder Helper Script
=============================

This script automates the process of building a macOS .app bundle for the
CCOM Bathymetry Downloader application.

Usage:
    python build_mac_app.py [options]

Options:
    --icon-only      Only convert icon to .icns format
    --no-icon        Build without icon
    --create-dmg     Create a DMG installer after building
    --clean          Clean build artifacts before building
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

__version__ = "2025.1"

# Paths
SCRIPT_DIR = Path(__file__).parent
MEDIA_DIR = SCRIPT_DIR / "media"
DIST_DIR = SCRIPT_DIR / "dist"
BUILD_DIR = SCRIPT_DIR / "build"
APP_NAME = "CCOM Bathymetry Downloader"
APP_VERSION = __version__
BUNDLE_ID = "edu.unh.ccom.bathymetry-downloader"


def print_step(message):
    """Print a formatted step message."""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}\n")


def check_prerequisites():
    """Check if required tools are installed."""
    print_step("Checking Prerequisites")
    
    missing = []
    
    # Check Python
    if not shutil.which("python3"):
        missing.append("python3")
    else:
        print("✓ Python 3 found")
    
    # Check pip
    if not shutil.which("pip3"):
        missing.append("pip3")
    else:
        print("✓ pip3 found")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        missing.append("PyInstaller (install with: pip3 install pyinstaller)")
    
    # Check Homebrew (optional but recommended)
    if shutil.which("brew"):
        print("✓ Homebrew found")
        # Check GDAL
        if shutil.which("gdal-config"):
            print("✓ GDAL found")
        else:
            print("⚠ GDAL not found (install with: brew install gdal)")
    else:
        print("⚠ Homebrew not found (recommended for GDAL/PROJ)")
    
    if missing:
        print(f"\n❌ Missing prerequisites: {', '.join(missing)}")
        return False
    
    return True


def convert_icon_to_icns():
    """Convert icon to .icns format."""
    print_step("Converting Icon to .icns Format")
    
    icon_png = MEDIA_DIR / "CCOM.png"
    icon_ico = MEDIA_DIR / "CCOM.ico"
    icon_icns = MEDIA_DIR / "CCOM.icns"
    
    # Check if .icns already exists
    if icon_icns.exists():
        response = input(f"{icon_icns} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Skipping icon conversion.")
            return icon_icns
    
    # Try to find source icon
    source_icon = None
    if icon_png.exists():
        source_icon = icon_png
        print(f"Found source icon: {icon_png}")
    elif icon_ico.exists():
        source_icon = icon_ico
        print(f"Found source icon: {icon_ico}")
    else:
        print("⚠ No icon file found (CCOM.png or CCOM.ico)")
        return None
    
    # Create iconset directory
    iconset_dir = MEDIA_DIR / "CCOM.iconset"
    if iconset_dir.exists():
        shutil.rmtree(iconset_dir)
    iconset_dir.mkdir()
    
    try:
        # Convert to iconset using sips (macOS built-in tool)
        print("Creating iconset...")
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        
        for size in sizes:
            # Create 1x and 2x versions
            for scale in [1, 2]:
                output_size = size * scale
                output_name = f"icon_{size}x{size}{'' if scale == 1 else '@2x'}.png"
                output_path = iconset_dir / output_name
                
                cmd = [
                    "sips",
                    "-z", str(output_size), str(output_size),
                    str(source_icon),
                    "--out", str(output_path)
                ]
                subprocess.run(cmd, check=True, capture_output=True)
        
        # Convert iconset to .icns
        print("Converting iconset to .icns...")
        cmd = [
            "iconutil",
            "-c", "icns",
            str(iconset_dir),
            "-o", str(icon_icns)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Clean up iconset
        shutil.rmtree(iconset_dir)
        
        print(f"✓ Icon converted successfully: {icon_icns}")
        return icon_icns
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error converting icon: {e}")
        if iconset_dir.exists():
            shutil.rmtree(iconset_dir)
        return None
    except FileNotFoundError:
        print("❌ 'sips' or 'iconutil' not found. These are macOS built-in tools.")
        print("   Please run this script on macOS.")
        return None


def clean_build_artifacts():
    """Clean previous build artifacts."""
    print_step("Cleaning Build Artifacts")
    
    dirs_to_clean = [BUILD_DIR, DIST_DIR]
    files_to_clean = [SCRIPT_DIR / f"{APP_NAME}.spec"]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"Removing {dir_path}...")
            shutil.rmtree(dir_path)
    
    for file_path in files_to_clean:
        if file_path.exists():
            print(f"Removing {file_path}...")
            file_path.unlink()
    
    print("✓ Clean complete")


def build_app(icon_path=None, no_icon=False):
    """Build the macOS app using PyInstaller."""
    print_step("Building macOS App with PyInstaller")
    
    # Prepare PyInstaller command
    cmd = [
        "pyinstaller",
        "--onedir",
        "--windowed",
        "--name", APP_NAME,
        "--add-data", f"media:media",
        "--hidden-import", "rasterio.sample",
        "--hidden-import", "rasterio._example",
        "--hidden-import", "rasterio._features",
        "--hidden-import", "rasterio._fill",
        "--hidden-import", "rasterio.features",
        "--hidden-import", "rasterio.fill",
        "--hidden-import", "rasterio.mask",
        "--hidden-import", "rasterio.merge",
        "--hidden-import", "rasterio.plot",
        "--hidden-import", "rasterio.shutil",
        "--hidden-import", "rasterio.vrt",
    ]
    
    if icon_path and not no_icon:
        cmd.extend(["--icon", str(icon_path)])
        print(f"Using icon: {icon_path}")
    else:
        print("Building without icon")
    
    cmd.append("main.py")
    
    print(f"Running: {' '.join(cmd)}")
    print("\nThis may take several minutes...\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✓ PyInstaller build complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ PyInstaller build failed: {e}")
        return False


def create_app_bundle():
    """Create the .app bundle structure."""
    print_step("Creating .app Bundle")
    
    app_bundle = DIST_DIR / f"{APP_NAME}.app"
    contents_dir = app_bundle / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    # Remove existing app bundle if it exists
    if app_bundle.exists():
        print(f"Removing existing {app_bundle}...")
        shutil.rmtree(app_bundle)
    
    # Create directory structure
    macos_dir.mkdir(parents=True)
    resources_dir.mkdir(parents=True)
    
    # Copy executable and dependencies from PyInstaller output
    source_dir = DIST_DIR / APP_NAME
    if not source_dir.exists():
        print(f"❌ PyInstaller output directory not found: {source_dir}")
        return False
    
    print(f"Copying files from {source_dir} to {macos_dir}...")
    for item in source_dir.iterdir():
        dest = macos_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    
    # Copy icon if available
    icon_icns = MEDIA_DIR / "CCOM.icns"
    if icon_icns.exists():
        shutil.copy2(icon_icns, resources_dir / "CCOM.icns")
        print(f"✓ Icon copied to Resources")
    
    # Create Info.plist
    info_plist = contents_dir / "Info.plist"
    create_info_plist(info_plist)
    
    print(f"✓ App bundle created: {app_bundle}")
    return True


def create_info_plist(plist_path):
    """Create Info.plist file for the app bundle."""
    print("Creating Info.plist...")
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>{BUNDLE_ID}</string>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>{APP_VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>{APP_VERSION}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleIconFile</key>
    <string>CCOM</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2025 Center for Coastal and Ocean Mapping, University of New Hampshire</string>
</dict>
</plist>"""
    
    with open(plist_path, 'w') as f:
        f.write(plist_content)
    
    print(f"✓ Info.plist created: {plist_path}")


def create_dmg():
    """Create a DMG installer."""
    print_step("Creating DMG Installer")
    
    if not shutil.which("create-dmg"):
        print("⚠ 'create-dmg' not found.")
        print("  Install with: brew install create-dmg")
        print("  Or create DMG manually using Disk Utility")
        return False
    
    app_bundle = DIST_DIR / f"{APP_NAME}.app"
    if not app_bundle.exists():
        print(f"❌ App bundle not found: {app_bundle}")
        return False
    
    dmg_name = f"CCOM_Bathymetry_Downloader_V{APP_VERSION}.dmg"
    dmg_path = DIST_DIR / dmg_name
    
    # Remove existing DMG
    if dmg_path.exists():
        dmg_path.unlink()
    
    cmd = [
        "create-dmg",
        "--volname", APP_NAME,
        "--window-pos", "200", "120",
        "--window-size", "600", "400",
        "--icon-size", "100",
        "--icon", f"{APP_NAME}.app", "150", "190",
        "--hide-extension", f"{APP_NAME}.app",
        "--app-drop-link", "450", "190",
        str(dmg_path),
        str(app_bundle)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True, cwd=DIST_DIR)
        print(f"\n✓ DMG created: {dmg_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ DMG creation failed: {e}")
        return False


def fix_permissions():
    """Fix permissions and remove quarantine attribute."""
    print_step("Fixing Permissions")
    
    app_bundle = DIST_DIR / f"{APP_NAME}.app"
    if not app_bundle.exists():
        return
    
    # Remove quarantine attribute (allows app to run without Gatekeeper warning)
    cmd = ["xattr", "-cr", str(app_bundle)]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print("✓ Removed quarantine attribute")
    except subprocess.CalledProcessError:
        print("⚠ Could not remove quarantine attribute (may need to run manually)")
    
    # Make executable
    executable = app_bundle / "Contents" / "MacOS" / APP_NAME
    if executable.exists():
        os.chmod(executable, 0o755)
        print("✓ Set executable permissions")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Build macOS app bundle for CCOM Bathymetry Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--icon-only",
        action="store_true",
        help="Only convert icon to .icns format"
    )
    parser.add_argument(
        "--no-icon",
        action="store_true",
        help="Build without icon"
    )
    parser.add_argument(
        "--create-dmg",
        action="store_true",
        help="Create a DMG installer after building"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"  CCOM Bathymetry Downloader - Mac App Builder")
    print(f"  Version {APP_VERSION}")
    print(f"{'='*60}\n")
    
    # Check if running on macOS
    if sys.platform != "darwin":
        print("❌ This script is designed for macOS only.")
        print("   Please run this script on a Mac.")
        sys.exit(1)
    
    # Icon conversion only
    if args.icon_only:
        convert_icon_to_icns()
        return
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please install missing tools.")
        sys.exit(1)
    
    # Clean if requested
    if args.clean:
        clean_build_artifacts()
    
    # Convert icon
    icon_path = None
    if not args.no_icon:
        icon_path = convert_icon_to_icns()
        if not icon_path:
            response = input("\nContinue without icon? (y/n): ")
            if response.lower() != 'y':
                print("Build cancelled.")
                sys.exit(1)
    
    # Build app
    if not build_app(icon_path, args.no_icon):
        print("\n❌ Build failed. Check errors above.")
        sys.exit(1)
    
    # Create app bundle
    if not create_app_bundle():
        print("\n❌ App bundle creation failed.")
        sys.exit(1)
    
    # Fix permissions
    fix_permissions()
    
    # Create DMG if requested
    if args.create_dmg:
        create_dmg()
    
    # Final message
    app_bundle = DIST_DIR / f"{APP_NAME}.app"
    print_step("Build Complete!")
    print(f"✓ App bundle: {app_bundle}")
    print(f"\nTo test the app, run:")
    print(f"  open '{app_bundle}'")
    print(f"\nTo distribute, you may want to:")
    print(f"  1. Code sign the app (requires Apple Developer ID)")
    print(f"  2. Notarize the app (for macOS 10.15+)")
    print(f"  3. Create a DMG: python build_mac_app.py --create-dmg")


if __name__ == "__main__":
    main()


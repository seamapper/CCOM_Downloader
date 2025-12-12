# CCOM Bathymetry Downloader

A PyQt6-based desktop application for downloading bathymetry data from ArcGIS ImageServer REST endpoints and exporting it as GeoTIFF files with interactive area selection.

## Features

- **Interactive Map Display**: Visualize bathymetry data with an interactive map widget
- **Area Selection**: Click and drag to select areas of interest for download
- **Multiple Layer Support**:
  - World Imagery basemap (optional)
  - Bathymetry hillshade underlay layer
  - Main bathymetry layer with adjustable opacity
  - Overlay blend mode for enhanced visualization
- **Raster Function**: Uses "DAR - StdDev - BlueGreen" for consistent visualization
- **Cell Size Selection**: Choose from 4m, 8m, or 16m pixel resolution
- **Coordinate Systems**: Support for EPSG:3857 (Web Mercator) and EPSG:4326 (WGS84)
- **Coordinate Display**: Real-time display of selected area in both Web Mercator and Geographic (WGS84) coordinates
- **Pixel Count Display**: Shows expected pixel dimensions based on selected area and cell size
- **Maximum Size Validation**: Prevents downloads exceeding 14,000 × 14,000 pixels
- **Automatic Filename Generation**: Default filename includes cell size and timestamp
- **Mouse Controls**:
  - Mouse wheel: Zoom in/out (centered on window)
  - Middle-click drag: Pan the map
  - Left-click drag: Select area for download

## Requirements

- Python 3.8 or higher
- PyQt6 >= 6.6.0
- requests >= 2.31.0
- rasterio >= 1.3.9
- numpy >= 1.24.0
- Pillow >= 10.0.0
- pyproj >= 3.6.0

## Installation

1. Clone the repository:
```bash
git clone https://github.com/seamapper/CCOM_Downloader.git
cd CCOM_Downloader
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running from Source

```bash
python main.py
```

### Running the Executable

A pre-built Windows executable is available in the `dist/` directory:
- `CCOM Bathymetry Downloader V2025.1.exe`

Simply double-click the executable to run the application.

### Using the Application

1. **Select an Area**: Click and drag on the map to select the area you want to download
2. **Adjust Settings**:
   - Choose cell size (4m, 8m, or 16m)
   - Select output coordinate system (EPSG:3857 or EPSG:4326)
   - Toggle basemap visibility
   - Toggle hillshade layer
   - Adjust opacity of the main bathymetry layer
   - Enable/disable overlay blend mode
3. **Download**: Click "Download Selected Area" button
4. **Save File**: Choose a save location in the file dialog (default filename includes cell size and timestamp)

## Data Source

The application connects to the CCOM ArcGIS ImageServer:
- **Service URL**: `https://gis.ccom.unh.edu/server/rest/services/WGOM_LI_SNE/WGOM_LI_SNE_BTY_4m_20231005_WMAS_IS/ImageServer`
- **Raster Function**: DAR - StdDev - BlueGreen
- **Hillshade Function**: Multidirectional Hillshade 3x

## Output Format

Downloads are saved as GeoTIFF files with:
- Proper georeferencing
- NoData value handling
- Coordinate system information embedded
- LZW compression

## Building the Executable

### Windows

To build a Windows executable:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --icon=media\CCOM.ico --name="CCOM Bathymetry Downloader V2025.1" main.py
```

The executable will be created in the `dist/` directory.

### macOS

**Quick Start (Recommended):**

Use the automated build script:

```bash
python3 build_mac_app.py
```

This script will:
- Check prerequisites
- Convert the icon to .icns format
- Build the app with PyInstaller
- Create the .app bundle structure
- Set up Info.plist
- Fix permissions

**Options:**
- `--icon-only`: Only convert icon to .icns format
- `--no-icon`: Build without icon
- `--create-dmg`: Create a DMG installer after building
- `--clean`: Clean build artifacts before building

**Manual Build:**

To build a macOS application (.app bundle) manually:

#### Prerequisites

1. **Install Xcode Command Line Tools** (if not already installed):
   ```bash
   xcode-select --install
   ```

2. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. **Install required system libraries**:
   ```bash
   brew install gdal proj geos
   ```

4. **Set environment variables** (add to your `~/.zshrc` or `~/.bash_profile`):
   ```bash
   export GDAL_CONFIG=$(brew --prefix gdal)/bin/gdal-config
   export PROJ_LIB=$(brew --prefix proj)/share/proj
   ```

#### Building the App

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Create an icon file** (if you have a .png or .ico file):
   - Convert to .icns format using `iconutil` or an online converter
   - Place it in the `media/` directory as `CCOM.icns`
   - Or skip the icon parameter if you don't have one

3. **Build the application**:
   ```bash
   pyinstaller --onedir --windowed \
     --name="CCOM Bathymetry Downloader" \
     --icon=media/CCOM.icns \
     --add-data="media:media" \
     --hidden-import=rasterio.sample \
     --hidden-import=rasterio._example \
     --hidden-import=rasterio._features \
     --hidden-import=rasterio._fill \
     --hidden-import=rasterio.features \
     --hidden-import=rasterio.fill \
     --hidden-import=rasterio.mask \
     --hidden-import=rasterio.merge \
     --hidden-import=rasterio.plot \
     --hidden-import=rasterio.shutil \
     --hidden-import=rasterio.vrt \
     main.py
   ```

   **Note**: Use `--onedir` instead of `--onefile` for macOS, as it's more reliable and easier to debug.

4. **Create the .app bundle**:
   ```bash
   cd dist
   mkdir -p "CCOM Bathymetry Downloader.app/Contents/MacOS"
   mkdir -p "CCOM Bathymetry Downloader.app/Contents/Resources"
   
   # Move the main executable
   mv "CCOM Bathymetry Downloader/CCOM Bathymetry Downloader" "CCOM Bathymetry Downloader.app/Contents/MacOS/"
   
   # Move all dependencies
   cp -r "CCOM Bathymetry Downloader"/* "CCOM Bathymetry Downloader.app/Contents/MacOS/"
   
   # Copy icon if available
   cp ../media/CCOM.icns "CCOM Bathymetry Downloader.app/Contents/Resources/" 2>/dev/null || true
   ```

5. **Create Info.plist** (optional, for better app metadata):
   ```bash
   cat > "CCOM Bathymetry Downloader.app/Contents/Info.plist" << EOF
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>CFBundleExecutable</key>
       <string>CCOM Bathymetry Downloader</string>
       <key>CFBundleIdentifier</key>
       <string>edu.unh.ccom.bathymetry-downloader</string>
       <key>CFBundleName</key>
       <string>CCOM Bathymetry Downloader</string>
       <key>CFBundleVersion</key>
       <string>2025.1</string>
       <key>CFBundleShortVersionString</key>
       <string>2025.1</string>
       <key>CFBundleIconFile</key>
       <string>CCOM</string>
       <key>NSHighResolutionCapable</key>
       <true/>
   </dict>
   </plist>
   EOF
   ```

#### Alternative: Using py2app (Mac-specific)

1. **Install py2app**:
   ```bash
   pip install py2app
   ```

2. **Create a setup.py file**:
   ```python
   from setuptools import setup
   
   APP = ['main.py']
   DATA_FILES = ['media']
   OPTIONS = {
       'argv_emulation': False,
       'packages': ['PyQt6', 'rasterio', 'numpy', 'PIL', 'pyproj', 'requests'],
       'includes': ['rasterio.sample', 'rasterio._example', 'rasterio._features'],
       'iconfile': 'media/CCOM.icns',
       'plist': {
           'CFBundleName': 'CCOM Bathymetry Downloader',
           'CFBundleDisplayName': 'CCOM Bathymetry Downloader',
           'CFBundleGetInfoString': 'CCOM Bathymetry Downloader v2025.1',
           'CFBundleIdentifier': 'edu.unh.ccom.bathymetry-downloader',
           'CFBundleVersion': '2025.1',
           'CFBundleShortVersionString': '2025.1',
           'NSHighResolutionCapable': True,
       }
   }
   
   setup(
       app=APP,
       data_files=DATA_FILES,
       options={'py2app': OPTIONS},
       setup_requires=['py2app'],
   )
   ```

3. **Build the app**:
   ```bash
   python setup.py py2app
   ```

   The app will be created in the `dist/` directory.

#### Creating a DMG Installer (Optional)

To create a disk image (.dmg) for distribution:

1. **Install create-dmg** (optional tool):
   ```bash
   brew install create-dmg
   ```

2. **Create the DMG**:
   ```bash
   create-dmg \
     --volname "CCOM Bathymetry Downloader" \
     --window-pos 200 120 \
     --window-size 600 400 \
     --icon-size 100 \
     --icon "CCOM Bathymetry Downloader.app" 150 190 \
     --hide-extension "CCOM Bathymetry Downloader.app" \
     --app-drop-link 450 190 \
     "CCOM_Bathymetry_Downloader_V2025.1.dmg" \
     "CCOM Bathymetry Downloader.app"
   ```

#### Troubleshooting macOS Build Issues

- **"rasterio not found" errors**: Make sure GDAL is properly installed via Homebrew and environment variables are set
- **"App is damaged" warning**: This is often a code signing issue. You may need to:
  ```bash
  xattr -cr "CCOM Bathymetry Downloader.app"
  ```
- **Missing dependencies**: Check the `dist/` folder and ensure all required libraries are included
- **Large app size**: This is normal for PyQt6 apps with geospatial libraries. Consider using `--exclude-module` to remove unused modules

#### Code Signing and Notarization (For Distribution)

If you plan to distribute the app outside the Mac App Store:

1. **Get an Apple Developer ID** (requires paid Apple Developer account)

2. **Code sign the app**:
   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" "CCOM Bathymetry Downloader.app"
   ```

3. **Notarize the app** (required for macOS 10.15+):
   ```bash
   xcrun altool --notarize-app \
     --primary-bundle-id "edu.unh.ccom.bathymetry-downloader" \
     --username "your-apple-id@example.com" \
     --password "@keychain:AC_PASSWORD" \
     --file "CCOM_Bathymetry_Downloader_V2025.1.dmg"
   ```

The executable/app will be created in the `dist/` directory.

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## Author

**Paul Johnson**  
Center for Coastal and Ocean Mapping  
University of New Hampshire  
Email: pjohnson@ccom.unh.edu

## Version

Current version: **2025.1**

## Acknowledgments

- Center for Coastal and Ocean Mapping (CCOM), University of New Hampshire
- Built with PyQt6, rasterio, and other open-source libraries

## Support

For issues, questions, or contributions, please open an issue on the [GitHub repository](https://github.com/seamapper/CCOM_Downloader/issues).

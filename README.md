# CCOM Bathymetry Downloader

A PyQt6-based desktop application for downloading bathymetry data from ArcGIS ImageServer REST endpoints and exporting it as GeoTIFF files with interactive area selection.

## Features

- **Interactive Map Display**: Visualize bathymetry data with an interactive map widget
- **Area Selection**: Click and drag to select areas of interest for download
- **Multiple Data Sources**: Switch between different bathymetry datasets (Hi Resolution and Regional)
- **Multiple Layer Support**:
  - World Imagery basemap (optional)
  - Bathymetry hillshade underlay layer (automatically enables blend mode)
  - Main bathymetry layer with adjustable opacity
  - Automatic blend mode when hillshade is enabled
- **Dynamic Raster Function Selection**: Automatically selects raster function based on area of interest pixel dimensions
  - Areas ≤ 4000 pixels (both dimensions): "DAR - StdDev - BlueGreen"
  - Areas > 4000 pixels (either dimension): "StdDev - BlueGreen"
- **Dynamic Cell Size Selection**: Cell size options automatically adjust based on selected data source (1x, 2x, 3x, 4x, 5x base resolution)
- **Coordinate Systems**: Support for EPSG:3857 (Web Mercator) and EPSG:4326 (WGS84)
- **Coordinate Display**: Real-time display of selected area in both Web Mercator and Geographic (WGS84) coordinates
- **Pixel Count Display**: Shows expected pixel dimensions based on selected area and cell size (displayed in Output Options)
- **Map Legend**: Legend in upper left corner showing box color meanings
- **Refresh Map Button**: Refresh the map display for the currently shown area
- **Tile Download Support**: Automatically tiles large downloads for reliable data retrieval
- **Automatic Filename Generation**: Default filename includes cell size and timestamp
- **Visual Feedback**:
  - Yellow dashed box: Dataset bounds
  - Green dashed box: Valid user selection (Area of Interest)
  - Red dashed box: Selection too large
  - Black background: NoData areas when basemap is disabled
  - Legend: Upper left corner shows box color meanings
- **Mouse Controls**:
  - Mouse wheel: Zoom in/out (centered on window)
  - Middle-click drag: Pan the map (shows red dashed pan line)
  - Left-click drag: Select area for download (green dashed box)

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

A pre-built Windows executable is available in the [GitHub Releases](https://github.com/seamapper/CCOM_Downloader/releases):
- `CCOM Bathymetry Downloader V2025.3.exe`

Download the latest release and double-click the executable to run the application.

### Using the Application

1. **Select Data Source**: Choose from available bathymetry datasets (defaults to highest resolution)
2. **Select an Area**: Click and drag on the map to select the area you want to download
   - The initial dataset bounds are shown with a yellow dashed box
   - Your selection is shown with a green dashed box while drawing
   - Valid selections remain green; invalid (too large) selections turn red
3. **Adjust Settings**:
   - Choose cell size (options vary by data source: 1x, 2x, 3x, 4x, 5x base resolution)
   - Select output coordinate system (EPSG:3857 or EPSG:4326)
   - View pixel count in Output Options (shows expected download dimensions)
   - Toggle basemap visibility (when off, NoData areas appear black)
   - Toggle hillshade layer (automatically enables blend mode)
   - Adjust opacity of the main bathymetry layer
   - Use "Refresh Map" button to reload the current map display
4. **Download**: Click "Download Selected Area" button (bold when manual selection is active)
   - Enable "Tile Download" for large datasets (recommended, enabled by default)
   - Choose save location if no default output directory is set
5. **Save File**: Default filename includes cell size and timestamp

## Data Sources

The application supports multiple CCOM ArcGIS ImageServer data sources:

### WGOM-LI-SNE Hi Resolution
- **Service URL**: `https://gis.ccom.unh.edu/server/rest/services/WGOM_LI_SNE/WGOM_LI_SNE_BTY_4m_20231005_WMAS_2_IS/ImageServer`
- **Base Resolution**: 4m
- **Raster Function**: Dynamic selection based on area pixel dimensions
  - ≤ 4000 pixels (both dimensions): "DAR - StdDev - BlueGreen"
  - > 4000 pixels (either dimension): "StdDev - BlueGreen"
- **Hillshade Function**: Multidirectional Hillshade 3x

### WGOM-LI-SNE Regional
- **Service URL**: `https://gis.ccom.unh.edu/server/rest/services/WGOM_LI_SNE/WGOM_LI_SNE_BTY_20231004_16m_2_WMAS_IS/ImageServer`
- **Base Resolution**: 16m
- **Raster Function**: Dynamic selection based on area pixel dimensions
  - ≤ 4000 pixels (both dimensions): "DAR - StdDev - BlueGreen"
  - > 4000 pixels (either dimension): "StdDev - BlueGreen"
- **Hillshade Function**: Multidirectional Hillshade 3x

Cell size options automatically adjust based on the selected data source (1x, 2x, 3x, 4x, 5x the base resolution).

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
pyinstaller "CCOM Bathymetry Downloader V2025.3.spec"
```

Or use the command line:

```bash
pyinstaller --onefile --noconsole --icon=media\CCOM.ico --name="CCOM Bathymetry Downloader V2025.3" main.py
```

The executable will be created in the `dist/` directory.

**Note**: The spec file includes PROJ data files and rasterio hidden imports required for coordinate transformations and GeoTIFF creation.

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
       <string>2025.3</string>
       <key>CFBundleShortVersionString</key>
       <string>2025.3</string>
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
           'CFBundleGetInfoString': 'CCOM Bathymetry Downloader v2025.3',
           'CFBundleIdentifier': 'edu.unh.ccom.bathymetry-downloader',
           'CFBundleVersion': '2025.3',
           'CFBundleShortVersionString': '2025.3',
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
     "CCOM_Bathymetry_Downloader_V2025.3.dmg" \
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
     --file "CCOM_Bathymetry_Downloader_V2025.3.dmg"
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

Current version: **2025.3**

### Version History

**2025.3** (Current)
- Added dynamic raster function selection based on area pixel dimensions (for both Hi Resolution and Regional)
- Added Refresh Map button to reload current map display
- Added legend in upper left corner showing box color meanings
- Moved pixel count display to Output Options groupbox
- Added 4x and 5x cell size options to dropdown
- Fixed pixel size calculation to use actual service pixel sizes
- Fixed data source switching to properly reload map when URL changes
- Updated service URLs for both data sources
- Added green color formatting for raster function status messages in log
- Removed all debug code

**2025.2**
- Fixed initial map load bounds and box positioning
- Added data source selection (multiple datasets)
- Added tile download option for large datasets
- Auto blend mode with hillshade (removed separate checkbox)
- Black NoData areas when basemap is disabled
- Green selection box while drawing
- Bold download button for manual selections only
- Dynamic cell size options based on data source
- Improved zoom to full extent behavior

**2025.1**
- First release of the program
- Interactive map with area selection
- Multiple layer support
- Coordinate system conversion
- GeoTIFF export functionality

## Acknowledgments

- Center for Coastal and Ocean Mapping (CCOM), University of New Hampshire
- Built with PyQt6, rasterio, and other open-source libraries

## Support

For issues, questions, or contributions, please open an issue on the [GitHub repository](https://github.com/seamapper/CCOM_Downloader/issues).

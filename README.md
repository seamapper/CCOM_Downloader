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

To build the executable yourself:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --icon=media\CCOM.ico --name="CCOM Bathymetry Downloader V2025.1" main.py
```

The executable will be created in the `dist/` directory.

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

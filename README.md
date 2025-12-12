# CCOM Bathymetry Downloader

A PyQt6 application for downloading bathymetry data from the CCOM ArcGIS ImageServer and exporting it as GeoTIFF files.

## Features

- Interactive map display with Haxby-styled bathymetry visualization
- Area selection tool for choosing download regions (click and drag)
- Pan and zoom navigation (Ctrl+Click to pan, mouse wheel to zoom)
- Download selected areas as GeoTIFF files with raw bathymetry values
- Coordinate system conversion support (EPSG:3857, EPSG:4326)
- Progress tracking and status updates
- Real-time coordinate display

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### How to Use

1. **Navigate the Map**:
   - Use mouse wheel to zoom in/out
   - Hold Ctrl and click-drag to pan the map
   - Click "Fit to Extent" to view the full service area

2. **Select an Area**:
   - Click and drag on the map to draw a selection rectangle
   - The selected coordinates will appear in the "Selected Area" panel
   - Click "Clear Selection" to remove the selection

3. **Configure Output**:
   - Choose output coordinate system (EPSG:3857 or EPSG:4326)
   - Click "Browse..." to select output file path

4. **Download**:
   - Click "Download Selected Area" to start the download
   - Monitor progress in the progress bar and status log
   - The GeoTIFF file will be saved when complete

## Requirements

- Python 3.8+
- See requirements.txt for package dependencies

## Data Source

This application downloads bathymetry data from:
- **Service**: CCOM WGOM-LI-SNE Bathymetry (4m resolution)
- **REST Endpoint**: https://gis.ccom.unh.edu/server/rest/services/WGOM-LI-SNE/WGOM_LI_SNE_BTY_4m_20231005_IS/ImageServer
- **Map Visualization**: Uses "Haxby Percent Clip DRA" raster function for display
- **Download Format**: Raw F32 bathymetry values exported as GeoTIFF

## Notes

- The map displays styled bathymetry (Haxby colormap) for visualization
- Downloaded GeoTIFF files contain raw bathymetry values (F32 format)
- Large area downloads may take several minutes depending on size
- Maximum download size is limited by the service (15000x15000 pixels)


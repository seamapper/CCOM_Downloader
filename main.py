"""
Main application for CCOM Bathymetry Downloader.
"""
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QComboBox, QProgressBar, QTextEdit,
                             QGroupBox, QMessageBox, QCheckBox, QSlider)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from map_widget import MapWidget
from download_module import BathymetryDownloader
import requests
import json
import pyproj


class ServiceInfoLoader(QThread):
    """Thread for loading service information asynchronously."""
    loaded = pyqtSignal(dict)  # Emits extent dict and raster functions
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        
    def run(self):
        """Load service information from REST endpoint."""
        try:
            url = f"{self.base_url}?f=json"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Extract extent
            extent = data.get("extent", {})
            extent_dict = {
                "xmin": extent.get("xmin", -8254538.5),
                "ymin": extent.get("ymin", 4898563.25),
                "xmax": extent.get("xmax", -7411670.5),
                "ymax": extent.get("ymax", 5636075.25)
            }
            
            # Extract raster functions
            raster_functions = ["None"]  # Always include "None" option
            raster_function_infos = data.get("rasterFunctionInfos", [])
            for rf_info in raster_function_infos:
                name = rf_info.get("name", "")
                if name and name != "None":
                    raster_functions.append(name)
            
            result = {
                "extent": extent_dict,
                "raster_functions": raster_functions
            }
            
            self.loaded.emit(result)
            
        except requests.exceptions.Timeout:
            self.error.emit("Connection timeout. Using default extent.")
        except requests.exceptions.RequestException as e:
            self.error.emit(f"Network error: {str(e)}. Using default extent.")
        except Exception as e:
            self.error.emit(f"Error loading service info: {str(e)}. Using default extent.")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://gis.ccom.unh.edu/server/rest/services/WGOM_LI_SNE/WGOM_LI_SNE_BTY_4m_20231005_WMAS_IS/ImageServer"
        # Use known extent as fallback (will be updated when service info loads)
        self.service_extent = (-8254538.5, 4898559.25, -7411670.5, 5636075.25)
        self.downloader = None
        self.service_loader = None
        
        self.init_ui()
        self.load_service_info()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("CCOM Bathymetry Downloader")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Map
        self.map_group = QGroupBox("Map")
        self.map_group.setObjectName("Map")  # Set object name for finding
        map_layout = QVBoxLayout()
        
        # Map controls
        map_controls = QHBoxLayout()
        self.fit_extent_btn = QPushButton("Fit to Extent")
        self.fit_extent_btn.clicked.connect(self.fit_to_extent)
        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        map_controls.addWidget(self.fit_extent_btn)
        map_controls.addWidget(self.clear_selection_btn)
        map_controls.addStretch()
        
        # Raster function is fixed to "DAR - StdDev - BlueGreen"
        
        map_layout.addLayout(map_controls)
        
        # Basemap controls
        basemap_controls = QHBoxLayout()
        self.basemap_checkbox = QCheckBox("Show World Imagery Basemap")
        self.basemap_checkbox.setChecked(True)
        self.basemap_checkbox.stateChanged.connect(self.on_basemap_toggled)
        basemap_controls.addWidget(self.basemap_checkbox)
        
        self.hillshade_checkbox = QCheckBox("Show Bathymetry Hillshade")
        self.hillshade_checkbox.setChecked(True)  # On by default
        self.hillshade_checkbox.stateChanged.connect(self.on_hillshade_toggled)
        basemap_controls.addWidget(self.hillshade_checkbox)
        
        basemap_controls.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(60)  # 60% opacity by default
        self.opacity_slider.setMaximumWidth(100)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        basemap_controls.addWidget(self.opacity_slider)
        basemap_controls.addStretch()
        
        map_layout.addLayout(basemap_controls)
        
        # Map widget (will be created after service info is loaded)
        self.map_widget = None
        self.loading_label = QLabel("Loading service info...")
        map_layout.addWidget(self.loading_label)
        
        self.map_group.setLayout(map_layout)
        main_layout.addWidget(self.map_group, stretch=2)
        
        # Right panel - Controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Selection info
        selection_group = QGroupBox("Selected Area")
        selection_main_layout = QVBoxLayout()
        
        # Horizontal layout for coordinate groupboxes
        selection_coords_layout = QHBoxLayout()
        
        # WebMercator groupbox (left)
        webmercator_group = QGroupBox("WebMercator")
        webmercator_layout = QVBoxLayout()
        
        self.xmin_edit = QLineEdit()
        self.xmin_edit.setPlaceholderText("XMin")
        self.ymin_edit = QLineEdit()
        self.ymin_edit.setPlaceholderText("YMin")
        self.xmax_edit = QLineEdit()
        self.xmax_edit.setPlaceholderText("XMax")
        self.ymax_edit = QLineEdit()
        self.ymax_edit.setPlaceholderText("YMax")
        
        webmercator_layout.addWidget(QLabel("XMin:"))
        webmercator_layout.addWidget(self.xmin_edit)
        webmercator_layout.addWidget(QLabel("YMin:"))
        webmercator_layout.addWidget(self.ymin_edit)
        webmercator_layout.addWidget(QLabel("XMax:"))
        webmercator_layout.addWidget(self.xmax_edit)
        webmercator_layout.addWidget(QLabel("YMax:"))
        webmercator_layout.addWidget(self.ymax_edit)
        
        webmercator_group.setLayout(webmercator_layout)
        selection_coords_layout.addWidget(webmercator_group)
        
        # Geographic groupbox (right)
        geographic_group = QGroupBox("Geographic")
        geographic_layout = QVBoxLayout()
        
        self.west_edit = QLineEdit()
        self.west_edit.setPlaceholderText("West")
        self.west_edit.setReadOnly(True)  # Read-only, calculated from WebMercator
        self.south_edit = QLineEdit()
        self.south_edit.setPlaceholderText("South")
        self.south_edit.setReadOnly(True)
        self.east_edit = QLineEdit()
        self.east_edit.setPlaceholderText("East")
        self.east_edit.setReadOnly(True)
        self.north_edit = QLineEdit()
        self.north_edit.setPlaceholderText("North")
        self.north_edit.setReadOnly(True)
        
        geographic_layout.addWidget(QLabel("West:"))
        geographic_layout.addWidget(self.west_edit)
        geographic_layout.addWidget(QLabel("South:"))
        geographic_layout.addWidget(self.south_edit)
        geographic_layout.addWidget(QLabel("East:"))
        geographic_layout.addWidget(self.east_edit)
        geographic_layout.addWidget(QLabel("North:"))
        geographic_layout.addWidget(self.north_edit)
        
        geographic_group.setLayout(geographic_layout)
        selection_coords_layout.addWidget(geographic_group)
        
        selection_main_layout.addLayout(selection_coords_layout)
        
        # Pixel count display at the bottom
        self.pixel_count_label = QLabel("Expected pixels: --")
        self.pixel_count_label.setStyleSheet("font-weight: bold; padding: 5px;")
        selection_main_layout.addWidget(self.pixel_count_label)
        
        selection_group.setLayout(selection_main_layout)
        right_layout.addWidget(selection_group)
        
        # Output options
        output_group = QGroupBox("Output Options")
        output_layout = QVBoxLayout()
        
        # Cell size selector
        output_layout.addWidget(QLabel("Cell Size (m):"))
        self.cell_size_combo = QComboBox()
        self.cell_size_combo.addItems(["4", "8", "16"])
        self.cell_size_combo.setCurrentText("4")  # Default to 4m
        self.cell_size_combo.currentTextChanged.connect(self.on_cell_size_changed)
        output_layout.addWidget(self.cell_size_combo)
        
        output_layout.addWidget(QLabel("Output CRS:"))
        self.crs_combo = QComboBox()
        self.crs_combo.addItems(["EPSG:3857", "EPSG:4326"])
        output_layout.addWidget(self.crs_combo)
        
        output_layout.addWidget(QLabel("Output Path:"))
        path_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_output_path)
        path_layout.addWidget(self.output_path_edit)
        path_layout.addWidget(self.browse_btn)
        output_layout.addLayout(path_layout)
        
        output_group.setLayout(output_layout)
        right_layout.addWidget(output_group)
        
        # Download button
        self.download_btn = QPushButton("Download Selected Area")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setEnabled(False)
        right_layout.addWidget(self.download_btn)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        right_layout.addWidget(progress_group)
        
        # Status log
        log_group = QGroupBox("Status Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        right_layout.addStretch()
        
        main_layout.addWidget(right_panel, stretch=1)
        
    def load_service_info(self):
        """Load service information from REST endpoint in background thread."""
        # Start with default extent and initialize map immediately
        self.log_message("Initializing map widget with default extent...")
        self.init_map_widget()
        if self.map_widget:
            self.log_message("Map widget created successfully on startup")
        else:
            self.log_message("WARNING: Map widget is None after initial creation attempt")
        
        # Try to load actual service info in background
        self.service_loader = ServiceInfoLoader(self.base_url)
        self.service_loader.loaded.connect(self.on_service_info_loaded)
        self.service_loader.error.connect(self.on_service_info_error)
        self.service_loader.start()
        
    def on_service_info_loaded(self, service_data):
        """Handle successful service info load."""
        extent_dict = service_data.get("extent", {})
        self.service_extent = (
            extent_dict["xmin"],
            extent_dict["ymin"],
            extent_dict["xmax"],
            extent_dict["ymax"]
        )
        self.log_message("Service info loaded successfully")
        
        # Raster function is fixed to "DAR - StdDev - BlueGreen" - no need to update combo box
        
        # Ensure map widget is initialized (this will remove loading label)
        if self.map_widget is None:
            self.log_message("Initializing map widget...")
            self.init_map_widget()
        
        # Update map extent (but don't reload if map widget already exists and is loading)
        if self.map_widget:
            self.log_message(f"Updating map extent: {self.service_extent}")
            self.map_widget.extent = self.service_extent
            # Only reload if map hasn't been loaded yet and isn't currently loading
            if not self.map_widget.map_loaded and not getattr(self.map_widget, '_loading', False):
                self.map_widget.map_loaded = False  # Reset flag to allow reload
                QTimer.singleShot(300, self.map_widget.load_map)  # Longer delay to avoid conflicts
        else:
            self.log_message("ERROR: Map widget is None after initialization attempt")
            
    def on_service_info_error(self, error_message):
        """Handle service info load error."""
        self.log_message(error_message)
        # Continue with default extent - map should already be initialized
            
    def init_map_widget(self):
        """Initialize the map widget."""
        if self.service_extent is None:
            self.log_message("ERROR: service_extent is None, cannot initialize map")
            return
            
        # Get map group and layout - use stored reference
        if not hasattr(self, 'map_group') or not self.map_group:
            self.log_message("ERROR: map_group not found")
            return
            
        layout = self.map_group.layout()
        if not layout:
            self.log_message("ERROR: Map QGroupBox has no layout")
            return
            
        # Remove loading label if it exists - try multiple approaches
        label_removed = False
        
        # First, try to remove via the stored reference
        if hasattr(self, 'loading_label') and self.loading_label:
            try:
                layout.removeWidget(self.loading_label)
                self.loading_label.hide()
                self.loading_label.setParent(None)
                self.loading_label.deleteLater()
                self.loading_label = None
                label_removed = True
            except:
                pass
        
        # Also search for any QLabel with "Loading" text in the layout
        if not label_removed:
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, QLabel) and "Loading" in widget.text():
                        try:
                            layout.removeWidget(widget)
                            widget.hide()
                            widget.setParent(None)
                            widget.deleteLater()
                            label_removed = True
                            break
                        except:
                            pass
                    
        # Create map widget if it doesn't exist
        if self.map_widget is None:
            try:
                # Use fixed raster function
                raster_function = "DAR - StdDev - BlueGreen"
                show_basemap = self.basemap_checkbox.isChecked() if hasattr(self, 'basemap_checkbox') else True
                show_hillshade = self.hillshade_checkbox.isChecked() if hasattr(self, 'hillshade_checkbox') else True
                initial_opacity = self.opacity_slider.value() / 100.0 if hasattr(self, 'opacity_slider') else 0.6
                self.log_message(f"Creating MapWidget with extent: {self.service_extent}, raster function: {raster_function}, show_basemap: {show_basemap}, show_hillshade: {show_hillshade}")
                self.map_widget = MapWidget(self.base_url, self.service_extent, raster_function=raster_function, show_basemap=show_basemap, show_hillshade=show_hillshade)
                self.map_widget.bathymetry_opacity = initial_opacity
                self.map_widget.selectionChanged.connect(self.on_selection_changed)
                self.map_widget.selectionCompleted.connect(self.on_selection_completed)
                layout.addWidget(self.map_widget)
                self.map_widget.show()
                # Force UI update
                self.map_group.update()
                layout.update()
                self.log_message("MapWidget created and added to layout successfully")
                
                # Trigger map load after a short delay to ensure widget is sized
                self.log_message("Scheduling map load in 200ms...")
                QTimer.singleShot(200, lambda: self.trigger_map_load())
            except Exception as e:
                self.log_message(f"ERROR creating MapWidget: {e}")
                import traceback
                self.log_message(traceback.format_exc())
                self.map_widget = None
                
    def trigger_map_load(self):
        """Trigger map load - called via timer."""
        if self.map_widget:
            self.log_message(f"Triggering map load, widget size: {self.map_widget.width()}x{self.map_widget.height()}")
            self.map_widget.load_map()
        else:
            self.log_message("ERROR: map_widget is None when trying to trigger load")
            
    def fit_to_extent(self):
        """Fit map to full service extent."""
        if self.map_widget and self.service_extent:
            self.map_widget.extent = self.service_extent
            self.map_widget.clear_selection()
            self.map_widget.load_map()
            
    def clear_selection(self):
        """Clear the map selection."""
        if self.map_widget:
            self.map_widget.clear_selection()
            
    # Raster function is fixed to "DAR - StdDev - BlueGreen" - no handler needed
            
    def on_basemap_toggled(self, state):
        """Handle basemap checkbox toggle."""
        if self.map_widget:
            show_basemap = (state == Qt.CheckState.Checked.value or state == 2)
            self.map_widget.show_basemap = show_basemap
            if show_basemap:
                # Reload map to get basemap
                self.map_widget.load_map()
            else:
                # Just update display
                self.map_widget.update()
                
    def on_hillshade_toggled(self, state):
        """Handle hillshade checkbox toggle."""
        if self.map_widget:
            show_hillshade = (state == Qt.CheckState.Checked.value or state == 2)
            self.map_widget.show_hillshade = show_hillshade
            if show_hillshade:
                # Reload map to get hillshade layer
                self.map_widget.load_map()
            else:
                # Just update display
                self.map_widget.update()
                
    def on_opacity_changed(self, value):
        """Handle opacity slider change."""
        if self.map_widget:
            opacity = value / 100.0  # Convert 0-100 to 0.0-1.0
            self.map_widget.bathymetry_opacity = opacity
            self.map_widget.update()  # Trigger repaint
            
    def on_cell_size_changed(self, cell_size_text):
        """Handle cell size change - update pixel count if selection exists."""
        # Update pixel count display if there's a current selection
        if hasattr(self, 'selected_bbox') and self.selected_bbox:
            xmin, ymin, xmax, ymax = self.selected_bbox
            self.update_coordinate_display(xmin, ymin, xmax, ymax)
            
    def update_coordinate_display(self, xmin, ymin, xmax, ymax):
        """Update both WebMercator and Geographic coordinate displays."""
        # Update WebMercator coordinates
        self.xmin_edit.setText(f"{xmin:.2f}")
        self.ymin_edit.setText(f"{ymin:.2f}")
        self.xmax_edit.setText(f"{xmax:.2f}")
        self.ymax_edit.setText(f"{ymax:.2f}")
        
        # Convert to Geographic (WGS84) coordinates
        try:
            transformer = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
            west, south = transformer.transform(xmin, ymin)
            east, north = transformer.transform(xmax, ymax)
            
            # Update Geographic coordinates
            self.west_edit.setText(f"{west:.6f}")
            self.south_edit.setText(f"{south:.6f}")
            self.east_edit.setText(f"{east:.6f}")
            self.north_edit.setText(f"{north:.6f}")
        except Exception as e:
            # If conversion fails, clear geographic fields
            self.west_edit.clear()
            self.south_edit.clear()
            self.east_edit.clear()
            self.north_edit.clear()
        
        # Calculate expected number of pixels based on selected cell size
        try:
            width_meters = xmax - xmin
            height_meters = ymax - ymin
            # Get cell size from dropdown (default to 4 if not available)
            cell_size = float(self.cell_size_combo.currentText()) if hasattr(self, 'cell_size_combo') else 4.0
            
            pixels_width = int(width_meters / cell_size)
            pixels_height = int(height_meters / cell_size)
            total_pixels = pixels_width * pixels_height
            
            # Check against maximum size (14,000 x 14,000)
            max_size = 14000
            exceeds_limit = pixels_width > max_size or pixels_height > max_size
            
            # Format with thousand separators
            pixels_width_str = f"{pixels_width:,}"
            pixels_height_str = f"{pixels_height:,}"
            total_pixels_str = f"{total_pixels:,}"
            
            if exceeds_limit:
                # Show warning in red
                self.pixel_count_label.setText(
                    f"⚠️ Expected pixels ({cell_size}m): {pixels_width_str} × {pixels_height_str} = {total_pixels_str} "
                    f"(EXCEEDS MAX: {max_size} × {max_size})"
                )
                self.pixel_count_label.setStyleSheet("font-weight: bold; padding: 5px; color: red;")
            else:
                self.pixel_count_label.setText(
                    f"Expected pixels ({cell_size}m): {pixels_width_str} × {pixels_height_str} = {total_pixels_str}"
                )
                self.pixel_count_label.setStyleSheet("font-weight: bold; padding: 5px;")
        except Exception as e:
            self.pixel_count_label.setText("Expected pixels: --")
            self.pixel_count_label.setStyleSheet("font-weight: bold; padding: 5px;")
            
    def on_selection_changed(self, xmin, ymin, xmax, ymax):
        """Handle selection change from map (during dragging)."""
        if xmin == 0 and ymin == 0 and xmax == 0 and ymax == 0:
            # Selection cleared
            self.xmin_edit.clear()
            self.ymin_edit.clear()
            self.xmax_edit.clear()
            self.ymax_edit.clear()
            self.west_edit.clear()
            self.south_edit.clear()
            self.east_edit.clear()
            self.north_edit.clear()
            self.pixel_count_label.setText("Expected pixels: --")
            self.download_btn.setEnabled(False)
        else:
            # Show real-time values while selecting
            self.update_coordinate_display(xmin, ymin, xmax, ymax)
            self.download_btn.setEnabled(True)
            
    def on_selection_completed(self, xmin, ymin, xmax, ymax):
        """Handle selection completion (when mouse is released) - zoom to selection."""
        if xmin != 0 or ymin != 0 or xmax != 0 or ymax != 0:
            # Store the selected bbox for download
            self.selected_bbox = (xmin, ymin, xmax, ymax)
            # Temporarily disconnect the selection changed signal to prevent clearing
            self.map_widget.selectionChanged.disconnect()
            self.zoom_to_selection(xmin, ymin, xmax, ymax)
            # Reconnect the signal
            self.map_widget.selectionChanged.connect(self.on_selection_changed)
            # Set the final bounds in the text fields after zoom (both coordinate systems)
            self.update_coordinate_display(xmin, ymin, xmax, ymax)
            self.download_btn.setEnabled(True)
            
    def zoom_to_selection(self, xmin, ymin, xmax, ymax):
        """Zoom map to the selected area."""
        if self.map_widget:
            # Store the selected bbox in world coordinates for drawing (original selection, no modifications)
            # This is what will be shown in the purple box and used for download
            self.map_widget.selected_bbox_world = (xmin, ymin, xmax, ymax)
            
            # Calculate the selected area dimensions
            selection_width = xmax - xmin
            selection_height = ymax - ymin
            
            # Add 5% padding around the selection
            padding_x = selection_width * 0.05
            padding_y = selection_height * 0.05
            
            # Start with padded extent
            padded_xmin = xmin - padding_x
            padded_ymin = ymin - padding_y
            padded_xmax = xmax + padding_x
            padded_ymax = ymax + padding_y
            
            padded_width = padded_xmax - padded_xmin
            padded_height = padded_ymax - padded_ymin
            
            # Get widget aspect ratio
            widget_width = self.map_widget.width()
            widget_height = self.map_widget.height()
            
            if widget_width > 0 and widget_height > 0:
                widget_aspect = widget_width / widget_height
                padded_aspect = padded_width / padded_height
                
                # Calculate center of padded area
                center_x = (padded_xmin + padded_xmax) / 2
                center_y = (padded_ymin + padded_ymax) / 2
                
                # Adjust extent to match widget aspect ratio while containing the padded selection
                if padded_aspect > widget_aspect:
                    # Padded area is wider than widget - use padded width, adjust height
                    new_width = padded_width
                    new_height = new_width / widget_aspect
                else:
                    # Padded area is taller than widget - use padded height, adjust width
                    new_height = padded_height
                    new_width = new_height * widget_aspect
                
                # Create new extent centered on the padded selection
                new_extent = (
                    center_x - new_width / 2,
                    center_y - new_height / 2,
                    center_x + new_width / 2,
                    center_y + new_height / 2
                )
            else:
                # Fallback to padded extent if widget size not available
                new_extent = (padded_xmin, padded_ymin, padded_xmax, padded_ymax)
            
            self.map_widget.extent = new_extent
            # Don't clear selection - keep it visible
            self.map_widget.load_map()
            
    def browse_output_path(self):
        """Browse for output file path."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save GeoTIFF",
            "",
            "GeoTIFF Files (*.tif *.tiff);;All Files (*)"
        )
        if file_path:
            self.output_path_edit.setText(file_path)
            
    def start_download(self):
        """Start downloading the selected area."""
        # Get bbox from stored selection or manual entry
        bbox = None
        
        # First try to use stored selected bbox
        if hasattr(self, 'selected_bbox') and self.selected_bbox:
            bbox = self.selected_bbox
        # Then try to get from map widget
        elif self.map_widget:
            bbox = self.map_widget.get_selection_bbox()
        # Finally try manual entry
        else:
            try:
                xmin_text = self.xmin_edit.text()
                ymin_text = self.ymin_edit.text()
                xmax_text = self.xmax_edit.text()
                ymax_text = self.ymax_edit.text()
                
                # Check if fields have actual values (not just placeholders)
                if xmin_text and ymin_text and xmax_text and ymax_text:
                    bbox = (
                        float(xmin_text),
                        float(ymin_text),
                        float(xmax_text),
                        float(ymax_text)
                    )
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter valid coordinates.")
                return
                
        if not bbox:
            QMessageBox.warning(self, "No Selection", "Please select an area on the map.")
            return
            
        output_path = self.output_path_edit.text()
        if not output_path:
            QMessageBox.warning(self, "No Output Path", "Please specify an output file path.")
            return
            
        output_crs = self.crs_combo.currentText()
        cell_size = float(self.cell_size_combo.currentText())  # Get cell size in meters
        
        # Check if selection exceeds maximum size (14,000 x 14,000 pixels)
        xmin, ymin, xmax, ymax = bbox
        width_meters = xmax - xmin
        height_meters = ymax - ymin
        pixels_width = int(width_meters / cell_size)
        pixels_height = int(height_meters / cell_size)
        max_size = 14000
        
        if pixels_width > max_size or pixels_height > max_size:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Selection Too Large")
            msg.setText(
                f"Selected area exceeds maximum download size ({max_size:,} × {max_size:,} pixels).\n\n"
                f"Requested size: {pixels_width:,} × {pixels_height:,} pixels.\n\n"
                f"Please either:\n"
                f"1. Select a smaller area, or\n"
                f"2. Increase the cell size (currently {cell_size}m)"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            return
        
        # Disable download button
        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting download...")
        
        # Create downloader thread
        self.downloader = BathymetryDownloader(
            self.base_url,
            bbox,
            output_path,
            output_crs,
            pixel_size=cell_size,
            max_size=max_size
        )
        self.downloader.progress.connect(self.progress_bar.setValue)
        self.downloader.status.connect(self.on_status_update)
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.error.connect(self.on_download_error)
        self.downloader.start()
        
    def on_status_update(self, message):
        """Handle status update from downloader."""
        self.status_label.setText(message)
        self.log_message(message)
        
    def on_download_finished(self, file_path):
        """Handle download completion."""
        self.status_label.setText(f"Download complete: {file_path}")
        self.log_message(f"✓ Download complete: {file_path}")
        self.download_btn.setEnabled(True)
        QMessageBox.information(self, "Success", f"GeoTIFF saved to:\n{file_path}")
        
    def on_download_error(self, error_message):
        """Handle download error."""
        self.status_label.setText(f"Error: {error_message}")
        self.log_message(f"✗ Error: {error_message}")
        self.download_btn.setEnabled(True)
        QMessageBox.critical(self, "Download Error", error_message)
        
    def log_message(self, message):
        """Add message to log."""
        self.log_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def closeEvent(self, event):
        """Handle window close event."""
        if self.downloader and self.downloader.isRunning():
            reply = QMessageBox.question(
                self,
                "Download in Progress",
                "A download is in progress. Do you want to cancel it and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.downloader.cancel()
                self.downloader.wait(3000)  # Wait up to 3 seconds
            else:
                event.ignore()
                return
        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


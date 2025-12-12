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
        
        # Raster function selector
        map_controls.addWidget(QLabel("Raster Function:"))
        self.raster_function_combo = QComboBox()
        self.raster_function_combo.addItem("Shaded Relief - Haxby - MD Hillshade 2")  # Default
        self.raster_function_combo.currentTextChanged.connect(self.on_raster_function_changed)
        map_controls.addWidget(self.raster_function_combo)
        
        map_layout.addLayout(map_controls)
        
        # Basemap controls
        basemap_controls = QHBoxLayout()
        self.basemap_checkbox = QCheckBox("Show World Imagery Basemap")
        self.basemap_checkbox.setChecked(True)
        self.basemap_checkbox.stateChanged.connect(self.on_basemap_toggled)
        basemap_controls.addWidget(self.basemap_checkbox)
        
        basemap_controls.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)  # 100% opacity (fully opaque)
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
        selection_layout = QVBoxLayout()
        
        self.xmin_edit = QLineEdit()
        self.xmin_edit.setPlaceholderText("XMin")
        self.ymin_edit = QLineEdit()
        self.ymin_edit.setPlaceholderText("YMin")
        self.xmax_edit = QLineEdit()
        self.xmax_edit.setPlaceholderText("XMax")
        self.ymax_edit = QLineEdit()
        self.ymax_edit.setPlaceholderText("YMax")
        
        selection_layout.addWidget(QLabel("XMin:"))
        selection_layout.addWidget(self.xmin_edit)
        selection_layout.addWidget(QLabel("YMin:"))
        selection_layout.addWidget(self.ymin_edit)
        selection_layout.addWidget(QLabel("XMax:"))
        selection_layout.addWidget(self.xmax_edit)
        selection_layout.addWidget(QLabel("YMax:"))
        selection_layout.addWidget(self.ymax_edit)
        
        selection_group.setLayout(selection_layout)
        right_layout.addWidget(selection_group)
        
        # Output options
        output_group = QGroupBox("Output Options")
        output_layout = QVBoxLayout()
        
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
        
        # Update raster function combo box with available functions
        raster_functions = service_data.get("raster_functions", [])
        if raster_functions:
            current_selection = self.raster_function_combo.currentText()
            self.raster_function_combo.clear()
            self.raster_function_combo.addItems(raster_functions)
            # Try to restore previous selection or use default
            index = self.raster_function_combo.findText(current_selection)
            if index >= 0:
                self.raster_function_combo.setCurrentIndex(index)
            else:
                # Try to find the default
                default_index = self.raster_function_combo.findText("Shaded Relief - Haxby - MD Hillshade 2")
                if default_index >= 0:
                    self.raster_function_combo.setCurrentIndex(default_index)
                elif self.raster_function_combo.count() > 0:
                    self.raster_function_combo.setCurrentIndex(0)
        
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
                # Get initial raster function from combo box
                initial_raster_function = self.raster_function_combo.currentText() if hasattr(self, 'raster_function_combo') else "Shaded Relief - Haxby - MD Hillshade 2"
                show_basemap = self.basemap_checkbox.isChecked() if hasattr(self, 'basemap_checkbox') else True
                initial_opacity = self.opacity_slider.value() / 100.0 if hasattr(self, 'opacity_slider') else 1.0
                self.log_message(f"Creating MapWidget with extent: {self.service_extent}, raster function: {initial_raster_function}, show_basemap: {show_basemap}")
                self.map_widget = MapWidget(self.base_url, self.service_extent, raster_function=initial_raster_function, show_basemap=show_basemap)
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
            
    def on_raster_function_changed(self, raster_function):
        """Handle raster function selection change."""
        if self.map_widget:
            self.log_message(f"Changing raster function to: {raster_function}")
            self.map_widget.set_raster_function(raster_function)
            
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
                
    def on_opacity_changed(self, value):
        """Handle opacity slider change."""
        if self.map_widget:
            opacity = value / 100.0  # Convert 0-100 to 0.0-1.0
            self.map_widget.bathymetry_opacity = opacity
            self.map_widget.update()  # Trigger repaint
            
    def on_selection_changed(self, xmin, ymin, xmax, ymax):
        """Handle selection change from map (during dragging)."""
        if xmin == 0 and ymin == 0 and xmax == 0 and ymax == 0:
            # Selection cleared
            self.xmin_edit.clear()
            self.ymin_edit.clear()
            self.xmax_edit.clear()
            self.ymax_edit.clear()
            self.download_btn.setEnabled(False)
        else:
            # Show real-time values while selecting
            self.xmin_edit.setText(f"{xmin:.2f}")
            self.ymin_edit.setText(f"{ymin:.2f}")
            self.xmax_edit.setText(f"{xmax:.2f}")
            self.ymax_edit.setText(f"{ymax:.2f}")
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
            # Set the final bounds in the text fields after zoom
            self.xmin_edit.setText(f"{xmin:.2f}")
            self.ymin_edit.setText(f"{ymin:.2f}")
            self.xmax_edit.setText(f"{xmax:.2f}")
            self.ymax_edit.setText(f"{ymax:.2f}")
            self.download_btn.setEnabled(True)
            
    def zoom_to_selection(self, xmin, ymin, xmax, ymax):
        """Zoom map to the selected area."""
        if self.map_widget:
            # Store the selected bbox in world coordinates for drawing (before any modifications)
            self.map_widget.selected_bbox_world = (xmin, ymin, xmax, ymax)
            
            # Add a 5% padding around the selection
            width = xmax - xmin
            height = ymax - ymin
            padding_x = width * 0.05
            padding_y = height * 0.05
            
            # Calculate new extent with padding, maintaining the selection's aspect ratio
            new_extent = (
                xmin - padding_x,
                ymin - padding_y,
                xmax + padding_x,
                ymax + padding_y
            )
            
            # Get widget aspect ratio
            widget_width = self.map_widget.width()
            widget_height = self.map_widget.height()
            
            if widget_width > 0 and widget_height > 0:
                widget_aspect = widget_width / widget_height
                selection_aspect = width / height
                
                # If the selection aspect ratio is very different from widget, 
                # we might need to adjust, but let's preserve the selection's shape
                # The service will handle the rendering based on the extent we provide
                pass  # Keep the extent as-is to preserve selection shape
            
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
        
        # Disable download button
        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting download...")
        
        # Create downloader thread
        self.downloader = BathymetryDownloader(
            self.base_url,
            bbox,
            output_path,
            output_crs
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


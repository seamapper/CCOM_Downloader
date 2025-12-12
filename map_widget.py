"""
Map widget for displaying bathymetry data and selecting areas of interest.
"""
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QRect, QPoint, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap, QImage
import requests
from io import BytesIO
from PIL import Image
import numpy as np


class BasemapLoader(QThread):
    """Thread for loading basemap (World Imagery) tiles."""
    tileLoaded = pyqtSignal(QPixmap)
    
    def __init__(self, bbox, size):
        super().__init__()
        self.bbox = bbox  # (xmin, ymin, xmax, ymax)
        self.size = size  # (width, height)
        self.basemap_url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
        
    def run(self):
        """Load basemap tile from World Imagery service."""
        try:
            xmin, ymin, xmax, ymax = self.bbox
            width, height = self.size
            
            params = {
                "bbox": f"{xmin},{ymin},{xmax},{ymax}",
                "size": f"{width},{height}",
                "format": "png",
                "f": "image",
                "transparent": "false"
            }
            
            response = requests.get(self.basemap_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Load directly into QPixmap
            img_bytes = BytesIO()
            img = Image.open(BytesIO(response.content))
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes.getvalue(), 'PNG')
            
            self.tileLoaded.emit(pixmap)
            
        except Exception as e:
            print(f"Error loading basemap: {e}")
            self.tileLoaded.emit(QPixmap())


class MapTileLoader(QThread):
    """Thread for loading map tiles asynchronously."""
    tileLoaded = pyqtSignal(QPixmap, float, float, float, float)  # pixmap, xmin, ymin, xmax, ymax
    
    def __init__(self, base_url, bbox, size, raster_function="Haxby Percent Clip DRA"):
        super().__init__()
        self.base_url = base_url
        self.bbox = bbox  # (xmin, ymin, xmax, ymax)
        self.size = size  # (width, height)
        self.raster_function = raster_function
        
    def run(self):
        """Load tile from ArcGIS ImageServer."""
        try:
            xmin, ymin, xmax, ymax = self.bbox
            width, height = self.size
            
            print(f"Loading map tile: bbox=({xmin:.2f}, {ymin:.2f}, {xmax:.2f}, {ymax:.2f}), size={width}x{height}")
            
            # Build export URL
            url = f"{self.base_url}/exportImage"
            params = {
                "bbox": f"{xmin},{ymin},{xmax},{ymax}",
                "size": f"{width},{height}",
                "format": "png",
                "f": "image"
            }
            
            # Add raster function as renderingRule if specified
            if self.raster_function and self.raster_function != "None":
                import json
                rendering_rule = {"rasterFunction": self.raster_function}
                params["renderingRule"] = json.dumps(rendering_rule)
                print(f"Using raster function: {self.raster_function}")
            
            # Build full URL for debugging
            from urllib.parse import urlencode
            full_url = f"{url}?{urlencode(params)}"
            print(f"Full URL: {full_url}")
            print(f"Requesting: {url} with params: {params}")
            
            # Request image
            response = requests.get(url, params=params, timeout=30)
            print(f"Response status: {response.status_code}")
            response.raise_for_status()
            
            print(f"Response content length: {len(response.content)} bytes")
            print(f"Response content type: {response.headers.get('Content-Type', 'unknown')}")
            
            # Convert to QPixmap - use a more reliable method
            img = Image.open(BytesIO(response.content))
            print(f"Image opened: {img.size}, mode: {img.mode}")
            
            # Save to bytes and load directly into QPixmap
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Load directly into QPixmap from bytes
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes.getvalue(), 'PNG')
            
            if pixmap.isNull():
                # Fallback: convert via RGB array
                print("Direct load failed, trying array conversion...")
                img_rgb = img.convert("RGB")
                img_array = np.array(img_rgb, dtype=np.uint8)
                height, width, channel = img_array.shape
                
                # Ensure array is contiguous and copy the data
                if not img_array.flags['C_CONTIGUOUS']:
                    img_array = np.ascontiguousarray(img_array)
                
                # Create QImage - need to keep array in scope
                bytes_per_line = 3 * width
                q_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                # Copy the image to ensure data persists
                q_image = q_image.copy()
                pixmap = QPixmap.fromImage(q_image)
            
            # Verify pixmap has content
            if not pixmap.isNull():
                test_img = pixmap.toImage()
                if not test_img.isNull():
                    test_color = test_img.pixelColor(pixmap.width()//2, pixmap.height()//2)
                    print(f"Pixmap center pixel: R={test_color.red()}, G={test_color.green()}, B={test_color.blue()}")
            
            print(f"Created pixmap: {pixmap.width()}x{pixmap.height()}, isNull: {pixmap.isNull()}")
            
            print("Emitting tileLoaded signal...")
            self.tileLoaded.emit(pixmap, xmin, ymin, xmax, ymax)
            print("tileLoaded signal emitted")
            
        except Exception as e:
            print(f"Error loading tile: {e}")
            import traceback
            traceback.print_exc()
            # Emit empty pixmap on error
            self.tileLoaded.emit(QPixmap(), *self.bbox)


class MapWidget(QWidget):
    """Interactive map widget for displaying bathymetry and selecting areas."""
    
    selectionChanged = pyqtSignal(float, float, float, float)  # xmin, ymin, xmax, ymax
    selectionCompleted = pyqtSignal(float, float, float, float)  # xmin, ymin, xmax, ymax - emitted when selection is finished
    
    def __init__(self, base_url, initial_extent, parent=None, raster_function="Shaded Relief - Haxby - MD Hillshade 2", show_basemap=True):
        super().__init__(parent)
        self.base_url = base_url
        self.extent = initial_extent  # (xmin, ymin, xmax, ymax)
        self.current_pixmap = QPixmap()
        self.basemap_pixmap = QPixmap()
        self.show_basemap = show_basemap
        self.bathymetry_opacity = 1.0  # Opacity for bathymetry layer (0.0 to 1.0) - default 100%
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self.is_panning = False
        self.pan_start = None
        self.raster_function = raster_function
        self.map_loaded = False
        self._loading = False  # Flag to prevent multiple simultaneous loads
        self.selected_bbox_world = None  # Store selected bbox in world coordinates for persistent display
        print(f"MapWidget initialized with raster function: {self.raster_function}, show_basemap: {self.show_basemap}")
        
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        
        # Don't load map immediately - wait for widget to be shown and sized
        # The load will be triggered by showEvent or when explicitly called
        
    def set_raster_function(self, raster_function):
        """Set the raster function for map display."""
        self.raster_function = raster_function
        self.load_map()
        
    def showEvent(self, event):
        """Handle widget being shown - trigger map load if not already loaded."""
        super().showEvent(event)
        print(f"MapWidget showEvent called, map_loaded={self.map_loaded}, size={self.width()}x{self.height()}")
        if not self.map_loaded:
            # Use a timer to ensure widget is fully sized
            from PyQt6.QtCore import QTimer
            print("Scheduling map load via timer...")
            QTimer.singleShot(100, self.load_map)
            
    def load_map(self):
        """Load map for current extent."""
        # Prevent multiple simultaneous loads
        if hasattr(self, '_loading') and self._loading:
            print("load_map() already in progress, skipping...")
            return
            
        self._loading = True
        
        print("=" * 50)
        print("load_map() called!")
        print(f"Widget visible: {self.isVisible()}")
        print(f"Widget size: {self.width()}x{self.height()}")
        print(f"Extent: {self.extent}")
        print(f"Base URL: {self.base_url}")
        
        # Ensure widget has a valid size
        widget_width = self.width()
        widget_height = self.height()
        
        # If widget has no size yet, use minimum size
        if widget_width <= 0 or widget_height <= 0:
            widget_width = 800
            widget_height = 600
            print(f"Widget has no size yet, using default: {widget_width}x{widget_height}")
        else:
            print(f"Widget size: {widget_width}x{widget_height}")
        
        # Use widget size to fill the window completely
        size = (widget_width, widget_height)
        
        print(f"Starting map load with extent: {self.extent}, size: {size}")
        print(f"Using raster function: {self.raster_function}")
        
        # Stop any existing loaders
        if hasattr(self, 'loader') and self.loader and self.loader.isRunning():
            print("Stopping existing loader...")
            self.loader.terminate()
            self.loader.wait(1000)  # Wait up to 1 second
        if hasattr(self, 'basemap_loader') and self.basemap_loader and self.basemap_loader.isRunning():
            print("Stopping existing basemap loader...")
            self.basemap_loader.terminate()
            self.basemap_loader.wait(1000)  # Wait up to 1 second
        
        # Load basemap if enabled
        if self.show_basemap:
            print("Loading basemap...")
            self.basemap_loader = BasemapLoader(self.extent, size)
            self.basemap_loader.tileLoaded.connect(self.on_basemap_loaded)
            self.basemap_loader.finished.connect(lambda: setattr(self, '_loading', False))
            self.basemap_loader.start()
        
        # Load bathymetry layer
        print("Creating MapTileLoader...")
        self.loader = MapTileLoader(self.base_url, self.extent, size, self.raster_function)
        print("Connecting signals...")
        self.loader.tileLoaded.connect(self.on_tile_loaded)
        self.loader.finished.connect(self.on_loader_finished)
        self.loader.finished.connect(lambda: setattr(self, '_loading', False))
        print("Starting loader thread...")
        self.loader.start()
        print(f"Loader thread started, isRunning: {self.loader.isRunning()}")
        self.map_loaded = True
        print("=" * 50)
        
    def on_basemap_loaded(self, pixmap):
        """Handle basemap tile loaded."""
        if not pixmap.isNull():
            widget_size = self.size()
            if widget_size.width() > 0 and widget_size.height() > 0:
                if widget_size.width() == pixmap.width() and widget_size.height() == pixmap.height():
                    self.basemap_pixmap = pixmap
                else:
                    self.basemap_pixmap = pixmap.scaled(
                        widget_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
            else:
                self.basemap_pixmap = pixmap
            print(f"Basemap loaded: {self.basemap_pixmap.width()}x{self.basemap_pixmap.height()}")
            self.update()  # Trigger repaint
        
    def on_loader_finished(self):
        """Handle loader thread finishing."""
        # If we still have an empty pixmap, the load might have failed
        if self.current_pixmap.isNull():
            print("Warning: Map tile loader finished but no pixmap was loaded")
        
    def on_tile_loaded(self, pixmap, xmin, ymin, xmax, ymax):
        """Handle loaded tile."""
        print(f"on_tile_loaded called! pixmap.isNull: {pixmap.isNull()}, size: {pixmap.width()}x{pixmap.height()}")
        if not pixmap.isNull():
            # Check if pixmap has actual content (not all white/transparent)
            # Sample a few pixels to verify
            sample_image = pixmap.toImage()
            if not sample_image.isNull():
                # Sample a few pixels
                colors = []
                for x in [10, pixmap.width()//2, pixmap.width()-10]:
                    for y in [10, pixmap.height()//2, pixmap.height()-10]:
                        if x < pixmap.width() and y < pixmap.height():
                            color = sample_image.pixelColor(x, y)
                            colors.append((color.red(), color.green(), color.blue()))
                print(f"Sample pixel colors: {colors[:3]}...")  # Print first 3
            
            widget_size = self.size()
            print(f"Widget size in on_tile_loaded: {widget_size.width()}x{widget_size.height()}")
            
            # Don't scale if sizes match - use pixmap directly
            if widget_size.width() == pixmap.width() and widget_size.height() == pixmap.height():
                print("Pixmap size matches widget, using directly")
                self.current_pixmap = pixmap
            elif widget_size.width() > 0 and widget_size.height() > 0:
                # Scale to fit widget while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    widget_size, 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                print(f"Scaled pixmap: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
                self.current_pixmap = scaled_pixmap
            else:
                # Widget not sized yet, use pixmap as-is
                print("Widget not sized, using pixmap as-is")
                self.current_pixmap = pixmap
                
            self.extent = (xmin, ymin, xmax, ymax)
            print(f"Setting current_pixmap, isNull: {self.current_pixmap.isNull()}, size: {self.current_pixmap.width()}x{self.current_pixmap.height()}")
            print(f"Calling update() to repaint widget")
            self.update()  # Trigger repaint
            self.repaint()  # Force immediate repaint
            print(f"Map tile loaded successfully: {pixmap.width()}x{pixmap.height()}")
        else:
            print("Error: Received null pixmap from tile loader")
            
    def screen_to_world(self, point):
        """Convert screen coordinates to world coordinates."""
        if self.current_pixmap.isNull():
            return None
            
        pixmap_rect = self.current_pixmap.rect()
        pixmap_rect.moveCenter(self.rect().center())
        
        if not pixmap_rect.contains(point):
            return None
            
        # Calculate relative position in pixmap
        rel_x = (point.x() - pixmap_rect.left()) / pixmap_rect.width()
        rel_y = (point.y() - pixmap_rect.top()) / pixmap_rect.height()
        
        # Convert to world coordinates
        xmin, ymin, xmax, ymax = self.extent
        world_x = xmin + rel_x * (xmax - xmin)
        world_y = ymax - rel_y * (ymax - ymin)  # Y is inverted in screen coordinates
        
        return (world_x, world_y)
        
    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates."""
        if self.current_pixmap.isNull():
            return None
            
        pixmap_rect = self.current_pixmap.rect()
        pixmap_rect.moveCenter(self.rect().center())
        
        xmin, ymin, xmax, ymax = self.extent
        rel_x = (world_x - xmin) / (xmax - xmin)
        rel_y = (ymax - world_y) / (ymax - ymin)  # Y is inverted
        
        screen_x = pixmap_rect.left() + rel_x * pixmap_rect.width()
        screen_y = pixmap_rect.top() + rel_y * pixmap_rect.height()
        
        return QPoint(int(screen_x), int(screen_y))
        
    def get_selection_bbox(self):
        """Get the bounding box of the current selection in world coordinates."""
        if not self.selection_start or not self.selection_end:
            return None
            
        start_world = self.screen_to_world(self.selection_start)
        end_world = self.screen_to_world(self.selection_end)
        
        if not start_world or not end_world:
            return None
            
        xmin = min(start_world[0], end_world[0])
        xmax = max(start_world[0], end_world[0])
        ymin = min(start_world[1], end_world[1])
        ymax = max(start_world[1], end_world[1])
        
        return (xmin, ymin, xmax, ymax)
        
    def clear_selection(self):
        """Clear the current selection."""
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self.selected_bbox_world = None  # Also clear persistent selection
        self.update()
        self.selectionChanged.emit(0, 0, 0, 0)
        
    def world_bbox_to_screen_rect(self, bbox_world):
        """Convert world bbox to screen rectangle for drawing."""
        if bbox_world is None:
            return None
            
        xmin, ymin, xmax, ymax = bbox_world
        
        # Convert corners to screen coordinates
        top_left = self.world_to_screen(xmin, ymax)
        bottom_right = self.world_to_screen(xmax, ymin)
        
        if top_left and bottom_right:
            return QRect(top_left, bottom_right)
        return None
        
    def mousePressEvent(self, event):
        """Handle mouse press for selection or panning."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Left button for selection only
            # Clear previous selection when starting a new one
            self.clear_selection()
            self.selection_start = event.position().toPoint()
            self.selection_end = self.selection_start
            self.is_selecting = True
            self.update()
        elif event.button() == Qt.MouseButton.MiddleButton:
            # Middle button for panning
            self.is_panning = True
            self.pan_start = event.position().toPoint()
            self.update()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for selection or panning."""
        if self.is_selecting:
            self.selection_end = event.position().toPoint()
            bbox = self.get_selection_bbox()
            if bbox:
                self.selectionChanged.emit(*bbox)
            self.update()
        elif self.is_panning and self.pan_start:
            # Calculate pan delta
            current_pos = event.position().toPoint()
            delta = current_pos - self.pan_start
            
            # Convert screen delta to world delta
            pixmap_rect = self.current_pixmap.rect()
            pixmap_rect.moveCenter(self.rect().center())
            
            if not pixmap_rect.isNull():
                xmin, ymin, xmax, ymax = self.extent
                world_width = xmax - xmin
                world_height = ymax - ymin
                
                rel_delta_x = -delta.x() / pixmap_rect.width() * world_width
                rel_delta_y = delta.y() / pixmap_rect.height() * world_height
                
                # Update extent
                self.extent = (
                    xmin + rel_delta_x,
                    ymin + rel_delta_y,
                    xmax + rel_delta_x,
                    ymax + rel_delta_y
                )
                self.pan_start = current_pos
                self.clear_selection()
                self.load_map()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release for selection or panning."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_selecting:
                self.selection_end = event.position().toPoint()
                self.is_selecting = False
                bbox = self.get_selection_bbox()
                if bbox:
                    # Store the selected bbox in world coordinates for persistent display
                    self.selected_bbox_world = bbox
                    self.selectionChanged.emit(*bbox)
                    # Emit selection completed signal for zooming
                    self.selectionCompleted.emit(*bbox)
                # Clear the active selection rectangle (red dashed line)
                self.selection_start = None
                self.selection_end = None
                self.update()
            elif self.is_panning:
                self.is_panning = False
                self.pan_start = None
        elif event.button() == Qt.MouseButton.MiddleButton and self.is_panning:
            self.is_panning = False
            self.pan_start = None
            
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        if self.current_pixmap.isNull():
            return
            
        # Get center of widget in world coordinates
        widget_center = QPoint(self.width() // 2, self.height() // 2)
        world_pos = self.screen_to_world(widget_center)
        
        if not world_pos:
            # Fallback: use center of extent if screen_to_world fails
            xmin, ymin, xmax, ymax = self.extent
            center_x = (xmin + xmax) / 2
            center_y = (ymin + ymax) / 2
            world_pos = (center_x, center_y)
            
        # Calculate zoom factor
        zoom_factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        
        # Calculate new extent centered on window center
        xmin, ymin, xmax, ymax = self.extent
        width = (xmax - xmin) / zoom_factor
        height = (ymax - ymin) / zoom_factor
        
        center_x, center_y = world_pos
        new_xmin = center_x - width / 2
        new_xmax = center_x + width / 2
        new_ymin = center_y - height / 2
        new_ymax = center_y + height / 2
        
        self.extent = (new_xmin, new_ymin, new_xmax, new_ymax)
        self.clear_selection()
        self.load_map()
        
    def resizeEvent(self, event):
        """Handle widget resize."""
        super().resizeEvent(event)
        if not self.current_pixmap.isNull():
            self.current_pixmap = self.current_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.update()
            
    def paintEvent(self, event):
        """Paint the map and selection rectangle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        widget_rect = self.rect()
        
        # Draw basemap first (if available)
        if self.show_basemap and not self.basemap_pixmap.isNull():
            basemap_rect = self.basemap_pixmap.rect()
            x = (widget_rect.width() - basemap_rect.width()) // 2
            y = (widget_rect.height() - basemap_rect.height()) // 2
            target_rect = QRect(x, y, basemap_rect.width(), basemap_rect.height())
            painter.drawPixmap(target_rect, self.basemap_pixmap)
        else:
            # Fill background if no basemap
            painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        # Draw bathymetry layer on top (with opacity)
        if not self.current_pixmap.isNull():
            pixmap_rect = self.current_pixmap.rect()
            
            # Center the pixmap in the widget
            x = (widget_rect.width() - pixmap_rect.width()) // 2
            y = (widget_rect.height() - pixmap_rect.height()) // 2
            target_rect = QRect(x, y, pixmap_rect.width(), pixmap_rect.height())
            
            # Draw with opacity
            painter.setOpacity(self.bathymetry_opacity)
            painter.drawPixmap(target_rect, self.current_pixmap)
            painter.setOpacity(1.0)  # Reset opacity
        elif not self.show_basemap:
            # Draw placeholder only if basemap is not shown
            painter.fillRect(self.rect(), QColor(200, 200, 200))
            status_text = "Loading map..."
            if hasattr(self, 'loader') and self.loader and self.loader.isRunning():
                status_text = "Loading map..."
            else:
                status_text = "No map data available"
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, status_text)
            
        # Draw selection rectangle (always on top)
        # First draw the persistent selected bbox if it exists
        if self.selected_bbox_world:
            bbox_screen = self.world_bbox_to_screen_rect(self.selected_bbox_world)
            if bbox_screen:
                pen = QPen(QColor(128, 0, 128), 2, Qt.PenStyle.DashLine)  # Purple dashed line
                brush = QBrush(QColor(128, 0, 128, 20))  # Light purple fill
                painter.setPen(pen)
                painter.setBrush(brush)
                painter.drawRect(bbox_screen)
        
        # Draw active selection rectangle (while dragging)
        if self.selection_start and self.selection_end:
            selection_rect = QRect(self.selection_start, self.selection_end).normalized()
            pen = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine)
            brush = QBrush(QColor(255, 0, 0, 30))
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(selection_rect)


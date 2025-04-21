import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
from typing import Optional, Dict, Callable
import logging
import time
from src.utils.camera_manager import CameraManager
from src.utils.frame_buffer import CircularFrameBuffer

# Configure logging
logger = logging.getLogger(__name__)

class CameraGridView(ttk.Frame):
    def __init__(self, parent, camera_manager: CameraManager):
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.frame_buffer = CircularFrameBuffer(buffer_size=3)  # Triple buffering
        self.last_update_time = 0
        self.update_interval = 1.0 / 60  # Target 60 FPS for smooth display
        self.photo_image = None  # Keep track of current PhotoImage
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the grid view UI"""
        self.video_label = ttk.Label(self)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def update_frame(self, processed_frame=None):
        """Update the grid view with current camera frames"""
        # Check if enough time has passed since last update
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return
            
        # Get frames and push to buffer
        grid_frame = self.camera_manager.get_grid_frames()
        if grid_frame.size > 0:
            try:
                # Use processed frame if available (contains face detection overlays)
                display_frame = processed_frame if processed_frame is not None else grid_frame
                
                # Push frame to buffer
                self.frame_buffer.push_frame(display_frame)
                
                # Get frame from buffer for display
                frame_to_display = self.frame_buffer.peek_frame()
                if frame_to_display is None:
                    return
                
                # Convert to PhotoImage
                # Resize frame if too large
                h, w = frame_to_display.shape[:2]
                if w > 1280 or h > 720:  # Max size for display
                    scale = min(1280/w, 720/h)
                    new_size = (int(w * scale), int(h * scale))
                    frame_to_display = cv2.resize(frame_to_display, new_size)
                    logger.debug(f"Resized frame from {w}x{h} to {new_size[0]}x{new_size[1]}")

                # Convert frame for display
                image = cv2.cvtColor(frame_to_display, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(image)
                
                # Create new PhotoImage only if needed
                if self.photo_image is None:
                    self.photo_image = ImageTk.PhotoImage(image=image)
                else:
                    # Update existing PhotoImage
                    self.photo_image.paste(image)
                
                # Update label with current PhotoImage
                self.video_label.configure(image=self.photo_image)
                self.last_update_time = current_time
                logger.debug("Grid view updated successfully")
            except Exception as e:
                logger.error(f"Failed to update grid view: {str(e)}", exc_info=True)
        else:
            logger.warning("No frames available for grid view")

class SingleCameraView(ttk.Frame):
    def __init__(self, parent, camera_manager: CameraManager, camera_id: str):
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.camera_id = camera_id
        self.frame_buffer = CircularFrameBuffer(buffer_size=3)  # Triple buffering
        self.last_update_time = 0
        self.update_interval = 1.0 / 60  # Target 60 FPS for smooth display
        self.photo_image = None  # Keep track of current PhotoImage
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the single camera view UI"""
        # Video frame
        self.video_frame = ttk.Frame(self)
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status frame
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Status: Running")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Controls frame
        self.controls_frame = ttk.Frame(self)
        self.controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.controls_frame, text="Settings", 
                  command=self.show_settings).pack(side=tk.LEFT, padx=5)
        
    def update_frame(self, processed_frame=None):
        """Update the camera view with current frame"""
        # Check if enough time has passed since last update
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return
            
        frame = self.camera_manager.get_frame(self.camera_id)
        if frame is not None:
            try:
                # Use processed frame if available (contains face detection overlays)
                display_frame = processed_frame if processed_frame is not None else frame
                
                # Push frame to buffer
                self.frame_buffer.push_frame(display_frame)
                
                # Get frame from buffer for display
                frame_to_display = self.frame_buffer.peek_frame()
                if frame_to_display is None:
                    return
                
                # Convert to PhotoImage
                # Resize frame if too large
                h, w = frame_to_display.shape[:2]
                if w > 1280 or h > 720:  # Max size for display
                    scale = min(1280/w, 720/h)
                    new_size = (int(w * scale), int(h * scale))
                    frame_to_display = cv2.resize(frame_to_display, new_size)
                    logger.debug(f"Resized frame from {w}x{h} to {new_size[0]}x{new_size[1]}")

                # Convert frame for display
                image = cv2.cvtColor(frame_to_display, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(image)
                
                # Create new PhotoImage only if needed
                if self.photo_image is None:
                    self.photo_image = ImageTk.PhotoImage(image=image)
                else:
                    # Update existing PhotoImage
                    self.photo_image.paste(image)
                
                # Update label with current PhotoImage
                self.video_label.configure(image=self.photo_image)
                self.last_update_time = current_time
                logger.debug(f"Camera view {self.camera_id} updated successfully")
                
                # Update status
                status = self.camera_manager.get_camera_status(self.camera_id)
                if status:
                    self.status_label.configure(
                        text=f"Status: {status.get('running', False)}, "
                             f"FPS: {status.get('fps', 0)}"
                    )
                    logger.debug(f"Camera {self.camera_id} status: {status}")
            except Exception as e:
                logger.error(f"Failed to update camera view {self.camera_id}: {str(e)}", exc_info=True)
        else:
            logger.warning(f"No frame available for camera {self.camera_id}")
                
    def show_settings(self):
        """Show camera settings dialog"""
        settings_dialog = CameraSettingsDialog(self, self.camera_id, self.camera_manager)
        self.wait_window(settings_dialog)

class CameraSettingsDialog(tk.Toplevel):
    def __init__(self, parent, camera_id: str, camera_manager: CameraManager):
        super().__init__(parent)
        self.camera_id = camera_id
        self.camera_manager = camera_manager
        
        self.title(f"Camera Settings - {camera_id}")
        self.geometry("400x300")
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the settings dialog UI"""
        # Resolution frame
        resolution_frame = ttk.LabelFrame(self, text="Resolution")
        resolution_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(resolution_frame, text="Width:").grid(row=0, column=0, padx=5, pady=5)
        self.width_var = tk.StringVar(value="640")
        width_entry = ttk.Entry(resolution_frame, textvariable=self.width_var)
        width_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(resolution_frame, text="Height:").grid(row=1, column=0, padx=5, pady=5)
        self.height_var = tk.StringVar(value="480")
        height_entry = ttk.Entry(resolution_frame, textvariable=self.height_var)
        height_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # FPS frame
        fps_frame = ttk.LabelFrame(self, text="Frame Rate")
        fps_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(fps_frame, text="FPS:").grid(row=0, column=0, padx=5, pady=5)
        self.fps_var = tk.StringVar(value="30")
        fps_entry = ttk.Entry(fps_frame, textvariable=self.fps_var)
        fps_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Apply", 
                  command=self.apply_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", 
                  command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
    def apply_settings(self):
        """Apply the camera settings"""
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            fps = int(self.fps_var.get())
            
            camera = self.camera_manager.cameras.get(self.camera_id)
            if camera:
                camera.set_resolution(width, height)
                camera.set_fps(fps)
                
        except ValueError:
            tk.messagebox.showerror("Error", "Invalid values provided")
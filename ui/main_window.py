import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import threading
import time
import logging
from PIL import Image, ImageTk

from .widgets import ControlPanel
from config import CAMERA_CONFIG

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from .dialogs import (
    create_registration_dialog, show_attendance_logs,
    show_saved_faces, select_facial_features, AddCameraDialog
)
from .camera_view import CameraGridView, SingleCameraView
from tracking.tracker import FaceTracker
from attendance.logger import AttendanceLogger
from face_recognition.initializers import face_app, use_insightface, face_database
from face_recognition.recognition import recognize_face, detect_facial_features
from config import DETECTION_CONFIG
from src.utils.detection import FaceDetector
from src.utils.camera_manager import CameraManager

class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Camera Face Recognition System")
        self.root.geometry("1200x700")

        # Initialize camera manager
        self.camera_manager = CameraManager()
        
        try:
            # Add default local camera
            logger.info("Initializing default camera")
            default_camera = self.camera_manager.create_local_camera(0)
            if not self.camera_manager.add_camera("main_camera", default_camera):
                logger.error("Failed to initialize default camera")
                messagebox.showwarning("Warning",
                    "Failed to initialize default camera. Check camera connections.")

        except Exception as e:
            logger.error(f"Error initializing default camera: {str(e)}")
            messagebox.showerror("Error",
                f"Failed to initialize camera system: {str(e)}")

        # Initialize other components
        self.tracker = FaceTracker()
        self.attendance_logger = AttendanceLogger()
        self.face_detector = FaceDetector()
        
        # Setup main UI components
        self.setup_ui()
        
        # Control variables
        self.running = True
        self.current_frame = None

        # Performance tracking
        self.frame_times = []
        self.detection_times = []
        self.recognition_times = []

        # Set up cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start UI update loop with configured interval
        self.root.after(CAMERA_CONFIG.get('CAMERA_UPDATE_INTERVAL', 33), self.update_ui)

    def setup_ui(self):
        """Setup the main UI layout"""
        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add grid view tab
        self.grid_view = CameraGridView(self.notebook, self.camera_manager)
        self.notebook.add(self.grid_view, text="Grid View")

        # Add individual camera tabs
        self.camera_tabs = {}
        for camera_id, camera in self.camera_manager.cameras.items():
            tab = SingleCameraView(self.notebook, self.camera_manager, camera_id)
            self.notebook.add(tab, text=camera.name)
            self.camera_tabs[camera_id] = tab

        # Control panel with callbacks
        callbacks = {
            'register': lambda: create_registration_dialog(self.root, self.current_frame, face_app),
            'view_faces': lambda: show_saved_faces(self.root),
            'view_logs': lambda: show_attendance_logs(self.root),
            'add_camera': self.show_add_camera_dialog
        }
        self.control_panel = ControlPanel(self.main_container, callbacks)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

    def process_detected_faces(self, faces, small_frame, scale, display_frame):
        """Process detected faces and update UI"""
        recognized_names = []
        feature_options = self.control_panel.get_feature_detection_options()
        faces_list = []  # Collect all faces with recognition info
        
        for face in faces:
            bbox = face.bbox.astype(int)
            x, y, x2, y2 = bbox
            w, h = x2 - x, y2 - y
            
            # Debug print for coordinates
            print("\nFace Detection Debug:")
            print(f"Original bbox: x={x}, y={y}, x2={x2}, y2={y2}")
            print(f"Width={w}, Height={h}")

            # Filter by size
            if not (DETECTION_CONFIG['min_face_size'] <= w <= DETECTION_CONFIG['max_face_size'] and
                    DETECTION_CONFIG['min_face_size'] <= h <= DETECTION_CONFIG['max_face_size']):
                continue

            # Scale back to original coordinates
            orig_bbox = self.tracker.process_detected_face(face, scale)
            if not orig_bbox:
                continue

            # Recognize face
            name = "Unknown"
            confidence = 0.0

            if hasattr(face, 'embedding') and face.embedding is not None:
                rec_start = time.time()
                name, confidence = recognize_face(face.embedding)
                self.recognition_times.append(time.time() - rec_start)
                if name != "Unknown":
                    recognized_names.append(name)

            # Scale coordinates back to display frame size
            x_display = int(x / scale)
            y_display = int(y / scale)
            w_display = int(w / scale)
            h_display = int(h / scale)
            
            # Debug print for scaled coordinates
            print(f"Scaled coordinates: x={x_display}, y={y_display}, w={w_display}, h={h_display}")
            
            # Add face info to list
            faces_list.append(((x_display, y_display, w_display, h_display), name, confidence))
        
        # Draw all faces at once
        if faces_list:
            display_frame = self.face_detector.draw_faces(display_frame, faces_list, show_landmarks=False)

            # Draw facial features if enabled
            if face.det_score > 0.5:
                color_map = {
                    "green": (0, 255, 0),
                    "red": (0, 0, 255),
                    "blue": (255, 0, 0),
                    "yellow": (0, 255, 255)
                }
                feature_color = color_map.get(feature_options['color'], (0, 255, 0))

                # Detect and draw facial features
                eyes, mouth = detect_facial_features(face)

                if eyes and feature_options['detect_eyes']:
                    for eye in eyes:
                        ex, ey, ew, eh = [int(v/scale) for v in eye]
                        cv2.rectangle(display_frame, (ex, ey),
                                    (ex+ew, ey+eh), feature_color, 2)
                        cv2.putText(display_frame, "Eye", (ex, ey-5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, feature_color, 1)

                if mouth and feature_options['detect_mouth']:
                    mx, my, mw, mh = [int(v/scale) for v in mouth]
                    cv2.rectangle(display_frame, (mx, my),
                                (mx+mw, my+mh), feature_color, 2)
                    cv2.putText(display_frame, "Mouth", (mx, my-5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, feature_color, 1)

        return recognized_names

    def update_ui(self):
        """Update UI components"""
        if not self.running:
            return

        try:
            start_time = time.time()
            
            # Get current frame for processing
            frame = None
            current_tab = self.notebook.select()
            current_widget = self.notebook.tab(current_tab, "text") if current_tab else None
            logger.debug(f"Current tab: {current_widget}")

            if current_widget == "Grid View":
                # Update grid view and use first camera for detection
                self.grid_view.update_frame()
                frames = self.camera_manager.get_all_frames()
                if frames:
                    frame = next(iter(frames.values()))
            else:
                # Update single camera view
                for camera_id, tab in self.camera_tabs.items():
                    if str(tab) == str(current_tab):
                        frame = self.camera_manager.get_frame(camera_id)
                        break

            # Process frame for face detection
            if frame is not None and frame.size > 0:
                try:
                    self.current_frame = frame.copy()
                    
                    # Update tracking and get processed frame
                    tracking_success, small_frame, scale, display_frame = self.tracker.update(frame)

                    # Run detection periodically or when tracking fails
                    if self.tracker.should_detect():
                        detection_start = time.time()
                        faces = []
                        recognized_names = []

                        if use_insightface:
                            # Detect faces
                            faces = face_app.get(small_frame)
                            
                            if faces:
                                # Process detected faces
                                recognized_names = self.process_detected_faces(faces, small_frame, scale, display_frame)
                                
                                # Update detection time stats
                                self.detection_times.append(time.time() - detection_start)
                                
                                if faces:
                                    try:
                                        # Initialize tracking with best face
                                        best_face = max(faces, key=lambda x: x.det_score)
                                        if self.tracker.initialize_tracking(small_frame, best_face):
                                            logger.debug("Face tracking initialized")
                                        
                                        # Update presence tracking and UI
                                        self.attendance_logger.update_presence(recognized_names)
                                        present_text, away_text = self.attendance_logger.get_presence_status()
                                        
                                        self.control_panel.update_status(
                                            f"Detection: {len(faces)} faces",
                                            len(faces),
                                            present_text,
                                            away_text
                                        )
                                        
                                        logger.debug(f"Processed {len(faces)} faces")
                                    except Exception as e:
                                        logger.error(f"Error processing detection results: {str(e)}", exc_info=True)
                                
                                # Update displays with processed frame
                                if current_widget == "Grid View":
                                    self.grid_view.update_frame(display_frame)
                                else:
                                    for tab in self.camera_tabs.values():
                                        if str(tab) == str(current_tab):
                                            tab.update_frame(display_frame)
                                            break
                            else:
                                logger.debug("No faces detected in frame")
                                # Update displays with original frame
                                if current_widget == "Grid View":
                                    self.grid_view.update_frame()
                                else:
                                    for tab in self.camera_tabs.values():
                                        if str(tab) == str(current_tab):
                                            tab.update_frame()
                                            break
                        else:
                            logger.warning("InsightFace not initialized")
                            # Update displays with original frame
                            if current_widget == "Grid View":
                                self.grid_view.update_frame()
                            else:
                                for tab in self.camera_tabs.values():
                                    if str(tab) == str(current_tab):
                                        tab.update_frame()
                                        break

                except Exception as e:
                    logger.error(f"Error processing frame: {str(e)}", exc_info=True)
            else:
                logger.debug("No valid frame available for processing")
        except Exception as e:
            logger.error(f"Error in update_ui: {str(e)}")
            messagebox.showerror("Error", f"Error updating camera view: {str(e)}")

            if frame is not None:
                self.current_frame = frame.copy()

                # Run face detection and recognition
                detection_start = time.time()
                faces = []
                recognized_names = []

                if use_insightface:
                    faces = face_app.get(frame)
                    recognized_names = self.process_detected_faces(faces, frame, 1.0, frame)

                    # Update detection time stats
                    self.detection_times.append(time.time() - detection_start)

                    # Update presence tracking and UI
                    self.attendance_logger.update_presence(recognized_names)
                    present_text, away_text = self.attendance_logger.get_presence_status()
                    
                    self.control_panel.update_status(
                        f"Detection: {len(faces)} faces",
                        len(faces),
                        present_text,
                        away_text
                    )

        # Update performance stats
        self.frame_times.append(time.time() - start_time)
        if len(self.frame_times) > 10:
            fps = 1 / np.mean(self.frame_times[-10:])
            avg_det = np.mean(self.detection_times[-10:]) * \
                1000 if self.detection_times else 0
            avg_rec = np.mean(self.recognition_times[-10:]) * \
                1000 if self.recognition_times else 0
            self.control_panel.update_stats(fps, avg_det, avg_rec)

        # Schedule next update using the configured interval
        if self.running:
            update_interval = CAMERA_CONFIG.get('CAMERA_UPDATE_INTERVAL', 33)  # ~30 FPS default
            logger.debug(f"Scheduling next update in {update_interval}ms")
            self.root.after(update_interval, self.update_ui)

    def show_add_camera_dialog(self):
        """Show dialog to add a new camera"""
        dialog = AddCameraDialog(self.root, self)
        self.root.wait_window(dialog)

    def on_closing(self):
        """Handle window closing"""
        logger.info("Application shutting down...")
        self.running = False
        
        try:
            # Clean up camera resources
            if hasattr(self, 'camera_manager'):
                self.camera_manager.cleanup()
                
            # Destroy the window
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            self.root.destroy()

    def add_camera(self, camera_type: str, **kwargs):
        """Add a new camera to the system"""
        try:
            if camera_type == "local":
                camera = self.camera_manager.create_local_camera(
                    device_id=int(kwargs.get("device_id", 0))
                )
            else:  # IP camera
                camera = self.camera_manager.create_ip_camera(
                    url=kwargs["url"],
                    protocol=kwargs.get("protocol", "http"),
                    credentials={
                        "username": kwargs.get("username"),
                        "password": kwargs.get("password")
                    } if kwargs.get("username") else None
                )

            # Generate unique camera ID
            camera_id = f"camera_{len(self.camera_manager.cameras)}"
            
            # Add to camera manager
            if self.camera_manager.add_camera(camera_id, camera):
                # Add new tab
                tab = SingleCameraView(self.notebook, self.camera_manager, camera_id)
                self.notebook.add(tab, text=camera.name)
                self.camera_tabs[camera_id] = tab
                return True
                
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to add camera: {str(e)}")
        return False

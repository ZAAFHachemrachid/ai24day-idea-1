import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from .theme import setup_theme, get_color, get_font, get_padding
from ..utils.camera_manager import CameraManager
from ..utils.performance_logger import PerformanceLogger
from ..face_recognition.initializers import face_app, use_insightface, face_database
from ..face_recognition.recognition import recognize_face
from ..tracking.tracker import FaceTracker
from ..attendance.logger import AttendanceLogger
from ..utils.detection import FaceDetector
from ..config.config import CAMERA_CONFIG, DETECTION_CONFIG
from ..utils.parallel import (
    ThreadSafeFrameBuffer,
    FaceDetectionPool,
    RecognitionPool,
    DrawingPool,
    DrawRequest
)
import time
import cv2
import numpy as np
from ..config.config import CAMERA_CONFIG
import logging
from queue import Queue
import threading

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FaceRecognitionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Setup theme
        setup_theme()
        
        # Configure window
        self.title("Multi-Camera Face Recognition System")
        self.geometry("1200x700")
        self.configure(fg_color=get_color("background"))
        
        # Initialize camera manager and other components
        self.init_components()
        
        # Setup main UI
        self.setup_ui()
        
        # Control variables
        self.running = True
        self.current_frame = None
        self._frame_counter = 0
        self._frame_lock = threading.Lock()
        self.detected_faces = set()  # Track currently detected faces
        
        # Initialize performance logger
        self.perf_logger = PerformanceLogger.instance()
        
        # Performance tracking
        self.frame_times = []
        self.detection_times = []
        self.recognition_times = []
        
        # Processing queues
        self.frame_buffer = ThreadSafeFrameBuffer()
        
        # Set up cleanup on window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start UI update loop
        self.after(CAMERA_CONFIG.get('CAMERA_UPDATE_INTERVAL', 33), self.update_ui)
    
    def init_components(self):
        """Initialize system components"""
        try:
            # Initialize camera manager
            self.camera_manager = CameraManager()
            
            # Add default local camera
            default_camera = self.camera_manager.create_local_camera(0)
            if not self.camera_manager.add_camera("main_camera", default_camera):
                self.show_error("Failed to initialize default camera. Check camera connections.")
        
        except Exception as e:
            self.show_error(f"Failed to initialize camera system: {str(e)}")
        
        # Initialize processing pools
        self.detection_pool = FaceDetectionPool()
        self.recognition_pool = RecognitionPool()
        self.drawing_pool = DrawingPool()
        
        # Initialize other components
        self.tracker = FaceTracker()
        self.attendance_logger = AttendanceLogger()
        self.face_detector = FaceDetector()
    
    def setup_ui(self):
        """Setup the main UI layout"""
        # Main container
        self.main_container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.main_container.pack(
            fill="both",
            expand=True,
            padx=get_padding("medium"),
            pady=get_padding("medium")
        )
        
        # Create notebook/tabview for camera views
        self.setup_camera_views()
        
        # Create control panel
        self.setup_control_panel()
    
    def setup_camera_views(self):
        """Setup the camera view tabs"""
        from .components.camera_view import CameraGridView, SingleCameraView

        self.tab_view = ctk.CTkTabview(
            self.main_container,
            fg_color=get_color("surface")
        )
        self.tab_view.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, get_padding("medium"))
        )
        
        # Add grid view tab
        self.tab_view.add("Grid View")
        self.grid_view = CameraGridView(self.tab_view.tab("Grid View"), self.camera_manager)
        self.grid_view.pack(fill="both", expand=True)
        
        # Add individual camera tabs
        self.camera_tabs = {}
        for camera_id, camera in self.camera_manager.cameras.items():
            tab_name = camera.name
            self.tab_view.add(tab_name)
            tab = SingleCameraView(self.tab_view.tab(tab_name), self.camera_manager, camera_id)
            tab.pack(fill="both", expand=True)
            self.camera_tabs[camera_id] = tab
    
    def setup_control_panel(self):
        """Setup the control panel"""
        from .components.control_panel import ControlPanel
        
        # Create callbacks dictionary
        callbacks = {
            'register': self.register_face,
            'view_faces': self.view_saved_faces,
            'view_logs': self.view_attendance_logs,
            'add_camera': self.show_add_camera_dialog
        }
        
        # Create control panel
        self.control_panel = ControlPanel(
            self.main_container,
            callbacks=callbacks
        )
        self.control_panel.pack(
            side="right",
            fill="y",
            padx=(0, get_padding("medium")),
            pady=get_padding("medium")
        )

    def update_ui(self):
        """Update UI components"""
        if not self.running:
            return

        try:
            start_time = time.time()
            
            # Get current frame for processing
            frame = None
            current_tab = self.tab_view.get()
            
            if current_tab == "Grid View":
                # Update grid view and use first camera for detection
                frames = self.camera_manager.get_all_frames()
                if frames:
                    frame = next(iter(frames.values()))
                    self.grid_view.update_frame()
            else:
                # Update single camera view
                for camera_id, tab in self.camera_tabs.items():
                    camera = self.camera_manager.cameras.get(camera_id)
                    if camera and camera.name == current_tab:
                        frame = self.camera_manager.get_frame(camera_id)
                        if frame is not None:
                            tab.update_frame(frame)
                        break

            # Process frame for face detection
            if frame is not None and frame.size > 0:
                try:
                    self.current_frame = frame.copy()
                    
                    # Update tracking and get processed frame
                    tracking_success, small_frame, scale, display_frame = self.tracker.update(frame)

                    # Run detection periodically or when tracking fails
                    if self.tracker.should_detect():
                        # Get next frame ID
                        with self._frame_lock:
                            frame_id = self._frame_counter
                            self._frame_counter += 1
                        
                        # Submit frame for detection
                        self.detection_pool.process_frame(small_frame)
                        
                        # Get detection results
                        detection_result = self.detection_pool.get_result()
                        if detection_result:
                            # Update detection times
                            self.detection_times.append(detection_result.processing_time)
                            
                            # Process detected faces in parallel
                            faces_info = []
                            recognized_faces = {}
                            
                            # Submit faces for recognition
                            if detection_result.faces:
                                for face_id, face in enumerate(detection_result.faces):
                                    if hasattr(face, 'embedding') and face.embedding is not None:
                                        # Get face coordinates
                                        bbox = face.bbox.astype(int)
                                        x, y, x2, y2 = bbox
                                        w, h = x2 - x, y2 - y

                                        # Filter by size
                                        if not (DETECTION_CONFIG['min_face_size'] <= w <= DETECTION_CONFIG['max_face_size'] and
                                                DETECTION_CONFIG['min_face_size'] <= h <= DETECTION_CONFIG['max_face_size']):
                                            continue

                                        # Generate consistent face ID using frame and detection IDs
                                        persistent_face_id = f"{frame_id}_{face_id}"
                                        
                                        # Submit for recognition
                                        self.recognition_pool.process_face(
                                            face.embedding,
                                            face_id,
                                            frame_id,
                                            persistent_face_id
                                        )

                                # Collect recognition results
                                while True:
                                    recognition_result = self.recognition_pool.get_result()
                                    if not recognition_result:
                                        break
                                        
                                    # Get face coordinates - use original face_id for detection lookup
                                    face = detection_result.faces[recognition_result.face_id]
                                    bbox = face.bbox.astype(int)
                                    x, y, x2, y2 = bbox
                                    w, h = x2 - x, y2 - y
                                    
                                    # Scale coordinates back to display frame size
                                    x_display = int(x / scale)
                                    y_display = int(y / scale)
                                    w_display = int(w / scale)
                                    h_display = int(h / scale)
                                    
                                    # Use the persistent ID from the recognition result
                                    persistent_face_id = recognition_result.persistent_id
                                    
                                    try:
                                        # Add face info with error checking
                                        bbox = (x_display, y_display, w_display, h_display)
                                        name = recognition_result.name if recognition_result else "Unknown"
                                        confidence = recognition_result.confidence if recognition_result else 0.0
                                        
                                        faces_info.append((
                                            bbox,
                                            name,
                                            confidence
                                        ))
                                    except Exception as e:
                                        logger.error(f"Error adding face info: {str(e)}")
                                        continue
                                    
                                    if recognition_result.name != "Unknown":
                                        # Use the persistent ID for attendance tracking
                                        recognized_faces[recognition_result.persistent_id] = recognition_result.name
                                        # Add to detected faces
                                        self.detected_faces.add(recognition_result.name)
                                        
                                    # Update recognition times
                                    self.recognition_times.append(recognition_result.processing_time)
                            
                            # Submit frame for drawing with error handling
                            try:
                                if faces_info:
                                    # Validate face info format
                                    valid_faces = []
                                    for face_info in faces_info:
                                        try:
                                            if len(face_info) == 3 and len(face_info[0]) == 4:
                                                valid_faces.append(face_info)
                                        except (IndexError, TypeError):
                                            continue
                                    
                                    if valid_faces:
                                        draw_request = DrawRequest(
                                            display_frame,
                                            frame_id,
                                            valid_faces,
                                            show_landmarks=False
                                        )
                                        self.drawing_pool.process_frame(draw_request)
                            except Exception as e:
                                logger.error(f"Error creating draw request: {str(e)}")
                            
                            # Get drawing result
                            draw_result = self.drawing_pool.get_result()
                            if draw_result:
                                display_frame = draw_result.frame
                                
                                # Update displays with processed frame
                                if current_tab == "Grid View":
                                    self.grid_view.update_frame(display_frame)
                                else:
                                    for tab in self.camera_tabs.values():
                                        if str(tab) == str(current_tab):
                                            tab.update_frame(display_frame)
                                            break
                            
                            # Update presence tracking and UI
                            self.attendance_logger.update_presence(recognized_faces)
                            present_text, away_text = self.attendance_logger.get_presence_status()
                            
                            self.control_panel.update_status(
                                f"Detection: {len(faces_info)} faces",
                                len(faces_info),
                                present_text,
                                away_text
                            )
                            
                            # Update face list with currently detected faces
                            self.control_panel.face_list.update_face_list(self.detected_faces)
                            
                            # Reset detected faces for next frame
                            self.detected_faces.clear()

                except Exception as e:
                    logger.error(f"Error processing frame: {str(e)}", exc_info=True)

            # Calculate performance metrics
            frame_time = time.time() - start_time
            self.frame_times.append(frame_time)
            
            if len(self.frame_times) > 10:
                # Calculate averages
                fps = 1 / np.mean(self.frame_times[-10:])
                avg_det = np.mean(self.detection_times[-10:]) * 1000 if self.detection_times else 0
                avg_rec = np.mean(self.recognition_times[-10:]) * 1000 if self.recognition_times else 0
                
                # Update UI
                self.control_panel.update_stats(fps, avg_det, avg_rec)
                
                # Log frame processed for FPS tracking
                self.perf_logger.log_frame_processed()
                
                # Clear old metrics
                if len(self.frame_times) > 100:
                    self.frame_times = self.frame_times[-50:]
                if len(self.detection_times) > 100:
                    self.detection_times = self.detection_times[-50:]
                if len(self.recognition_times) > 100:
                    self.recognition_times = self.recognition_times[-50:]

        except Exception as e:
            logger.error(f"Error in update_ui: {str(e)}")

        # Schedule next update
        if self.running:
            self.after(CAMERA_CONFIG.get('CAMERA_UPDATE_INTERVAL', 33), self.update_ui)
    
    def register_face(self):
        """Show enhanced registration dialog with multiple poses"""
        from .components.dialogs import create_registration_dialog
        create_registration_dialog(self, self.camera_manager, face_app)
    
    def view_saved_faces(self):
        """Show saved faces dialog"""
        from .components.dialogs import show_saved_faces
        show_saved_faces(self)
    
    def view_attendance_logs(self):
        """Show attendance logs dialog"""
        from .components.dialogs import show_attendance_logs
        show_attendance_logs(self)
    
    def show_add_camera_dialog(self):
        """Show dialog to add a new camera"""
        from .components.dialogs import AddCameraDialog
        dialog = AddCameraDialog(self)
        self.wait_window(dialog)
    
    def add_camera(self, camera_type: str, **kwargs):
        """Add a new camera to the system"""
        try:
            # Create camera instance
            if camera_type == "local":
                camera = self.camera_manager.create_local_camera(kwargs['device_id'])
            else:
                # Create credentials dict if username/password provided
                credentials = None
                if kwargs.get('username') or kwargs.get('password'):
                    credentials = {
                        'username': kwargs.get('username'),
                        'password': kwargs.get('password')
                    }
                
                # Ensure URL has video endpoint for IP cameras
                url = kwargs['url']
                if not url.endswith('/video'):
                    url = f"{url.rstrip('/')}/video"
                logger.debug(f"Using camera URL: {url}")
                
                camera = self.camera_manager.create_ip_camera(
                    url,
                    protocol='http',
                    credentials=credentials
                )
            
            # Generate unique camera ID
            camera_id = f"camera_{len(self.camera_manager.cameras) + 1}"
            
            # Add to camera manager
            if not self.camera_manager.add_camera(camera_id, camera):
                raise Exception("Failed to add camera to manager")
            
            # Add new tab for camera
            from .components.camera_view import SingleCameraView
            tab_name = camera.name or f"Camera {len(self.camera_tabs) + 1}"
            self.tab_view.add(tab_name)
            tab = SingleCameraView(self.tab_view.tab(tab_name), self.camera_manager, camera_id)
            tab.pack(fill="both", expand=True)
            self.camera_tabs[camera_id] = tab
            
            # Force an immediate UI update
            self.update_ui()
            logger.debug(f"Added new camera tab: {tab_name}")
            
        except Exception as e:
            raise Exception(f"Failed to add camera: {str(e)}")
    
    def show_error(self, message: str):
        """Show error dialog"""
        CTkMessagebox(
            self,
            title="Error",
            message=message,
            icon="cancel"
        )
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        
        # Shutdown performance logger
        if hasattr(self, 'perf_logger'):
            self.perf_logger.shutdown()
        
        try:
            # Shutdown processing pools
            if hasattr(self, 'detection_pool'):
                self.detection_pool.shutdown()
            if hasattr(self, 'recognition_pool'):
                self.recognition_pool.shutdown()
            if hasattr(self, 'drawing_pool'):
                self.drawing_pool.shutdown()
                
            # Clean up camera resources
            if hasattr(self, 'camera_manager'):
                self.camera_manager.cleanup()
            
            # Clear frame buffer
            if hasattr(self, 'frame_buffer'):
                self.frame_buffer.clear()
            
            # Destroy window
            self.destroy()
            
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            self.destroy()

def main():
    """Run the application"""
    app = FaceRecognitionApp()
    app.mainloop()

if __name__ == "__main__":
    main()
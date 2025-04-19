import cv2
import time
from typing import Callable, Optional
from datetime import datetime

class CameraControls:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.last_capture_time = 0
        self.capture_cooldown = 1.0  # Cooldown in seconds between captures
        self.on_capture_callback: Optional[Callable] = None
        self.on_status_change: Optional[Callable] = None
        self.preview_window_name = "Camera Preview"

    def start(self, device_id: int = 0) -> bool:
        """Start the camera capture"""
        try:
            self.cap = cv2.VideoCapture(device_id)
            if not self.cap.isOpened():
                self._update_status("Failed to open camera")
                return False
                
            self.is_running = True
            self._update_status("Camera started")
            return True
            
        except Exception as e:
            self._update_status(f"Camera error: {str(e)}")
            return False

    def stop(self):
        """Stop the camera capture"""
        if self.cap:
            self.is_running = False
            self.cap.release()
            cv2.destroyAllWindows()
            self._update_status("Camera stopped")

    def read_frame(self):
        """Read a frame from the camera"""
        if not self.is_running or not self.cap:
            return None

        ret, frame = self.cap.read()
        return frame if ret else None

    def capture_photo(self) -> Optional[tuple[str, bytes]]:
        """Capture a photo when spacebar is pressed"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_capture_time < self.capture_cooldown:
            return None
            
        frame = self.read_frame()
        if frame is not None:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
            
            # Convert frame to bytes
            _, buffer = cv2.imencode('.jpg', frame)
            image_bytes = buffer.tobytes()
            
            # Update last capture time
            self.last_capture_time = current_time
            
            # Call capture callback if set
            if self.on_capture_callback:
                self.on_capture_callback(filename, image_bytes)
            
            return filename, image_bytes
            
        return None

    def handle_key(self, key: int) -> bool:
        """Handle keyboard input"""
        if key == ord(' '):  # Spacebar
            return self.capture_photo() is not None
        elif key == ord('r'):  # R key for retake
            self._update_status("Ready to retake photo")
            return True
        elif key == 27:  # ESC key
            self.stop()
            return False
        return True

    def show_preview(self, frame, status_text: Optional[str] = None):
        """Show camera preview with optional status text"""
        if frame is not None:
            # Add status text if provided
            if status_text:
                cv2.putText(
                    frame,
                    status_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
            
            # Show the frame
            cv2.imshow(self.preview_window_name, frame)

    def set_capture_callback(self, callback: Callable):
        """Set callback for when a photo is captured"""
        self.on_capture_callback = callback

    def set_status_callback(self, callback: Callable):
        """Set callback for status updates"""
        self.on_status_change = callback

    def _update_status(self, status: str):
        """Update camera status"""
        if self.on_status_change:
            self.on_status_change(status)
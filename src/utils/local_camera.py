import cv2
import numpy as np
from typing import Optional
import logging
from .camera_source import CameraSource
from src.config import CAMERA_CONFIG

# Configure logging
logger = logging.getLogger(__name__)

class LocalCamera(CameraSource):
    def __init__(self, device_id: int = 0):
        super().__init__()
        self.device_id = device_id
        self.cap = None
        self.name = f"Local Camera {device_id}"
        self.reconnect_attempts = 3
        self.current_attempt = 0
        
        # Set default configuration
        self.frame_width = CAMERA_CONFIG['default']['width']
        self.frame_height = CAMERA_CONFIG['default']['height']
        self.fps = CAMERA_CONFIG['default']['fps']

    def start(self) -> bool:
        """Start the local camera capture"""
        fallback_resolutions = [
            (640, 480),  # VGA
            (800, 600),  # SVGA
            (320, 240),  # QVGA
            (1280, 720), # HD
            (960, 540)   # qHD
        ]
        
        try:
            logger.debug(f"Initializing camera device {self.device_id}")
            self.cap = cv2.VideoCapture(self.device_id)
            
            if not self.cap.isOpened():
                error_msg = "Failed to open camera"
                logger.error(error_msg)
                self._update_error(error_msg)
                return False
            
            # Try to set requested resolution first
            logger.debug(f"Attempting requested settings: {self.frame_width}x{self.frame_height} @ {self.fps}fps")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, CAMERA_CONFIG['default']['buffer_size'])
            
            # Verify if requested settings were applied
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            # If actual resolution doesn't match requested, try fallback resolutions
            if abs(actual_width - self.frame_width) > 1 or abs(actual_height - self.frame_height) > 1:
                logger.warning(f"Requested resolution not supported: got {actual_width}x{actual_height}")
                
                for width, height in fallback_resolutions:
                    logger.debug(f"Trying fallback resolution: {width}x{height}")
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    
                    actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    
                    if abs(actual_width - width) <= 1 and abs(actual_height - height) <= 1:
                        logger.info(f"Using fallback resolution: {width}x{height}")
                        self.frame_width = width
                        self.frame_height = height
                        break
            
            logger.debug(f"Final camera settings: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            if not self.cap.isOpened():
                error_msg = "Failed to open camera"
                logger.error(error_msg)
                self._update_error(error_msg)
                return False

            self.is_running = True
            self._update_error(None)
            logger.info(f"Successfully initialized camera {self.device_id}")
            return True

        except Exception as e:
            self._update_error(f"Camera error: {str(e)}")
            return False

    def stop(self) -> None:
        """Stop the camera capture"""
        if self.cap:
            self.is_running = False
            self.cap.release()
            self.cap = None
            self._update_error(None)

    def read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the camera"""
        if not self.is_running or not self.cap:
            logger.warning("Attempted to read frame but camera is not running")
            return None

        ret, frame = self.cap.read()
        
        if not ret or frame is None:
            logger.warning(f"Failed to read frame from camera {self.device_id}")
            self._handle_read_error()
            return None
            
        # Check frame dimensions
        if frame.shape[:2] != (self.frame_height, self.frame_width):
            logger.debug(f"Resizing frame from {frame.shape[:2]} to {self.frame_height}x{self.frame_width}")
            frame = cv2.resize(frame, (self.frame_width, self.frame_height))
            
        if frame.size == 0:
            logger.warning(f"Got empty frame from camera {self.device_id}")
            return None
            
        self.last_frame = frame
        self.current_attempt = 0  # Reset attempt counter on successful read
        return frame

    def _handle_read_error(self) -> None:
        """Handle camera read errors with reconnection attempts"""
        self.current_attempt += 1
        self._update_error(f"Failed to read frame (Attempt {self.current_attempt}/{self.reconnect_attempts})")
        
        if self.current_attempt >= self.reconnect_attempts:
            self.stop()
            return
            
        # Attempt to reconnect
        self.stop()
        self.start()

    def set_resolution(self, width: int, height: int) -> bool:
        """Resolution changes are disabled to maintain fixed size"""
        logger.warning("Camera resolution changes are disabled")
        return False

    def set_fps(self, fps: int) -> bool:
        """Set the camera frame rate"""
        if super().set_fps(fps):
            if self.cap and self.is_running:
                self.cap.set(cv2.CAP_PROP_FPS, fps)
            return True
        return False
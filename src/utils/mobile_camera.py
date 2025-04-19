import cv2
import numpy as np
from typing import Optional, Tuple, List
import logging
import time
from .camera_source import CameraSource
from config import CAMERA_CONFIG

# Configure logging
logger = logging.getLogger(__name__)

class MobileCamera(CameraSource):
    """
    Class for handling mobile devices connected via USB that appear as video devices
    """
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.cap = None
        self.name = f"Mobile Camera ({device_id})"
        self.reconnect_attempts = CAMERA_CONFIG['mobile']['reconnect_attempts']
        self.current_attempt = 0
        self.last_reconnect_time = 0
        
        # Set default configuration from mobile settings
        self.frame_width = CAMERA_CONFIG['mobile']['default_resolution']['width']
        self.frame_height = CAMERA_CONFIG['mobile']['default_resolution']['height']
        self.fps = CAMERA_CONFIG['default']['fps']
        self.buffer_size = CAMERA_CONFIG['mobile']['buffer_size']

    def start(self) -> bool:
        """Start the mobile camera capture"""
        try:
            logger.debug(f"Initializing mobile camera device {self.device_id}")
            self.cap = cv2.VideoCapture(self.device_id)
            
            if not self.cap.isOpened():
                error_msg = f"Failed to open mobile camera {self.device_id}"
                logger.error(error_msg)
                self._update_error(error_msg)
                return False
                
            # Get native resolution first
            native_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            native_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            logger.info(f"Device native resolution: {native_width}x{native_height}")
            
            # Start with native resolution
            self.frame_width = int(native_width)
            self.frame_height = int(native_height)
            
            # Configure camera settings
            self._configure_camera()
            
            self.is_running = True
            self._update_error(None)
            logger.info(f"Successfully initialized mobile camera {self.device_id}")
            return True

        except Exception as e:
            error_msg = f"Mobile camera initialization error: {str(e)}"
            logger.error(error_msg)
            self._update_error(error_msg)
            return False

    def _configure_camera(self) -> None:
        """Configure camera settings"""
        # Set buffer size to minimize latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
        
        # Try to set desired resolution if different from native
        desired_width = CAMERA_CONFIG['mobile']['default_resolution']['width']
        desired_height = CAMERA_CONFIG['mobile']['default_resolution']['height']
        
        if desired_width != self.frame_width or desired_height != self.frame_height:
            logger.debug(f"Attempting to change resolution from {self.frame_width}x{self.frame_height} "
                        f"to {desired_width}x{desired_height}")
            
            # Try setting new resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, desired_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, desired_height)
            
            # Verify if change was successful
            new_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            new_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            if abs(new_width - desired_width) <= 1 and abs(new_height - desired_height) <= 1:
                logger.info(f"Successfully changed resolution to {desired_width}x{desired_height}")
                self.frame_width = desired_width
                self.frame_height = desired_height
            else:
                logger.warning(f"Failed to change resolution, keeping native: {self.frame_width}x{self.frame_height}")
        
        # Set FPS
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        logger.info(f"Camera running at {actual_fps} FPS")

    def _verify_camera_settings(self) -> bool:
        """Verify final camera settings"""
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        if abs(actual_width - self.frame_width) > 1 or abs(actual_height - self.frame_height) > 1:
            logger.warning(f"Camera reports different resolution than set: "
                         f"expected {self.frame_width}x{self.frame_height}, "
                         f"got {actual_width}x{actual_height}")
            # Update our stored dimensions to match reality
            self.frame_width = int(actual_width)
            self.frame_height = int(actual_height)
            
        logger.info(f"Camera configured with resolution: {self.frame_width}x{self.frame_height}")
        return True

    def read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the mobile camera"""
        if not self.is_running or not self.cap:
            return None

        ret, frame = self.cap.read()
        
        if not ret or frame is None:
            logger.warning(f"Failed to read frame from mobile camera {self.device_id}")
            self._handle_read_error()
            return None
            
        # Ensure frame has correct dimensions
        if frame.shape[:2] != (self.frame_height, self.frame_width):
            frame = cv2.resize(frame, (self.frame_width, self.frame_height))
            
        if frame.size == 0:
            logger.warning(f"Got empty frame from mobile camera {self.device_id}")
            return None
            
        self.last_frame = frame
        self.current_attempt = 0  # Reset attempt counter on successful read
        return frame

    def _handle_read_error(self) -> None:
        """Handle mobile camera read errors with reconnection attempts"""
        current_time = time.time()
        
        # Check if enough time has passed since last reconnect attempt
        if current_time - self.last_reconnect_time < CAMERA_CONFIG['mobile']['reconnect_timeout']:
            return
            
        self.current_attempt += 1
        self.last_reconnect_time = current_time
        
        self._update_error(f"Failed to read frame (Attempt {self.current_attempt}/{self.reconnect_attempts})")
        
        if self.current_attempt >= self.reconnect_attempts:
            logger.error(f"Mobile camera {self.device_id} failed after {self.reconnect_attempts} attempts")
            self.stop()
            return
            
        # Attempt to reconnect
        logger.info(f"Attempting to reconnect to mobile camera {self.device_id}")
        self.stop()
        self.start()

    def stop(self) -> None:
        """Stop the mobile camera capture"""
        if self.cap:
            self.is_running = False
            self.cap.release()
            self.cap = None
            self._update_error(None)
            logger.info(f"Stopped mobile camera {self.device_id}")

    def get_status(self) -> dict:
        """Get the current status of the mobile camera"""
        status = super().get_status()
        status.update({
            'device_id': self.device_id,
            'resolution': f"{self.frame_width}x{self.frame_height}",
            'reconnect_attempts': f"{self.current_attempt}/{self.reconnect_attempts}"
        })
        return status

    def __del__(self):
        """Cleanup when the camera object is destroyed"""
        self.stop()
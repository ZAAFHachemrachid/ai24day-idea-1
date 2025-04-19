import cv2
import numpy as np
import requests
import logging
from typing import Optional, Dict
from urllib.parse import urlparse
from .camera_source import CameraSource

# Configure logging
logger = logging.getLogger(__name__)

class IPCamera(CameraSource):
    def __init__(self, url: str, protocol: str = "http", credentials: Optional[Dict] = None):
        super().__init__()
        self.url = url
        self.protocol = protocol.lower()
        self.credentials = credentials or {}
        self.cap = None
        self.name = f"IP Camera ({urlparse(url).netloc})"
        self.reconnect_attempts = 3
        self.current_attempt = 0
        self.connection_timeout = 10.0

    def start(self) -> bool:
        """Start the IP camera stream"""
        try:
            if self.protocol == "rtsp":
                return self._start_rtsp()
            else:
                return self._start_http()

        except Exception as e:
            self._update_error(f"Camera error: {str(e)}")
            return False

    def _start_rtsp(self) -> bool:
        """Start RTSP stream"""
        try:
            # Build RTSP URL with credentials if provided
            url = self.url
            if self.credentials:
                parsed = urlparse(self.url)
                url = f"{parsed.scheme}://{self.credentials.get('username', '')}:{self.credentials.get('password', '')}@{parsed.netloc}{parsed.path}"

            # Configure OpenCV capture with RTSP settings
            self.cap = cv2.VideoCapture(url)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            
            # Set default resolution to something reasonable
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            logger.debug("Set camera resolution to 640x480")
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            
            if not self.cap.isOpened():
                self._update_error("Failed to open RTSP stream")
                return False

            self.is_running = True
            self._update_error(None)
            return True

        except Exception as e:
            self._update_error(f"RTSP error: {str(e)}")
            return False

    def _start_http(self) -> bool:
        """Start HTTP stream"""
        try:
            # Test connection first
            auth = None
            if self.credentials:
                auth = (self.credentials.get('username', ''), 
                       self.credentials.get('password', ''))
            
            response = requests.get(self.url, 
                                  auth=auth, 
                                  timeout=self.connection_timeout,
                                  stream=True)
            
            if response.status_code != 200:
                self._update_error(f"HTTP error: {response.status_code}")
                return False

            # Configure OpenCV capture for HTTP stream
            # Try MJPEG stream URL first
            mjpeg_url = f"{self.url}/video" if not self.url.endswith('/video') else self.url
            self.cap = cv2.VideoCapture(mjpeg_url)
            
            if not self.cap.isOpened():
                # Fall back to default URL
                self.cap = cv2.VideoCapture(self.url)
            
            if not self.cap.isOpened():
                self._update_error("Failed to open HTTP stream")
                return False

            self.is_running = True
            self._update_error(None)
            return True

        except requests.RequestException as e:
            self._update_error(f"HTTP connection error: {str(e)}")
            return False
        except Exception as e:
            self._update_error(f"HTTP error: {str(e)}")
            return False

    def stop(self) -> None:
        """Stop the camera stream"""
        if self.cap:
            self.is_running = False
            self.cap.release()
            self.cap = None
            self._update_error(None)

    def read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the camera stream"""
        if not self.is_running or not self.cap:
            logger.warning("Camera is not running or capture is not initialized")
            return None

        ret, frame = self.cap.read()
        if ret and frame is not None and frame.size > 0:
            h, w = frame.shape[:2]
            if w > 1920 or h > 1080:  # Limit frame size to Full HD
                scale = min(1920/w, 1080/h)
                new_size = (int(w * scale), int(h * scale))
                frame = cv2.resize(frame, new_size)
            logger.debug(f"Successfully read frame with shape: {frame.shape}")
        
        if not ret:
            self._handle_read_error()
            return None
            
        self.last_frame = frame
        self.current_attempt = 0  # Reset attempt counter on successful read
        return frame

    def _handle_read_error(self) -> None:
        """Handle stream read errors with reconnection attempts"""
        self.current_attempt += 1
        self._update_error(f"Failed to read frame (Attempt {self.current_attempt}/{self.reconnect_attempts})")
        
        if self.current_attempt >= self.reconnect_attempts:
            self.stop()
            return
            
        # Attempt to reconnect
        self.stop()
        self.start()

    def set_protocol(self, protocol: str) -> bool:
        """Change the streaming protocol"""
        if protocol.lower() not in ["rtsp", "http"]:
            return False
            
        was_running = self.is_running
        if was_running:
            self.stop()
            
        self.protocol = protocol.lower()
        
        if was_running:
            return self.start()
        return True
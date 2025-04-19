from abc import ABC, abstractmethod
import cv2
import numpy as np
from typing import Optional, Tuple, Dict

class CameraSource(ABC):
    def __init__(self):
        self.is_running = False
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 30
        self.last_frame = None
        self.last_error = None
        self.name = "Camera"

    @abstractmethod
    def start(self) -> bool:
        """Start the camera source"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the camera source"""
        pass

    @abstractmethod
    def read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the camera source"""
        pass

    def get_status(self) -> Dict:
        """Get the current status of the camera"""
        return {
            "running": self.is_running,
            "resolution": (self.frame_width, self.frame_height),
            "fps": self.fps,
            "error": self.last_error,
            "name": self.name
        }

    def set_resolution(self, width: int, height: int) -> bool:
        """Set the camera resolution"""
        self.frame_width = width
        self.frame_height = height
        return True

    def set_fps(self, fps: int) -> bool:
        """Set the camera frame rate"""
        self.fps = fps
        return True

    def set_name(self, name: str) -> None:
        """Set the camera name"""
        self.name = name

    def _update_error(self, error: Optional[str]) -> None:
        """Update the last error message"""
        self.last_error = error
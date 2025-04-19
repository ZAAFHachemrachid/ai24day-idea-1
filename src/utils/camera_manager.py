from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from .camera_source import CameraSource
from .local_camera import LocalCamera
from .ip_camera import IPCamera

class CameraManager:
    def __init__(self):
        self.cameras: Dict[str, CameraSource] = {}
        self.camera_threads: Dict[str, threading.Thread] = {}
        self._lock = threading.Lock()
        self.frame_buffer: Dict[str, np.ndarray] = {}
        self.active = True
        
    def add_camera(self, camera_id: str, camera: CameraSource) -> bool:
        """Add a camera to the manager"""
        with self._lock:
            if camera_id in self.cameras:
                return False
                
            self.cameras[camera_id] = camera
            logger.debug(f"Attempting to start camera {camera_id}")
            if camera.start():
                # Start camera reading thread
                thread = threading.Thread(
                    target=self._camera_loop,
                    args=(camera_id,),
                    daemon=True
                )
                self.camera_threads[camera_id] = thread
                thread.start()
                logger.debug(f"Successfully started camera {camera_id} and its reading thread")
                return True
            else:
                logger.error(f"Failed to start camera {camera_id}")
                del self.cameras[camera_id]
                return False

    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera from the manager"""
        with self._lock:
            if camera_id not in self.cameras:
                return False
                
            # Stop the camera and thread
            camera = self.cameras[camera_id]
            camera.stop()
            
            # Remove from dictionaries
            del self.cameras[camera_id]
            if camera_id in self.frame_buffer:
                del self.frame_buffer[camera_id]
            if camera_id in self.camera_threads:
                del self.camera_threads[camera_id]
                
            return True

    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Get the latest frame from a specific camera"""
        with self._lock:
            frame = self.frame_buffer.get(camera_id)
            if frame is not None:
                try:
                    # Validate frame
                    if not isinstance(frame, np.ndarray) or frame.size == 0:
                        logger.warning(f"Invalid frame in buffer for camera {camera_id}")
                        return None
                    return frame.copy()  # Return a copy to prevent modification
                except Exception as e:
                    logger.error(f"Error retrieving frame for camera {camera_id}: {str(e)}")
                    return None
            return None

    def get_all_frames(self) -> Dict[str, np.ndarray]:
        """Get the latest frames from all cameras"""
        with self._lock:
            return self.frame_buffer.copy()

    def get_grid_frames(self, grid_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """Get frames arranged in a grid"""
        frames = self.get_all_frames()
        if not frames:
            return np.array([])

        # Calculate grid dimensions if not provided
        if grid_size is None:
            n = len(frames)
            cols = int(np.ceil(np.sqrt(n)))
            rows = int(np.ceil(n / cols))
        else:
            rows, cols = grid_size

        # Get frame dimensions from first frame
        sample_frame = next(iter(frames.values()))
        h, w = sample_frame.shape[:2]

        # Create grid
        grid = np.zeros((h * rows, w * cols, 3), dtype=np.uint8)
        
        for idx, frame in enumerate(frames.values()):
            i, j = divmod(idx, cols)
            if i < rows and j < cols:  # Ensure we don't exceed grid dimensions
                y, x = i * h, j * w
                # Resize frame if dimensions don't match
                if frame.shape[:2] != (h, w):
                    frame = cv2.resize(frame, (w, h))
                grid[y:y+h, x:x+w] = frame

        return grid

    def get_camera_status(self, camera_id: str) -> Optional[Dict]:
        """Get status of a specific camera"""
        with self._lock:
            camera = self.cameras.get(camera_id)
            return camera.get_status() if camera else None

    def get_all_camera_status(self) -> Dict[str, Dict]:
        """Get status of all cameras"""
        with self._lock:
            return {
                camera_id: camera.get_status()
                for camera_id, camera in self.cameras.items()
            }

    def _camera_loop(self, camera_id: str) -> None:
        """Background thread for reading camera frames"""
        camera = self.cameras.get(camera_id)
        if not camera:
            return

        logger.debug(f"Starting camera loop for {camera_id}")
        frame_count = 0
        while self.active and camera_id in self.cameras:
            try:
                frame = camera.read_frame()
                if frame is not None and isinstance(frame, np.ndarray) and frame.size > 0:
                    with self._lock:
                        self.frame_buffer[camera_id] = frame.copy()
                    frame_count += 1
                    if frame_count % 30 == 0:  # Log every 30 frames
                        logger.debug(f"Camera {camera_id} processed {frame_count} frames")
                else:
                    logger.warning(f"Invalid frame received from camera {camera_id}")
                    continue
            except Exception as e:
                logger.error(f"Error reading frame from camera {camera_id}: {str(e)}")
                time.sleep(0.1)  # Prevent tight loop on errors

    def stop_all(self) -> None:
        """Stop all cameras and threads"""
        logger.info("Stopping all cameras...")
        self.active = False
        
        with self._lock:
            for camera_id in list(self.cameras.keys()):
                try:
                    logger.debug(f"Stopping camera {camera_id}")
                    self.remove_camera(camera_id)
                except Exception as e:
                    logger.error(f"Error stopping camera {camera_id}: {str(e)}")

    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up camera manager resources")
        try:
            self.stop_all()
            
            # Clear all buffers
            with self._lock:
                self.frame_buffer.clear()
                self.cameras.clear()
                self.camera_threads.clear()
            
            logger.info("Camera manager cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Cleanup when the manager is destroyed"""
        self.cleanup()

    @staticmethod
    def create_local_camera(device_id: int = 0) -> LocalCamera:
        """Factory method to create a local camera"""
        return LocalCamera(device_id)

    @staticmethod
    def create_ip_camera(url: str, protocol: str = "http", 
                        credentials: Optional[Dict] = None) -> IPCamera:
        """Factory method to create an IP camera"""
        return IPCamera(url, protocol, credentials)
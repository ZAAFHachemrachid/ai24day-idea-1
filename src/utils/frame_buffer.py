"""
Implements a thread-safe circular frame buffer for smooth frame processing and display.
"""

import threading
import numpy as np
from collections import deque
from typing import Optional, Tuple
import time
import logging

logger = logging.getLogger(__name__)

class CircularFrameBuffer:
    def __init__(self, buffer_size: int = 3):
        """Initialize the circular frame buffer.
        
        Args:
            buffer_size: Number of frames to buffer (default: 3 for triple buffering)
        """
        self.buffer_size = max(2, buffer_size)  # Minimum 2 for double buffering
        self.frames = deque(maxlen=self.buffer_size)
        self.lock = threading.Lock()
        self.frame_ready = threading.Event()
        self.last_frame_time = 0
        self.frame_interval = 1.0 / 30  # Default to 30 FPS
        
    def push_frame(self, frame: np.ndarray) -> bool:
        """Push a new frame to the buffer.
        
        Args:
            frame: The frame to add to the buffer
            
        Returns:
            bool: True if frame was added, False if buffer is full
        """
        if frame is None or frame.size == 0:
            return False
            
        with self.lock:
            # Maintain frame timing
            current_time = time.time()
            time_since_last = current_time - self.last_frame_time
            
            # Skip frame if we're pushing too fast
            if time_since_last < self.frame_interval:
                return False
                
            # Add frame to buffer
            try:
                self.frames.append(frame.copy())
                self.last_frame_time = current_time
                self.frame_ready.set()
                return True
            except Exception as e:
                logger.error(f"Error pushing frame to buffer: {str(e)}")
                return False
                
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the next frame from the buffer.
        
        Returns:
            The next frame or None if buffer is empty
        """
        with self.lock:
            if not self.frames:
                return None
            try:
                return self.frames[0].copy()
            except Exception as e:
                logger.error(f"Error getting frame from buffer: {str(e)}")
                return None
                
    def peek_frame(self) -> Optional[np.ndarray]:
        """Peek at the next frame without removing it.
        
        Returns:
            The next frame or None if buffer is empty
        """
        with self.lock:
            if not self.frames:
                return None
            try:
                return self.frames[0].copy()
            except Exception as e:
                logger.error(f"Error peeking frame: {str(e)}")
                return None
                
    def pop_frame(self) -> Optional[np.ndarray]:
        """Remove and return the next frame.
        
        Returns:
            The next frame or None if buffer is empty
        """
        with self.lock:
            if not self.frames:
                return None
            try:
                return self.frames.popleft()
            except Exception as e:
                logger.error(f"Error popping frame: {str(e)}")
                return None
                
    def clear(self):
        """Clear all frames from the buffer."""
        with self.lock:
            self.frames.clear()
            self.frame_ready.clear()
            
    def is_empty(self) -> bool:
        """Check if buffer is empty.
        
        Returns:
            True if empty, False otherwise
        """
        with self.lock:
            return len(self.frames) == 0
            
    def is_full(self) -> bool:
        """Check if buffer is full.
        
        Returns:
            True if full, False otherwise
        """
        with self.lock:
            return len(self.frames) >= self.buffer_size
            
    def get_stats(self) -> Tuple[int, int, float]:
        """Get buffer statistics.
        
        Returns:
            Tuple containing:
            - Current number of frames
            - Buffer size
            - Current frame interval
        """
        with self.lock:
            return (len(self.frames), self.buffer_size, self.frame_interval)
            
    def set_fps(self, fps: float):
        """Set the target frame rate.
        
        Args:
            fps: Target frames per second
        """
        if fps <= 0:
            return
        self.frame_interval = 1.0 / fps
        
    def wait_for_frame(self, timeout: Optional[float] = None) -> bool:
        """Wait for a new frame to become available.
        
        Args:
            timeout: How long to wait in seconds, or None to wait forever
            
        Returns:
            True if frame available, False if timed out
        """
        return self.frame_ready.wait(timeout)
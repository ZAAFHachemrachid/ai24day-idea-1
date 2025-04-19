"""
Implements a thread-safe frame buffer for managing video frames between threads.
"""

import threading
from typing import Optional, Dict
import numpy as np
import cv2
from queue import Queue


class ThreadSafeFrameBuffer:
    """A thread-safe buffer for managing frames between capture and processing threads."""
    
    def __init__(self, max_size: int = 10):
        """Initialize the frame buffer.
        
        Args:
            max_size: Maximum number of frames to store in the buffer
        """
        self.max_size = max_size
        self._buffer = Queue(maxsize=max_size)
        self._current_frame = None
        self._lock = threading.Lock()
        
    def put_frame(self, frame: np.ndarray) -> bool:
        """Add a frame to the buffer.
        
        Args:
            frame: The frame to add
            
        Returns:
            bool: True if frame was added, False if buffer is full
        """
        if frame is None:
            return False
            
        try:
            # Make a copy to prevent modification of the original frame
            frame_copy = frame.copy()
            
            # Try to add to queue, don't block if full
            self._buffer.put(frame_copy, block=False)
            
            with self._lock:
                self._current_frame = frame_copy
                
            return True
        except:
            return False
            
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the next frame from the buffer.
        
        Returns:
            The next frame or None if buffer is empty
        """
        try:
            return self._buffer.get(block=False)
        except:
            return None
            
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame.
        
        Returns:
            The most recent frame or None if no frames available
        """
        with self._lock:
            return self._current_frame.copy() if self._current_frame is not None else None
            
    def clear(self):
        """Clear all frames from the buffer."""
        while not self._buffer.empty():
            try:
                self._buffer.get(block=False)
            except:
                pass
        
        with self._lock:
            self._current_frame = None
            
    @property
    def size(self) -> int:
        """Get current number of frames in buffer."""
        return self._buffer.qsize()
        
    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return self._buffer.empty()
        
    @property
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return self._buffer.full()
"""
Implements a thread pool for parallel face detection processing.
"""

import threading
from queue import Queue
from typing import List, Optional, Tuple, Dict
import numpy as np
import cv2
from face_recognition.initializers import face_app
import logging

logger = logging.getLogger(__name__)

class DetectionResult:
    """Container for face detection results."""
    
    def __init__(self, faces: List,  # List of insightface detection results
                 frame_id: int,
                 processing_time: float):
        """
        Args:
            faces: List of detected faces from insightface
            frame_id: ID of the processed frame
            processing_time: Time taken to process the frame in seconds
        """
        self.faces = faces
        self.frame_id = frame_id
        self.processing_time = processing_time


class FaceDetectionPool:
    """Thread pool for parallel face detection processing."""
    
    def __init__(self, num_workers: int = 4):
        """Initialize the detection thread pool.
        
        Args:
            num_workers: Number of worker threads to create
        """
        self.num_workers = num_workers
        self.input_queue = Queue()
        self.result_queue = Queue()
        self.workers: List[threading.Thread] = []
        self.active = True
        self._frame_counter = 0
        self._lock = threading.Lock()
        
        # Start worker threads
        for _ in range(num_workers):
            worker = threading.Thread(target=self._detection_worker)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
    def process_frame(self, frame: np.ndarray) -> int:
        """Submit a frame for processing.
        
        Args:
            frame: The frame to process
            
        Returns:
            frame_id: ID assigned to this frame
        """
        if frame is None:
            return -1
            
        with self._lock:
            frame_id = self._frame_counter
            self._frame_counter += 1
            
        self.input_queue.put((frame_id, frame.copy()))
        return frame_id
        
    def get_result(self) -> Optional[DetectionResult]:
        """Get the next available detection result.
        
        Returns:
            DetectionResult object or None if no results available
        """
        try:
            return self.result_queue.get(block=False)
        except:
            return None
            
    def _detection_worker(self):
        """Worker thread function for face detection."""
        while self.active:
            try:
                # Get next frame from queue
                frame_id, frame = self.input_queue.get(timeout=1.0)
                
                try:
                    # Process frame using insightface
                    start_time = cv2.getTickCount()
                    faces = face_app.get(frame)
                    end_time = cv2.getTickCount()
                    
                    # Calculate processing time
                    processing_time = (end_time - start_time) / cv2.getTickFrequency()
                    
                    # Put results in output queue
                    result = DetectionResult(faces, frame_id, processing_time)
                    self.result_queue.put(result)
                    
                except Exception as e:
                    logger.error(f"Error in detection worker: {str(e)}")
                    continue
                    
            except:
                continue
                
    def shutdown(self):
        """Stop all worker threads."""
        self.active = False
        
        # Clear queues
        while not self.input_queue.empty():
            try:
                self.input_queue.get(block=False)
            except:
                pass
                
        while not self.result_queue.empty():
            try:
                self.result_queue.get(block=False)
            except:
                pass
                
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=1.0)
            
        self.workers.clear()
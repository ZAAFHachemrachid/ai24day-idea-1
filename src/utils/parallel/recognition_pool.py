"""
Implements a thread pool for parallel face recognition processing.
"""

import threading
from queue import Queue
from typing import List, Optional, Tuple, Dict
import numpy as np
import cv2
from ...face_recognition.recognition import recognize_face
from ...face_recognition.initializers import face_app
from ..performance_logger import PerformanceLogger


class RecognitionResult:
    """Container for face recognition results."""
    
    def __init__(self,
                 face_id: int,
                 frame_id: int,
                 persistent_id: str,
                 name: str,
                 confidence: float,
                 processing_time: float):
        """
        Args:
            face_id: ID of the face in the frame
            frame_id: ID of the processed frame
            persistent_id: Persistent ID for tracking the face
            name: Recognized name
            confidence: Recognition confidence score
            processing_time: Time taken to process in seconds
        """
        self.face_id = face_id
        self.frame_id = frame_id
        self.persistent_id = persistent_id
        self.name = name
        self.confidence = confidence
        self.processing_time = processing_time


class RecognitionPool:
    """Thread pool for parallel face recognition processing."""
    
    def __init__(self, num_workers: int = 2):
        """Initialize the recognition thread pool.
        
        Args:
            num_workers: Number of worker threads to create
        """
        self.num_workers = num_workers
        self.input_queue = Queue()
        self.result_queue = Queue()
        self.workers: List[threading.Thread] = []
        self.active = True
        
        # Start worker threads
        for _ in range(num_workers):
            worker = threading.Thread(target=self._recognition_worker)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
    def process_face(self,
                    face_embedding: np.ndarray,
                    face_id: int,
                    frame_id: int,
                    persistent_id: str):
        """Submit a face embedding for recognition.
        
        Args:
            face_embedding: The face embedding vector to process
            face_id: ID of the face in the frame
            frame_id: ID of the frame this face is from
            persistent_id: Persistent ID for tracking the face
        """
        if face_embedding is None:
            return
            
        self.input_queue.put((face_embedding, face_id, frame_id, persistent_id))
        
    def get_result(self) -> Optional[RecognitionResult]:
        """Get the next available recognition result.
        
        Returns:
            RecognitionResult object or None if no results available
        """
        try:
            return self.result_queue.get(block=False)
        except:
            return None
            
    def _recognition_worker(self):
        """Worker thread function for face recognition."""
        while self.active:
            try:
                # Get next face from queue
                face_embedding, face_id, frame_id, persistent_id = self.input_queue.get(timeout=1.0)
                
                # Process face
                start_time = cv2.getTickCount()
                name, confidence = recognize_face(face_embedding)
                end_time = cv2.getTickCount()
                
                # Calculate processing time
                processing_time = (end_time - start_time) / cv2.getTickFrequency()
                
                # Log performance metrics
                perf_logger = PerformanceLogger.instance()
                perf_logger.log_recognition_time(processing_time)
                
                # Put results in output queue
                result = RecognitionResult(
                    face_id,
                    frame_id,
                    persistent_id,
                    name,
                    confidence,
                    processing_time
                )
                self.result_queue.put(result)
                
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
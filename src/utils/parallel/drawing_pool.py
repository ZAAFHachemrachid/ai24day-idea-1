"""
Implements a thread pool for parallel frame drawing operations.
"""

import threading
from queue import Queue
from typing import List, Optional, Tuple, Dict
import numpy as np
import cv2
from src.utils.detection import FaceDetector
import logging

logger = logging.getLogger(__name__)

class DrawRequest:
    """Container for drawing request data."""
    
    def __init__(self,
                 frame: np.ndarray,
                 frame_id: int,
                 faces_info: List[Tuple[Tuple[int, int, int, int], str, float]],
                 show_landmarks: bool = True):
        """
        Args:
            frame: Frame to draw on
            frame_id: ID of the frame
            faces_info: List of tuples ((x,y,w,h), name, confidence)
            show_landmarks: Whether to show facial landmarks
        """
        self.frame = frame
        self.frame_id = frame_id
        self.faces_info = faces_info
        self.show_landmarks = show_landmarks


class DrawResult:
    """Container for drawing results."""
    
    def __init__(self,
                 frame: np.ndarray,
                 frame_id: int,
                 processing_time: float):
        """
        Args:
            frame: Processed frame with drawings
            frame_id: ID of the processed frame
            processing_time: Time taken for drawing operations
        """
        self.frame = frame
        self.frame_id = frame_id
        self.processing_time = processing_time


class DrawingPool:
    """Thread pool for parallel drawing operations."""
    
    def __init__(self, num_workers: int = 1):
        """Initialize the drawing thread pool.
        
        Args:
            num_workers: Number of worker threads to create
        """
        self.num_workers = num_workers
        self.input_queue = Queue()
        self.result_queue = Queue()
        self.workers: List[threading.Thread] = []
        self.active = True
        
        # Create face detector instance for drawing
        self.face_detector = FaceDetector()
        
        # Start worker threads
        for _ in range(num_workers):
            worker = threading.Thread(target=self._drawing_worker)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
    def process_frame(self, request: DrawRequest):
        """Submit a frame for drawing operations.
        
        Args:
            request: DrawRequest object containing frame and drawing data
        """
        if request is None or request.frame is None or request.frame.size == 0:
            logger.warning("Invalid drawing request received")
            return

        try:
            # Validate frame and faces info
            if not isinstance(request.frame, np.ndarray):
                logger.warning("Invalid frame type in drawing request")
                return
                
            if not request.faces_info or not isinstance(request.faces_info, list):
                logger.warning("Invalid faces info in drawing request")
                return
                
            self.input_queue.put(request)
        except Exception as e:
            logger.error(f"Error processing drawing request: {str(e)}")
        
    def get_result(self) -> Optional[DrawResult]:
        """Get the next available drawing result.
        
        Returns:
            DrawResult object or None if no results available
        """
        try:
            return self.result_queue.get(block=False)
        except:
            return None
            
    def _drawing_worker(self):
        """Worker thread function for drawing operations."""
        while self.active:
            try:
                # Get next request from queue
                request = self.input_queue.get(timeout=1.0)
                
                # Process drawing
                start_time = cv2.getTickCount()
                
                try:
                    # Validate frame before copying
                    if request.frame is None or request.frame.size == 0:
                        logger.warning("Invalid frame in drawing request")
                        continue

                    # Make a copy of the frame for drawing
                    frame = request.frame.copy()
                    
                    # Draw faces and information
                    frame = self.face_detector.draw_faces(
                        frame,
                        request.faces_info,
                        show_landmarks=request.show_landmarks
                    )

                    if frame is None:
                        logger.warning("Drawing operation returned None frame")
                        continue

                except Exception as e:
                    logger.error(f"Error during drawing operation: {str(e)}")
                    continue
                
                end_time = cv2.getTickCount()
                
                # Calculate processing time
                processing_time = (end_time - start_time) / cv2.getTickFrequency()
                
                # Put results in output queue
                result = DrawResult(
                    frame,
                    request.frame_id,
                    processing_time
                )
                self.result_queue.put(result)
                
            except Exception as e:
                logger.error(f"Error in drawing worker: {str(e)}")
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
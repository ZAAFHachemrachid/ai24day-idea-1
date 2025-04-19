import cv2
import numpy as np
from src.utils.utils import create_tracker, preprocess_frame
from src.config import DETECTION_CONFIG

class FaceTracker:
    def __init__(self):
        self.tracker = create_tracker() if DETECTION_CONFIG['enable_tracking'] else None
        self.tracking_initialized = False
        self.tracking_box = None
        self.tracked_faces = {}
        self.last_detected_boxes = []
        self.frame_count = 0

    def reset_tracker(self):
        """Reset the tracker instance"""
        self.tracker = create_tracker()
        self.tracking_initialized = False
        self.tracking_box = None

    def update(self, frame):
        """Update tracking with current frame"""
        self.frame_count += 1
        small_frame, scale = preprocess_frame(frame, DETECTION_CONFIG['processing_width'])
        display_frame = frame.copy()

        # Tracking update
        tracking_success = False
        if self.tracking_initialized and self.tracker:
            tracking_success, tracking_box = self.tracker.update(small_frame)
            if tracking_success:
                # Scale box back to original size
                x, y, w, h = [int(v/scale) for v in tracking_box]
                cv2.rectangle(display_frame, (x, y),
                              (x+w, y+h), (0, 255, 255), 2)
                cv2.putText(display_frame, "Tracking", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        return tracking_success, small_frame, scale, display_frame

    def initialize_tracking(self, small_frame, face):
        """Initialize tracking with detected face"""
        if not self.tracker:
            return False

        bbox = face.bbox.astype(int)
        x, y, x2, y2 = bbox
        w, h = x2 - x, y2 - y

        # Reinitialize tracker
        self.reset_tracker()
        if self.tracker:
            self.tracker.init(small_frame, (x, y, w, h))
            self.tracking_initialized = True
            return True
        return False

    def should_detect(self):
        """Determine if face detection should run on current frame"""
        return (self.frame_count % DETECTION_CONFIG['detection_interval'] == 0 or
                not self.tracking_initialized)

    def process_detected_face(self, face, scale):
        """Process a detected face and update tracking data"""
        bbox = face.bbox.astype(int)
        x, y, x2, y2 = bbox
        w, h = x2 - x, y2 - y

        # Filter by size
        if not (DETECTION_CONFIG['min_face_size'] <= w <= DETECTION_CONFIG['max_face_size'] and
                DETECTION_CONFIG['min_face_size'] <= h <= DETECTION_CONFIG['max_face_size']):
            return None

        # Scale back to original coordinates
        orig_bbox = [int(v/scale) for v in [x, y, w, h]]
        face_id = f"{x}_{y}_{w}_{h}"
        
        face_data = {
            'bbox': orig_bbox,
            'last_seen': self.frame_count
        }
        self.tracked_faces[face_id] = face_data
        
        return orig_bbox

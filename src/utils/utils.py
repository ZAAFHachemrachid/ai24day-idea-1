import cv2
import numpy as np

def create_tracker():
    """Create and return an OpenCV tracker"""
    try:
        if int(cv2.__version__.split('.')[0]) >= 4:
            try:
                return cv2.TrackerKCF_create()
            except:
                return cv2.legacy.TrackerKCF_create()
        else:
            return cv2.Tracker_create('KCF')
    except:
        return None

def preprocess_frame(frame, target_width):
    """Optimized frame preprocessing"""
    try:
        # Check frame validity
        if frame is None or frame.size == 0:
            raise ValueError("Invalid frame")

        # Ensure frame is in BGR format (OpenCV default)
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        elif frame.shape[2] == 1:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # Downsample for faster processing while maintaining aspect ratio
        height, width = frame.shape[:2]
        scale = target_width / width
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)

        # Convert to RGB for InsightFace
        small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Ensure proper data type and range
        if small_frame.dtype != np.uint8:
            small_frame = small_frame.astype(np.uint8)

        return small_frame, scale

    except Exception as e:
        print(f"Error preprocessing frame: {str(e)}")
        return None, 1.0

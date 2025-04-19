import numpy as np

class DistanceTracker:
    def __init__(self, known_face_width=15.0, smoothing_window=5):
        """
        Initialize the distance tracker
        
        Args:
            known_face_width (float): Average human face width in cm (default 15cm)
            smoothing_window (int): Number of frames to use for smoothing
        """
        self.known_face_width = known_face_width  # cm
        self.smoothing_window = smoothing_window
        self.distance_history = {}
        self.focal_length = None
        self.correction_factor = 1/1.7  # Correction factor based on real-world testing
    
    def calibrate_focal_length(self, known_distance, face_width_pixels, frame_width):
        """
        Calibrate focal length using a known distance and face width
        
        Args:
            known_distance (float): Known distance from camera in cm
            face_width_pixels (int): Width of face in pixels
            frame_width (int): Width of frame in pixels
        """
        # Using the formula: focal_length = (face_width_pixels * known_distance) / known_face_width
        self.focal_length = (face_width_pixels * known_distance) / self.known_face_width
    
    def estimate_distance(self, face_width_pixels, frame_width):
        """
        Estimate distance to face using face width in pixels
        
        Args:
            face_width_pixels (int): Width of detected face in pixels
            frame_width (int): Width of frame in pixels
            
        Returns:
            float: Estimated distance in cm, or None if focal length not calibrated
        """
        if self.focal_length is None:
            # If not calibrated, use a rough estimate based on frame width
            self.focal_length = frame_width * 1.5
        
        # Calculate raw distance using the formula: distance = (known_face_width * focal_length) / face_width_pixels
        raw_distance = (self.known_face_width * self.focal_length) / face_width_pixels
        
        # Apply correction factor to get actual distance
        corrected_distance = raw_distance * self.correction_factor
        return corrected_distance
    
    def get_distance(self, face_bbox, frame_width):
        """
        Get smoothed distance for a face
        
        Args:
            face_bbox (tuple): (x, y, w, h) coordinates of face
            frame_width (int): Width of frame in pixels
            
        Returns:
            dict: Distance information including:
                - distance_cm: Distance in centimeters
                - distance_m: Distance in meters
                - smoothed: Whether the value is smoothed
        """
        x, y, w, h = face_bbox
        face_id = f"{x}_{y}_{w}_{h}"
        
        # Calculate raw distance
        raw_distance = self.estimate_distance(w, frame_width)
        
        # Update history
        if face_id not in self.distance_history:
            self.distance_history[face_id] = []
            
        history = self.distance_history[face_id]
        history.append(raw_distance)
        
        # Keep only recent history
        if len(history) > self.smoothing_window:
            history.pop(0)
            
        # Calculate smoothed distance
        smoothed_distance = np.mean(history)
        
        return {
            'distance_cm': smoothed_distance,
            'distance_m': smoothed_distance / 100.0,
            'smoothed': len(history) > 1
        }
    
    def cleanup_stale_faces(self, current_faces):
        """
        Remove distance history for faces no longer being tracked
        
        Args:
            current_faces (list): List of (x,y,w,h) tuples for current faces
        """
        current_face_ids = {f"{x}_{y}_{w}_{h}" for (x, y, w, h) in current_faces}
        stale_faces = set(self.distance_history.keys()) - current_face_ids
        
        for face_id in stale_faces:
            del self.distance_history[face_id]
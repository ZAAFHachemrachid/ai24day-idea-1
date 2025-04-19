import numpy as np

class PositionTracker:
    def __init__(self, smoothing_window=5):
        self.frame_width = None
        self.frame_center = None
        self.position_history = {}
        self.smoothing_window = smoothing_window

    def update_frame_dimensions(self, frame):
        """Update frame dimensions and center point"""
        height, width = frame.shape[:2]
        self.frame_width = width
        self.frame_center = width // 2

    def _calculate_relative_position(self, face_center_x):
        """Calculate relative position as percentage from center"""
        # Convert to percentage (-100 to +100)
        # negative is left, positive is right
        return ((face_center_x - self.frame_center) / (self.frame_width / 2)) * 100

    def get_face_position(self, face_bbox):
        """
        Determine face position relative to center
        Args:
            face_bbox: Tuple of (x, y, w, h) coordinates
        Returns:
            Dict containing position info
        """
        if self.frame_center is None:
            raise ValueError("Frame dimensions not initialized. Call update_frame_dimensions first.")

        x, y, w, h = face_bbox
        face_center_x = x + (w // 2)
        face_id = f"{x}_{y}_{w}_{h}"

        # Calculate relative position
        relative_pos = self._calculate_relative_position(face_center_x)

        # Update position history for this face
        if face_id not in self.position_history:
            self.position_history[face_id] = []
        
        history = self.position_history[face_id]
        history.append(relative_pos)
        
        # Keep only recent history
        if len(history) > self.smoothing_window:
            history.pop(0)

        # Calculate smoothed position
        smoothed_pos = np.mean(history)

        return {
            'position': 'left' if smoothed_pos < 0 else 'right',
            'relative_position': smoothed_pos,  # -100 to +100
            'distance_from_center': abs(face_center_x - self.frame_center),
            'center_x': face_center_x,
            'raw_position': relative_pos
        }

    def cleanup_stale_faces(self, current_faces):
        """Remove position history for faces no longer being tracked"""
        current_face_ids = {f"{x}_{y}_{w}_{h}" for (x, y, w, h) in current_faces}
        stale_faces = set(self.position_history.keys()) - current_face_ids
        
        for face_id in stale_faces:
            del self.position_history[face_id]
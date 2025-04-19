# Position Tracking Implementation Plan

## Overview
Add functionality to detect and display whether a user is on the left or right side of the camera frame.

## Technical Design

### 1. Position Tracker Class
Create new class in `src/utils/position_tracking.py`:

```python
class PositionTracker:
    def __init__(self):
        self.frame_width = None
        self.frame_center = None
        self.position_history = {}  # Store recent positions for smoothing

    def update_frame_dimensions(self, frame):
        # Update frame dimensions and center point
        height, width = frame.shape[:2]
        self.frame_width = width
        self.frame_center = width // 2

    def get_face_position(self, face_bbox):
        # Calculate face center and determine position
        x, y, w, h = face_bbox
        face_center_x = x + (w // 2)
        
        # Return position and distance from center
        return {
            'position': 'left' if face_center_x < self.frame_center else 'right',
            'distance_from_center': abs(face_center_x - self.frame_center),
            'center_x': face_center_x
        }
```

### 2. FaceDetector Modifications
Update `draw_faces()` method in `src/utils/detection.py`:

```python
def draw_faces(self, frame, faces, show_landmarks=True):
    # Initialize position tracker if not exists
    if not hasattr(self, 'position_tracker'):
        self.position_tracker = PositionTracker()
    
    self.position_tracker.update_frame_dimensions(frame)
    
    for (x, y, w, h) in faces:
        # Get position info
        position_info = self.position_tracker.get_face_position((x, y, w, h))
        
        # Draw face rectangle and position indicator
        color = (0, 255, 0) if user else (0, 165, 255)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        # Add position text
        position_text = f"Position: {position_info['position']}"
        cv2.putText(frame, position_text, (x, y-30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
```

## Implementation Steps

1. Create `position_tracking.py`:
   - Implement PositionTracker class
   - Add position calculation logic
   - Include smoothing for stable position detection

2. Modify `detection.py`:
   - Add position tracking integration
   - Update visualization code
   - Add position indicators

3. Testing:
   - Test with different face positions
   - Verify smooth transitions
   - Check position accuracy

## Expected Results

The system will:
- Display user position (left/right) in real-time
- Show clear visual indicators
- Maintain smooth position tracking
- Work alongside existing face detection

## Future Enhancements
- Add vertical position tracking (top/bottom)
- Implement position-based triggers
- Add distance-from-camera estimation
- Support multiple face positions simultaneously
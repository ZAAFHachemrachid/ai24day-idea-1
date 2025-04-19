# Camera-to-Person Distance Measurement

## Overview
Add functionality to estimate the distance between the camera and detected persons using face size and camera parameters.

## Technical Approach

### 1. Distance Estimation Method
1. **Face Size Method**
   - Uses the known average human face width (~15cm)
   - Compare detected face width in pixels to estimate distance
   - Formula: `distance = (known_face_width * focal_length) / face_width_pixels`
   - Apply correction factor of 1/1.7 to adjust for real-world measurements

2. **Camera Calibration**
   - Store camera parameters (focal length, sensor size)
   - Use these for more accurate measurements

### 2. Implementation Components

1. **CameraCalibration Class**
```python
class CameraCalibration:
    def __init__(self):
        self.focal_length = None  # mm
        self.sensor_width = None  # mm
        self.known_face_width = 15  # cm (average human face width)
        self.correction_factor = 1/1.7  # Empirically determined correction
```

2. **Distance Tracker Extension**
```python
class DistanceTracker:
    def calculate_distance(self, face_width_pixels, frame_width):
        # Apply correction factor to raw distance
        raw_distance = (self.known_face_width * self.focal_length) / face_width_pixels
        return raw_distance * self.correction_factor
```

### 3. UI Updates
- Add distance overlay on video feed
- Show distance in meters/feet
- Optional: Color-coded indicators for different distance ranges

## Current Status

Real-world testing showed measurements were off by a factor of ~1.7:
- At 1m actual distance: System showed 1.7m
- At 2m actual distance: System showed 3.4m

Solution: Apply a correction factor of 1/1.7 to compensate for this systematic error.

## Implementation Steps

1. Update distance calculation logic
   - Add correction factor to DistanceTracker
   - Apply correction in distance calculations
   - Verify accuracy with real-world measurements

2. Update UI as needed
   - Keep existing distance display format
   - Consider adding confidence indicators

## Expected Benefits
1. More accurate real-world distance measurements
2. Better spatial awareness
3. Improved reliability for distance-based features
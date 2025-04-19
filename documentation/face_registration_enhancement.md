# Face Registration Enhancement Plan

## Overview
Enhance face registration to capture multiple poses for better recognition accuracy:
- 5 front-facing burst shots
- 2 side profile shots
- 4 slightly tilted back shots
- 5 fully tilted back shots

## UI Components

### RegistrationDialog Class
```python
class EnhancedRegistrationDialog(BaseDialog):
    def __init__(self, parent, camera_manager, face_app):
        self.poses_captured = {
            'front': [],    # 5 shots
            'side': [],     # 2 shots
            'tilt': [],     # 4 shots
            'back': []      # 5 shots
        }
        self.current_pose = 'front'
        self.pose_requirements = {
            'front': 5,
            'side': 2,
            'tilt': 4,
            'back': 5
        }
```

### UI Layout
1. Camera Preview Panel
   - Live camera feed
   - Pose guide overlay
   - Capture progress indicator

2. Instruction Panel
   - Current pose instructions
   - Visual guide for desired pose
   - Progress indicators for each pose type

3. Control Panel
   - Capture button
   - Reset button
   - Complete button (enabled when all poses captured)

## Pose Instructions
1. Front Pose (5 shots)
   - "Look directly at camera"
   - "Keep neutral expression"
   - Progress: [○○○○○] → [●●●●●]

2. Side Profile (2 shots)
   - "Turn head 90° to right/left"
   - "Keep eyes level"
   - Progress: [○○] → [●●]

3. Slight Tilt (4 shots)
   - "Tilt head slightly back"
   - "Keep face visible"
   - Progress: [○○○○] → [●●●●]

4. Full Tilt (5 shots)
   - "Tilt head back further"
   - "Maintain facial visibility"
   - Progress: [○○○○○] → [●●●●●]

## Implementation Details

### Face Capture Process
```python
def capture_pose(self):
    # Capture frame
    frame = self.camera_manager.get_frame()
    
    # Detect face and quality check
    faces = self.face_app.get(frame)
    if self.validate_pose(faces):
        self.poses_captured[self.current_pose].append(frame)
        self.update_progress()
```

### Pose Validation
```python
def validate_pose(self, faces):
    if not faces:
        return False
        
    face = faces[0]
    if self.current_pose == 'front':
        return self.validate_front_pose(face)
    elif self.current_pose == 'side':
        return self.validate_side_pose(face)
    # etc.
```

### Database Storage
```python
class FaceEntry:
    name: str
    embeddings: {
        'front': List[np.array],
        'side': List[np.array],
        'tilt': List[np.array],
        'back': List[np.array]
    }
```

## User Flow
1. Start registration
2. Enter name
3. Follow pose sequence:
   a. Front poses (5)
   b. Side profiles (2)
   c. Slight tilt (4)
   d. Full tilt (5)
4. Review and confirm
5. Save to database

## Technical Considerations
1. Face Detection Quality
   - Ensure good lighting
   - Check face alignment
   - Validate pose angles

2. Storage Format
   - Store multiple embeddings per person
   - Optimize matching algorithm

3. Error Handling
   - Pose validation failures
   - Storage errors
   - Camera issues

## Next Steps
1. Switch to Code mode
2. Implement EnhancedRegistrationDialog
3. Update face database structure
4. Implement pose validation
5. Test registration flow

## Migration Plan
1. Create new dialog implementation
2. Update database schema
3. Test with various lighting conditions
4. Update recognition logic for multiple poses
5. Add user guidance system
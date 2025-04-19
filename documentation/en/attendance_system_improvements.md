# Attendance System Improvements Implementation Plan

## Overview

This document outlines the implementation plan for improving the attendance system with:
1. 10-second presence verification before logging attendance
2. Enhanced handling of unknown faces
3. Selection interface for unknown face registration

## 1. Presence Verification System

### New Component: PresenceVerifier
```python
class PresenceVerifier:
    def __init__(self, verification_time=10):
        self.face_timestamps = {}  # face_id -> first_seen_time
        self.verified_faces = set()
        self.verification_time = verification_time
        
    def update_face(self, face_id, current_time):
        if face_id not in self.face_timestamps:
            self.face_timestamps[face_id] = current_time
            
    def check_verification(self, face_id, current_time):
        if face_id in self.verified_faces:
            return True
            
        if face_id in self.face_timestamps:
            presence_time = current_time - self.face_timestamps[face_id]
            if presence_time >= self.verification_time:
                self.verified_faces.add(face_id)
                return True
        return False
```

### Updates to AttendanceLogger
```python
class AttendanceLogger:
    def __init__(self):
        # Existing initialization
        self.presence_verifier = PresenceVerifier()
        
    def update_presence(self, recognized_names, current_time=None):
        if current_time is None:
            current_time = datetime.now().timestamp()
            
        # Update presence verification
        for name, face_id in recognized_names.items():
            self.presence_verifier.update_face(face_id, current_time)
            if self.presence_verifier.check_verification(face_id, current_time):
                # Proceed with attendance logging
                if name not in self.people_at_desk:
                    self.people_at_desk.add(name)
                    self.log_attendance(name, "arrival")
```

## 2. Unknown Faces Management

### New Component: UnknownFacesManager
```python
class UnknownFacesManager:
    def __init__(self, max_unknowns=10):
        self.unknown_faces = {}  # face_id -> embedding
        self.face_timestamps = {}  # face_id -> first_seen_time
        self.max_unknowns = max_unknowns
        
    def add_unknown_face(self, face_id, embedding, timestamp):
        if len(self.unknown_faces) >= self.max_unknowns:
            # Remove oldest unknown face
            oldest_face = min(self.face_timestamps.items(), key=lambda x: x[1])[0]
            self.remove_face(oldest_face)
            
        self.unknown_faces[face_id] = embedding
        self.face_timestamps[face_id] = timestamp
        
    def remove_face(self, face_id):
        self.unknown_faces.pop(face_id, None)
        self.face_timestamps.pop(face_id, None)
        
    def get_unknown_faces(self):
        return list(self.unknown_faces.items())
```

### Updates to Recognition System
```python
class RecognitionPool:
    def __init__(self, num_workers=2):
        # Existing initialization
        self.unknown_faces_manager = UnknownFacesManager()
        
    def process_face(self, face_embedding, face_id, frame_id):
        # Existing processing
        if result.name == "Unknown":
            self.unknown_faces_manager.add_unknown_face(
                face_id,
                face_embedding,
                time.time()
            )
```

## 3. UI Components

### New Dialog: UnknownFacesDialog
```python
class UnknownFacesDialog(ctk.CTkToplevel):
    def __init__(self, parent, unknown_faces):
        super().__init__(parent)
        self.title("Unknown Faces Registration")
        
        self.unknown_faces = unknown_faces
        self.selected_face = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Create scrollable frame for face thumbnails
        self.faces_frame = ctk.CTkScrollableFrame(self)
        self.faces_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add face thumbnails and selection buttons
        for face_id, embedding in self.unknown_faces:
            frame = ctk.CTkFrame(self.faces_frame)
            frame.pack(fill="x", pady=5)
            
            # Add face thumbnail
            # Add selection button
            
        # Add registration controls
        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.pack(fill="x", padx=10, pady=5)
        
        self.register_button = ctk.CTkButton(
            self,
            text="Register Selected Face",
            command=self.register_face
        )
        self.register_button.pack(pady=10)
```

## Implementation Steps

1. Presence Verification:
   - Create PresenceVerifier class
   - Integrate with AttendanceLogger
   - Add presence time tracking
   - Update logging logic to respect verification period

2. Unknown Faces Management:
   - Create UnknownFacesManager class
   - Modify recognition system to track unknown faces
   - Implement face pool maintenance (adding/removing faces)
   - Add storage for face embeddings

3. UI Updates:
   - Create UnknownFacesDialog class
   - Add face thumbnail display
   - Implement face selection interface
   - Add registration controls
   - Connect to face recognition system

4. Integration:
   - Connect PresenceVerifier with recognition system
   - Hook up UnknownFacesManager with UI
   - Update main application flow
   - Add error handling and edge cases

5. Testing:
   - Test presence verification timing
   - Verify unknown faces storage and cleanup
   - Test face registration workflow
   - Validate integration points

## Notes

- The system will maintain a pool of unknown faces with their embeddings
- Only faces present for 10+ seconds will be logged
- Users can select from multiple unknown faces during registration
- Old unknown faces will be automatically cleaned up
- The UI will show presence verification progress

## Dependencies

- customtkinter
- OpenCV
- face_recognition module
- numpy
- PIL

## Migration

1. Back up existing attendance logs
2. Update database schema if needed
3. Deploy new components
4. Verify existing functionality remains intact
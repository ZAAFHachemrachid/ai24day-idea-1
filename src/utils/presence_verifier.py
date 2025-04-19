"""
Implements presence verification for the attendance system.
Tracks how long faces have been present and verifies minimum presence duration.
"""

import time
from dataclasses import dataclass
from typing import Dict, Set, Optional

@dataclass
class PresenceStatus:
    """Container for face presence status information."""
    first_seen_time: float
    is_verified: bool
    total_presence_time: float = 0.0

class PresenceVerifier:
    """Tracks and verifies face presence duration."""
    
    def __init__(self, verification_time: float = 10.0):
        """Initialize the presence verifier.
        
        Args:
            verification_time: Minimum time in seconds a face must be present
                             to be verified (default: 10 seconds)
        """
        self.verification_time = verification_time
        self._face_status: Dict[str, PresenceStatus] = {}
        
    def update_face(self, face_id: str, current_time: Optional[float] = None) -> None:
        """Update tracking for a detected face.
        
        Args:
            face_id: Unique identifier for the face
            current_time: Current timestamp (default: time.time())
        """
        if current_time is None:
            current_time = time.time()
            
        # Add new faces to tracking
        if face_id not in self._face_status:
            self._face_status[face_id] = PresenceStatus(
                first_seen_time=current_time,
                is_verified=False
            )
        
        # Update presence time for existing faces
        status = self._face_status[face_id]
        if not status.is_verified:
            status.total_presence_time = current_time - status.first_seen_time
            
            # Check if verification threshold reached
            if status.total_presence_time >= self.verification_time:
                status.is_verified = True
                
    def check_verification(self, face_id: str) -> bool:
        """Check if a face has been verified as present long enough.
        
        Args:
            face_id: Unique identifier for the face
            
        Returns:
            bool: True if face has been present for required duration
        """
        status = self._face_status.get(face_id)
        return status is not None and status.is_verified

    def get_presence_time(self, face_id: str) -> float:
        """Get how long a face has been present.
        
        Args:
            face_id: Unique identifier for the face
            
        Returns:
            float: Total time face has been present in seconds
        """
        status = self._face_status.get(face_id)
        return status.total_presence_time if status else 0.0

    def reset_verification(self, face_id: str) -> None:
        """Reset verification status for a face.
        
        Args:
            face_id: Unique identifier for the face
        """
        if face_id in self._face_status:
            status = self._face_status[face_id]
            status.is_verified = False
            status.total_presence_time = 0.0
            status.first_seen_time = time.time()

    def clear_face(self, face_id: str) -> None:
        """Remove tracking for a face.
        
        Args:
            face_id: Unique identifier for the face
        """
        self._face_status.pop(face_id, None)

    def get_all_status(self) -> Dict[str, PresenceStatus]:
        """Get presence status for all tracked faces.
        
        Returns:
            Dict mapping face IDs to their PresenceStatus
        """
        return self._face_status.copy()
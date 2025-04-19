import os
from datetime import datetime
from typing import Dict, Set, Tuple

from config import ATTENDANCE_LOG, AWAY_THRESHOLD
from src.utils.presence_verifier import PresenceVerifier

class AttendanceLogger:
    def __init__(self, verification_time: float = 10.0):
        self.people_at_desk = set()
        self.people_away = set()
        self.last_seen_times = {}
        self.face_names: Dict[str, str] = {}  # face_id -> name
        self.name_faces: Dict[str, str] = {}  # name -> face_id
        self.presence_verifier = PresenceVerifier(verification_time)
        self.initialize_log_file()

    def initialize_log_file(self):
        """Create attendance log file if not exists"""
        if not os.path.exists(ATTENDANCE_LOG):
            with open(ATTENDANCE_LOG, 'w') as f:
                f.write("Name,Date,Arrival Time,Departure Time\n")

    def log_attendance(self, name, action):
        """Log attendance event (arrival or departure)"""
        now = datetime.now()
        entry = f"{name},{now.strftime('%Y-%m-%d')},{now.strftime('%H:%M:%S')}"

        if action == "arrival":
            entry += ",\n"
        else:  # departure
            entry = ""
            with open(ATTENDANCE_LOG, 'r') as f:
                lines = f.readlines()

            found = False
            for i, line in enumerate(lines):
                if line.startswith(name) and line.strip().endswith(','):
                    entry = f"{line.strip()}{now.strftime('%H:%M:%S')}\n"
                    lines[i] = entry
                    found = True
                    break

            if not found:
                return

            with open(ATTENDANCE_LOG, 'w') as f:
                f.writelines(lines)
            return

        with open(ATTENDANCE_LOG, 'a') as f:
            f.write(entry)

    def update_presence(self, recognized_faces: Dict[str, str], current_time=None):
        """Update presence status of recognized people
        
        Args:
            recognized_faces: Dict mapping face_ids to names
            current_time: Current timestamp (default: now)
        """
        if current_time is None:
            current_time = datetime.now().timestamp()

        # Filter out unknown faces and update face->name mappings
        current_faces = {
            face_id: name
            for face_id, name in recognized_faces.items()
            if name != "Unknown"
        }
        
        # Update presence verification for all detected faces
        for face_id, name in current_faces.items():
            self.presence_verifier.update_face(face_id, current_time)
            
            # Map face_id to name if new
            if face_id not in self.face_names or self.face_names[face_id] != name:
                self.face_names[face_id] = name
                self.name_faces[name] = face_id
        
        # Check for newly verified faces
        for face_id, name in current_faces.items():
            if self.presence_verifier.check_verification(face_id):
                self.last_seen_times[name] = current_time
                if name in self.people_away:
                    self.people_away.remove(name)
                    self.people_at_desk.add(name)
                    self.log_attendance(name, "arrival")
        
        # Check for people who have been away for too long
        for name, face_id in list(self.name_faces.items()):
            if face_id not in current_faces:
                time_away = current_time - self.last_seen_times.get(name, 0)
                if time_away > AWAY_THRESHOLD and name in self.people_at_desk:
                    self.people_at_desk.remove(name)
                    self.people_away.add(name)
                    self.log_attendance(name, "departure")
                    # Reset verification when person leaves
                    self.presence_verifier.reset_verification(face_id)

    def get_presence_status(self):
        """Get lists of present and away people"""
        present_text = ", ".join(self.people_at_desk) if self.people_at_desk else "None"
        away_text = ", ".join(self.people_away) if self.people_away else "None"
        return present_text, away_text

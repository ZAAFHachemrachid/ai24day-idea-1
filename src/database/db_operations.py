from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from src.database.models import (
    User, FaceSample, Place, RecognitionEvent,
    Attendance, DeleteAuditLog, init_db
)

class DatabaseOperations:
    def __init__(self):
        self.engine = init_db()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    # User operations
    def add_user(self, name):
        """Add a new user to the database"""
        user = User(name=name)
        self.session.add(user)
        self.session.commit()
        return user

    def get_user(self, user_id):
        """Get user by ID"""
        return self.session.query(User).filter(User.id == user_id).first()

    def get_all_users(self, include_deleted: bool = True) -> List[User]:
        """
        Get all users
        
        Args:
            include_deleted: Whether to include soft-deleted users
        """
        query = self.session.query(User)
        if not include_deleted:
            query = query.filter(User.deleted_at.is_(None))
        return query.order_by(User.name).all()
    
    def get_deleted_users(self) -> List[User]:
        """Get only soft-deleted users"""
        return self.session.query(User).filter(
            User.deleted_at.isnot(None)
        ).order_by(User.deleted_at.desc()).all()

    def update_user(self, user_id, name):
        """Update user information"""
        user = self.get_user(user_id)
        if user:
            user.name = name
            self.session.commit()
        return user

    # Face Sample operations
    def add_face_sample(self, user_id, image_path):
        """Add a new face sample for a user"""
        face_sample = FaceSample(user_id=user_id, image_path=image_path)
        self.session.add(face_sample)
        self.session.commit()
        return face_sample

    def get_user_face_samples(self, user_id: int, include_deleted: bool = True) -> List[FaceSample]:
        """
        Get all face samples for a user
        
        Args:
            user_id: ID of the user
            include_deleted: Whether to include soft-deleted samples
        """
        query = self.session.query(FaceSample).filter(FaceSample.user_id == user_id)
        if not include_deleted:
            query = query.filter(FaceSample.deleted_at.is_(None))
        return query.order_by(FaceSample.created_at).all()
    
    def get_deletion_history(self, user_id: Optional[int] = None) -> List[DeleteAuditLog]:
        """
        Get deletion history for a user or all users
        
        Args:
            user_id: Optional user ID to filter by
        """
        query = self.session.query(DeleteAuditLog)
        if user_id:
            query = query.filter(DeleteAuditLog.user_id == user_id)
        return query.order_by(DeleteAuditLog.performed_at.desc()).all()
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive stats for a user"""
        user = self.get_user(user_id)
        if not user:
            return {}
            
        face_samples = self.get_user_face_samples(user_id)
        recognition_events = self.get_user_recognition_events(user_id)
        attendance_stats = self.get_attendance_stats(user_id)
        
        return {
            'name': user.name,
            'created_at': user.created_at,
            'deleted_at': user.deleted_at,
            'face_samples': len(face_samples),
            'recognition_events': len(recognition_events),
            'avg_confidence': self.get_user_avg_confidence(user_id),
            'attendance_rate': attendance_stats.get('attendance_rate', 0),
            'total_duration': attendance_stats.get('total_duration_minutes', 0)
        }

    # Place operations
    def add_place(self, name, description=""):
        """Add a new place"""
        place = Place(name=name, description=description)
        self.session.add(place)
        self.session.commit()
        return place

    def get_place(self, place_id):
        """Get place by ID"""
        return self.session.query(Place).filter(Place.id == place_id).first()

    def get_all_places(self):
        """Get all places"""
        return self.session.query(Place).all()

    def update_place(self, place_id, name=None, description=None):
        """Update place information"""
        place = self.get_place(place_id)
        if place:
            if name:
                place.name = name
            if description:
                place.description = description
            self.session.commit()
        return place

    # Recognition Event operations
    def add_recognition_event(self, user_id, place_id, image_path, confidence_score=None):
        """Record a new recognition event with confidence score"""
        event = RecognitionEvent(
            user_id=user_id,
            place_id=place_id,
            image_path=image_path,
            confidence_score=confidence_score
        )
        self.session.add(event)
        self.session.commit()
        return event

    def get_user_recognition_events(self, user_id):
        """Get all recognition events for a user"""
        return self.session.query(RecognitionEvent).filter(
            RecognitionEvent.user_id == user_id
        ).order_by(RecognitionEvent.timestamp.desc()).all()

    def get_place_recognition_events(self, place_id):
        """Get all recognition events at a place"""
        return self.session.query(RecognitionEvent).filter(
            RecognitionEvent.place_id == place_id
        ).order_by(RecognitionEvent.timestamp.desc()).all()

    def get_recent_recognition_events(self, limit=10):
        """Get recent recognition events"""
        return self.session.query(RecognitionEvent).order_by(
            RecognitionEvent.timestamp.desc()
        ).limit(limit).all()

    def get_user_avg_confidence(self, user_id):
        """Get average confidence score for a user's recognitions"""
        events = self.session.query(RecognitionEvent).filter(
            RecognitionEvent.user_id == user_id,
            RecognitionEvent.confidence_score.isnot(None)
        ).all()
        
        if not events:
            return None
            
        scores = [event.confidence_score for event in events]
        return sum(scores) / len(scores)

    # Attendance operations
    def mark_attendance(self, user_id):
        """Mark a user as present for today"""
        today = date.today()
        # Check if attendance record for today already exists
        attendance = self.session.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.date == today
        ).first()
        
        current_time = datetime.now()
        
        if attendance:
            # Update existing record
            if not attendance.is_present:
                attendance.is_present = True
                attendance.check_in_time = current_time
            else:
                # Update check-out time and calculate duration
                attendance.check_out_time = current_time
                if attendance.check_in_time:
                    duration = (current_time - attendance.check_in_time).total_seconds() / 60
                    attendance.duration_minutes = int(duration)
        else:
            # Create new attendance record
            attendance = Attendance(
                user_id=user_id,
                date=today,
                check_in_time=current_time,
                is_present=True
            )
            self.session.add(attendance)
            
        self.session.commit()
        return attendance
    
    def get_user_attendance(self, user_id, start_date=None, end_date=None):
        """Get attendance records for a user within a date range"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)  # Default to last 30 days
        if not end_date:
            end_date = date.today()
            
        return self.session.query(Attendance).filter(
            Attendance.user_id == user_id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).order_by(Attendance.date.desc()).all()
    
    def get_daily_attendance(self, target_date=None):
        """Get all attendance records for a specific date"""
        if not target_date:
            target_date = date.today()
            
        return self.session.query(Attendance).filter(
            Attendance.date == target_date
        ).all()
    
    def get_attendance_stats(self, user_id, days=30):
        """Get attendance statistics for a user"""
        start_date = date.today() - timedelta(days=days)
        
        attendance_records = self.get_user_attendance(user_id, start_date)
        
        total_days = len(attendance_records)
        present_days = sum(1 for record in attendance_records if record.is_present)
        total_duration = sum(record.duration_minutes for record in attendance_records)
        
        return {
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": total_days - present_days,
            "attendance_rate": (present_days / total_days * 100) if total_days > 0 else 0,
            "total_duration_minutes": total_duration,
            "average_duration_minutes": (total_duration / present_days) if present_days > 0 else 0
        }
        
    def cleanup_deleted_records(self, days: int = 30) -> Dict[str, Any]:
        """
        Clean up records that have been soft deleted for the specified number of days
        
        Args:
            days: Number of days after which to permanently delete records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find expired users
        expired_users = self.session.query(User).filter(
            User.deleted_at < cutoff_date
        ).all()
        
        results = {
            'users_removed': 0,
            'samples_removed': 0,
            'events_removed': 0
        }
        
        for user in expired_users:
            # Count related records
            results['samples_removed'] += len(user.face_samples)
            results['events_removed'] += len(user.recognition_events)
            results['users_removed'] += 1
            
            # Delete user (will cascade to related records)
            self.session.delete(user)
        
        if results['users_removed'] > 0:
            self.session.commit()
        
        return results

    def __del__(self):
        """Cleanup database session"""
        self.session.close()
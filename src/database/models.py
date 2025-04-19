from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Query
from datetime import datetime, date
from typing import Optional

Base = declarative_base()

class SoftDeleteMixin:
    deleted_at = Column(DateTime, nullable=True)

    def soft_delete(self) -> None:
        """Mark record as deleted"""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore soft-deleted record"""
        self.deleted_at = None

    @classmethod
    def not_deleted(cls) -> Query:
        """Query filter for not deleted records"""
        return Query([cls]).filter(cls.deleted_at.is_(None))

class User(Base, SoftDeleteMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships with cascade deletes
    face_samples = relationship("FaceSample", back_populates="user",
                              cascade="all, delete-orphan")
    recognition_events = relationship("RecognitionEvent", back_populates="user",
                                    cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(name='{self.name}', deleted={self.deleted_at is not None})>"

    def archive(self) -> None:
        """Archive user and related records"""
        self.soft_delete()
        for sample in self.face_samples:
            sample.soft_delete()

class FaceSample(Base, SoftDeleteMixin):
    __tablename__ = 'face_samples'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    image_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    archived_path = Column(String, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="face_samples")
    
    def __repr__(self):
        return f"<FaceSample(user_id={self.user_id}, deleted={self.deleted_at is not None})>"

class Place(Base):
    __tablename__ = 'places'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    
    # Relationship
    recognition_events = relationship("RecognitionEvent", back_populates="place")
    
    def __repr__(self):
        return f"<Place(name='{self.name}')>"

class RecognitionEvent(Base):
    __tablename__ = 'recognition_events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    place_id = Column(Integer, ForeignKey('places.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    image_path = Column(String, nullable=False)
    confidence_score = Column(Float)  # Added confidence score
    
    # Relationships
    user = relationship("User", back_populates="recognition_events")
    place = relationship("Place", back_populates="recognition_events")
    
    def __repr__(self):
        return f"<RecognitionEvent(user_id={self.user_id}, place_id={self.place_id}, confidence={self.confidence_score:.2f})>"

class Attendance(Base):
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(DateTime, default=date.today)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    is_present = Column(Boolean, default=False)
    duration_minutes = Column(Integer, default=0)
    
    # Relationship
    user = relationship("User", backref="attendance_records")
    
    def __repr__(self):
        return f"<Attendance(user_id={self.user_id}, date={self.date}, is_present={self.is_present})>"

class DeleteAuditLog(Base):
    __tablename__ = 'delete_audit_log'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(50), nullable=False)  # 'delete' or 'restore'
    details = Column(JSON)
    performed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<DeleteAuditLog(user_id={self.user_id}, action='{self.action}')>"

    @classmethod
    def log_deletion(cls, session, user_id: int, details: Optional[dict] = None) -> None:
        """Log a deletion event"""
        log = cls(user_id=user_id, action='delete', details=details)
        session.add(log)
    
    @classmethod
    def log_restoration(cls, session, user_id: int, details: Optional[dict] = None) -> None:
        """Log a restoration event"""
        log = cls(user_id=user_id, action='restore', details=details)
        session.add(log)

# Database initialization function
def init_db():
    engine = create_engine('sqlite:///database.sqlite')
    Base.metadata.create_all(engine)
    return engine
import os
import shutil
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models import User, FaceSample, DeleteAuditLog

class DeleteManager:
    def __init__(self, db_session: Session):
        self.session = db_session
        self.archive_root = os.path.join('faces', 'archived')
        os.makedirs(self.archive_root, exist_ok=True)

    def _create_archive_path(self, user_id: int) -> str:
        """Create timestamped archive directory for user"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(self.archive_root, f"user_{user_id}", timestamp)
        os.makedirs(path, exist_ok=True)
        return path

    def _archive_face_images(self, user: User, archive_path: str) -> None:
        """Move face images to archive directory"""
        for sample in user.face_samples:
            if os.path.exists(sample.image_path):
                # Create archived file path
                filename = os.path.basename(sample.image_path)
                archived_path = os.path.join(archive_path, filename)
                
                # Move file to archive
                shutil.move(sample.image_path, archived_path)
                
                # Update database record
                sample.archived_path = archived_path
                sample.soft_delete()

    def delete_users(self, user_ids: List[int], archive: bool = True) -> dict:
        """
        Soft delete users and their related data
        
        Args:
            user_ids: List of user IDs to delete
            archive: Whether to archive face images (default True)
            
        Returns:
            Dict with results including success count and errors
        """
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': []
        }

        for user_id in user_ids:
            try:
                # Get user and verify existence
                user = self.session.query(User).get(user_id)
                if not user:
                    raise ValueError(f"User {user_id} not found")

                # Create archive directory if needed
                archive_path = self._create_archive_path(user_id) if archive else None

                # Archive face images if requested
                if archive:
                    self._archive_face_images(user, archive_path)

                # Soft delete user (cascades to related records)
                user.archive()

                # Log deletion
                DeleteAuditLog.log_deletion(
                    self.session,
                    user_id,
                    details={
                        'archive_path': archive_path,
                        'sample_count': len(user.face_samples),
                        'archived_at': datetime.utcnow().isoformat()
                    }
                )

                results['success_count'] += 1

            except Exception as e:
                results['error_count'] += 1
                results['errors'].append({
                    'user_id': user_id,
                    'error': str(e)
                })

        # Commit all changes
        if results['success_count'] > 0:
            self.session.commit()

        return results

    def restore_users(self, user_ids: List[int]) -> dict:
        """
        Restore soft-deleted users and their data
        
        Args:
            user_ids: List of user IDs to restore
            
        Returns:
            Dict with results including success count and errors
        """
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': []
        }

        for user_id in user_ids:
            try:
                # Get user including deleted records
                user = self.session.query(User).get(user_id)
                if not user:
                    raise ValueError(f"User {user_id} not found")

                # Restore face samples
                for sample in user.face_samples:
                    if sample.archived_path and os.path.exists(sample.archived_path):
                        # Move file back from archive
                        shutil.move(sample.archived_path, sample.image_path)
                        sample.archived_path = None
                    sample.restore()

                # Restore user
                user.restore()

                # Log restoration
                DeleteAuditLog.log_restoration(
                    self.session,
                    user_id,
                    details={
                        'restored_at': datetime.utcnow().isoformat(),
                        'sample_count': len(user.face_samples)
                    }
                )

                results['success_count'] += 1

            except Exception as e:
                results['error_count'] += 1
                results['errors'].append({
                    'user_id': user_id,
                    'error': str(e)
                })

        # Commit all changes
        if results['success_count'] > 0:
            self.session.commit()

        return results

    def cleanup_expired(self, days: int = 30) -> dict:
        """
        Permanently delete expired archived records
        
        Args:
            days: Number of days to keep archives (default 30)
            
        Returns:
            Dict with cleanup results
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        results = {
            'users_deleted': 0,
            'files_deleted': 0,
            'errors': []
        }

        # Find expired deleted users
        expired_users = self.session.query(User).filter(
            User.deleted_at < cutoff_date
        ).all()

        for user in expired_users:
            try:
                # Delete archived files
                archive_dir = os.path.join(self.archive_root, f"user_{user.id}")
                if os.path.exists(archive_dir):
                    shutil.rmtree(archive_dir)
                    results['files_deleted'] += 1

                # Permanently delete user record
                self.session.delete(user)
                results['users_deleted'] += 1

            except Exception as e:
                results['errors'].append({
                    'user_id': user.id,
                    'error': str(e)
                })

        if results['users_deleted'] > 0:
            self.session.commit()

        return results
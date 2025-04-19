import os
import shutil
import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, User, FaceSample, DeleteAuditLog
from src.utils.delete_manager import DeleteManager

class TestDeleteManager(unittest.TestCase):
    def setUp(self):
        """Set up test database and files"""
        # Create test database
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Set up test directories
        self.test_faces_dir = 'test_faces'
        self.active_dir = os.path.join(self.test_faces_dir, 'active')
        self.archive_dir = os.path.join(self.test_faces_dir, 'archived')
        os.makedirs(self.active_dir, exist_ok=True)
        
        # Create test user with face samples
        self.user = User(name="Test User")
        self.session.add(self.user)
        self.session.commit()
        
        # Create test face images
        self.face_paths = []
        for i in range(3):
            path = os.path.join(self.active_dir, f'face_{i}.jpg')
            with open(path, 'w') as f:
                f.write('test image data')
            self.face_paths.append(path)
            
            sample = FaceSample(user_id=self.user.id, image_path=path)
            self.session.add(sample)
        
        self.session.commit()
        
        # Initialize delete manager
        self.manager = DeleteManager(self.session)
        self.manager.archive_root = self.archive_dir
    
    def tearDown(self):
        """Clean up test data"""
        self.session.close()
        if os.path.exists(self.test_faces_dir):
            shutil.rmtree(self.test_faces_dir)
    
    def test_soft_delete(self):
        """Test soft deletion of user"""
        # Perform deletion
        results = self.manager.delete_users([self.user.id])
        
        self.assertEqual(results['success_count'], 1)
        self.assertEqual(results['error_count'], 0)
        
        # Verify user is soft deleted
        user = self.session.query(User).get(self.user.id)
        self.assertIsNotNone(user.deleted_at)
        
        # Verify face samples are soft deleted
        for sample in user.face_samples:
            self.assertIsNotNone(sample.deleted_at)
            self.assertIsNotNone(sample.archived_path)
            self.assertTrue(os.path.exists(sample.archived_path))
        
        # Verify original files are moved
        for path in self.face_paths:
            self.assertFalse(os.path.exists(path))
        
        # Verify audit log
        logs = self.session.query(DeleteAuditLog).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, 'delete')
        self.assertEqual(logs[0].user_id, self.user.id)
    
    def test_restore(self):
        """Test restoration of deleted user"""
        # Delete first
        self.manager.delete_users([self.user.id])
        
        # Then restore
        results = self.manager.restore_users([self.user.id])
        
        self.assertEqual(results['success_count'], 1)
        self.assertEqual(results['error_count'], 0)
        
        # Verify user is restored
        user = self.session.query(User).get(self.user.id)
        self.assertIsNone(user.deleted_at)
        
        # Verify face samples are restored
        for sample in user.face_samples:
            self.assertIsNone(sample.deleted_at)
            self.assertIsNone(sample.archived_path)
        
        # Verify files are moved back
        for path in self.face_paths:
            self.assertTrue(os.path.exists(path))
        
        # Verify audit log
        logs = self.session.query(DeleteAuditLog).filter_by(
            action='restore'
        ).all()
        self.assertEqual(len(logs), 1)
    
    def test_cleanup_expired(self):
        """Test cleanup of expired deleted records"""
        # Delete user
        self.manager.delete_users([self.user.id])
        
        # Modify deletion timestamp to be old
        user = self.session.query(User).get(self.user.id)
        user.deleted_at = datetime.utcnow() - timedelta(days=31)
        self.session.commit()
        
        # Run cleanup
        results = self.manager.cleanup_expired(days=30)
        
        self.assertEqual(results['users_deleted'], 1)
        self.assertEqual(results['files_deleted'], 1)
        
        # Verify user is permanently deleted
        user = self.session.query(User).get(self.user.id)
        self.assertIsNone(user)
        
        # Verify archived files are deleted
        self.assertFalse(os.path.exists(
            os.path.join(self.archive_root, f"user_{self.user.id}")
        ))
    
    def test_multi_user_delete(self):
        """Test deleting multiple users"""
        # Create additional test users
        user2 = User(name="Test User 2")
        self.session.add(user2)
        user3 = User(name="Test User 3")
        self.session.add(user3)
        self.session.commit()
        
        # Delete multiple users
        results = self.manager.delete_users([
            self.user.id, user2.id, user3.id
        ])
        
        self.assertEqual(results['success_count'], 3)
        self.assertEqual(results['error_count'], 0)
        
        # Verify all users are soft deleted
        for user_id in [self.user.id, user2.id, user3.id]:
            user = self.session.query(User).get(user_id)
            self.assertIsNotNone(user.deleted_at)

if __name__ == '__main__':
    unittest.main()
#!/usr/bin/env python3

import os
import sys
import pickle
import shutil

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine
from src.database.models import Base
from src.database.db_operations import DatabaseOperations

def reset_face_database():
    """Reset the face recognition database"""
    try:
        face_db_path = 'face_data/face_database.pkl'
        face_data_dir = 'face_data'
        
        # Remove face database file
        if os.path.exists(face_db_path):
            print(f"Removing face database: {face_db_path}")
            os.remove(face_db_path)
        
        # Create empty face database
        os.makedirs(face_data_dir, exist_ok=True)
        empty_db = {}
        with open(face_db_path, 'wb') as f:
            pickle.dump(empty_db, f)
            
        print("Face database reset successfully")
        return True
        
    except Exception as e:
        print(f"Error resetting face database: {str(e)}")
        return False

def reset_database():
    """Remove existing database and create a fresh one with the new schema"""
    try:
        # Database file path
        db_path = 'database.sqlite'
        
        # Remove existing database if it exists
        if os.path.exists(db_path):
            print(f"Removing existing database: {db_path}")
            os.remove(db_path)
        
        # Create new database with updated schema
        print("Creating new database with updated schema...")
        engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(engine)
        
        # Initialize database operations to verify
        db = DatabaseOperations()
        
        # Verify database connection
        try:
            db.get_all_users()
            print("Database successfully reset and verified!")
            return True
        except Exception as e:
            print(f"Error verifying database: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Error resetting database: {str(e)}")
        return False

if __name__ == '__main__':
    print("This will delete all existing data and create fresh databases.")
    print("Warning: This includes removing all face recognition data!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() == 'yes':
        success = True
        
        # Reset SQL database
        if not reset_database():
            success = False
            
        # Reset face database
        if not reset_face_database():
            success = False
            
        if success:
            print("\nAll databases reset successfully. You can now restart the application.")
            sys.exit(0)
        else:
            print("\nFailed to reset one or more databases. Please check the errors above.")
            sys.exit(1)
    else:
        print("\nDatabase reset cancelled.")
        sys.exit(0)
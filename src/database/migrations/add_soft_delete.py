import os
import sys
from sqlalchemy import create_engine, text

def run_migration():
    """Add soft delete support to database"""
    try:
        # Initialize database connection
        engine = create_engine('sqlite:///database.sqlite')
        
        # Add deleted_at column to users table
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN deleted_at TIMESTAMP;
            """))
            
            # Add deleted_at and archived_path columns to face_samples table
            conn.execute(text("""
                ALTER TABLE face_samples 
                ADD COLUMN deleted_at TIMESTAMP;
            """))
            
            conn.execute(text("""
                ALTER TABLE face_samples 
                ADD COLUMN archived_path VARCHAR;
            """))
            
            # Create delete_audit_log table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS delete_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action VARCHAR(50) NOT NULL,
                    details JSON,
                    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
            """))
            
            conn.commit()
            
        print("Successfully added soft delete support to database")
        return True
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        return False

if __name__ == '__main__':
    if run_migration():
        sys.exit(0)
    else:
        sys.exit(1)
import os
import pickle
import cv2
import numpy as np
import insightface
import datetime
from insightface.app import FaceAnalysis
from config import DATA_DIR, FACE_DB_PATH

# Initialize HOG detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

def initialize_insightface():
    """Initialize InsightFace with optimized settings"""
    try:
        face_app = FaceAnalysis(
            name='buffalo_sc',
            providers=['CPUExecutionProvider'],
            root=os.path.join(DATA_DIR, "models")
        )
        face_app.prepare(
            ctx_id=0,
            det_size=(640, 640),  # Increased detection size for better distance detection
            det_thresh=0.45  # Lowered threshold to detect faces at greater distances
        )
        print("InsightFace initialized with optimized settings")
        return face_app, True
    except Exception as e:
        print(f"Failed to initialize InsightFace: {e}")
        return None, False

class FaceEntry:
    """Class to store face data with multiple pose embeddings"""
    def __init__(self):
        self.embeddings = {
            'front': [],  # 5 front-facing embeddings
            'side': [],   # 2 side profile embeddings
            'tilt': [],   # 4 slightly tilted embeddings
            'back': []    # 5 fully tilted embeddings
        }
        self.registered_at = datetime.datetime.now()
    
    def add_embedding(self, pose_type, embedding):
        """Add an embedding for a specific pose"""
        max_embeddings = {
            'front': 5,
            'side': 2,
            'tilt': 4,
            'back': 5
        }
        if len(self.embeddings[pose_type]) < max_embeddings[pose_type]:
            self.embeddings[pose_type].append(embedding)
            return True
        return False
    
    def is_complete(self):
        """Check if all required poses are captured"""
        required_counts = {
            'front': 5,
            'side': 2,
            'tilt': 4,
            'back': 5
        }
        return all(len(self.embeddings[pose]) == count
                  for pose, count in required_counts.items())

def load_face_database():
    """Load the face database from disk"""
    face_database = {}
    if os.path.exists(FACE_DB_PATH):
        try:
            with open(FACE_DB_PATH, 'rb') as f:
                db_data = pickle.load(f)
                
                # Convert old format to new if needed
                for name, data in db_data.items():
                    if isinstance(data, (list, np.ndarray)):
                        # Convert old single embedding to new format
                        face_entry = FaceEntry()
                        face_entry.embeddings['front'].append(data)
                        face_database[name] = face_entry
                    else:
                        face_database[name] = data
                        
            print(f"Loaded {len(face_database)} faces from database")
        except Exception as e:
            print(f"Error loading face database: {e}")
    return face_database

def save_face_database(face_database):
    """Save the face database to disk"""
    try:
        # Create backup of existing database
        if os.path.exists(FACE_DB_PATH):
            backup_path = f"{FACE_DB_PATH}.bak"
            with open(FACE_DB_PATH, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())
        
        # Save new database
        with open(FACE_DB_PATH, 'wb') as f:
            pickle.dump(face_database, f)
        
        # Verify save
        with open(FACE_DB_PATH, 'rb') as f:
            verify_db = pickle.load(f)
            if len(verify_db) != len(face_database):
                raise Exception("Database verification failed")
            
        print(f"Saved {len(face_database)} faces to database")
        return True
        
    except Exception as e:
        print(f"Error saving face database: {e}")
        # Restore backup if exists
        if os.path.exists(f"{FACE_DB_PATH}.bak"):
            with open(f"{FACE_DB_PATH}.bak", 'rb') as src, open(FACE_DB_PATH, 'wb') as dst:
                dst.write(src.read())
            print("Restored database from backup")
        return False

# Initialize global variables
face_app, use_insightface = initialize_insightface()
face_database = load_face_database()

import os
import sys

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.db_operations import DatabaseOperations

def create_directories():
    """Create necessary directories for the application"""
    dirs = [
        'data/face_samples',
        'data/recognition_events',
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

def test_database():
    """Test database operations"""
    db = DatabaseOperations()
    
    # Test User operations
    print("\nTesting User operations...")
    test_user = db.add_user("Test User")
    print(f"Added user: {test_user}")
    
    # Test Place operations
    print("\nTesting Place operations...")
    test_place = db.add_place("Test Room", "A test location")
    print(f"Added place: {test_place}")
    
    # Test Face Sample operations
    print("\nTesting Face Sample operations...")
    sample_path = "data/face_samples/test_sample.jpg"
    face_sample = db.add_face_sample(test_user.id, sample_path)
    print(f"Added face sample: {face_sample}")
    
    # Test Recognition Event operations
    print("\nTesting Recognition Event operations...")
    event_path = "data/recognition_events/test_event.jpg"
    event = db.add_recognition_event(test_user.id, test_place.id, event_path)
    print(f"Added recognition event: {event}")
    
    # Test retrieval operations
    print("\nTesting retrieval operations...")
    users = db.get_all_users()
    places = db.get_all_places()
    recent_events = db.get_recent_recognition_events(limit=5)
    
    print(f"Total users: {len(users)}")
    print(f"Total places: {len(places)}")
    print(f"Recent events: {len(recent_events)}")

def main():
    print("Initializing Face Recognition System...")
    create_directories()
    print("\nTesting database operations...")
    test_database()
    print("\nInitialization complete!")

if __name__ == "__main__":
    main()
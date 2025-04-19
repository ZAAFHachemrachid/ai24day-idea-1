import os

# Configuration settings
DETECTION_CONFIG = {
    'detection_interval': 5,
    'min_face_size': 20,  # Reduced to detect smaller faces at greater distances
    'max_face_size': 400,  # Increased max size for closer faces
    'recognition_threshold': 0.45,  # Further relaxed for distance recognition
    'tracking_confidence_threshold': 0.55,  # Adjusted for better tracking
    'processing_width': 1280,  # Increased for better resolution
    'enable_tracking': True,
    'use_face_landmarks': True,
    'optimize_for_distance': True,
    'recognition_scales': [1.0, 0.75, 1.25],  # Try multiple scales for better recognition
    'presence_verification_time': 10.0  # Time in seconds before confirming attendance
}

# Directory setup
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_data")
os.makedirs(DATA_DIR, exist_ok=True)
FACE_DB_PATH = os.path.join(DATA_DIR, "face_database.pkl")
ATTENDANCE_LOG = os.path.join(DATA_DIR, "attendance_log.csv")

# Tracking configuration
AWAY_THRESHOLD = 30  # Seconds before marking someone as away

# Camera configurations
CAMERA_CONFIG = {
    'default': {
        'width': 320,  # Small, fixed resolution
        'height': 240,
        'fps': 30,
        'buffer_size': 1  # Reduce latency
    },
    'ip': {
        'reconnect_attempts': 3,
        'connection_timeout': 10.0,
        'supported_protocols': ['rtsp', 'http'],
        'default_protocol': 'http'
    },
    'grid': {
        'max_columns': 3,  # Maximum number of columns in grid view
        'cell_width': 320,  # Match default camera resolution
        'cell_height': 240,  # Match default camera resolution
    }
}

# Camera status update interval (ms)
CAMERA_UPDATE_INTERVAL = 50  # 20 FPS for better performance

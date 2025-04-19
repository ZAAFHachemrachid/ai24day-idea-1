import numpy as np
import cv2
from config import DETECTION_CONFIG
from .initializers import face_database

def recognize_face(face_embedding):
    """Enhanced face recognition optimized for distance"""
    if not face_database:
        return "Unknown", 0.0

    best_match = ("Unknown", 0.0)
    face_norm = np.linalg.norm(face_embedding)

    for name, face_entry in face_database.items():
        if not isinstance(face_entry, dict):
            # Handle old database format
            embeddings = [face_entry] if isinstance(face_entry, (list, np.ndarray)) else face_entry.embeddings['front']
        else:
            # Get all embeddings from different poses
            embeddings = []
            for pose_embeddings in face_entry.embeddings.values():
                embeddings.extend(pose_embeddings)

        # Try recognition at multiple scales
        for scale in DETECTION_CONFIG['recognition_scales']:
            scaled_embedding = face_embedding * scale
            scaled_norm = face_norm * scale

            for ref_embedding in embeddings:
                if ref_embedding is None:
                    continue

                # Normalize reference embedding
                ref_norm = np.linalg.norm(ref_embedding)
                
                # Enhanced similarity calculation
                similarity = np.dot(scaled_embedding, ref_embedding) / (scaled_norm * ref_norm)
                
                # Apply distance-aware weighting
                similarity = similarity * (1.0 + 0.2 * (1.0 - abs(1.0 - scale)))

                # Early return for very confident matches
                if similarity > 0.8:
                    return name, similarity

                if similarity > best_match[1]:
                    best_match = (name, similarity)

    # Use relaxed threshold for distance recognition
    return best_match if best_match[1] >= DETECTION_CONFIG['recognition_threshold'] else ("Unknown", best_match[1])

def detect_facial_features(face):
    """Detect eyes and mouth from face landmarks"""
    if not hasattr(face, 'kps') or face.kps is None:
        return None, None

    # InsightFace facial landmarks:
    # 0: right eye, 1: left eye, 2: nose, 3: right mouth, 4: left mouth
    landmarks = face.kps.astype(int)

    # Calculate eye regions
    right_eye = landmarks[0]
    left_eye = landmarks[1]

    # Calculate mouth region from right and left mouth corners
    mouth_right = landmarks[3]
    mouth_left = landmarks[4]

    # Create bounding boxes for eyes (expand by 10 pixels around landmark)
    right_eye_bbox = (right_eye[0]-15, right_eye[1]-10, 30, 20)
    left_eye_bbox = (left_eye[0]-15, left_eye[1]-10, 30, 20)

    # Create bounding box for mouth (expand around landmarks)
    mouth_center_x = (mouth_right[0] + mouth_left[0]) // 2
    mouth_center_y = (mouth_right[1] + mouth_left[1]) // 2
    mouth_width = int(abs(mouth_right[0] - mouth_left[0]) * 1.5)
    mouth_height = int(mouth_width * 0.4)  # Proportional height
    mouth_bbox = (mouth_center_x - mouth_width//2,
                  mouth_center_y - mouth_height//2,
                  mouth_width, mouth_height)

    eyes = [right_eye_bbox, left_eye_bbox]
    
    return eyes, mouth_bbox

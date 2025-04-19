import cv2
import numpy as np
import logging
import time
from src.database.db_operations import DatabaseOperations
from src.utils.position_tracking import PositionTracker
from src.utils.distance_tracking import DistanceTracker
from src.utils.tracking import MotionPredictor
from src.face_recognition.recognition import recognize_face

# Configure logging
logger = logging.getLogger(__name__)

class FaceDetector:
    def __init__(self):
        self.db = DatabaseOperations()
        # Load the pre-trained face detection cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        # Load eye cascade for additional verification
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        # Initialize position and distance trackers
        self.position_tracker = PositionTracker()
        self.distance_tracker = DistanceTracker()
        # Initialize motion predictors for each face
        self.motion_predictors = {}
        # Last frame timestamp for dt calculation
        self.last_frame_time = time.time()
        # Current frame's unknown faces
        self.current_unknown_faces = []
        
    def detect_faces(self, frame):
        """Detect faces in the frame and return their coordinates"""
        if frame is None:
            return []
            
        # Calculate dt for motion prediction
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time
            
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_height, frame_width = frame.shape[:2]
        
        # Use motion predictions to optimize detection
        detected_faces = []
        
        # First check predicted regions for known faces
        for face_id, predictor in self.motion_predictors.items():
            # Get predicted search region
            x, y, w, h = predictor.get_search_region(frame_width, frame_height)
            confidence = predictor.get_confidence()
            
            # Only search predicted region if confidence is high enough
            if confidence > 0.5:
                roi_gray = gray[y:y+h, x:x+w]
                
                # Detect in ROI
                faces_in_roi = self.face_cascade.detectMultiScale(
                    roi_gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                # Adjust coordinates to full frame
                for (fx, fy, fw, fh) in faces_in_roi:
                    detected_faces.append((x + fx, y + fy, fw, fh))
        
        # Scan full frame at reduced frequency for new faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        detected_faces.extend(list(faces))
        
        # Verify faces by checking for eyes
        verified_faces = []
        for (x, y, w, h) in detected_faces:
            face_gray = gray[y:y+h, x:x+w]
            eyes = self.eye_cascade.detectMultiScale(face_gray)
            if len(eyes) >= 1:  # At least one eye detected
                verified_faces.append((x, y, w, h))
                
                # Update motion predictor
                face_id = f"{x}_{y}_{w}_{h}"
                face_center_x = x + w//2
                face_center_y = y + h//2
                
                if face_id in self.motion_predictors:
                    self.motion_predictors[face_id].update(face_center_x, face_center_y)
                else:
                    predictor = MotionPredictor(dt=dt)
                    predictor.initialize(face_center_x, face_center_y)
                    self.motion_predictors[face_id] = predictor
        
        # Cleanup stale predictors
        current_face_ids = {f"{x}_{y}_{w}_{h}" for (x, y, w, h) in verified_faces}
        stale_ids = set(self.motion_predictors.keys()) - current_face_ids
        for face_id in stale_ids:
            del self.motion_predictors[face_id]
        
        return verified_faces
        
    def compare_faces(self, face_img, reference_img):
        """Compare two face images and return similarity score"""
        # Convert images to same size
        face_img = cv2.resize(face_img, (256, 256))
        reference_img = cv2.resize(reference_img, (256, 256))
        
        # Convert to grayscale
        if len(face_img.shape) == 3:
            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        if len(reference_img.shape) == 3:
            reference_img = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
            
        # Calculate similarity using normalized correlation
        correlation = cv2.matchTemplate(face_img, reference_img, cv2.TM_CCORR_NORMED)[0][0]
        return correlation * 100  # Convert to percentage
    
    def find_matching_user(self, face_img, min_confidence=60):
        """Find matching user from database"""
        users = self.db.get_all_users()
        best_match = None
        best_confidence = 0
        
        for user in users:
            # Get user's face samples
            samples = self.db.get_user_face_samples(user.id)
            for sample in samples:
                try:
                    reference_img = cv2.imread(sample.image_path)
                    if reference_img is not None:
                        confidence = self.compare_faces(face_img, reference_img)
                        if confidence > best_confidence and confidence >= min_confidence:
                            best_confidence = confidence
                            best_match = user
                except Exception as e:
                    print(f"Error comparing with sample {sample.image_path}: {e}")
                    continue
        
        # If we found a match, mark attendance
        if best_match and best_confidence >= min_confidence:
            self.db.mark_attendance(best_match.id)
        
        return best_match, best_confidence
    
    def draw_faces(self, frame, faces_with_info, show_landmarks=True, show_predictions=True):
        """Draw rectangles around detected faces and optionally show facial landmarks
        Args:
            frame: The frame to draw on
            faces_with_info: List of tuples ((x,y,w,h), name, confidence)
            show_landmarks: Whether to show facial landmarks
        """
        # Update frame dimensions for tracking
        self.position_tracker.update_frame_dimensions(frame)
        frame_width = frame.shape[1]
        
        # Reset unknown faces list
        self.current_unknown_faces = []
        
        for face_info in faces_with_info:
            try:
                # Safely unpack face information
                if len(face_info) != 3:
                    logger.error(f"Invalid face info format: {face_info}")
                    continue
                    
                bbox, name, confidence = face_info
                if len(bbox) != 4:
                    logger.error(f"Invalid bbox format: {bbox}")
                    continue
                    
                x, y, w, h = bbox
                
                # Draw face rectangle with color based on recognition
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                
                # Get position information
                position_info = self.position_tracker.get_face_position((x, y, w, h))
                
                # Set position color (red for left, green for right)
                position_color = (0, 255, 0) if position_info['position'] == 'right' else (0, 0, 255)
                
                # Get distance information
                distance_info = self.distance_tracker.get_distance((x, y, w, h), frame_width)
                
                # Calculate vertical spacing
                base_y = y - 150  # Start higher above the face to accommodate distance
                spacing = 35  # Space between text elements
                
                # Draw position text (LEFT/RIGHT)
                position_text = position_info['position'].upper()
                text_size = cv2.getTextSize(position_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)[0]
                text_x = x + (w - text_size[0]) // 2
                
                # Black background for position text
                cv2.rectangle(frame,
                           (text_x - 10, base_y - 25),
                           (text_x + text_size[0] + 10, base_y + 5),
                           (0, 0, 0),
                           -1)
                
                # Draw position text
                cv2.putText(frame, position_text,
                          (text_x, base_y),
                          cv2.FONT_HERSHEY_SIMPLEX, 1.2, position_color, 2)
                
                # Draw percentage below position
                percentage_text = f"{abs(position_info['relative_position']):.0f}%"
                perc_size = cv2.getTextSize(percentage_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
                perc_x = x + (w - perc_size[0]) // 2
                perc_y = base_y + spacing
                
                # Black background for percentage
                cv2.rectangle(frame,
                           (perc_x - 10, perc_y - 25),
                           (perc_x + perc_size[0] + 10, perc_y + 5),
                           (0, 0, 0),
                           -1)
                
                # Draw percentage
                cv2.putText(frame, percentage_text,
                          (perc_x, perc_y),
                          cv2.FONT_HERSHEY_SIMPLEX, 1.0, position_color, 2)
                
                # Draw direction arrow
                arrow_y = base_y + spacing * 2
                arrow_start = (x + w//2, arrow_y)
                arrow_length = 40
                arrow_end = (arrow_start[0] - arrow_length, arrow_y) if position_info['position'] == 'left' \
                           else (arrow_start[0] + arrow_length, arrow_y)
                cv2.arrowedLine(frame, arrow_start, arrow_end, position_color, 3, tipLength=0.5)
                
                # Draw distance information
                distance_text = f"{distance_info['distance_m']:.1f}m"
                dist_size = cv2.getTextSize(distance_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
                dist_x = x + (w - dist_size[0]) // 2
                dist_y = arrow_y + spacing
                
                # Black background for distance
                cv2.rectangle(frame,
                           (dist_x - 10, dist_y - 25),
                           (dist_x + dist_size[0] + 10, dist_y + 5),
                           (0, 0, 0),
                           -1)
                
                # Draw distance text in blue
                cv2.putText(frame, distance_text,
                          (dist_x, dist_y),
                          cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 165, 0), 2)
                
                if show_landmarks:
                    # Get the face ROI
                    face_roi = frame[y:y+h, x:x+w]
                    face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
                    
                    # Detect eyes in the face region
                    eyes = self.eye_cascade.detectMultiScale(face_gray)
                    
                    # Draw eyes
                    for (ex, ey, ew, eh) in eyes:
                        center = (x + ex + ew//2, y + ey + eh//2)
                        cv2.circle(frame, center, 2, color, 2)
                
                # Prepare identification text
                if name != "Unknown":
                    text = f"{name}"
                    if confidence > 0:
                        text += f" ({confidence:.1f}%)"
                        
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                    name_x = x + (w - text_size[0]) // 2
                    name_y = y - 25  # Space above face
                    
                    # Black background
                    cv2.rectangle(frame,
                               (name_x - 5, name_y - 20),
                               (name_x + text_size[0] + 5, name_y + 5),
                               (0, 0, 0),
                               -1)
                    
                    # Draw name text in green
                    cv2.putText(frame, text, (name_x, name_y),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                else:
                    # For unknown faces, add to list for sequential numbering
                    self.current_unknown_faces.append((x, y))
                    
            except Exception as e:
                logger.error(f"Error processing face: {str(e)}")
                continue
        
        # Add detection count
        # Clean up stale face tracking data
        # Get coordinates for cleanup - with error handling
        face_coords = []
        for face_info in faces_with_info:
            try:
                bbox = face_info[0]  # Get bbox tuple
                if len(bbox) == 4:
                    face_coords.append(bbox)
            except (IndexError, TypeError):
                continue
        self.position_tracker.cleanup_stale_faces(face_coords)
        self.distance_tracker.cleanup_stale_faces(face_coords)
        
        # Number unknown faces from left to right
        if self.current_unknown_faces:
            # Sort unknown faces by x coordinate to ensure consistent numbering
            self.current_unknown_faces.sort(key=lambda pos: pos[0])
            
            # Create a dictionary mapping (x,y) to face width for easier lookup
            # Create a dictionary mapping (x,y) to face width with error handling
            face_info = {}
            for face_data in faces_with_info:
                try:
                    x, y, w, h = face_data[0]  # Get bbox tuple
                    face_info[(x,y)] = (w,h)
                except (IndexError, TypeError, ValueError):
                    continue
            
            # Number the unknown faces
            for i, (ux, uy) in enumerate(self.current_unknown_faces):
                if (ux, uy) in face_info:
                    w, h = face_info[(ux, uy)]
                    text = f"Unknown #{i+1}"
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                    name_x = ux + (w - text_size[0]) // 2
                    name_y = uy - 25  # Match the spacing of known faces
                    
                    # Black background
                    cv2.rectangle(frame,
                                (name_x - 5, name_y - 20),
                                (name_x + text_size[0] + 5, name_y + 5),
                                (0, 0, 0),
                                -1)
                    
                    # Draw unknown face number in pure red
                    cv2.putText(frame, text, (name_x, name_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Reset unknown faces list for next frame
        self.current_unknown_faces = []
        
        # Add detection count using faces_with_info
        cv2.putText(frame, f"Detected: {len(faces_with_info)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Draw prominent center line
        height = frame.shape[0]
        center_x = frame.shape[1] // 2
        
        # Yellow center line
        cv2.line(frame, (center_x, 0), (center_x, height),
                (0, 255, 255), 3)
        
        # Add "CENTER LINE" text
        cv2.putText(frame, "CENTER",
                    (center_x - 45, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
        
        # Draw motion predictions if enabled
        if show_predictions:
            for face_info in faces_with_info:
                try:
                    bbox, name, _ = face_info
                    x, y, w, h = bbox
                    face_id = f"{x}_{y}_{w}_{h}"
                    
                    if face_id in self.motion_predictors:
                        predictor = self.motion_predictors[face_id]
                        
                        # Get next predicted position
                        pred_x, pred_y = predictor.predict()
                        confidence = predictor.get_confidence()
                        
                        # Draw prediction point with confidence-based color
                        color = (0, int(255 * confidence), int(255 * (1 - confidence)))
                        cv2.circle(frame, (int(pred_x), int(pred_y)), 5, color, -1)
                        
                        # Draw line from current to predicted position
                        current_center = (x + w//2, y + h//2)
                        cv2.line(frame, current_center, (int(pred_x), int(pred_y)), color, 2)
                        
                        # Draw search region
                        if confidence > 0.5:
                            search_x, search_y, search_w, search_h = predictor.get_search_region(frame.shape[1], frame.shape[0])
                            cv2.rectangle(frame, (search_x, search_y),
                                        (search_x + search_w, search_y + search_h),
                                        color, 1)
                            
                except (IndexError, ValueError) as e:
                    logger.error(f"Error drawing prediction: {str(e)}")
                    continue
        
        return frame
import cv2
import numpy as np
import math
from typing import List, Tuple, Optional

class FaceProcessor:
    def __init__(self):
        # Load the eye detector cascade
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    
    def align_face(self, face_img: np.ndarray) -> np.ndarray:
        """
        Align face based on eye positions to standardize face orientation
        """
        try:
            # Convert to grayscale if needed
            if len(face_img.shape) == 3:
                gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_img.copy()
            
            # Detect eyes in the face region
            eyes = self.eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            
            # Need at least two eyes for alignment
            if len(eyes) >= 2:
                # Sort eyes by x-coordinate to get left and right eye
                eyes = sorted(eyes, key=lambda x: x[0])
                
                # Get eye centers
                left_eye = (eyes[0][0] + eyes[0][2] // 2, eyes[0][1] + eyes[0][3] // 2)
                right_eye = (eyes[1][0] + eyes[1][2] // 2, eyes[1][1] + eyes[1][3] // 2)
                
                # Calculate angle between eyes
                dx = right_eye[0] - left_eye[0]
                dy = right_eye[1] - left_eye[1]
                angle = math.degrees(math.atan2(dy, dx))
                
                # Get center point between eyes
                center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
                
                # Get rotation matrix
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                
                # Apply affine transformation
                height, width = face_img.shape[:2]
                aligned_face = cv2.warpAffine(face_img, rotation_matrix, (width, height), flags=cv2.INTER_CUBIC)
                
                return aligned_face
            
            # If we can't detect two eyes, return original image
            return face_img
            
        except Exception as e:
            print(f"Error aligning face: {e}")
            return face_img
    
    def assess_face_quality(self, face_img: np.ndarray) -> Tuple[bool, float, str]:
        """
        Assess the quality of a face image for recognition
        Returns: (is_good_quality, quality_score, message)
        """
        try:
            # Convert to grayscale if needed
            if len(face_img.shape) == 3:
                gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_img.copy()
            
            quality_score = 0.0
            issues = []
            
            # Check resolution (minimum 100x100 pixels)
            height, width = gray.shape[:2]
            min_dimension = min(height, width)
            if min_dimension < 100:
                issues.append(f"Low resolution: {width}x{height}")
            else:
                # Add points for resolution (max 30 points)
                quality_score += min(30, min_dimension / 10)
            
            # Check brightness and contrast
            mean_brightness = np.mean(gray)
            std_contrast = np.std(gray)
            
            # Brightness should be between 80-180 (for 8-bit grayscale)
            if mean_brightness < 80:
                issues.append(f"Too dark: {mean_brightness:.1f}")
            elif mean_brightness > 180:
                issues.append(f"Too bright: {mean_brightness:.1f}")
            else:
                # Add points for good brightness (max 20 points)
                brightness_score = 20 - abs(mean_brightness - 130) / 5
                quality_score += max(0, brightness_score)
            
            # Contrast should be at least 40
            if std_contrast < 40:
                issues.append(f"Low contrast: {std_contrast:.1f}")
            else:
                # Add points for good contrast (max 20 points)
                quality_score += min(20, std_contrast / 3)
            
            # Check for eyes
            eyes = self.eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            if len(eyes) < 2:
                issues.append(f"Eyes not clearly visible: {len(eyes)} detected")
            else:
                # Add points for detected eyes (max 30 points)
                quality_score += 30
            
            # Normalize quality score to 0-100
            quality_score = min(100, quality_score)
            
            # Determine if quality is good enough (threshold at 60)
            is_good_quality = quality_score >= 60 and len(issues) <= 1
            
            # Create message
            if issues:
                message = ", ".join(issues)
            else:
                message = "Good quality"
            
            return is_good_quality, quality_score, message
            
        except Exception as e:
            print(f"Error assessing face quality: {e}")
            return False, 0.0, f"Error: {str(e)}"
    
    def generate_augmented_samples(self, face_img: np.ndarray, num_samples: int = 5) -> List[np.ndarray]:
        """
        Generate augmented face samples for training
        """
        augmented_samples = []
        
        try:
            # Original image is always included
            augmented_samples.append(face_img.copy())
            
            height, width = face_img.shape[:2]
            center = (width // 2, height // 2)
            
            # 1. Slight rotations (±10 degrees)
            for angle in [-10, -5, 5, 10]:
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(face_img, rotation_matrix, (width, height), 
                                         borderMode=cv2.BORDER_REPLICATE)
                augmented_samples.append(rotated)
            
            # 2. Small scale variations (±5%)
            for scale in [0.95, 1.05]:
                scaled_width = int(width * scale)
                scaled_height = int(height * scale)
                scaled = cv2.resize(face_img, (scaled_width, scaled_height))
                
                # Create a blank canvas of original size
                canvas = np.zeros_like(face_img)
                
                # Calculate position to paste the scaled image
                x_offset = max(0, (width - scaled_width) // 2)
                y_offset = max(0, (height - scaled_height) // 2)
                
                # Paste the scaled image onto the canvas
                if len(face_img.shape) == 3:  # Color image
                    canvas[y_offset:y_offset+scaled_height, x_offset:x_offset+scaled_width] = scaled
                else:  # Grayscale image
                    canvas[y_offset:y_offset+scaled_height, x_offset:x_offset+scaled_width] = scaled
                
                augmented_samples.append(canvas)
            
            # 3. Brightness/contrast adjustments
            # Increase brightness
            bright = cv2.convertScaleAbs(face_img, alpha=1.0, beta=20)
            augmented_samples.append(bright)
            
            # Decrease brightness
            dark = cv2.convertScaleAbs(face_img, alpha=1.0, beta=-20)
            augmented_samples.append(dark)
            
            # Increase contrast
            contrast_high = cv2.convertScaleAbs(face_img, alpha=1.2, beta=0)
            augmented_samples.append(contrast_high)
            
            # Decrease contrast
            contrast_low = cv2.convertScaleAbs(face_img, alpha=0.8, beta=0)
            augmented_samples.append(contrast_low)
            
            # Limit to requested number of samples
            return augmented_samples[:num_samples]
            
        except Exception as e:
            print(f"Error generating augmented samples: {e}")
            # Return at least the original image if available
            if augmented_samples:
                return augmented_samples
            return [face_img]  # Return original as fallback
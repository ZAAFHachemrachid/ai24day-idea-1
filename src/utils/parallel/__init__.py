"""
This package contains the parallel processing infrastructure for face detection and recognition.
"""

from .frame_buffer import ThreadSafeFrameBuffer
from .detection_pool import FaceDetectionPool, DetectionResult
from .recognition_pool import RecognitionPool, RecognitionResult
from .drawing_pool import DrawingPool, DrawRequest, DrawResult

__all__ = [
    'ThreadSafeFrameBuffer',
    'FaceDetectionPool',
    'DetectionResult',
    'RecognitionPool',
    'RecognitionResult',
    'DrawingPool',
    'DrawRequest',
    'DrawResult'
]
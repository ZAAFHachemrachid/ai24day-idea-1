#!/usr/bin/env python3
import cv2
import os
import sys
import time
import logging
from typing import Dict, List

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.camera_manager import CameraManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_device_permissions(device_path: str) -> Dict[str, bool]:
    """Check device file permissions"""
    try:
        stats = os.stat(device_path)
        return {
            'exists': True,
            'readable': os.access(device_path, os.R_OK),
            'writable': os.access(device_path, os.W_OK),
            'mode': oct(stats.st_mode)[-3:],  # Last 3 digits of octal mode
            'user': stats.st_uid,
            'group': stats.st_gid
        }
    except Exception as e:
        return {
            'exists': False,
            'error': str(e)
        }

def test_device_capture(device_path: str, num_frames: int = 10) -> Dict:
    """Test capturing frames from device"""
    results = {
        'can_open': False,
        'can_read': False,
        'frame_size': None,
        'fps': 0,
        'errors': []
    }
    
    try:
        cap = cv2.VideoCapture(device_path)
        results['can_open'] = cap.isOpened()
        
        if results['can_open']:
            # Try reading frames
            start_time = time.time()
            frames_read = 0
            
            for _ in range(num_frames):
                ret, frame = cap.read()
                if ret and frame is not None:
                    frames_read += 1
                    if results['frame_size'] is None:
                        results['frame_size'] = f"{frame.shape[1]}x{frame.shape[0]}"
                else:
                    results['errors'].append(f"Failed to read frame {frames_read + 1}")
                    
            end_time = time.time()
            duration = end_time - start_time
            
            if duration > 0:
                results['fps'] = frames_read / duration
                
            results['can_read'] = frames_read > 0
            results['frames_read'] = frames_read
            
        cap.release()
            
    except Exception as e:
        results['errors'].append(str(e))
        
    return results

def main():
    logger.info("Starting camera diagnostic...")
    
    # Check for video devices
    manager = CameraManager()
    devices = manager.list_video_devices(verbose=True)
    
    if not devices:
        logger.error("No video devices found!")
        logger.info("Please check:")
        logger.info("1. USB cable connection")
        logger.info("2. USB debugging is enabled on phone")
        logger.info("3. DroidCam or similar app is running")
        return
        
    logger.info("\nDetailed device analysis:")
    for device in devices:
        path = device['path']
        logger.info(f"\nAnalyzing device: {path}")
        
        # Check permissions
        perms = check_device_permissions(path)
        if perms['exists']:
            logger.info(f"Permissions:")
            logger.info(f"  Mode: {perms['mode']}")
            logger.info(f"  Readable: {perms['readable']}")
            logger.info(f"  Writable: {perms['writable']}")
        else:
            logger.error(f"Device file not found: {perms.get('error')}")
            continue
            
        # Test capture
        logger.info("\nTesting capture:")
        results = test_device_capture(path)
        
        if results['can_open']:
            logger.info("  Device opened successfully")
            if results['can_read']:
                logger.info(f"  Resolution: {results['frame_size']}")
                logger.info(f"  FPS: {results['fps']:.1f}")
                logger.info(f"  Frames read: {results['frames_read']}")
            else:
                logger.error("  Could not read frames!")
        else:
            logger.error("  Failed to open device!")
            
        if results['errors']:
            logger.error("\nErrors encountered:")
            for error in results['errors']:
                logger.error(f"  {error}")
                
    logger.info("\nDiagnostic complete!")

if __name__ == "__main__":
    main()
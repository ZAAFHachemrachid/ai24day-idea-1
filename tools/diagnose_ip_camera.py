#!/usr/bin/env python3
import sys
import os
import requests
import logging
from urllib.parse import urlparse

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.ip_camera import IPCamera
from src.utils.camera_manager import CameraManager

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_network_connection(url: str) -> dict:
    """Test basic network connectivity to the camera"""
    result = {
        'can_resolve': False,
        'can_connect': False,
        'port_open': False,
        'errors': []
    }
    
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (554 if parsed.scheme == 'rtsp' else 80)
        
        # Try HTTP connection first
        try:
            response = requests.get(url, timeout=5)
            result['can_connect'] = response.status_code == 200
            result['status_code'] = response.status_code
        except requests.exceptions.ConnectionError as e:
            result['errors'].append(f"Connection error: {str(e)}")
        except requests.exceptions.Timeout:
            result['errors'].append("Connection timed out")
        except requests.exceptions.RequestException as e:
            result['errors'].append(f"Request error: {str(e)}")
            
    except Exception as e:
        result['errors'].append(f"Error during network test: {str(e)}")
    
    return result

def main():
    if len(sys.argv) < 2:
        logger.error("Please provide the camera URL")
        logger.info("Usage: python diagnose_ip_camera.py <camera_url>")
        logger.info("Example: python diagnose_ip_camera.py http://192.168.1.100:8080/video")
        return

    camera_url = sys.argv[1]
    logger.info(f"Testing IP camera at: {camera_url}")
    
    # Test network connectivity
    logger.info("\nTesting network connectivity...")
    net_result = test_network_connection(camera_url)
    
    if net_result['errors']:
        logger.error("Network connectivity issues detected:")
        for error in net_result['errors']:
            logger.error(f"  - {error}")
        logger.info("\nPlease check:")
        logger.info("1. Camera is powered on and connected to the network")
        logger.info("2. Camera IP address is correct")
        logger.info("3. Camera port is accessible (no firewall blocking)")
        logger.info("4. Network cable/WiFi connection is stable")
        return
        
    # Test camera connection
    logger.info("\nTesting camera connection...")
    try:
        camera = IPCamera(camera_url)
        if camera.start():
            logger.info("Successfully connected to camera")
            frame = camera.read_frame()
            if frame is not None:
                logger.info(f"Successfully read frame: {frame.shape}")
            else:
                logger.error("Could not read frame from camera")
            camera.stop()
        else:
            logger.error("Failed to start camera")
            if camera._last_error:
                logger.error(f"Error: {camera._last_error}")
    except Exception as e:
        logger.error(f"Error testing camera: {str(e)}")

if __name__ == "__main__":
    main()
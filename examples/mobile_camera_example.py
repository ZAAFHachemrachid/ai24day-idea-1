import cv2
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.camera_manager import CameraManager

def main():
    # Create camera manager instance
    camera_manager = CameraManager()
    
    # List available video devices
    devices = camera_manager.list_video_devices()
    
    if not devices:
        print("No video devices found!")
        return
        
    print("\nAvailable video devices:")
    for device in devices:
        print(f"- {device['name']} ({device['path']})")
    
    # Let user select a device
    device_path = input("\nEnter device path (e.g., /dev/video2): ").strip()
    
    try:
        # Create mobile camera instance
        mobile_cam = CameraManager.create_mobile_camera(device_path)
        
        # Add camera to manager
        if not camera_manager.add_camera("mobile_cam", mobile_cam):
            print("Failed to add mobile camera!")
            return
            
        print("\nPress 'q' to quit")
        
        # Main display loop
        while True:
            # Get frame from camera
            frame = camera_manager.get_frame("mobile_cam")
            
            if frame is not None:
                # Display the frame
                cv2.imshow("Mobile Camera Feed", frame)
                
                # Get camera status
                status = camera_manager.get_camera_status("mobile_cam")
                if status:
                    print(f"\rResolution: {status['resolution']}", end='')
            
            # Check for 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Cleanup
        camera_manager.cleanup()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
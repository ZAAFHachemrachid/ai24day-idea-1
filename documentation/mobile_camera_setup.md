# Mobile Camera Setup Guide

## Overview
This guide explains how to use your mobile device's camera as a video input source for the attendance system by connecting it via USB cable.

## Requirements
1. USB cable compatible with your mobile device
2. Mobile device with camera
3. Required software:
   - For Android: Any USB webcam app (e.g., DroidCam, IP Webcam)
   - For iOS: Similar webcam apps available on the App Store

## Setup Steps

### Android Setup
1. Install a USB webcam app from the Play Store
2. Connect your device via USB cable
3. Enable USB debugging on your Android device:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times to enable Developer Options
   - Go to Settings → Developer Options
   - Enable "USB Debugging"
4. Launch the webcam app and select USB connection mode

### iOS Setup
1. Install a compatible webcam app
2. Connect your device via USB cable
3. Follow the app's specific instructions for USB connection

## Using the Mobile Camera

1. Run the example script to list available devices:
```bash
python examples/mobile_camera_example.py
```

2. The script will show available video devices:
```
Available video devices:
- Video Device 0 (/dev/video0)
- Video Device 1 (/dev/video1)
- Video Device 2 (/dev/video2)
```

3. Select the appropriate device when prompted

## Troubleshooting

### Device Not Detected
1. Make sure USB debugging is enabled (Android)
2. Disconnect and reconnect the USB cable
3. Try a different USB port
4. Verify the webcam app is running on your mobile device

### Poor Performance
1. Try lower resolution settings in config.py
2. Ensure USB cable is properly connected
3. Check if USB port supports required bandwidth

### Common Issues
1. Black screen
   - Check if another application is using the camera
   - Restart the webcam app on your mobile device
   
2. Lag or delay
   - Reduce resolution in config.py
   - Check USB cable quality
   - Try different USB ports

3. Connection drops
   - Check USB cable connection
   - Verify USB debugging remains enabled
   - Keep mobile device screen on

## Integration with Main Application

To use the mobile camera in the main application:

```python
from src.utils.camera_manager import CameraManager

# Create camera manager
manager = CameraManager()

# List available devices
devices = manager.list_video_devices()

# Create mobile camera (replace with your device path)
mobile_cam = manager.create_mobile_camera("/dev/video2")

# Add to manager
manager.add_camera("mobile_cam", mobile_cam)
```

## Configuration Options

Mobile camera settings can be adjusted in `config.py`:

```python
CAMERA_CONFIG = {
    'mobile': {
        'default_resolution': {
            'width': 1280,
            'height': 720
        },
        'reconnect_attempts': 5,
        'reconnect_timeout': 3.0,
        'buffer_size': 2
    }
}
```

Adjust these settings based on your device capabilities and requirements.
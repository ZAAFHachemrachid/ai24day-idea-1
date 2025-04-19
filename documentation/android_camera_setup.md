# Android Phone Camera Setup Guide

## Prerequisites

1. Android phone with USB cable
2. USB webcam app (recommended options):
   - DroidCam
   - IP Webcam
   - USB Camera Pro

## Setup Steps

1. **Install USB Webcam App**
   - Install one of the recommended apps from Play Store
   - Launch the app and grant required permissions

2. **Enable USB Debugging**
   ```
   1. Go to Settings
   2. Scroll to "About phone"
   3. Find "Build number"
   4. Tap "Build number" 7 times to enable Developer Options
   5. Go back to Settings
   6. Find "Developer options"
   7. Enable "USB debugging"
   ```

3. **Connect Phone**
   1. Connect phone via USB cable
   2. Select "USB for..." notification when it appears
   3. Choose "File Transfer" or "PTP" mode
   4. Allow USB debugging when prompted

4. **App Configuration**
   1. Open the webcam app
   2. Select USB connection mode (if available)
   3. Grant any additional permissions requested

## Troubleshooting

### Phone Not Detected
1. Check USB cable connection
2. Verify USB debugging is enabled
3. Try different USB ports
4. Check phone notifications for USB configuration
5. Try disconnecting and reconnecting the cable

### Permission Issues
1. Check Android USB debugging prompt
2. Grant all permissions requested by the webcam app
3. Try toggling USB debugging off and on
4. Restart the phone if needed

### DroidCam Specific Setup
1. Install DroidCam from Play Store
2. Enable USB debugging
3. Connect via USB
4. Choose "File Transfer" mode
5. Launch DroidCam
6. Select "USB" connection mode
7. Device should appear as `/dev/video2` or similar

### IP Webcam Specific Setup
1. Install IP Webcam from Play Store
2. Enable USB debugging
3. Connect via USB
4. Start server in the app
5. Choose "USB mode" if available

## Common Issues

1. **Black Screen**
   - Check if camera is in use by another app
   - Restart the webcam app
   - Toggle USB debugging

2. **No Device Found**
   - Verify USB debugging is enabled
   - Check USB connection mode
   - Try different USB ports
   - Restart phone and computer

3. **Permission Denied**
   - Grant all requested permissions
   - Check USB debugging authorization
   - Reinstall webcam app if needed

## Testing Connection

After setup:
```bash
# List video devices
ls /dev/video*

# Should show something like:
# /dev/video0 /dev/video1 /dev/video2

# Run the example
python examples/mobile_camera_example.py
```

Make sure to select the correct video device when prompted (usually the highest number).
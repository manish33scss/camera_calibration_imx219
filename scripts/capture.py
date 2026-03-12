#!/usr/bin/env python3
"""
Simple Camera Capture with Live Preview
Press 'b' to capture current frame
Press 'q' to quit
"""

import cv2
import os
import time
from datetime import datetime

gst_pipeline = (
    "nvarguscamerasrc ! "
    "video/x-raw(memory:NVMM), width=640, height=480, framerate=30/1 ! "
    "nvvidconv flip-method=2 ! "
    "nvvidconv ! video/x-raw, format=BGRx ! "
    "videoconvert ! video/x-raw, format=BGR ! appsink"
)

# Open camera
print("Opening camera...")
cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("ERROR: Failed to open camera")
    exit(1)

print("Camera opened successfully!")
print("\nControls:")
print("  'b' - capture current frame")
print("  'q' - quit")
print("-" * 40)

# Create captures directory
capture_dir = "captures"
os.makedirs(capture_dir, exist_ok=True)
print(f"Images will be saved to: {capture_dir}/")

frame_count = 0

try:
    while True:
        # Read frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
         
        display_frame = frame.copy()
        cv2.putText(display_frame, "Press 'b' to capture, 'q' to quit", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(display_frame, f"Captured: {frame_count} images", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
       
        cv2.imshow('Camera Preview - Press b to capture', display_frame)
        
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\nQuitting...")
            break
            
        elif key == ord('b'):
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{capture_dir}/capture_{timestamp}.jpg"
            
            # Save the original frame  
            cv2.imwrite(filename, frame)
            frame_count += 1
            print(f"  ✓ Captured: {filename}")

except KeyboardInterrupt:
    print("\n\nInterrupted by user")

finally:
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print(f"\nDone! {frame_count} images saved to {capture_dir}/")

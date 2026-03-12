#!/usr/bin/env python3
"""
Calibrated Camera Viewer with Interactive ROI Selection
- Live calibrated video
- Press 's' to freeze frame and select ROI by clicking 4 corners
- Shows side-by-side view: Original (left) vs ROI-cropped (right)
- ROI is saved and loaded automatically
"""

import cv2
import numpy as np
import json
import os
from datetime import datetime

class CalibratedROISelector:
    def __init__(self, calib_file='calibration.json', roi_file='roi_settings.json'):
        # Load calibration
        with open(calib_file, 'r') as f:
            calib = json.load(f)
        
        self.camera_matrix = np.array(calib['camera_matrix'])
        self.dist_coeffs = np.array(calib['distortion_coefficients'])
        
        # Camera settings
        self.width, self.height = 640, 480
        
        # Create undistortion maps
        self.new_camera_matrix, _ = cv2.getOptimalNewCameraMatrix(
            self.camera_matrix, self.dist_coeffs, (self.width, self.height), 0.3, (self.width, self.height)
        )
        
        self.mapx, self.mapy = cv2.initUndistortRectifyMap(
            self.camera_matrix, self.dist_coeffs, None, self.new_camera_matrix, 
            (self.width, self.height), 5
        )
        
        # ROI settings
        self.roi_file = roi_file
        self.roi_corners = None
        self.use_roi = False
        self.show_side_by_side = True  # Show side-by-side view
        
        # Load saved ROI if exists
        self.load_roi()
        
        # ROI selection state
        self.selecting_roi = False
        self.selected_points = []
        self.frozen_frame = None
        
        # Initialize camera
        self.init_camera()
    
    def init_camera(self):
        """Initialize GStreamer pipeline"""
        gst_pipeline = (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), width=640, height=480, framerate=30/1 ! "
            "nvvidconv flip-method=2 ! "
            "nvvidconv ! video/x-raw, format=BGRx ! "
            "videoconvert ! video/x-raw, format=BGR ! appsink"
        )
        
        self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera")
    
    def load_roi(self):
        """Load saved ROI corners"""
        if os.path.exists(self.roi_file):
            try:
                with open(self.roi_file, 'r') as f:
                    data = json.load(f)
                    self.roi_corners = np.array(data['corners'], dtype=np.int32)
                    self.use_roi = True
                    print(f" Loaded ROI: {self.roi_corners.tolist()}")
            except Exception as e:
                print(f"⚠️ Failed to load ROI: {e}")
    
    def save_roi(self):
        """Save ROI corners to file"""
        if self.roi_corners is not None:
            data = {
                'corners': self.roi_corners.tolist(),
                'timestamp': datetime.now().isoformat(),
                'image_size': [self.width, self.height]
            }
            with open(self.roi_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f" ROI saved to {self.roi_file}")
    
    def mouse_callback(self, event, x, y, flags, param):
        """Mouse callback for ROI selection"""
        if event == cv2.EVENT_LBUTTONDOWN and len(self.selected_points) < 4:
            self.selected_points.append([x, y])
            print(f"  Point {len(self.selected_points)}: ({x}, {y})")
            
            # Draw point
            cv2.circle(self.frozen_frame, (x, y), 5, (0, 255, 0), -1)
            
            # Draw lines between points
            if len(self.selected_points) > 1:
                cv2.line(self.frozen_frame, 
                        tuple(self.selected_points[-2]), 
                        tuple(self.selected_points[-1]), 
                        (0, 255, 0), 2)
            
            # If we have 4 points, close the polygon
            if len(self.selected_points) == 4:
                cv2.line(self.frozen_frame,
                        tuple(self.selected_points[-1]),
                        tuple(self.selected_points[0]),
                        (0, 255, 0), 2)
                
                # Fill with semi-transparent overlay
                overlay = self.frozen_frame.copy()
                cv2.fillPoly(overlay, [np.array(self.selected_points)], (0, 255, 0))
                cv2.addWeighted(overlay, 0.2, self.frozen_frame, 0.8, 0, self.frozen_frame)
                
                print("\nROI selected! Press:")
                print("  'y' - accept and save (will show side-by-side view)")
                print("  'r' - reset selection")
            
            cv2.imshow('ROI Selection - Click 4 Corners', self.frozen_frame)
    
    def select_roi_interactive(self, frame):
        """Freeze frame and let user select ROI by clicking"""
        self.frozen_frame = frame.copy()
        self.selected_points = []
        self.selecting_roi = True
        
        cv2.namedWindow('ROI Selection - Click 4 Corners')
        cv2.setMouseCallback('ROI Selection - Click 4 Corners', self.mouse_callback)
        
        # Instructions overlay
        h, w = self.frozen_frame.shape[:2]
        cv2.putText(self.frozen_frame, "Click 4 corners in order (clockwise)", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(self.frozen_frame, "Points selected: 0/4", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        while self.selecting_roi:
            # Update point counter
            display_frame = self.frozen_frame.copy()
            cv2.putText(display_frame, f"Points selected: {len(self.selected_points)}/4", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow('ROI Selection - Click 4 Corners', display_frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                self.selecting_roi = False
                return None
            elif key == ord('r'):
                # Reset selection
                self.frozen_frame = frame.copy()
                self.selected_points = []
                print(" Selection reset")
            elif key == ord('y') and len(self.selected_points) == 4:
                # Accept selection
                self.roi_corners = np.array(self.selected_points, dtype=np.int32)
                self.use_roi = True
                self.show_side_by_side = True
                self.save_roi()
                self.selecting_roi = False
                cv2.destroyWindow('ROI Selection - Click 4 Corners')
                print("\nROI accepted! Switching to side-by-side view...")
                return self.roi_corners
        
        cv2.destroyWindow('ROI Selection - Click 4 Corners')
        return None
    
    def apply_roi(self, frame):
        """Apply ROI crop to frame"""
        if self.roi_corners is not None and self.use_roi:
            # Get bounding rectangle of ROI
            x, y, w, h = cv2.boundingRect(self.roi_corners)
            
            # Crop to bounding box
            cropped = frame[y:y+h, x:x+w]
            
            # Resize back to original dimensions
            if cropped.size > 0:
                return cv2.resize(cropped, (self.width, self.height))
        return frame
    
    def create_side_by_side(self, original, roi_applied):
        """Create side-by-side view of original and ROI-cropped video"""
        # Make copies to avoid modifying originals
        left = original.copy()
        right = roi_applied.copy()
        
        # Add labels
        h, w = left.shape[:2]
        
        # Left side (Original)
        cv2.putText(left, "ORIGINAL", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw ROI outline on original if active
        if self.roi_corners is not None and self.use_roi:
            cv2.polylines(left, [self.roi_corners], True, (0, 255, 0), 2)
        
        # Right side (ROI)
        cv2.putText(right, "ROI CROPPED", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Stack horizontally
        side_by_side = np.hstack((left, right))
        
        # Add instructions at bottom
        cv2.putText(side_by_side, "Press 'v' to toggle view | 's' new ROI | 'r' toggle ROI | 'q' quit", 
                   (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return side_by_side
    
    def draw_roi_outline(self, frame):
        """Draw ROI outline on frame"""
        if self.roi_corners is not None and self.use_roi:
            cv2.polylines(frame, [self.roi_corners], True, (0, 255, 0), 2)
        return frame
    
    def run(self):
        """Main loop"""
        print("\n" + "="*70)
        print("CALIBRATED CAMERA WITH SIDE-BY-SIDE ROI VIEW")
        print("="*70)
        print("Controls:")
        print("  's' - freeze frame and select ROI (click 4 corners)")
        print("  'y' - accept ROI (switches to side-by-side view)")
        print("  'v' - toggle between side-by-side and single view")
        print("  'r' - toggle ROI on/off")
        print("  'c' - clear ROI")
        print("  'q' - quit")
        print("="*70)
        
        if self.roi_corners is not None:
            print(f"\n Active ROI: {self.roi_corners.tolist()}")
            print(" Showing side-by-side view")
        
        while True:
            # Read frame
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Apply undistortion
            undistorted = cv2.remap(frame, self.mapx, self.mapy, cv2.INTER_LINEAR)
            
            # Create ROI-applied version
            roi_frame = self.apply_roi(undistorted.copy())
            
            # Determine what to display
            if self.show_side_by_side and self.roi_corners is not None and self.use_roi:
                # Side-by-side view
                display_frame = self.create_side_by_side(undistorted, roi_frame)
            else:
                # Single view
                display_frame = roi_frame if self.use_roi else undistorted
                display_frame = self.draw_roi_outline(display_frame)
                
                # Add info text
                cv2.putText(display_frame, f"Mode: {'ROI' if self.use_roi else 'Original'}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                           (0, 255, 0) if self.use_roi else (255, 255, 255), 2)
                cv2.putText(display_frame, "Press 'v' for side-by-side", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show frame
            cv2.imshow('Calibrated Camera - Side-by-Side ROI', display_frame)
            
            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Freeze frame and select ROI
                print("\n ROI Selection Mode:")
                print("  Click 4 corners in clockwise order")
                print("  Press 'y' to accept, 'r' to reset, 'q' to cancel")
                self.select_roi_interactive(undistorted)
            elif key == ord('v'):
                # Toggle side-by-side view
                self.show_side_by_side = not self.show_side_by_side
                mode = "side-by-side" if self.show_side_by_side else "single"
                print(f"Switched to {mode} view")
            elif key == ord('r'):
                # Toggle ROI
                if self.roi_corners is not None:
                    self.use_roi = not self.use_roi
                    print(f"ROI {'enabled' if self.use_roi else 'disabled'}")
            elif key == ord('c'):
                # Clear ROI
                self.roi_corners = None
                self.use_roi = False
                self.show_side_by_side = False
                if os.path.exists(self.roi_file):
                    os.remove(self.roi_file)
                print(" ROI cleared")
        
        self.cap.release()
        cv2.destroyAllWindows()

def main():
    # Check for calibration file
    if not os.path.exists('calibration.json'):
        print("calibration.json not found!")
        print("Please run calibration first.")
        return 1
    
    # Create ROI selector
    selector = CalibratedROISelector(
        calib_file='calibration.json',
        roi_file='roi_settings.json'
    )
    
    # Run
    selector.run()
    return 0

if __name__ == "__main__":
    exit(main())

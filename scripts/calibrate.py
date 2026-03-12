#!/usr/bin/env python3
"""
Simplified Camera Calibration Script
Works with your captured JPG images
run : python3 calibrate.py ./captures/ -x 9 -y 6 --preview-corners
"""

import numpy as np
import cv2
import glob
import os
import argparse
import json

def detect_corners(image_dir, grid_x, grid_y, grid_size, use_sb_alg=False):
    """
    Detect chessboard corners in all images
    """
    # 3D points of chessboard corners in world space
    objp = np.zeros((grid_x * grid_y, 3), np.float32)
    objp[:, :2] = np.mgrid[0:grid_x, 0:grid_y].T.reshape(-1, 2) * grid_size
    
    # Arrays to store object points and image points
    objpoints = []  # 3D points in real world
    imgpoints = []  # 2D points in image plane
    valid_images = []
    
    # Get all JPG images
    images = glob.glob(os.path.join(image_dir, '*.jpg'))
    images.sort()
    
    print(f"Found {len(images)} images")
    print("-" * 50)
    
    for fname in images:
        print(f"Processing {os.path.basename(fname)}... ", end='', flush=True)
        
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Find chessboard corners
        if use_sb_alg:
            ret, corners = cv2.findChessboardCornersSB(gray, (grid_x, grid_y))
        else:
            ret, corners = cv2.findChessboardCorners(gray, (grid_x, grid_y))
            
            if ret:
                # Refine corners to subpixel accuracy
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        
        if ret:
            print("✓ corners found")
            objpoints.append(objp)
            imgpoints.append(corners)
            valid_images.append(fname)
        else:
            print("✗ no corners detected")
    
    print("-" * 50)
    print(f"Successfully detected corners in {len(valid_images)}/{len(images)} images")
    
    # Show which images worked
    if len(valid_images) < len(images):
        print("\nFailed images:")
        for img in set(images) - set(valid_images):
            print(f"  - {os.path.basename(img)}")
    
    return objpoints, imgpoints, valid_images

def calibrate_camera(objpoints, imgpoints, image_shape):
    """
    Perform camera calibration
    """
    print("\nCalibrating camera...")
    
    h, w = image_shape[:2]
    
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, (w, h), None, None
    )
    
    if not ret:
        print("Calibration failed!")
        return None
    
    # Calculate reprojection error
    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        mean_error += error
    
    print(f"Reprojection error: {mean_error/len(objpoints):.4f} pixels")
    print(f"  (< 0.5 is excellent, < 1.0 is good)")
    
    # Get optimal camera matrix
    optimal_matrix, roi = cv2.getOptimalNewCameraMatrix(
        camera_matrix, dist_coeffs, (w, h), 1, (w, h)
    )
    
    return {
        'camera_matrix': camera_matrix,
        'dist_coeffs': dist_coeffs,
        'optimal_matrix': optimal_matrix,
        'roi': roi,
        'rvecs': rvecs,
        'tvecs': tvecs,
        'image_size': (w, h)
    }

def save_results(calib_results, output_file):
    """
    Save calibration results to JSON file
    """
    results = {
        'camera_matrix': calib_results['camera_matrix'].tolist(),
        'distortion_coefficients': calib_results['dist_coeffs'].tolist(),
        'optimal_camera_matrix': calib_results['optimal_matrix'].tolist(),
        'roi': calib_results['roi'],
        'image_width': calib_results['image_size'][0],
        'image_height': calib_results['image_size'][1],
        'reprojection_error': calib_results.get('reprojection_error', 0)
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")

def preview_corners(image_dir, valid_images, grid_x, grid_y, imgpoints):
    """
    Preview detected corners on images
    """
    print("\nPreviewing corners (press any key to continue, 'q' to quit)")
    
    for fname, corners in zip(valid_images, imgpoints):
        img = cv2.imread(fname)
        cv2.drawChessboardCorners(img, (grid_x, grid_y), corners, True)
        
        cv2.imshow('Detected Corners', img)
        key = cv2.waitKey(0)
        if key == ord('q'):
            break
    
    cv2.destroyAllWindows()

def preview_undistorted(image_dir, valid_images, calib_results):
    """
    Preview undistorted vs original images
    """
    print("\nPreviewing undistorted images (press any key to continue, 'q' to quit)")
    
    camera_matrix = calib_results['camera_matrix']
    dist_coeffs = calib_results['dist_coeffs']
    optimal_matrix = calib_results['optimal_matrix']
    
    for fname in valid_images:
        img = cv2.imread(fname)
        h, w = img.shape[:2]
        
        # Undistort
        dst = cv2.undistort(img, camera_matrix, dist_coeffs, None, optimal_matrix)
        
        # Show side by side
        combined = np.hstack((img, dst))
        
        # Add labels
        cv2.putText(combined, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(combined, "Undistorted", (w + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow('Original vs Undistorted', combined)
        key = cv2.waitKey(0)
        if key == ord('q'):
            break
    
    cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description='Camera calibration from captured images')
    parser.add_argument('image_dir', help='Directory containing calibration images')
    parser.add_argument('-x', '--grid-x', type=int, default=9, 
                        help='Number of inner corners in X direction (default: 9)')
    parser.add_argument('-y', '--grid-y', type=int, default=6,
                        help='Number of inner corners in Y direction (default: 6)')
    parser.add_argument('-s', '--square-size', type=float, default=0.025,
                        help='Size of chessboard squares in meters (default: 0.025)')
    parser.add_argument('-o', '--output', default='calibration.json',
                        help='Output JSON file (default: calibration.json)')
    parser.add_argument('--preview-corners', action='store_true',
                        help='Preview detected corners')
    parser.add_argument('--preview-undistorted', action='store_true',
                        help='Preview undistorted images')
    parser.add_argument('--use-sb', action='store_true',
                        help='Use sector-based corner detection algorithm')
    
    args = parser.parse_args()
    
    # Check if directory exists
    if not os.path.exists(args.image_dir):
        print(f"Error: Directory '{args.image_dir}' not found")
        return 1
    
    print("=" * 60)
    print("CAMERA CALIBRATION")
    print("=" * 60)
    print(f"Image directory: {args.image_dir}")
    print(f"Chessboard: {args.grid_x}x{args.grid_y} corners")
    print(f"Square size: {args.square_size} m")
    print("-" * 60)
    
    # Step 1: Detect corners
    objpoints, imgpoints, valid_images = detect_corners(
        args.image_dir, args.grid_x, args.grid_y, args.square_size, args.use_sb
    )
    
    if len(objpoints) < 5:
        print("\nNeed at least 5 good images for calibration")
        return 1
    
    # Step 2: Preview corners if requested
    if args.preview_corners and valid_images:
        preview_corners(args.image_dir, valid_images, args.grid_x, args.grid_y, imgpoints)
    
    # Step 3: Run calibration
    test_img = cv2.imread(valid_images[0])
    calib_results = calibrate_camera(objpoints, imgpoints, test_img.shape)
    
    if calib_results is None:
        return 1
    
    # Step 4: Print results
    print("\n" + "=" * 60)
    print("CALIBRATION RESULTS")
    print("=" * 60)
    print("\nCamera Matrix:")
    print(calib_results['camera_matrix'])
    print("\nDistortion Coefficients (k1, k2, p1, p2, k3):")
    print(calib_results['dist_coeffs'].ravel())
    
    # Step 5: Preview undistorted if requested
    if args.preview_undistorted and valid_images:
        preview_undistorted(args.image_dir, valid_images, calib_results)
    
    # Step 6: Save results
    save_results(calib_results, args.output)
    
    return 0

if __name__ == "__main__":
    exit(main())

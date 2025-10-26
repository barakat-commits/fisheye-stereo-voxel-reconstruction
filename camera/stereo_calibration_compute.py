"""
Stereo Calibration Computation

Computes stereo calibration parameters from captured image pairs.
Outputs calibration files for use in 3D reconstruction.
"""

import cv2
import numpy as np
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def load_capture_data():
    """Load captured calibration images."""
    capture_file = Path("camera/stereo_calibration_images/capture_list.json")
    
    if not capture_file.exists():
        print(f"Error: {capture_file} not found")
        print("Run stereo_calibration_capture.py first!")
        return None
    
    with open(capture_file, 'r') as f:
        data = json.load(f)
    
    print(f"Loaded {data['num_captures']} image pairs")
    print(f"Checkerboard size: {data['checkerboard_size']}")
    
    return data


def prepare_object_points(checkerboard_size, square_size=1.0):
    """
    Prepare 3D object points for checkerboard.
    
    Args:
        checkerboard_size: (cols, rows) of inner corners
        square_size: Size of each square (default 1.0 for arbitrary units)
    
    Returns:
        objp: 3D points in checkerboard coordinate system
    """
    objp = np.zeros((checkerboard_size[0] * checkerboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:checkerboard_size[0],
                           0:checkerboard_size[1]].T.reshape(-1, 2)
    objp *= square_size
    
    return objp


def stereo_calibrate(capture_data):
    """
    Perform stereo calibration.
    
    Returns:
        Calibration parameters
    """
    checkerboard_size = tuple(capture_data['checkerboard_size'])
    captures = capture_data['captures']
    
    # Prepare object points
    objp = prepare_object_points(checkerboard_size)
    
    # Arrays to store points
    objpoints = []  # 3D points in real world space
    imgpoints_left = []  # 2D points in left image
    imgpoints_right = []  # 2D points in right image
    
    # Image size
    img_left = cv2.imread(captures[0]['left_image'], cv2.IMREAD_GRAYSCALE)
    image_size = img_left.shape[::-1]  # (width, height)
    
    print(f"\nImage size: {image_size}")
    print(f"Processing {len(captures)} image pairs...")
    
    # Load all corner data
    for i, capture in enumerate(captures):
        corners_left = np.array(capture['left_corners'], dtype=np.float32)
        corners_right = np.array(capture['right_corners'], dtype=np.float32)
        
        objpoints.append(objp)
        imgpoints_left.append(corners_left)
        imgpoints_right.append(corners_right)
        
        print(f"  [{i+1}/{len(captures)}] Loaded")
    
    print("\nPerforming stereo calibration...")
    print("This may take a minute...")
    
    # Calibration flags
    flags = cv2.CALIB_FIX_INTRINSIC
    
    # Stereo calibration
    ret, camera_matrix_left, dist_left, camera_matrix_right, dist_right, R, T, E, F = cv2.stereoCalibrate(
        objpoints,
        imgpoints_left,
        imgpoints_right,
        None, None,  # No initial camera matrices
        None, None,  # No initial distortion
        image_size,
        criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5),
        flags=0  # Calibrate everything
    )
    
    print(f"\n[OK] Stereo calibration complete!")
    print(f"RMS error: {ret:.4f} pixels")
    
    # Compute rectification
    print("\nComputing rectification...")
    
    R1, R2, P1, P2, Q, roi_left, roi_right = cv2.stereoRectify(
        camera_matrix_left, dist_left,
        camera_matrix_right, dist_right,
        image_size, R, T,
        alpha=0  # 0 = crop to valid pixels only
    )
    
    print("[OK] Rectification computed")
    
    return {
        'rms_error': ret,
        'image_size': image_size,
        'camera_matrix_left': camera_matrix_left,
        'dist_left': dist_left,
        'camera_matrix_right': camera_matrix_right,
        'dist_right': dist_right,
        'R': R,  # Rotation from left to right camera
        'T': T,  # Translation from left to right camera
        'E': E,  # Essential matrix
        'F': F,  # Fundamental matrix
        'R1': R1,  # Rectification transform (left)
        'R2': R2,  # Rectification transform (right)
        'P1': P1,  # Projection matrix (left)
        'P2': P2,  # Projection matrix (right)
        'Q': Q,   # Disparity-to-depth mapping matrix
        'roi_left': roi_left,
        'roi_right': roi_right
    }


def save_calibration(calib_data):
    """Save calibration to files."""
    output_dir = Path("camera")
    
    # Save as YAML (OpenCV format)
    yaml_file = output_dir / "stereo_calibration.yml"
    
    fs = cv2.FileStorage(str(yaml_file), cv2.FILE_STORAGE_WRITE)
    
    fs.write('rms_error', calib_data['rms_error'])
    fs.write('image_width', int(calib_data['image_size'][0]))
    fs.write('image_height', int(calib_data['image_size'][1]))
    
    fs.write('camera_matrix_left', calib_data['camera_matrix_left'])
    fs.write('distortion_left', calib_data['dist_left'])
    fs.write('camera_matrix_right', calib_data['camera_matrix_right'])
    fs.write('distortion_right', calib_data['dist_right'])
    
    fs.write('R', calib_data['R'])
    fs.write('T', calib_data['T'])
    fs.write('E', calib_data['E'])
    fs.write('F', calib_data['F'])
    
    fs.write('R1', calib_data['R1'])
    fs.write('R2', calib_data['R2'])
    fs.write('P1', calib_data['P1'])
    fs.write('P2', calib_data['P2'])
    fs.write('Q', calib_data['Q'])
    
    fs.release()
    
    print(f"\n[SAVED] Calibration: {yaml_file}")
    
    # Also save as JSON for easy reading
    json_file = output_dir / "stereo_calibration.json"
    
    json_data = {
        'rms_error': float(calib_data['rms_error']),
        'image_size': calib_data['image_size'],
        'camera_matrix_left': calib_data['camera_matrix_left'].tolist(),
        'distortion_left': calib_data['dist_left'].tolist(),
        'camera_matrix_right': calib_data['camera_matrix_right'].tolist(),
        'distortion_right': calib_data['dist_right'].tolist(),
        'R': calib_data['R'].tolist(),
        'T': calib_data['T'].tolist(),
        'baseline_meters': float(np.linalg.norm(calib_data['T']))
    }
    
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"[SAVED] JSON: {json_file}")
    
    return yaml_file, json_file


def print_summary(calib_data):
    """Print calibration summary."""
    print("\n" + "="*70)
    print("  STEREO CALIBRATION SUMMARY")
    print("="*70)
    print()
    print(f"RMS Error: {calib_data['rms_error']:.4f} pixels")
    if calib_data['rms_error'] < 0.5:
        print("  Excellent! (<0.5 pixels)")
    elif calib_data['rms_error'] < 1.0:
        print("  Good! (<1.0 pixel)")
    else:
        print("  Acceptable (might want to recapture)")
    print()
    
    # Baseline
    baseline = np.linalg.norm(calib_data['T'])
    print(f"Baseline (camera separation): {baseline:.4f} meters ({baseline*100:.2f} cm)")
    print(f"  Expected: ~0.50m (50cm)")
    if abs(baseline - 0.5) < 0.05:
        print("  Match! Correct!")
    else:
        print(f"  Difference: {(baseline - 0.5)*100:+.1f}cm")
    print()
    
    # Rotation
    R = calib_data['R']
    rotation_angle = np.arccos((np.trace(R) - 1) / 2) * 180 / np.pi
    print(f"Relative rotation: {rotation_angle:.2f} degrees")
    if rotation_angle < 5:
        print("  Good! Cameras nearly parallel")
    else:
        print("  Warning: Large rotation - check camera mounting")
    print()
    
    # LEFT camera
    print("LEFT Camera:")
    fx = calib_data['camera_matrix_left'][0, 0]
    fy = calib_data['camera_matrix_left'][1, 1]
    cx = calib_data['camera_matrix_left'][0, 2]
    cy = calib_data['camera_matrix_left'][1, 2]
    print(f"  fx={fx:.2f}, fy={fy:.2f}")
    print(f"  cx={cx:.2f}, cy={cy:.2f}")
    print(f"  Distortion: {calib_data['dist_left'].ravel()[:3]}")
    print()
    
    # RIGHT camera
    print("RIGHT Camera:")
    fx = calib_data['camera_matrix_right'][0, 0]
    fy = calib_data['camera_matrix_right'][1, 1]
    cx = calib_data['camera_matrix_right'][0, 2]
    cy = calib_data['camera_matrix_right'][1, 2]
    print(f"  fx={fx:.2f}, fy={fy:.2f}")
    print(f"  cx={cx:.2f}, cy={cy:.2f}")
    print(f"  Distortion: {calib_data['dist_right'].ravel()[:3]}")
    print()
    
    print("="*70)
    print("  NEXT STEPS")
    print("="*70)
    print()
    print("1. The calibration files are ready to use:")
    print("   - camera/stereo_calibration.yml")
    print("   - camera/stereo_calibration.json")
    print()
    print("2. I'll now update the stereo triangulation code to use these!")
    print()
    print("="*70)


def main():
    print("="*70)
    print("  STEREO CALIBRATION COMPUTATION")
    print("="*70)
    print()
    
    # Load captured data
    capture_data = load_capture_data()
    if capture_data is None:
        return
    
    print()
    
    # Perform calibration
    calib_data = stereo_calibrate(capture_data)
    
    # Save results
    yaml_file, json_file = save_calibration(calib_data)
    
    # Print summary
    print_summary(calib_data)


if __name__ == "__main__":
    main()




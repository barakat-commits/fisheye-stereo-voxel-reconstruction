"""
ArUco Stereo Calibration Computer

Processes captured ArUco images and computes stereo calibration.
"""

import cv2
import numpy as np
import json
from pathlib import Path


def load_captures(calib_dir):
    """
    Load capture metadata and images.
    """
    calib_dir = Path(calib_dir)
    
    # Load metadata
    with open(calib_dir / 'captures.json', 'r') as f:
        metadata = json.load(f)
    
    print(f"Found {len(metadata['captures'])} captures")
    
    # Load images
    image_pairs = []
    for capture in metadata['captures']:
        cap_id = capture['id']
        img_left = cv2.imread(str(calib_dir / f"left_{cap_id:03d}.png"), cv2.IMREAD_GRAYSCALE)
        img_right = cv2.imread(str(calib_dir / f"right_{cap_id:03d}.png"), cv2.IMREAD_GRAYSCALE)
        
        if img_left is not None and img_right is not None:
            image_pairs.append((img_left, img_right))
    
    print(f"Loaded {len(image_pairs)} image pairs")
    
    return metadata, image_pairs


def detect_aruco_in_images(image_pairs, board_config):
    """
    Detect ArUco markers in all image pairs.
    """
    # Setup ArUco detection (compatible with OpenCV 4.7+)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    aruco_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)
    
    board = cv2.aruco.GridBoard(
        (board_config['markers_x'], board_config['markers_y']),
        board_config['marker_length'],
        board_config['marker_separation'],
        aruco_dict
    )
    
    # Detect in all images
    all_corners_left = []
    all_ids_left = []
    all_corners_right = []
    all_ids_right = []
    valid_pairs = []
    
    print("\nDetecting ArUco markers...")
    for i, (img_left, img_right) in enumerate(image_pairs):
        # Detect left
        corners_left, ids_left, _ = detector.detectMarkers(img_left)
        
        # Detect right
        corners_right, ids_right, _ = detector.detectMarkers(img_right)
        
        # Refine detections
        if ids_left is not None and len(ids_left) > 0:
            corners_left, ids_left, _, _ = detector.refineDetectedMarkers(
                img_left, board, corners_left, ids_left, []
            )
        
        if ids_right is not None and len(ids_right) > 0:
            corners_right, ids_right, _, _ = detector.refineDetectedMarkers(
                img_right, board, corners_right, ids_right, []
            )
        
        # Only use pairs where both cameras detected markers
        if ids_left is not None and ids_right is not None:
            if len(ids_left) >= 10 and len(ids_right) >= 10:
                all_corners_left.append(corners_left)
                all_ids_left.append(ids_left)
                all_corners_right.append(corners_right)
                all_ids_right.append(ids_right)
                valid_pairs.append(i)
                print(f"  [{i:2d}] L:{len(ids_left):2d} R:{len(ids_right):2d} markers [OK]")
            else:
                print(f"  [{i:2d}] L:{len(ids_left):2d} R:{len(ids_right):2d} markers (too few)")
        else:
            print(f"  [{i:2d}] No markers detected")
    
    print(f"\nValid pairs: {len(valid_pairs)}/{len(image_pairs)}")
    
    return all_corners_left, all_ids_left, all_corners_right, all_ids_right, board


def calibrate_camera_aruco(corners_list, ids_list, board, image_size):
    """
    Calibrate a single camera using ArUco detections.
    """
    # Get board object points
    board_obj_points = board.getObjPoints()
    
    # Extract object and image points from ArUco detections
    object_points = []
    image_points = []
    
    for corners, ids in zip(corners_list, ids_list):
        if ids is not None and len(ids) > 0:
            # For this image, collect all corner points
            obj_pts = []
            img_pts = []
            
            for i, marker_id in enumerate(ids):
                marker_id = marker_id[0]
                
                # Get the 4 corners of this marker from board definition
                # board_obj_points[marker_id] is a (4, 3) array of 3D corners
                marker_corners_3d = board_obj_points[marker_id]
                marker_corners_2d = corners[i][0]  # corners[i] shape is (1, 4, 2), so corners[i][0] is (4, 2)
                
                # Add all 4 corners
                for j in range(4):
                    obj_pts.append(marker_corners_3d[j])
                    img_pts.append(marker_corners_2d[j])
            
            if len(obj_pts) > 0:
                # Reshape to (N, 1, 3) and (N, 1, 2) as expected by calibrateCamera
                obj_arr = np.array(obj_pts, dtype=np.float32).reshape(-1, 1, 3)
                img_arr = np.array(img_pts, dtype=np.float32).reshape(-1, 1, 2)
                object_points.append(obj_arr)
                image_points.append(img_arr)
    
    if len(object_points) == 0:
        return None, None, None
    
    # Calibrate using standard cv2.calibrateCamera
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        object_points,
        image_points,
        image_size,
        None,
        None
    )
    
    return camera_matrix, dist_coeffs, ret


def calibrate_stereo_aruco(corners_left, ids_left, corners_right, ids_right,
                          board, image_size, camera_matrix_left, dist_left,
                          camera_matrix_right, dist_right):
    """
    Perform stereo calibration using ArUco detections.
    """
    # Get board object points
    board_obj_points = board.getObjPoints()
    
    # Prepare matching object and image points
    object_points = []
    image_points_left = []
    image_points_right = []
    
    for i in range(len(corners_left)):
        # Find common markers between left and right cameras
        ids_l_set = set(ids_left[i][:,0])
        ids_r_set = set(ids_right[i][:,0])
        common_ids = sorted(ids_l_set & ids_r_set)
        
        if len(common_ids) < 4:  # Need at least 4 common markers
            continue
        
        # Build dictionaries for quick lookup
        left_dict = {ids_left[i][j,0]: j for j in range(len(ids_left[i]))}
        right_dict = {ids_right[i][j,0]: j for j in range(len(ids_right[i]))}
        
        # Extract points for common markers only
        obj_pts = []
        img_pts_l = []
        img_pts_r = []
        
        for marker_id in common_ids:
            marker_corners_3d = board_obj_points[marker_id]
            
            # Get corners from left camera
            left_idx = left_dict[marker_id]
            marker_corners_2d_left = corners_left[i][left_idx][0]
            
            # Get corners from right camera
            right_idx = right_dict[marker_id]
            marker_corners_2d_right = corners_right[i][right_idx][0]
            
            # Add all 4 corners
            for k in range(4):
                obj_pts.append(marker_corners_3d[k])
                img_pts_l.append(marker_corners_2d_left[k])
                img_pts_r.append(marker_corners_2d_right[k])
        
        if len(obj_pts) > 0:
            # Reshape to (N, 1, 3) and (N, 1, 2) as expected by stereoCalibrate
            obj_arr = np.array(obj_pts, dtype=np.float32).reshape(-1, 1, 3)
            img_l_arr = np.array(img_pts_l, dtype=np.float32).reshape(-1, 1, 2)
            img_r_arr = np.array(img_pts_r, dtype=np.float32).reshape(-1, 1, 2)
            object_points.append(obj_arr)
            image_points_left.append(img_l_arr)
            image_points_right.append(img_r_arr)
    
    print(f"\nStereo calibration with {len(object_points)} image pairs...")
    
    # Stereo calibration
    flags = cv2.CALIB_FIX_INTRINSIC
    
    ret, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(
        object_points,
        image_points_left,
        image_points_right,
        camera_matrix_left,
        dist_left,
        camera_matrix_right,
        dist_right,
        image_size,
        flags=flags
    )
    
    return ret, R, T, E, F


def main():
    print("="*70)
    print("  ARUCO STEREO CALIBRATION COMPUTER")
    print("="*70)
    print()
    
    calib_dir = Path("camera/aruco_calibration")
    
    if not (calib_dir / 'captures.json').exists():
        print("ERROR: No captures found!")
        print(f"Expected: {calib_dir}/captures.json")
        print()
        print("Run this first:")
        print("  python camera\\aruco_stereo_capture.py")
        return
    
    # Load captures
    print("Loading captures...")
    metadata, image_pairs = load_captures(calib_dir)
    board_config = metadata['board']
    
    if len(image_pairs) < 10:
        print(f"\n⚠️  WARNING: Only {len(image_pairs)} captures")
        print("Recommended: 20+ captures for good calibration")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Detect markers
    corners_left, ids_left, corners_right, ids_right, board = detect_aruco_in_images(
        image_pairs, board_config
    )
    
    if len(corners_left) < 10:
        print(f"\n[ERROR] Only {len(corners_left)} valid detections")
        print("Need at least 10 valid image pairs")
        print("Capture more images with better marker detection")
        return
    
    image_size = image_pairs[0][0].shape[::-1]  # (width, height)
    
    # Calibrate individual cameras
    print("\n" + "="*70)
    print("  INDIVIDUAL CAMERA CALIBRATION")
    print("="*70)
    
    print("\nCalibrating LEFT camera...")
    K_left, D_left, err_left = calibrate_camera_aruco(
        corners_left, ids_left, board, image_size
    )
    
    if K_left is None:
        print("[ERROR] Left camera calibration failed!")
        return
    
    print(f"[OK] Left camera calibrated (error: {err_left:.4f})")
    
    print("\nCalibrating RIGHT camera...")
    K_right, D_right, err_right = calibrate_camera_aruco(
        corners_right, ids_right, board, image_size
    )
    
    if K_right is None:
        print("[ERROR] Right camera calibration failed!")
        return
    
    print(f"[OK] Right camera calibrated (error: {err_right:.4f})")
    
    # Stereo calibration
    print("\n" + "="*70)
    print("  STEREO CALIBRATION")
    print("="*70)
    
    stereo_err, R, T, E, F = calibrate_stereo_aruco(
        corners_left, ids_left, corners_right, ids_right,
        board, image_size, K_left, D_left, K_right, D_right
    )
    
    print(f"[OK] Stereo calibration complete (error: {stereo_err:.4f})")
    
    # Save results
    print("\n" + "="*70)
    print("  CALIBRATION RESULTS")
    print("="*70)
    print()
    
    baseline = np.linalg.norm(T)
    print(f"Baseline (camera separation): {baseline:.4f}m ({baseline*100:.1f}cm)")
    print()
    print("Left Camera:")
    print(f"  fx: {K_left[0,0]:.2f}")
    print(f"  fy: {K_left[1,1]:.2f}")
    print(f"  cx: {K_left[0,2]:.2f}")
    print(f"  cy: {K_left[1,2]:.2f}")
    print(f"  k1: {D_left[0,0]:.6f}")
    print()
    print("Right Camera:")
    print(f"  fx: {K_right[0,0]:.2f}")
    print(f"  fy: {K_right[1,1]:.2f}")
    print(f"  cx: {K_right[0,2]:.2f}")
    print(f"  cy: {K_right[1,2]:.2f}")
    print(f"  k1: {D_right[0,0]:.6f}")
    print()
    print("Stereo:")
    print(f"  Rotation: {np.linalg.norm(cv2.Rodrigues(R)[0]):.4f} rad")
    print(f"  Translation: [{T[0,0]:.4f}, {T[1,0]:.4f}, {T[2,0]:.4f}]m")
    print()
    
    # Save to file
    output_file = calib_dir / "stereo_calibration.json"
    
    calibration_data = {
        'left_camera': {
            'camera_matrix': K_left.tolist(),
            'distortion': D_left.tolist(),
            'error': float(err_left)
        },
        'right_camera': {
            'camera_matrix': K_right.tolist(),
            'distortion': D_right.tolist(),
            'error': float(err_right)
        },
        'stereo': {
            'rotation': R.tolist(),
            'translation': T.tolist(),
            'essential': E.tolist(),
            'fundamental': F.tolist(),
            'error': float(stereo_err),
            'baseline': float(baseline)
        },
        'image_size': {
            'width': int(image_size[0]),
            'height': int(image_size[1])
        },
        'num_captures': len(corners_left)
    }
    
    with open(output_file, 'w') as f:
        json.dump(calibration_data, f, indent=2)
    
    print(f"[OK] Saved to: {output_file}")
    print()
    print("="*70)
    print("  SUCCESS!")
    print("="*70)
    print()
    print("You can now use this calibration for stereo reconstruction!")
    print()


if __name__ == "__main__":
    main()


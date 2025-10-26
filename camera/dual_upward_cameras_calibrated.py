"""
Dual Upward-Pointing Cameras with Calibration - 3D Reconstruction

Uses fisheye/wide-angle lens calibration for accurate undistortion.
"""

import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem
from calibration_loader import load_calibration
from utils.voxel_helpers import save_voxel_grid, print_grid_statistics


# Camera configuration
CAMERA_LEFT_POS = np.array([0.0, 0.0, 0.0])      # meters
CAMERA_RIGHT_POS = np.array([0.5, 0.0, 0.0])     # meters
BASELINE = 0.5  # meters


def pixel_to_voxel_calibrated(pixel_y, pixel_x, camera_calib, camera_pos,
                               grid_size=64, voxel_size=0.01):
    """
    Project pixel using calibrated camera model.
    
    Args:
        pixel_y, pixel_x: Pixel coordinates
        camera_calib: CameraCalibration object
        camera_pos: Camera position [x, y, z] in meters
        grid_size: Voxel grid dimension
        voxel_size: Voxel size in meters
    
    Returns:
        List of voxel coordinates (z, y, x) along the ray
    """
    # Get calibrated ray direction
    ray_dir = camera_calib.get_ray_direction(pixel_x, pixel_y)
    
    voxel_coords = []
    
    # Sample along ray at different heights above camera
    for height in np.arange(0.05, 0.8, voxel_size):
        # Solve for t where ray reaches this height
        # camera_pos + t * ray_dir = [?, height, ?]
        # camera_pos[1] + t * ray_dir[1] = height
        if abs(ray_dir[1]) < 0.01:  # Nearly horizontal ray
            continue
        
        t = (height - camera_pos[1]) / ray_dir[1]
        
        if t < 0:  # Behind camera
            continue
        
        # Point along ray
        point_3d = camera_pos + ray_dir * t
        
        # Convert to voxel grid coordinates
        # X: centered on baseline (-0.25 to +0.75m)
        # Y: height above ground (0 to +0.64m)
        # Z: depth from ground level (0 to +0.64m)
        vox_x = int((point_3d[0] + 0.25) / voxel_size)
        vox_y = int(point_3d[1] / voxel_size)
        vox_z = int(point_3d[2] / voxel_size)  # Z starts at 0 (ground level)
        
        # Check bounds
        if (0 <= vox_x < grid_size and 
            0 <= vox_y < grid_size and 
            0 <= vox_z < grid_size):
            voxel_coords.append((vox_z, vox_y, vox_x))
    
    return voxel_coords


def print_voxel_coordinate(vox_z, vox_y, vox_x, intensity, camera_name, voxel_size=0.01):
    """Print voxel coordinate with real-world position."""
    world_x = (vox_x * voxel_size) - 0.25
    world_y = vox_y * voxel_size
    world_z = vox_z * voxel_size  # Z=0 at ground level (camera position)
    
    print(f"[{camera_name}] Voxel ({vox_z:2d},{vox_y:2d},{vox_x:2d}) "
          f"= World ({world_x:+.2f}, {world_y:.2f}, {world_z:.2f})m "
          f"Intensity: {intensity:.2f}")


def main():
    """Run calibrated 3D reconstruction."""
    
    print("="*70)
    print("  CALIBRATED DUAL UPWARD CAMERAS - 3D RECONSTRUCTION")
    print("="*70)
    print()
    
    # Load calibration
    calib_file = "camera/calibration.yml"
    
    print("Loading camera calibration...")
    try:
        calib = load_calibration(calib_file)
        print("[OK] Using calibrated projection (lens distortion corrected)\n")
    except Exception as e:
        print(f"[ERROR] Could not load calibration: {e}")
        print("Please ensure camera/calibration.yml exists")
        return 1
    
    print("Camera Configuration:")
    print(f"  Left camera:   {CAMERA_LEFT_POS} m (pointing UP)")
    print(f"  Right camera:  {CAMERA_RIGHT_POS} m (pointing UP)")
    print(f"  Baseline:      {BASELINE} m")
    print(f"  Calibration:   {calib.camera_name}")
    print(f"  Focal length:  fx={calib.camera_matrix[0,0]:.1f}, fy={calib.camera_matrix[1,1]:.1f}")
    print(f"  Distortion k1: {calib.dist_coeffs[0]:.4f}")
    print()
    print("Voxel Space:")
    print("  X: -0.25m to +0.75m (1.0m width, centered on baseline)")
    print("  Y:  0.00m to +0.64m (0.64m height above ground)")
    print("  Z:  0.00m to +0.64m (0.64m depth from ground level)")
    print("  Resolution: 64x64x64 voxels (1cm per voxel)")
    print("  Origin: Ground level where cameras are positioned")
    print()
    
    grid_size = 64
    voxel_size = 0.01  # 1cm
    voxel_grid = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
    
    # Track which voxels were just filled
    voxel_print_threshold = 100
    last_printed_voxels = set()
    
    # Initialize cameras
    print("Initializing cameras...")
    cameras = DualASICameraSystem()
    cameras.configure(exposure=30000, gain=300)
    cameras.start_capture()
    print("[OK] Ready\n")
    
    time.sleep(0.5)
    
    # Get baseline
    prev_left, prev_right = cameras.capture_frame_pair()
    
    print("Recording for 15 seconds...")
    print("Move objects ABOVE the cameras!")
    print()
    print("Voxel coordinates will print when detected...")
    print("(Using calibrated undistortion for accurate 3D projection)")
    print()
    
    start_time = time.time()
    frame_count = 0
    motion_threshold = 25
    
    try:
        while time.time() - start_time < 15:
            # Capture
            img_left, img_right = cameras.capture_frame_pair()
            
            if img_left is None or img_right is None:
                continue
            
            frame_count += 1
            
            # Detect motion
            diff_left = np.abs(img_left.astype(np.int16) - prev_left.astype(np.int16))
            diff_right = np.abs(img_right.astype(np.int16) - prev_right.astype(np.int16))
            
            motion_left = diff_left > motion_threshold
            motion_right = diff_right > motion_threshold
            
            # Get motion pixel coordinates
            motion_coords_left = np.argwhere(motion_left)
            motion_coords_right = np.argwhere(motion_right)
            
            # Track new voxels this frame
            new_voxels = set()
            
            # Project left camera motion pixels with calibration
            for py, px in motion_coords_left:
                intensity = img_left[py, px] / 255.0
                if intensity > 0.3:
                    voxel_coords = pixel_to_voxel_calibrated(
                        py, px, calib,
                        CAMERA_LEFT_POS, grid_size, voxel_size
                    )
                    
                    for vox_z, vox_y, vox_x in voxel_coords:
                        old_value = voxel_grid[vox_z, vox_y, vox_x]
                        voxel_grid[vox_z, vox_y, vox_x] += intensity * 0.1
                        
                        # Print if newly significant
                        voxel_key = (vox_z, vox_y, vox_x)
                        if (voxel_grid[vox_z, vox_y, vox_x] > voxel_print_threshold and 
                            voxel_key not in last_printed_voxels):
                            print_voxel_coordinate(vox_z, vox_y, vox_x, 
                                                  voxel_grid[vox_z, vox_y, vox_x], 
                                                  "LEFT ", voxel_size)
                            new_voxels.add(voxel_key)
            
            # Project right camera motion pixels with calibration
            # Note: Using same calibration (assuming identical cameras)
            for py, px in motion_coords_right:
                intensity = img_right[py, px] / 255.0
                if intensity > 0.3:
                    voxel_coords = pixel_to_voxel_calibrated(
                        py, px, calib,
                        CAMERA_RIGHT_POS, grid_size, voxel_size
                    )
                    
                    for vox_z, vox_y, vox_x in voxel_coords:
                        old_value = voxel_grid[vox_z, vox_y, vox_x]
                        voxel_grid[vox_z, vox_y, vox_x] += intensity * 0.1
                        
                        voxel_key = (vox_z, vox_y, vox_x)
                        if (voxel_grid[vox_z, vox_y, vox_x] > voxel_print_threshold and 
                            voxel_key not in last_printed_voxels):
                            print_voxel_coordinate(vox_z, vox_y, vox_x,
                                                  voxel_grid[vox_z, vox_y, vox_x],
                                                  "RIGHT", voxel_size)
                            new_voxels.add(voxel_key)
            
            # Update printed voxels set
            last_printed_voxels.update(new_voxels)
            
            # Decay slightly
            voxel_grid *= 0.99
            
            # Status (every 10 frames)
            if frame_count % 10 == 0:
                non_zero = np.count_nonzero(voxel_grid)
                max_val = np.max(voxel_grid)
                print(f"\n[Frame {frame_count:3d}] Voxels: {non_zero:4d}, Max: {max_val:.1f}, "
                      f"Motion: L={len(motion_coords_left):4d} R={len(motion_coords_right):4d}\n")
            
            # Update previous
            prev_left = img_left.copy()
            prev_right = img_right.copy()
    
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    finally:
        cameras.stop_capture()
        cameras.close()
        
        print("\n" + "="*70)
        print("  RESULTS")
        print("="*70)
        print()
        print(f"Frames processed: {frame_count}")
        print(f"Unique voxels detected: {len(last_printed_voxels)}")
        print()
        
        print_grid_statistics(voxel_grid)
        
        # Save
        save_voxel_grid(voxel_grid, 'data/calibrated_voxels.bin')
        print("\n[OK] Saved to: data/calibrated_voxels.bin")
        print("\nVisualize with:")
        print("  python spacevoxelviewer.py data\\calibrated_voxels.bin --show-cameras --voxel-size 0.01")
        print("\nCompare with uncalibrated:")
        print("  python spacevoxelviewer.py data\\upward_cameras_voxels.bin --show-cameras --voxel-size 0.01")
        print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


"""
Correct Coordinate System - Z is Height!

COORDINATE SYSTEM (CORRECTED):
  X: Horizontal (left ← → right)
  Y: Depth (forward ← → back, horizontal)
  Z: HEIGHT (up ← → down, VERTICAL)
  
  Origin: Ground level where cameras sit (Z=0)
  
  Camera positions:
    Left:  (0.0, 0.0, 0.0) - at origin, ground level
    Right: (0.5, 0.0, 0.0) - 0.5m to the right, ground level
  
  Both cameras pointing UP along +Z axis (pitch=90°)
"""

import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem
from calibration_loader import load_calibration
from utils.voxel_helpers import save_voxel_grid, print_grid_statistics


CAMERA_LEFT_POS = np.array([0.0, 0.0, 0.0])   # X, Y, Z
CAMERA_RIGHT_POS = np.array([0.5, 0.0, 0.0])  # 0.5m to the right


def traverse_ray_3d_correct(camera_pos, ray_dir, grid_size=64, voxel_size=0.01, 
                            max_distance=1.0, intensity=1.0):
    """
    Traverse ray through 3D voxel grid with CORRECT coordinate system.
    Z is HEIGHT (vertical), Y is depth (horizontal).
    
    Args:
        camera_pos: Camera position [x, y, z] where Z=0 is ground
        ray_dir: Normalized ray direction [dx, dy, dz] where dz points up
        grid_size: Voxel grid dimension
        voxel_size: Size of each voxel in meters
        max_distance: Maximum ray length in meters
        intensity: Base intensity for this pixel (0-1)
    
    Returns:
        List of tuples: [(voxel_x, voxel_y, voxel_z, weighted_intensity), ...]
    """
    voxel_list = []
    visited = set()
    
    step_size = voxel_size * 0.5
    num_steps = int(max_distance / step_size)
    
    for i in range(num_steps):
        t = i * step_size
        
        # Point along ray: camera_pos + t * ray_dir
        point_3d = camera_pos + ray_dir * t
        
        # Skip if below ground (Z < 0)
        if point_3d[2] < 0:  # Z component is height
            continue
        
        # Convert to voxel coordinates
        # X: horizontal (-0.25 to +0.75)
        # Y: depth (0 to +0.64)
        # Z: height (0 to +0.64)
        vox_x = int((point_3d[0] + 0.25) / voxel_size)
        vox_y = int(point_3d[1] / voxel_size)
        vox_z = int(point_3d[2] / voxel_size)  # Z is HEIGHT
        
        # Check bounds
        if not (0 <= vox_x < grid_size and 
                0 <= vox_y < grid_size and 
                0 <= vox_z < grid_size):
            continue
        
        voxel_key = (vox_x, vox_y, vox_z)
        if voxel_key in visited:
            continue
        
        visited.add(voxel_key)
        
        # Distance-based falloff
        distance = np.linalg.norm(point_3d - camera_pos)
        falloff = 1.0 / (1.0 + distance * 0.2)
        
        weighted_intensity = intensity * falloff
        voxel_list.append((vox_x, vox_y, vox_z, weighted_intensity))
    
    return voxel_list


def print_voxel_coordinate(vox_x, vox_y, vox_z, intensity, camera_name, voxel_size=0.01):
    """
    Print voxel coordinate with CORRECT coordinate system.
    X=horizontal, Y=depth, Z=HEIGHT
    """
    world_x = (vox_x * voxel_size) - 0.25
    world_y = vox_y * voxel_size
    world_z = vox_z * voxel_size  # Z is HEIGHT above ground
    
    print(f"[{camera_name}] Voxel ({vox_x:2d},{vox_y:2d},{vox_z:2d}) "
          f"= World (X:{world_x:+.2f}, Y:{world_y:.2f}, Z:{world_z:.2f})m "
          f"Intensity: {intensity:.2f}")


def main():
    """
    Run 3D reconstruction with CORRECT coordinate system.
    Z is HEIGHT (vertical), Y is depth (horizontal).
    """
    
    print("="*70)
    print("  CORRECT COORDINATE SYSTEM - Z is Height!")
    print("="*70)
    print()
    print("Coordinate System:")
    print("  X: Horizontal (left ← → right)")
    print("  Y: Depth (forward ← → back, horizontal)")
    print("  Z: HEIGHT (up ← → down, VERTICAL)")
    print()
    print("  Origin: Z=0 is GROUND LEVEL where cameras sit")
    print()
    
    # Load calibration
    calib_file = "camera/calibration.yml"
    
    print("Loading camera calibration...")
    try:
        calib = load_calibration(calib_file)
        print("[OK] Fisheye calibration loaded\n")
    except Exception as e:
        print(f"[WARN] Could not load calibration: {e}")
        print("Continuing without calibration\n")
        calib = None
    
    print("Camera Configuration:")
    print(f"  Left camera:   {CAMERA_LEFT_POS} m (at ground, pointing UP)")
    print(f"  Right camera:  {CAMERA_RIGHT_POS} m (0.5m right, pointing UP)")
    print()
    print("Voxel Space:")
    print("  X: -0.25m to +0.75m (horizontal left-right)")
    print("  Y:  0.00m to +0.64m (depth forward)")
    print("  Z:  0.00m to +0.64m (HEIGHT above ground - VERTICAL)")
    print("  Resolution: 64x64x64 voxels (1cm per voxel)")
    print()
    
    grid_size = 64
    voxel_size = 0.01
    voxel_grid = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
    
    camera_hits = np.zeros((grid_size, grid_size, grid_size, 2), dtype=np.bool_)
    
    voxel_print_threshold = 50
    printed_voxels = set()
    
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
    print("Move objects ABOVE the cameras (increasing Z)!")
    print()
    
    start_time = time.time()
    frame_count = 0
    motion_threshold = 25
    
    try:
        while time.time() - start_time < 15:
            img_left, img_right = cameras.capture_frame_pair()
            
            if img_left is None or img_right is None:
                continue
            
            frame_count += 1
            
            # Detect motion
            diff_left = np.abs(img_left.astype(np.int16) - prev_left.astype(np.int16))
            diff_right = np.abs(img_right.astype(np.int16) - prev_right.astype(np.int16))
            
            motion_left = diff_left > motion_threshold
            motion_right = diff_right > motion_threshold
            
            motion_coords_left = np.argwhere(motion_left)
            motion_coords_right = np.argwhere(motion_right)
            
            camera_hits.fill(False)
            
            # Process left camera
            for py, px in motion_coords_left:
                pixel_intensity = img_left[py, px] / 255.0
                
                if pixel_intensity < 0.3:
                    continue
                
                # Get ray direction (calibrated if available)
                if calib is not None:
                    ray_dir = calib.get_ray_direction(px, py)
                else:
                    # Simple upward projection
                    norm_x = (px - 960) / 755.0
                    norm_y = (py - 540) / 752.0
                    # Ray pointing UP: (norm_x, norm_y, 1.0) where last component is Z (up)
                    ray_dir = np.array([norm_x, norm_y, 1.0])
                    ray_dir = ray_dir / np.linalg.norm(ray_dir)
                
                # Traverse ray with correct coordinate system
                voxels_on_ray = traverse_ray_3d_correct(
                    CAMERA_LEFT_POS, ray_dir, 
                    grid_size, voxel_size, 
                    max_distance=0.8, 
                    intensity=pixel_intensity
                )
                
                for vox_x, vox_y, vox_z, weighted_int in voxels_on_ray:
                    voxel_grid[vox_x, vox_y, vox_z] += weighted_int * 0.1
                    camera_hits[vox_x, vox_y, vox_z, 0] = True
                    
                    if (voxel_grid[vox_x, vox_y, vox_z] > voxel_print_threshold and
                        (vox_x, vox_y, vox_z) not in printed_voxels):
                        print_voxel_coordinate(vox_x, vox_y, vox_z,
                                             voxel_grid[vox_x, vox_y, vox_z],
                                             "LEFT ", voxel_size)
                        printed_voxels.add((vox_x, vox_y, vox_z))
            
            # Process right camera
            for py, px in motion_coords_right:
                pixel_intensity = img_right[py, px] / 255.0
                
                if pixel_intensity < 0.3:
                    continue
                
                if calib is not None:
                    ray_dir = calib.get_ray_direction(px, py)
                else:
                    norm_x = (px - 960) / 755.0
                    norm_y = (py - 540) / 752.0
                    ray_dir = np.array([norm_x, norm_y, 1.0])
                    ray_dir = ray_dir / np.linalg.norm(ray_dir)
                
                voxels_on_ray = traverse_ray_3d_correct(
                    CAMERA_RIGHT_POS, ray_dir,
                    grid_size, voxel_size,
                    max_distance=0.8,
                    intensity=pixel_intensity
                )
                
                for vox_x, vox_y, vox_z, weighted_int in voxels_on_ray:
                    voxel_grid[vox_x, vox_y, vox_z] += weighted_int * 0.1
                    camera_hits[vox_x, vox_y, vox_z, 1] = True
                    
                    if (voxel_grid[vox_x, vox_y, vox_z] > voxel_print_threshold and
                        (vox_x, vox_y, vox_z) not in printed_voxels):
                        print_voxel_coordinate(vox_x, vox_y, vox_z,
                                             voxel_grid[vox_x, vox_y, vox_z],
                                             "RIGHT", voxel_size)
                        printed_voxels.add((vox_x, vox_y, vox_z))
            
            # Multi-camera confidence boost
            both_cameras = camera_hits[:,:,:,0] & camera_hits[:,:,:,1]
            voxel_grid[both_cameras] *= 1.5
            
            # Temporal decay
            voxel_grid *= 0.99
            
            # Status
            if frame_count % 10 == 0:
                non_zero = np.count_nonzero(voxel_grid)
                max_val = np.max(voxel_grid)
                both_count = np.count_nonzero(both_cameras)
                print(f"\n[Frame {frame_count:3d}] Voxels: {non_zero:5d}, "
                      f"Both-cam: {both_count:4d}, Max: {max_val:.1f}\n")
            
            prev_left = img_left.copy()
            prev_right = img_right.copy()
    
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    finally:
        cameras.stop_capture()
        cameras.close()
        
        print("\n" + "="*70)
        print("  RESULTS - Correct Coordinate System")
        print("="*70)
        print()
        print(f"Frames processed: {frame_count}")
        print(f"Unique voxels detected: {len(printed_voxels)}")
        print()
        
        print_grid_statistics(voxel_grid)
        
        save_voxel_grid(voxel_grid, 'data/correct_coordinates_voxels.bin')
        print("\n[OK] Saved to: data/correct_coordinates_voxels.bin")
        print("\nCoordinate system: X=horizontal, Y=depth, Z=HEIGHT")
        print("Visualize with:")
        print("  python spacevoxelviewer.py data\\correct_coordinates_voxels.bin --show-cameras --voxel-size 0.01")
        print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())




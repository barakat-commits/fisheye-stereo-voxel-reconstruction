"""
Improved 3D Ray Traversal - Learning from Pixeltovoxelprojector

This implementation fixes our discrete-height sampling by properly
traversing the entire ray through the voxel grid, similar to how
the Pixeltovoxelprojector repositories handle ray casting.

Key improvements:
1. DDA-like 3D ray traversal (visits all voxels along ray)
2. Distance-based intensity falloff
3. Multi-camera confidence tracking
4. Better accumulation strategy
"""

import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem
from calibration_loader import load_calibration
from utils.voxel_helpers import save_voxel_grid, print_grid_statistics


CAMERA_LEFT_POS = np.array([0.0, 0.0, 0.0])
CAMERA_RIGHT_POS = np.array([0.5, 0.0, 0.0])


def traverse_ray_3d(camera_pos, ray_dir, grid_size=64, voxel_size=0.01, 
                    max_distance=1.0, intensity=1.0):
    """
    Traverse ray through 3D voxel grid using small steps.
    Returns list of (voxel_coords, weighted_intensity) along the ray.
    
    This is similar to the approach in Pixeltovoxelprojector repos,
    where the entire ray is sampled, not just discrete heights.
    
    Args:
        camera_pos: Camera position [x, y, z] in meters
        ray_dir: Normalized ray direction [x, y, z]
        grid_size: Voxel grid dimension
        voxel_size: Size of each voxel in meters
        max_distance: Maximum ray length in meters
        intensity: Base intensity for this pixel (0-1)
    
    Returns:
        List of tuples: [(voxel_z, voxel_y, voxel_x, weighted_intensity), ...]
    """
    voxel_list = []
    visited = set()  # Avoid double-counting same voxel
    
    # Step size: half a voxel for good coverage
    step_size = voxel_size * 0.5
    num_steps = int(max_distance / step_size)
    
    for i in range(num_steps):
        t = i * step_size
        
        # Point along ray
        point_3d = camera_pos + ray_dir * t
        
        # Skip if below ground
        if point_3d[1] < 0:
            continue
        
        # Convert to voxel coordinates
        vox_x = int((point_3d[0] + 0.25) / voxel_size)
        vox_y = int(point_3d[1] / voxel_size)
        vox_z = int(point_3d[2] / voxel_size)
        
        # Check bounds
        if not (0 <= vox_x < grid_size and 
                0 <= vox_y < grid_size and 
                0 <= vox_z < grid_size):
            continue
        
        # Skip if already visited
        voxel_key = (vox_z, vox_y, vox_x)
        if voxel_key in visited:
            continue
        
        visited.add(voxel_key)
        
        # Distance-based falloff (closer = more confident)
        distance = np.linalg.norm(point_3d - camera_pos)
        falloff = 1.0 / (1.0 + distance * 0.2)
        
        weighted_intensity = intensity * falloff
        voxel_list.append((vox_z, vox_y, vox_x, weighted_intensity))
    
    return voxel_list


def print_voxel_coordinate(vox_z, vox_y, vox_x, intensity, camera_name, voxel_size=0.01):
    """Print voxel coordinate with real-world position."""
    world_x = (vox_x * voxel_size) - 0.25
    world_y = vox_y * voxel_size
    world_z = vox_z * voxel_size
    
    print(f"[{camera_name}] Voxel ({vox_z:2d},{vox_y:2d},{vox_x:2d}) "
          f"= World ({world_x:+.2f}, {world_y:.2f}, {world_z:.2f})m "
          f"Intensity: {intensity:.2f}")


def main():
    """
    Run 3D reconstruction with improved ray traversal.
    Learning from Pixeltovoxelprojector approach.
    """
    
    print("="*70)
    print("  IMPROVED RAY TRAVERSAL - Learning from Pixeltovoxelprojector")
    print("="*70)
    print()
    print("Key Improvements:")
    print("  1. Full 3D ray traversal (not just discrete heights)")
    print("  2. Distance-based intensity falloff")
    print("  3. Multi-camera confidence tracking")
    print("  4. Better voxel accumulation")
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
    print(f"  Left camera:   {CAMERA_LEFT_POS} m (pointing UP)")
    print(f"  Right camera:  {CAMERA_RIGHT_POS} m (pointing UP)")
    print()
    print("Voxel Space:")
    print("  X: -0.25m to +0.75m (1.0m width)")
    print("  Y:  0.00m to +0.64m (0.64m height above ground)")
    print("  Z:  0.00m to +0.64m (0.64m depth from ground level)")
    print("  Resolution: 64x64x64 voxels (1cm per voxel)")
    print()
    
    grid_size = 64
    voxel_size = 0.01  # 1cm
    voxel_grid = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
    
    # Track which cameras see each voxel (for confidence)
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
    print("Move objects ABOVE the cameras!")
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
            
            motion_coords_left = np.argwhere(motion_left)
            motion_coords_right = np.argwhere(motion_right)
            
            # Reset camera hits for this frame
            camera_hits.fill(False)
            
            # Process left camera with improved ray traversal
            for py, px in motion_coords_left:
                pixel_intensity = img_left[py, px] / 255.0
                
                if pixel_intensity < 0.3:
                    continue
                
                # Get ray direction (with calibration if available)
                if calib is not None:
                    ray_dir = calib.get_ray_direction(px, py)
                else:
                    # Simple upward projection if no calibration
                    norm_x = (px - 960) / 755.0
                    norm_y = (py - 540) / 752.0
                    ray_dir = np.array([norm_x, 1.0, norm_y])
                    ray_dir = ray_dir / np.linalg.norm(ray_dir)
                
                # Traverse ray through voxel grid
                voxels_on_ray = traverse_ray_3d(
                    CAMERA_LEFT_POS, ray_dir, 
                    grid_size, voxel_size, 
                    max_distance=0.8, 
                    intensity=pixel_intensity
                )
                
                # Accumulate in voxel grid
                for vox_z, vox_y, vox_x, weighted_int in voxels_on_ray:
                    voxel_grid[vox_z, vox_y, vox_x] += weighted_int * 0.1
                    camera_hits[vox_z, vox_y, vox_x, 0] = True  # Left camera sees it
                    
                    # Print significant voxels
                    if (voxel_grid[vox_z, vox_y, vox_x] > voxel_print_threshold and
                        (vox_z, vox_y, vox_x) not in printed_voxels):
                        print_voxel_coordinate(vox_z, vox_y, vox_x,
                                             voxel_grid[vox_z, vox_y, vox_x],
                                             "LEFT ", voxel_size)
                        printed_voxels.add((vox_z, vox_y, vox_x))
            
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
                    ray_dir = np.array([norm_x, 1.0, norm_y])
                    ray_dir = ray_dir / np.linalg.norm(ray_dir)
                
                voxels_on_ray = traverse_ray_3d(
                    CAMERA_RIGHT_POS, ray_dir,
                    grid_size, voxel_size,
                    max_distance=0.8,
                    intensity=pixel_intensity
                )
                
                for vox_z, vox_y, vox_x, weighted_int in voxels_on_ray:
                    voxel_grid[vox_z, vox_y, vox_x] += weighted_int * 0.1
                    camera_hits[vox_z, vox_y, vox_x, 1] = True  # Right camera sees it
                    
                    if (voxel_grid[vox_z, vox_y, vox_x] > voxel_print_threshold and
                        (vox_z, vox_y, vox_x) not in printed_voxels):
                        print_voxel_coordinate(vox_z, vox_y, vox_x,
                                             voxel_grid[vox_z, vox_y, vox_x],
                                             "RIGHT", voxel_size)
                        printed_voxels.add((vox_z, vox_y, vox_x))
            
            # CONFIDENCE BOOST: Voxels seen by BOTH cameras = more confident!
            # (This is the "intersection" idea from Pixeltovoxelprojector)
            both_cameras = camera_hits[:,:,:,0] & camera_hits[:,:,:,1]
            voxel_grid[both_cameras] *= 1.5  # 50% confidence boost
            
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
        print("  RESULTS")
        print("="*70)
        print()
        print(f"Frames processed: {frame_count}")
        print(f"Unique high-confidence voxels: {len(printed_voxels)}")
        print()
        
        print_grid_statistics(voxel_grid)
        
        save_voxel_grid(voxel_grid, 'data/improved_ray_voxels.bin')
        print("\n[OK] Saved to: data/improved_ray_voxels.bin")
        print("\nVisualize with:")
        print("  python spacevoxelviewer.py data\\improved_ray_voxels.bin --show-cameras --voxel-size 0.01")
        print("\nCompare with old method:")
        print("  python spacevoxelviewer.py data\\calibrated_voxels.bin --show-cameras --voxel-size 0.01")
        print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())




"""
Configurable 3D Reconstruction - Production Ready

Uses JSON configuration for maximum flexibility.
Combines all improvements:
  - JSON configuration (from tesorrells/Pixeltovoxelprojector)
  - Full 3D ray traversal (from ConsistentlyInconsistentYT/Pixeltovoxelprojector)
  - Fisheye calibration (our advancement)
  - Multi-camera confidence (from Pixeltovoxelprojector)
"""

import numpy as np
import time
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem
from calibration_loader import load_calibration
from config_loader import load_config
from utils.voxel_helpers import save_voxel_grid, print_grid_statistics


def traverse_ray_3d(camera_pos, ray_dir, config, intensity=1.0):
    """
    Traverse ray through 3D voxel grid using configuration parameters.
    
    Args:
        camera_pos: Camera position [x, y, z] in meters
        ray_dir: Normalized ray direction [x, y, z]
        config: SystemConfig object with all parameters
        intensity: Base intensity for this pixel (0-1)
    
    Returns:
        List of tuples: [(voxel_z, voxel_y, voxel_x, weighted_intensity), ...]
    """
    voxel_list = []
    visited = set()
    
    # Get parameters from config
    grid_size = config.voxel_grid.size
    voxel_size = config.voxel_grid.voxel_size_meters
    max_distance = config.reconstruction.max_ray_distance_meters
    step_ratio = config.reconstruction.ray_step_size_ratio
    falloff_factor = config.reconstruction.distance_falloff_factor
    
    step_size = voxel_size * step_ratio
    num_steps = int(max_distance / step_size)
    
    for i in range(num_steps):
        t = i * step_size
        point_3d = camera_pos + ray_dir * t
        
        # Skip if below ground
        if point_3d[1] < 0:
            continue
        
        # Convert to voxel coordinates using config bounds
        vox_x = int((point_3d[0] - config.voxel_grid.x_min) / voxel_size)
        vox_y = int((point_3d[1] - config.voxel_grid.y_min) / voxel_size)
        vox_z = int((point_3d[2] - config.voxel_grid.z_min) / voxel_size)
        
        # Check bounds
        if not (0 <= vox_x < grid_size and 
                0 <= vox_y < grid_size and 
                0 <= vox_z < grid_size):
            continue
        
        voxel_key = (vox_z, vox_y, vox_x)
        if voxel_key in visited:
            continue
        
        visited.add(voxel_key)
        
        # Distance-based falloff using config parameter
        distance = np.linalg.norm(point_3d - camera_pos)
        falloff = 1.0 / (1.0 + distance * falloff_factor)
        
        weighted_intensity = intensity * falloff
        voxel_list.append((vox_z, vox_y, vox_x, weighted_intensity))
    
    return voxel_list


def print_voxel_coordinate(vox_z, vox_y, vox_x, intensity, camera_name, config):
    """Print voxel coordinate with real-world position."""
    voxel_size = config.voxel_grid.voxel_size_meters
    world_x = (vox_x * voxel_size) + config.voxel_grid.x_min
    world_y = (vox_y * voxel_size) + config.voxel_grid.y_min
    world_z = (vox_z * voxel_size) + config.voxel_grid.z_min
    
    print(f"[{camera_name}] Voxel ({vox_z:2d},{vox_y:2d},{vox_x:2d}) "
          f"= World ({world_x:+.2f}, {world_y:.2f}, {world_z:.2f})m "
          f"Intensity: {intensity:.2f}")


def main():
    """
    Run configurable 3D reconstruction.
    All parameters loaded from camera_config.json.
    """
    
    print("="*70)
    print("  CONFIGURABLE 3D RECONSTRUCTION - Production Ready")
    print("="*70)
    print()
    
    # Load configuration
    config_file = sys.argv[1] if len(sys.argv) > 1 else "camera/camera_config.json"
    
    try:
        config = load_config(config_file)
        print(f"[OK] Configuration loaded from: {config_file}\n")
    except Exception as e:
        print(f"[ERROR] Failed to load configuration: {e}")
        print("\nCreate camera/camera_config.json from template")
        return 1
    
    # Print configuration
    config.print_summary()
    
    # Load calibrations for each camera
    calibrations = {}
    for cam in config.cameras:
        if cam.calibration_file:
            try:
                calib = load_calibration(cam.calibration_file)
                calibrations[cam.id] = calib
                print(f"[OK] Calibration loaded for {cam.id} camera")
            except Exception as e:
                print(f"[WARN] Could not load calibration for {cam.id}: {e}")
                calibrations[cam.id] = None
        else:
            calibrations[cam.id] = None
    
    print()
    
    # Initialize voxel grid
    grid_size = config.voxel_grid.size
    voxel_size = config.voxel_grid.voxel_size_meters
    voxel_grid = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
    
    # Track camera hits for confidence
    num_cameras = len(config.cameras)
    camera_hits = np.zeros((grid_size, grid_size, grid_size, num_cameras), dtype=np.bool_)
    
    printed_voxels = set()
    
    # Initialize cameras
    print("Initializing cameras...")
    cameras = DualASICameraSystem()
    
    # Configure using config settings
    left_cam = config.get_camera_by_id('left')
    cameras.configure(exposure=left_cam.exposure_us, gain=left_cam.gain)
    cameras.start_capture()
    print("[OK] Cameras ready\n")
    
    time.sleep(config.recording.warmup_delay_seconds)
    
    # Get baseline
    prev_left, prev_right = cameras.capture_frame_pair()
    
    print(f"Recording for {config.recording.duration_seconds} seconds...")
    print("Move objects above the cameras!")
    print()
    
    start_time = time.time()
    frame_count = 0
    
    try:
        while time.time() - start_time < config.recording.duration_seconds:
            # Capture
            img_left, img_right = cameras.capture_frame_pair()
            
            if img_left is None or img_right is None:
                continue
            
            frame_count += 1
            
            # Detect motion
            diff_left = np.abs(img_left.astype(np.int16) - prev_left.astype(np.int16))
            diff_right = np.abs(img_right.astype(np.int16) - prev_right.astype(np.int16))
            
            motion_threshold = config.reconstruction.motion_threshold
            motion_left = diff_left > motion_threshold
            motion_right = diff_right > motion_threshold
            
            motion_coords_left = np.argwhere(motion_left)
            motion_coords_right = np.argwhere(motion_right)
            
            # Reset camera hits
            camera_hits.fill(False)
            
            # Process left camera
            left_config = config.get_camera_by_id('left')
            left_calib = calibrations['left']
            
            for py, px in motion_coords_left:
                pixel_intensity = img_left[py, px] / 255.0
                
                if pixel_intensity < 0.3:
                    continue
                
                # Get ray direction
                if left_calib is not None:
                    ray_dir = left_calib.get_ray_direction(px, py)
                else:
                    # Fallback: simple upward projection
                    norm_x = (px - 960) / 755.0
                    norm_y = (py - 540) / 752.0
                    ray_dir = np.array([norm_x, 1.0, norm_y])
                    ray_dir = ray_dir / np.linalg.norm(ray_dir)
                
                # Traverse ray
                voxels_on_ray = traverse_ray_3d(
                    left_config.position, ray_dir, config, pixel_intensity
                )
                
                # Accumulate
                for vox_z, vox_y, vox_x, weighted_int in voxels_on_ray:
                    voxel_grid[vox_z, vox_y, vox_x] += weighted_int * 0.1
                    camera_hits[vox_z, vox_y, vox_x, 0] = True
                    
                    # Print significant voxels
                    if (voxel_grid[vox_z, vox_y, vox_x] > config.reconstruction.voxel_print_threshold and
                        (vox_z, vox_y, vox_x) not in printed_voxels):
                        print_voxel_coordinate(vox_z, vox_y, vox_x,
                                             voxel_grid[vox_z, vox_y, vox_x],
                                             "LEFT ", config)
                        printed_voxels.add((vox_z, vox_y, vox_x))
            
            # Process right camera
            right_config = config.get_camera_by_id('right')
            right_calib = calibrations['right']
            
            for py, px in motion_coords_right:
                pixel_intensity = img_right[py, px] / 255.0
                
                if pixel_intensity < 0.3:
                    continue
                
                if right_calib is not None:
                    ray_dir = right_calib.get_ray_direction(px, py)
                else:
                    norm_x = (px - 960) / 755.0
                    norm_y = (py - 540) / 752.0
                    ray_dir = np.array([norm_x, 1.0, norm_y])
                    ray_dir = ray_dir / np.linalg.norm(ray_dir)
                
                voxels_on_ray = traverse_ray_3d(
                    right_config.position, ray_dir, config, pixel_intensity
                )
                
                for vox_z, vox_y, vox_x, weighted_int in voxels_on_ray:
                    voxel_grid[vox_z, vox_y, vox_x] += weighted_int * 0.1
                    camera_hits[vox_z, vox_y, vox_x, 1] = True
                    
                    if (voxel_grid[vox_z, vox_y, vox_x] > config.reconstruction.voxel_print_threshold and
                        (vox_z, vox_y, vox_x) not in printed_voxels):
                        print_voxel_coordinate(vox_z, vox_y, vox_x,
                                             voxel_grid[vox_z, vox_y, vox_x],
                                             "RIGHT", config)
                        printed_voxels.add((vox_z, vox_y, vox_x))
            
            # Multi-camera confidence boost
            both_cameras = camera_hits[:,:,:,0] & camera_hits[:,:,:,1]
            voxel_grid[both_cameras] *= config.reconstruction.multi_camera_boost
            
            # Temporal decay
            voxel_grid *= config.reconstruction.temporal_decay
            
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
        
        save_voxel_grid(voxel_grid, 'data/configurable_voxels.bin')
        print("\n[OK] Saved to: data/configurable_voxels.bin")
        print("\nVisualize with:")
        print("  python spacevoxelviewer.py data\\configurable_voxels.bin --show-cameras --voxel-size 0.01")
        print("\nConfiguration used:")
        print(f"  {config_file}")
        print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())




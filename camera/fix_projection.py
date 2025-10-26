"""
Fixed Voxel Projection with Correct Math

Fixes the projection so pixels actually map into the voxel grid.
"""

import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem
from utils.voxel_helpers import save_voxel_grid, print_grid_statistics


def pixel_to_voxel_fixed(pixel_y, pixel_x, img_height, img_width,
                          camera_idx, grid_size=64):
    """
    Fixed projection: simpler approach that actually fills voxels.
    
    Maps pixel coordinates directly to voxel space based on position.
    Left camera fills left side of grid, right fills right side.
    """
    # Normalize pixel position
    norm_x = pixel_x / img_width   # 0 to 1
    norm_y = pixel_y / img_height  # 0 to 1
    
    # Map to voxel grid
    vox_y = int(norm_y * grid_size)  # Top to bottom
    vox_z = int(grid_size / 2)       # Middle depth layer
    
    # Left camera fills left half, right camera fills right half
    if camera_idx == 0:  # Left camera
        vox_x = int(norm_x * grid_size / 2)  # Left half: 0-31
    else:  # Right camera
        vox_x = int(grid_size / 2 + norm_x * grid_size / 2)  # Right half: 32-63
    
    # Clamp to bounds
    vox_x = max(0, min(grid_size-1, vox_x))
    vox_y = max(0, min(grid_size-1, vox_y))
    vox_z = max(0, min(grid_size-1, vox_z))
    
    return (vox_z, vox_y, vox_x)


def main():
    """Run corrected motion to voxel mapping."""
    
    print("="*70)
    print("  FIXED VOXEL PROJECTION - Direct Mapping")
    print("="*70)
    print()
    print("This version uses corrected projection math:")
    print("  - Left camera -> left half of voxel grid")
    print("  - Right camera -> right half of voxel grid")
    print("  - Direct pixel-to-voxel mapping")
    print()
    
    grid_size = 64
    voxel_grid = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
    
    # Initialize cameras
    print("Initializing cameras...")
    cameras = DualASICameraSystem()
    cameras.configure(exposure=30000, gain=300)
    cameras.start_capture()
    print("[OK] Ready\n")
    
    time.sleep(0.5)
    
    # Get baseline
    prev_left, prev_right = cameras.capture_frame_pair()
    
    print("Recording for 10 seconds...")
    print("MOVE BRIGHT OBJECTS NOW!\n")
    
    start_time = time.time()
    frame_count = 0
    total_voxels_filled = 0
    motion_threshold = 25
    
    try:
        while time.time() - start_time < 10:
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
            
            voxels_this_frame = 0
            
            # Project left camera motion pixels
            for py, px in motion_coords_left:
                intensity = img_left[py, px] / 255.0
                if intensity > 0.2:  # Only bright enough pixels
                    vox_z, vox_y, vox_x = pixel_to_voxel_fixed(
                        py, px, 1080, 1920, camera_idx=0, grid_size=grid_size
                    )
                    voxel_grid[vox_z, vox_y, vox_x] += intensity * 0.1
                    voxels_this_frame += 1
            
            # Project right camera motion pixels
            for py, px in motion_coords_right:
                intensity = img_right[py, px] / 255.0
                if intensity > 0.2:
                    vox_z, vox_y, vox_x = pixel_to_voxel_fixed(
                        py, px, 1080, 1920, camera_idx=1, grid_size=grid_size
                    )
                    voxel_grid[vox_z, vox_y, vox_x] += intensity * 0.1
                    voxels_this_frame += 1
            
            # Decay slightly
            voxel_grid *= 0.99
            
            total_voxels_filled += voxels_this_frame
            
            # Status
            non_zero = np.count_nonzero(voxel_grid)
            max_val = np.max(voxel_grid)
            
            print(f"Frame {frame_count:3d} | "
                  f"Motion: L={len(motion_coords_left):5d} R={len(motion_coords_right):5d} | "
                  f"Voxels: {non_zero:5d} (max={max_val:5.2f}) | "
                  f"Filled: {voxels_this_frame:5d}",
                  end='\r')
            
            # Update previous
            prev_left = img_left.copy()
            prev_right = img_right.copy()
    
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    finally:
        cameras.stop_capture()
        cameras.close()
        
        print("\n\n" + "="*70)
        print("  RESULTS")
        print("="*70)
        print()
        print(f"Frames processed: {frame_count}")
        print(f"Total voxel updates: {total_voxels_filled:,}")
        print()
        
        print_grid_statistics(voxel_grid)
        
        # Save
        save_voxel_grid(voxel_grid, 'data/fixed_voxel_grid.bin')
        print("\n[OK] Saved to: data/fixed_voxel_grid.bin")
        print("\nVisualize with:")
        print("  python spacevoxelviewer.py data\\fixed_voxel_grid.bin")
        print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())




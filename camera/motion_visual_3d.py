"""
Enhanced Motion Detection with Visual Feedback
Shows moving pixels and their 3D projections in real-time
"""

import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem
from utils.voxel_helpers import save_voxel_grid, print_grid_statistics

try:
    import process_image_cpp
    CPP_AVAILABLE = True
except ImportError:
    CPP_AVAILABLE = False
    print("[WARN] C++ extension not available")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def project_motion_pixels_to_3d(motion_pixels, camera_pos, grid_size=64, voxel_size=1.0):
    """
    Project motion pixel coordinates to 3D voxel space.
    
    Args:
        motion_pixels: List of (y, x) pixel coordinates with motion
        camera_pos: Camera position in 3D space
        grid_size: Voxel grid dimension
        voxel_size: Size of each voxel
    
    Returns:
        voxel_coords: List of (z, y, x) voxel coordinates
    """
    voxel_coords = []
    
    # Simple projection: cast rays from camera through pixels into 3D space
    # Camera at camera_pos, looking at origin
    for pixel_y, pixel_x in motion_pixels:
        # Normalize pixel coordinates to [-1, 1]
        norm_x = (pixel_x / 1920.0 - 0.5) * 2.0
        norm_y = (pixel_y / 1080.0 - 0.5) * 2.0
        
        # Ray direction from camera through pixel
        ray_dir = np.array([norm_x * 50, norm_y * 50, 1.0])
        ray_dir = ray_dir / np.linalg.norm(ray_dir)
        
        # Cast ray into voxel grid
        # Sample points along ray
        for depth in range(10, 200, 10):  # Sample from 10mm to 200mm
            point_3d = camera_pos + ray_dir * depth
            
            # Convert to voxel coordinates
            vox_x = int((point_3d[0] + grid_size * voxel_size / 2) / voxel_size)
            vox_y = int((point_3d[1] + grid_size * voxel_size / 2) / voxel_size)
            vox_z = int((point_3d[2] + 100) / voxel_size)  # Offset forward
            
            # Check bounds
            if (0 <= vox_x < grid_size and 
                0 <= vox_y < grid_size and 
                0 <= vox_z < grid_size):
                voxel_coords.append((vox_z, vox_y, vox_x))
    
    return voxel_coords


def main():
    """Main function."""
    print("="*60)
    print("  Enhanced 3D Motion Detection & Visualization")
    print("="*60)
    
    # Configuration
    grid_size = 64
    motion_threshold = 25  # Lower threshold
    duration = 20  # seconds
    
    # Initialize voxel grid
    voxel_grid = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
    
    # Camera positions
    camera_left_pos = np.array([-50.0, 0.0, -150.0])
    camera_right_pos = np.array([50.0, 0.0, -150.0])
    
    # Initialize cameras
    print("\nInitializing cameras...")
    cameras = DualASICameraSystem()
    cameras.configure(width=1920, height=1080, exposure=15000, gain=300)
    cameras.start_capture()
    print("[OK] Cameras ready")
    
    # Previous frames
    prev_left = None
    prev_right = None
    
    frame_count = 0
    motion_detected_count = 0
    total_voxels_added = 0
    
    print("\n" + "="*60)
    print("  MOVE SOMETHING IN FRONT OF THE CAMERAS!")
    print("="*60)
    print("Starting in 3 seconds...")
    time.sleep(3)
    print("\n[RECORDING]\n")
    
    start_time = time.time()
    
    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break
            
            # Capture
            img_left, img_right = cameras.capture_frame_pair()
            
            if img_left is None or img_right is None:
                continue
            
            frame_count += 1
            
            if prev_left is None:
                prev_left = img_left.copy()
                prev_right = img_right.copy()
                continue
            
            # Detect motion
            diff_left = np.abs(img_left.astype(np.int16) - prev_left.astype(np.int16))
            diff_right = np.abs(img_right.astype(np.int16) - prev_right.astype(np.int16))
            
            motion_left = diff_left > motion_threshold
            motion_right = diff_right > motion_threshold
            
            motion_pixels_left = np.count_nonzero(motion_left)
            motion_pixels_right = np.count_nonzero(motion_right)
            
            # Project motion to 3D
            voxels_added = 0
            
            if motion_pixels_left > 200:  # Significant motion
                # Get pixel coordinates
                motion_coords_left = np.argwhere(motion_left)
                
                # Project to 3D
                voxel_coords = project_motion_pixels_to_3d(
                    motion_coords_left[:500],  # Limit to 500 pixels for speed
                    camera_left_pos,
                    grid_size,
                    1.0
                )
                
                # Fill voxels
                for vz, vy, vx in voxel_coords:
                    voxel_grid[vz, vy, vx] += 0.1  # Add intensity
                    voxels_added += 1
                
                motion_detected_count += 1
            
            if motion_pixels_right > 200:
                # Get pixel coordinates
                motion_coords_right = np.argwhere(motion_right)
                
                # Project to 3D
                voxel_coords = project_motion_pixels_to_3d(
                    motion_coords_right[:500],
                    camera_right_pos,
                    grid_size,
                    1.0
                )
                
                # Fill voxels
                for vz, vy, vx in voxel_coords:
                    voxel_grid[vz, vy, vx] += 0.1
                    voxels_added += 1
                
                motion_detected_count += 1
            
            total_voxels_added += voxels_added
            
            # Decay
            voxel_grid *= 0.99
            
            # Update previous frames
            prev_left = img_left.copy()
            prev_right = img_right.copy()
            
            # Display status
            non_zero = np.count_nonzero(voxel_grid)
            max_val = np.max(voxel_grid)
            
            print(f"Frame {frame_count:3d} | "
                  f"Motion: L={motion_pixels_left:5d} R={motion_pixels_right:5d} | "
                  f"Voxels: {non_zero:5d} (max={max_val:5.2f}) | "
                  f"Added: {voxels_added:4d} | "
                  f"Time: {elapsed:4.1f}s",
                  end='\r')
    
    except KeyboardInterrupt:
        print("\n\n[Stopped by user]")
    
    finally:
        # Save final grid
        print("\n\nSaving 3D motion map...")
        save_voxel_grid(voxel_grid, 'data/motion_visual_3d.bin')
        
        # Statistics
        print("\n" + "="*60)
        print("  RESULTS")
        print("="*60)
        print(f"\nFrames processed: {frame_count}")
        print(f"Frames with significant motion: {motion_detected_count}")
        print(f"Total voxels filled: {total_voxels_added:,}")
        
        print_grid_statistics(voxel_grid)
        
        # Close
        cameras.stop_capture()
        cameras.close()
        
        print("\n[OK] Complete!")
        print("\nVisualize with:")
        print("  python spacevoxelviewer.py data/motion_visual_3d.bin")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())




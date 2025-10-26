"""
Analyze Pixel-to-Voxel Projection

Captures a frame pair, detects motion, and shows detailed mapping
of which pixels project to which voxels.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[WARN] OpenCV not available - no image saving")


def analyze_projection():
    """Analyze pixel to voxel projection."""
    
    print("="*70)
    print("  PIXEL-TO-VOXEL PROJECTION ANALYSIS")
    print("="*70)
    print()
    
    # Camera setup
    camera_left_pos = np.array([-50.0, 0.0, -150.0])
    camera_right_pos = np.array([50.0, 0.0, -150.0])
    grid_size = 64
    voxel_size = 1.0
    
    print("Configuration:")
    print(f"  Left camera position:  {camera_left_pos}")
    print(f"  Right camera position: {camera_right_pos}")
    print(f"  Voxel grid: {grid_size}x{grid_size}x{grid_size}")
    print(f"  Voxel size: {voxel_size} mm")
    print()
    
    # Initialize cameras
    print("Initializing cameras...")
    cameras = DualASICameraSystem()
    cameras.configure(exposure=30000, gain=300)
    cameras.start_capture()
    print("[OK] Cameras initialized\n")
    
    # Wait and capture
    import time
    time.sleep(1)
    
    print("Capturing baseline frame...")
    img1_left, img1_right = cameras.capture_frame_pair()
    
    print("Waiting 2 seconds - MOVE SOMETHING NOW!")
    time.sleep(2)
    
    print("Capturing motion frame...")
    img2_left, img2_right = cameras.capture_frame_pair()
    
    cameras.stop_capture()
    cameras.close()
    
    if img1_left is None or img2_left is None:
        print("[ERROR] Failed to capture frames")
        return 1
    
    print("[OK] Frames captured\n")
    
    # Analyze
    print("="*70)
    print("  ANALYSIS")
    print("="*70)
    print()
    
    # Detect motion
    diff_left = np.abs(img2_left.astype(np.int16) - img1_left.astype(np.int16))
    diff_right = np.abs(img2_right.astype(np.int16) - img1_right.astype(np.int16))
    
    motion_threshold = 25
    motion_left = diff_left > motion_threshold
    motion_right = diff_right > motion_threshold
    
    motion_count_left = np.count_nonzero(motion_left)
    motion_count_right = np.count_nonzero(motion_right)
    
    print(f"Image brightness:")
    print(f"  Left:  {img2_left.mean():.1f} / 255")
    print(f"  Right: {img2_right.mean():.1f} / 255")
    print()
    
    print(f"Motion detected:")
    print(f"  Left:  {motion_count_left:,} pixels")
    print(f"  Right: {motion_count_right:,} pixels")
    print()
    
    # Analyze pixel projections
    def pixel_to_voxels(py, px, img_h, img_w, cam_pos, grid_sz, vox_sz):
        norm_x = (px / img_w - 0.5) * 2.0
        norm_y = (py / img_h - 0.5) * 2.0
        ray_dir = np.array([norm_x * 50, norm_y * 50, 1.0])
        ray_dir = ray_dir / np.linalg.norm(ray_dir)
        
        voxels = []
        for depth in range(10, 200, 10):
            pt = cam_pos + ray_dir * depth
            vx = int((pt[0] + grid_sz * vox_sz / 2) / vox_sz)
            vy = int((pt[1] + grid_sz * vox_sz / 2) / vox_sz)
            vz = int((pt[2] + 100) / vox_sz)
            
            if 0 <= vx < grid_sz and 0 <= vy < grid_sz and 0 <= vz < grid_sz:
                voxels.append((vz, vy, vx))
        
        return voxels
    
    # Sample some motion pixels
    motion_pixels_left = np.argwhere(motion_left)
    motion_pixels_right = np.argwhere(motion_right)
    
    print("Sample pixel-to-voxel projections:")
    print()
    
    if len(motion_pixels_left) > 0:
        # Sample 5 random motion pixels from left camera
        samples = motion_pixels_left[np.random.choice(len(motion_pixels_left), 
                                                       min(5, len(motion_pixels_left)), 
                                                       replace=False)]
        
        print("LEFT CAMERA:")
        for i, (py, px) in enumerate(samples):
            voxels = pixel_to_voxels(py, px, 1080, 1920, camera_left_pos, grid_size, voxel_size)
            intensity = img2_left[py, px]
            print(f"  Pixel ({py:4d}, {px:4d}) intensity={intensity:3d} -> {len(voxels)} voxels")
            if len(voxels) > 0:
                print(f"    First voxel:  {voxels[0]}")
                print(f"    Middle voxel: {voxels[len(voxels)//2]}")
                print(f"    Last voxel:   {voxels[-1]}")
    else:
        print("LEFT CAMERA: No motion detected")
    
    print()
    
    if len(motion_pixels_right) > 0:
        samples = motion_pixels_right[np.random.choice(len(motion_pixels_right),
                                                        min(5, len(motion_pixels_right)),
                                                        replace=False)]
        
        print("RIGHT CAMERA:")
        for i, (py, px) in enumerate(samples):
            voxels = pixel_to_voxels(py, px, 1080, 1920, camera_right_pos, grid_size, voxel_size)
            intensity = img2_right[py, px]
            print(f"  Pixel ({py:4d}, {px:4d}) intensity={intensity:3d} -> {len(voxels)} voxels")
            if len(voxels) > 0:
                print(f"    First voxel:  {voxels[0]}")
                print(f"    Middle voxel: {voxels[len(voxels)//2]}")
                print(f"    Last voxel:   {voxels[-1]}")
    else:
        print("RIGHT CAMERA: No motion detected")
    
    print()
    print("="*70)
    print("  KEY INSIGHTS")
    print("="*70)
    print()
    
    # Check why voxels might be empty
    if motion_count_left + motion_count_right == 0:
        print("[PROBLEM] No motion detected")
        print("  -> Move something in front of cameras")
    elif img2_left.mean() < 50:
        print("[PROBLEM] Scene too dark (brightness < 50/255)")
        print("  -> Add more light or increase gain/exposure")
    elif motion_count_left + motion_count_right < 1000:
        print("[PROBLEM] Very little motion detected")
        print("  -> Move brighter/larger objects")
    else:
        print("[OK] Motion detected and brightness adequate")
        
        # Check if voxels are in valid range
        sample_pixel_left = motion_pixels_left[0] if len(motion_pixels_left) > 0 else None
        if sample_pixel_left is not None:
            py, px = sample_pixel_left
            voxels = pixel_to_voxels(py, px, 1080, 1920, camera_left_pos, grid_size, voxel_size)
            
            if len(voxels) == 0:
                print("[PROBLEM] Pixels not projecting into voxel grid!")
                print("  -> Camera position or projection math needs adjustment")
            else:
                print("[OK] Pixels are projecting into valid voxel coordinates")
                intensity = img2_left[py, px]
                if intensity < 30:
                    print("[PROBLEM] Motion pixels are too dark (< 30/255)")
                    print("  -> Use brighter objects or increase exposure")
                else:
                    print(f"[OK] Motion pixel intensity adequate ({intensity}/255)")
    
    print()
    
    # Save visualization if OpenCV available
    if CV2_AVAILABLE:
        print("Saving visualization...")
        
        # Convert to RGB
        rgb_left = cv2.cvtColor(img2_left, cv2.COLOR_BAYER_RG2BGR)
        rgb_right = cv2.cvtColor(img2_right, cv2.COLOR_BAYER_RG2BGR)
        
        # Create overlay
        overlay_left = rgb_left.copy()
        overlay_right = rgb_right.copy()
        overlay_left[motion_left] = [0, 255, 0]
        overlay_right[motion_right] = [0, 255, 0]
        
        # Blend
        alpha = 0.5
        vis_left = cv2.addWeighted(rgb_left, 1-alpha, overlay_left, alpha, 0)
        vis_right = cv2.addWeighted(rgb_right, 1-alpha, overlay_right, alpha, 0)
        
        # Resize for saving
        scale = 0.5
        vis_left = cv2.resize(vis_left, (int(1920*scale), int(1080*scale)))
        vis_right = cv2.resize(vis_right, (int(1920*scale), int(1080*scale)))
        
        # Combine
        combined = np.hstack([vis_left, vis_right])
        
        # Add text
        cv2.putText(combined, f"Motion: L={motion_count_left} R={motion_count_right}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(combined, "Green = Motion", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Save
        cv2.imwrite('data/projection_debug.jpg', combined)
        print("[OK] Saved to: data/projection_debug.jpg")
        print("     View with: start data\\projection_debug.jpg")
    
    print()
    return 0


if __name__ == "__main__":
    sys.exit(analyze_projection())




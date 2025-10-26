"""
Debug Voxel Projection - Visual Troubleshooting Tool

Shows:
1. Dual camera feeds with green overlay on changing pixels
2. Voxel coordinates that each pixel projects to
3. Real-time projection visualization
"""

import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[ERROR] OpenCV (cv2) is required for this debug tool")
    print("Install with: pip install opencv-python")
    sys.exit(1)


def pixel_to_voxel_coords(pixel_y, pixel_x, img_height, img_width, 
                          camera_pos, grid_size=64, voxel_size=1.0):
    """
    Convert pixel coordinates to voxel grid coordinates.
    
    Args:
        pixel_y, pixel_x: Pixel coordinates in image
        img_height, img_width: Image dimensions
        camera_pos: Camera 3D position
        grid_size: Voxel grid dimension
        voxel_size: Size of each voxel
    
    Returns:
        List of (vox_z, vox_y, vox_x) coordinates along the ray
    """
    # Normalize pixel to [-1, 1]
    norm_x = (pixel_x / img_width - 0.5) * 2.0
    norm_y = (pixel_y / img_height - 0.5) * 2.0
    
    # Simple perspective projection
    # Ray from camera through pixel
    ray_dir = np.array([norm_x * 50, norm_y * 50, 1.0])
    ray_dir = ray_dir / np.linalg.norm(ray_dir)
    
    voxel_coords = []
    
    # Sample along ray at different depths
    for depth in range(10, 200, 10):  # 10mm to 200mm
        point_3d = camera_pos + ray_dir * depth
        
        # Convert to voxel coordinates
        vox_x = int((point_3d[0] + grid_size * voxel_size / 2) / voxel_size)
        vox_y = int((point_3d[1] + grid_size * voxel_size / 2) / voxel_size)
        vox_z = int((point_3d[2] + 100) / voxel_size)
        
        # Check bounds
        if (0 <= vox_x < grid_size and 
            0 <= vox_y < grid_size and 
            0 <= vox_z < grid_size):
            voxel_coords.append((vox_z, vox_y, vox_x))
    
    return voxel_coords


def main():
    """Main debug function."""
    
    print("="*70)
    print("  VOXEL PROJECTION DEBUG - Visual Troubleshooting")
    print("="*70)
    print()
    print("This tool shows:")
    print("  1. Both camera feeds side-by-side")
    print("  2. Green overlay on changing pixels (motion)")
    print("  3. Voxel coordinates for sample pixels")
    print()
    print("Controls:")
    print("  ESC or Q - Exit")
    print("  SPACE    - Pause/Resume")
    print()
    
    # Camera positions
    camera_left_pos = np.array([-50.0, 0.0, -150.0])
    camera_right_pos = np.array([50.0, 0.0, -150.0])
    grid_size = 64
    
    # Initialize cameras
    print("Initializing cameras...")
    cameras = DualASICameraSystem()
    
    # Configure for better brightness
    cameras.configure(
        width=1920,
        height=1080,
        exposure=30000,  # 30ms
        gain=300         # High gain
    )
    
    cameras.start_capture()
    print("[OK] Cameras ready\n")
    
    # Wait for first frame
    time.sleep(0.5)
    
    # Get baseline frames
    prev_left, prev_right = cameras.capture_frame_pair()
    
    if prev_left is None or prev_right is None:
        print("[ERROR] Could not capture initial frames")
        cameras.close()
        return 1
    
    print(f"Image size: {prev_left.shape}")
    print(f"Brightness: Left={prev_left.mean():.1f}, Right={prev_right.mean():.1f}")
    print()
    print("Starting visualization...")
    print("Move something bright in front of cameras!")
    print()
    
    frame_count = 0
    paused = False
    motion_threshold = 25
    
    # Sample points to track (center and corners)
    sample_points = [
        (540, 960, "Center"),      # Center
        (270, 480, "Top-Left"),    # Top-left quadrant
        (270, 1440, "Top-Right"),  # Top-right quadrant
        (810, 480, "Bot-Left"),    # Bottom-left quadrant
        (810, 1440, "Bot-Right"),  # Bottom-right quadrant
    ]
    
    try:
        while True:
            if not paused:
                # Capture new frames
                img_left, img_right = cameras.capture_frame_pair()
                
                if img_left is None or img_right is None:
                    continue
                
                frame_count += 1
                
                # Detect motion
                diff_left = np.abs(img_left.astype(np.int16) - prev_left.astype(np.int16))
                diff_right = np.abs(img_right.astype(np.int16) - prev_right.astype(np.int16))
                
                motion_left = diff_left > motion_threshold
                motion_right = diff_right > motion_threshold
                
                # Count motion pixels
                motion_count_left = np.count_nonzero(motion_left)
                motion_count_right = np.count_nonzero(motion_right)
                
                # Convert to RGB for visualization
                rgb_left = cv2.cvtColor(img_left, cv2.COLOR_BAYER_RG2BGR)
                rgb_right = cv2.cvtColor(img_right, cv2.COLOR_BAYER_RG2BGR)
                
                # Create motion overlay (green)
                overlay_left = rgb_left.copy()
                overlay_right = rgb_right.copy()
                
                # Highlight motion pixels in green
                overlay_left[motion_left] = [0, 255, 0]  # Green
                overlay_right[motion_right] = [0, 255, 0]
                
                # Blend with original
                alpha = 0.5
                display_left = cv2.addWeighted(rgb_left, 1-alpha, overlay_left, alpha, 0)
                display_right = cv2.addWeighted(rgb_right, 1-alpha, overlay_right, alpha, 0)
                
                # Resize for display (50% size)
                scale = 0.5
                new_w = int(1920 * scale)
                new_h = int(1080 * scale)
                display_left = cv2.resize(display_left, (new_w, new_h))
                display_right = cv2.resize(display_right, (new_w, new_h))
                
                # Add sample point markers and voxel info
                for py, px, label in sample_points:
                    # Scale coordinates
                    py_s = int(py * scale)
                    px_s = int(px * scale)
                    
                    # Check if this pixel has motion
                    has_motion_left = motion_left[py, px]
                    has_motion_right = motion_right[py, px]
                    
                    # Draw markers
                    color_left = (0, 255, 255) if has_motion_left else (255, 0, 0)  # Yellow if motion, blue if not
                    color_right = (0, 255, 255) if has_motion_right else (255, 0, 0)
                    
                    cv2.circle(display_left, (px_s, py_s), 5, color_left, 2)
                    cv2.circle(display_right, (px_s, py_s), 5, color_right, 2)
                    
                    # Get voxel coordinates
                    voxels_left = pixel_to_voxel_coords(py, px, 1080, 1920, 
                                                        camera_left_pos, grid_size)
                    voxels_right = pixel_to_voxel_coords(py, px, 1080, 1920,
                                                         camera_right_pos, grid_size)
                    
                    # Show first voxel coordinate as text
                    if len(voxels_left) > 0:
                        vox = voxels_left[len(voxels_left)//2]  # Middle voxel
                        text = f"V:{vox[0]},{vox[1]},{vox[2]}"
                        cv2.putText(display_left, text, (px_s+10, py_s), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, color_left, 1)
                
                # Add info text
                info_text = [
                    f"Frame: {frame_count}",
                    f"Motion: L={motion_count_left} R={motion_count_right}",
                    f"Bright: L={img_left.mean():.0f} R={img_right.mean():.0f}",
                    f"Threshold: {motion_threshold}",
                    "Yellow=Motion, Blue=Static"
                ]
                
                y_pos = 20
                for text in info_text:
                    cv2.putText(display_left, text, (10, y_pos),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                    y_pos += 20
                
                # Add camera labels
                cv2.putText(display_left, "LEFT CAMERA", (10, new_h-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(display_right, "RIGHT CAMERA", (10, new_h-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Combine side by side
                combined = np.hstack([display_left, display_right])
                
                # Add title bar
                title_bar = np.zeros((40, combined.shape[1], 3), dtype=np.uint8)
                cv2.putText(title_bar, "VOXEL PROJECTION DEBUG - Green=Motion, Markers=Sample Points",
                           (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                final_display = np.vstack([title_bar, combined])
                
                # Update previous frames
                prev_left = img_left.copy()
                prev_right = img_right.copy()
            
            else:
                # Paused - just show last frame
                pass
            
            # Display
            cv2.imshow('Voxel Projection Debug', final_display)
            
            # Handle keyboard
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27 or key == ord('q'):  # ESC or Q
                print("\nStopping...")
                break
            elif key == ord(' '):  # SPACE
                paused = not paused
                print("PAUSED" if paused else "RESUMED")
            elif key == ord('+') or key == ord('='):
                motion_threshold = min(100, motion_threshold + 5)
                print(f"Threshold: {motion_threshold}")
            elif key == ord('-') or key == ord('_'):
                motion_threshold = max(5, motion_threshold - 5)
                print(f"Threshold: {motion_threshold}")
    
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    finally:
        # Cleanup
        cv2.destroyAllWindows()
        cameras.stop_capture()
        cameras.close()
        
        print("\n" + "="*70)
        print("  DEBUG SUMMARY")
        print("="*70)
        print(f"Frames processed: {frame_count}")
        print(f"Final motion threshold: {motion_threshold}")
        print()
        print("Observations:")
        if motion_count_left + motion_count_right < 1000:
            print("  [LOW MOTION] Scene is mostly static or very dark")
            print("  -> Add lighting or move bright objects")
        else:
            print(f"  [MOTION DETECTED] {motion_count_left + motion_count_right} pixels")
        
        if img_left.mean() < 50:
            print("  [TOO DARK] Average brightness < 50/255")
            print("  -> Increase exposure or gain")
        else:
            print(f"  [BRIGHTNESS OK] Average: {img_left.mean():.0f}/255")
        
        print()
        print("The markers show sample pixel voxel projections:")
        print("  - Yellow markers = pixels with motion")
        print("  - Blue markers = static pixels")
        print("  - V:z,y,x numbers = voxel coordinates at mid-depth")
        print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())




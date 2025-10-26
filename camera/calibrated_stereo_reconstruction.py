"""
Calibrated Stereo Voxel Reconstruction

Uses ArUco stereo calibration for accurate 3D reconstruction.
"""

import cv2
import numpy as np
import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem


class CalibratedStereoReconstructor:
    def __init__(self, calibration_file):
        """
        Initialize with ArUco stereo calibration.
        
        Args:
            calibration_file: Path to stereo_calibration.json
        """
        # Load calibration
        print(f"Loading calibration from: {calibration_file}")
        with open(calibration_file, 'r') as f:
            calib = json.load(f)
        
        # Left camera parameters
        K_left = np.array(calib['left_camera']['camera_matrix'], dtype=np.float32)
        self.fx_left = K_left[0, 0]
        self.fy_left = K_left[1, 1]
        self.cx_left = K_left[0, 2]
        self.cy_left = K_left[1, 2]
        D_left = np.array(calib['left_camera']['distortion'], dtype=np.float32)
        self.k1_left = D_left[0, 0] if D_left.ndim > 1 else D_left[0]
        
        # Right camera parameters
        K_right = np.array(calib['right_camera']['camera_matrix'], dtype=np.float32)
        self.fx_right = K_right[0, 0]
        self.fy_right = K_right[1, 1]
        self.cx_right = K_right[0, 2]
        self.cy_right = K_right[1, 2]
        D_right = np.array(calib['right_camera']['distortion'], dtype=np.float32)
        self.k1_right = D_right[0, 0] if D_right.ndim > 1 else D_right[0]
        
        # Stereo parameters
        R = np.array(calib['stereo']['rotation'], dtype=np.float32)
        T = np.array(calib['stereo']['translation'], dtype=np.float32).reshape(3, 1)
        self.baseline = float(calib['stereo']['baseline'])
        
        # Camera positions in world coordinates
        # Left camera at origin
        self.cam_left_pos = np.array([0.0, 0.0, 0.0])
        
        # Right camera position from stereo calibration
        self.cam_right_pos = T.flatten()
        
        # Right camera rotation relative to left
        self.R_right = R
        
        # Voxel grid (1cm resolution, 1.5m x 1.5m x 1m volume)
        self.voxel_size = 0.01  # 1cm
        self.voxel_grid_size = (150, 150, 100)
        self.voxel_bounds = {
            'x': (-0.5, 1.0),     # 1.5m wide
            'y': (-0.75, 0.75),   # 1.5m deep
            'z': (0.0, 1.0)       # 0=ground, 1m high
        }
        self.voxels = np.zeros(self.voxel_grid_size, dtype=np.float32)
        
        # Motion detection
        self.prev_left = None
        self.prev_right = None
        self.motion_threshold = 30
        self.min_pixel_intensity = 100
        
        # Triangulation (strict for fisheye!)
        self.max_triangulation_error = 0.02  # 2cm - very strict to avoid false positives
        
        # Statistics
        self.frame_count = 0
        self.voxel_count = 0
        self.triangulation_count = 0
        self.triangulation_attempts = 0
        
        # Track recent positions for display
        self.recent_positions = []
        self.max_recent = 10
        
        print("\nCalibrated Stereo Reconstructor initialized:")
        print(f"  Left camera:")
        print(f"    fx={self.fx_left:.2f}, fy={self.fy_left:.2f}")
        print(f"    cx={self.cx_left:.2f}, cy={self.cy_left:.2f}")
        print(f"    k1={self.k1_left:.6f}")
        print(f"  Right camera:")
        print(f"    fx={self.fx_right:.2f}, fy={self.fy_right:.2f}")
        print(f"    cx={self.cx_right:.2f}, cy={self.cy_right:.2f}")
        print(f"    k1={self.k1_right:.6f}")
        print(f"  Baseline: {self.baseline:.4f}m ({self.baseline*100:.1f}cm)")
        print(f"  Voxel size: {self.voxel_size*100}cm")
        print(f"  Volume: {self.voxel_bounds}")
        print()
    
    def get_ray_direction(self, pixel_x, pixel_y, fx, fy, cx, cy, k1):
        """
        Convert pixel coordinates to 3D ray direction with fisheye correction.
        """
        # Normalize to [-1, 1]
        norm_x = (pixel_x - cx) / fx
        norm_y = (pixel_y - cy) / fy
        
        # Distance from center
        r = np.sqrt(norm_x**2 + norm_y**2)
        
        # Fisheye distortion correction
        if r > 0:
            theta = np.arctan(r)
            theta_distorted = theta * (1 + k1 * theta**2)
            scale = theta_distorted / r
            norm_x *= scale
            norm_y *= scale
        
        # Create 3D ray (Z is height, Y is depth, X is horizontal)
        ray = np.array([
            norm_x,   # Horizontal (X)
            norm_y,   # Depth (Y)
            1.0       # Up (Z - HEIGHT)
        ])
        
        # Normalize
        ray = ray / np.linalg.norm(ray)
        
        return ray
    
    def get_left_ray(self, pixel_x, pixel_y):
        """Get ray from left camera."""
        return self.get_ray_direction(
            pixel_x, pixel_y,
            self.fx_left, self.fy_left,
            self.cx_left, self.cy_left,
            self.k1_left
        )
    
    def get_right_ray(self, pixel_x, pixel_y):
        """Get ray from right camera, transformed to world coordinates."""
        # Get ray in right camera's coordinate system
        ray_right_cam = self.get_ray_direction(
            pixel_x, pixel_y,
            self.fx_right, self.fy_right,
            self.cx_right, self.cy_right,
            self.k1_right
        )
        
        # Transform to world coordinates using rotation matrix
        ray_world = self.R_right @ ray_right_cam
        ray_world = ray_world / np.linalg.norm(ray_world)
        
        return ray_world
    
    def closest_point_between_rays(self, origin1, dir1, origin2, dir2):
        """
        Find the closest point between two 3D rays.
        Returns (midpoint, distance) or (None, None) if parallel.
        """
        # Normalize directions
        dir1 = dir1 / np.linalg.norm(dir1)
        dir2 = dir2 / np.linalg.norm(dir2)
        
        # Check if rays are parallel (angle < 5 degrees)
        dot = np.dot(dir1, dir2)
        if abs(dot) > 0.996:  # cos(5°) ≈ 0.996
            return None, None
        
        # Vector between origins
        w0 = origin1 - origin2
        
        # Solve for closest points
        a = np.dot(dir1, dir1)
        b = np.dot(dir1, dir2)
        c = np.dot(dir2, dir2)
        d = np.dot(dir1, w0)
        e = np.dot(dir2, w0)
        
        denom = a * c - b * b
        if abs(denom) < 1e-6:
            return None, None
        
        s = (b * e - c * d) / denom
        t = (a * e - b * d) / denom
        
        # Closest points on each ray
        point1 = origin1 + s * dir1
        point2 = origin2 + t * dir2
        
        # Midpoint and distance
        midpoint = (point1 + point2) / 2.0
        distance = np.linalg.norm(point2 - point1)
        
        return midpoint, distance
    
    def triangulate_pixel_pair(self, px_left, py_left, px_right, py_right):
        """
        Triangulate 3D position from pixel correspondences.
        Returns (world_position, error) or (None, None) if invalid.
        """
        self.triangulation_attempts += 1
        
        # Get ray directions
        ray_left = self.get_left_ray(px_left, py_left)
        ray_right = self.get_right_ray(px_right, py_right)
        
        # Find intersection
        point_3d, error = self.closest_point_between_rays(
            self.cam_left_pos, ray_left,
            self.cam_right_pos, ray_right
        )
        
        if point_3d is None:
            return None, None
        
        # Validate
        if error > self.max_triangulation_error:
            return None, None
        
        # Check if point is in valid range
        if point_3d[2] < 0:  # Underground
            return None, None
        
        if point_3d[2] > 2.0:  # Too high (2m)
            return None, None
        
        return point_3d, error
    
    def world_to_voxel(self, world_pos):
        """
        Convert world position to voxel grid indices.
        """
        x, y, z = world_pos
        
        # Check bounds
        if not (self.voxel_bounds['x'][0] <= x < self.voxel_bounds['x'][1]):
            return None
        if not (self.voxel_bounds['y'][0] <= y < self.voxel_bounds['y'][1]):
            return None
        if not (self.voxel_bounds['z'][0] <= z < self.voxel_bounds['z'][1]):
            return None
        
        # Convert to voxel indices
        vx = int((x - self.voxel_bounds['x'][0]) / self.voxel_size)
        vy = int((y - self.voxel_bounds['y'][0]) / self.voxel_size)
        vz = int((z - self.voxel_bounds['z'][0]) / self.voxel_size)
        
        # Clamp to grid
        vx = max(0, min(vx, self.voxel_grid_size[0] - 1))
        vy = max(0, min(vy, self.voxel_grid_size[1] - 1))
        vz = max(0, min(vz, self.voxel_grid_size[2] - 1))
        
        return (vx, vy, vz)
    
    def accumulate_voxel(self, world_pos, confidence=1.0):
        """Add detection to voxel grid."""
        voxel_idx = self.world_to_voxel(world_pos)
        if voxel_idx is None:
            return False
        
        vx, vy, vz = voxel_idx
        self.voxels[vx, vy, vz] += confidence
        self.voxel_count += 1
        
        return True
    
    def detect_motion_pixels(self, current, previous, max_pixels=100):
        """Detect pixels with motion."""
        if previous is None:
            return []
        
        # Frame difference
        diff = cv2.absdiff(current, previous)
        
        # Find motion pixels
        motion_mask = diff > self.motion_threshold
        valid_mask = current > self.min_pixel_intensity
        combined_mask = motion_mask & valid_mask
        
        # Get pixel coordinates
        ys, xs = np.where(combined_mask)
        
        if len(xs) == 0:
            return []
        
        # Get intensities
        intensities = current[ys, xs]
        
        # Create list of (x, y, intensity)
        pixels = list(zip(xs, ys, intensities))
        
        # Sample if too many
        if len(pixels) > max_pixels:
            step = len(pixels) // max_pixels
            pixels = pixels[::step][:max_pixels]
        
        return pixels
    
    def process_frame_pair(self, img_left, img_right, show_display=True):
        """Process stereo frame pair and accumulate voxels."""
        self.frame_count += 1
        
        # Detect motion pixels
        pixels_left = self.detect_motion_pixels(img_left, self.prev_left)
        pixels_right = self.detect_motion_pixels(img_right, self.prev_right)
        
        # Store for next frame
        self.prev_left = img_left.copy()
        self.prev_right = img_right.copy()
        
        # Create visualization if requested
        vis_left = None
        vis_right = None
        if show_display:
            vis_left = cv2.cvtColor(img_left, cv2.COLOR_GRAY2BGR)
            vis_right = cv2.cvtColor(img_right, cv2.COLOR_GRAY2BGR)
            
            # Mark motion pixels in yellow
            for px, py, _ in pixels_left:
                cv2.circle(vis_left, (int(px), int(py)), 2, (0, 255, 255), -1)
            for px, py, _ in pixels_right:
                cv2.circle(vis_right, (int(px), int(py)), 2, (0, 255, 255), -1)
        
        # Need minimum motion in BOTH cameras to avoid random noise
        if len(pixels_left) < 5 or len(pixels_right) < 5:
            return 0, 0, 0, 0, vis_left, vis_right  # triangulations, successful, motion_left, motion_right, displays
        
        # Try to match pixels and triangulate
        triangulations = 0
        successful = 0
        successful_pixels_left = []
        successful_pixels_right = []
        
        for px_l, py_l, int_l in pixels_left[:50]:
            for px_r, py_r, int_r in pixels_right[:50]:
                # Pre-filter: Intensity similarity check
                # Corresponding points should have similar brightness
                intensity_diff = abs(int_l - int_r)
                if intensity_diff > 50:  # Allow 50 grayscale units difference
                    continue
                
                triangulations += 1
                
                # Try triangulation
                point_3d, error = self.triangulate_pixel_pair(px_l, py_l, px_r, py_r)
                
                if point_3d is not None:
                    # Accumulate voxel
                    confidence = (int_l + int_r) / (2.0 * 255.0)
                    if self.accumulate_voxel(point_3d, confidence):
                        successful += 1
                        self.triangulation_count += 1
                        successful_pixels_left.append((px_l, py_l))
                        successful_pixels_right.append((px_r, py_r))
                        
                        # Store recent position
                        self.recent_positions.append(point_3d.copy())
                        if len(self.recent_positions) > self.max_recent:
                            self.recent_positions.pop(0)
        
        # Mark successful triangulations in green
        if show_display and vis_left is not None:
            for px, py in successful_pixels_left:
                cv2.circle(vis_left, (int(px), int(py)), 3, (0, 255, 0), -1)
            for px, py in successful_pixels_right:
                cv2.circle(vis_right, (int(px), int(py)), 3, (0, 255, 0), -1)
        
        return triangulations, successful, len(pixels_left), len(pixels_right), vis_left, vis_right
    
    def get_recent_positions(self, count=5):
        """Get the most recent N triangulated positions."""
        if not self.recent_positions:
            return []
        return self.recent_positions[-count:]
    
    def save_voxels(self, output_path, min_confidence=1.0):
        """Save voxel grid to binary file."""
        # Adjustable threshold for filtering
        threshold = min_confidence
        occupied = self.voxels > threshold
        
        # Get indices and values
        indices = np.argwhere(occupied)
        values = self.voxels[occupied]
        
        # Convert to world coordinates
        world_coords = []
        for idx, val in zip(indices, values):
            vx, vy, vz = idx
            x = self.voxel_bounds['x'][0] + vx * self.voxel_size
            y = self.voxel_bounds['y'][0] + vy * self.voxel_size
            z = self.voxel_bounds['z'][0] + vz * self.voxel_size
            world_coords.append([x, y, z, val])
        
        world_coords = np.array(world_coords, dtype=np.float32)
        
        # Save
        with open(output_path, 'wb') as f:
            f.write(world_coords.tobytes())
        
        return len(world_coords)
    
    def print_stats(self):
        """Print reconstruction statistics."""
        success_rate = (self.triangulation_count / self.triangulation_attempts * 100
                       if self.triangulation_attempts > 0 else 0)
        
        print(f"\n{'='*70}")
        print(f"  RECONSTRUCTION STATISTICS")
        print(f"{'='*70}")
        print(f"Frames processed:        {self.frame_count}")
        print(f"Triangulation attempts:  {self.triangulation_attempts}")
        print(f"Successful triangles:    {self.triangulation_count}")
        print(f"Success rate:            {success_rate:.1f}%")
        print(f"Voxels accumulated:      {self.voxel_count}")
        print(f"\nConfidence Distribution:")
        print(f"  Total voxels touched:  {np.sum(self.voxels > 0.0)}")
        print(f"  Unique voxels (>1):    {np.sum(self.voxels > 1.0)}")
        print(f"  Confident (>2):        {np.sum(self.voxels > 2.0)}")
        print(f"  Very confident (>3):   {np.sum(self.voxels > 3.0)}")
        print(f"  Highly confident (>5): {np.sum(self.voxels > 5.0)}")
        if np.sum(self.voxels > 0) > 0:
            print(f"  Max confidence:        {self.voxels.max():.1f}")
        print(f"{'='*70}\n")


def main():
    print("="*70)
    print("  CALIBRATED STEREO VOXEL RECONSTRUCTION")
    print("  (Using ArUco stereo calibration)")
    print("="*70)
    print()
    
    # Check for calibration file
    calib_file = Path("camera/aruco_calibration/stereo_calibration.json")
    if not calib_file.exists():
        print("[ERROR] Calibration file not found!")
        print(f"Expected: {calib_file}")
        print()
        print("Run stereo calibration first:")
        print("  python camera\\aruco_stereo_capture.py")
        print("  python camera\\aruco_stereo_compute.py")
        return
    
    # Initialize reconstructor
    reconstructor = CalibratedStereoReconstructor(str(calib_file))
    
    # Initialize cameras
    print("Initializing cameras...")
    cameras = DualASICameraSystem()
    cameras.configure(exposure=20000, gain=200)
    cameras.start_capture()
    print("[OK] Cameras ready")
    print()
    
    print("CONTROLS:")
    print("  SPACE - Save voxels and view statistics")
    print("  Q - Quit")
    print("  T/t - Motion threshold (±5)")
    print("  I/i - Min intensity (±10)")
    print("  E/e - Triangulation error (±1cm)")
    print()
    print("Move objects above cameras to accumulate voxels...")
    print()
    
    # Create display window
    cv2.namedWindow("Calibrated Stereo Reconstruction", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Calibrated Stereo Reconstruction", 1280, 480)
    
    try:
        while True:
            # Capture frame pair
            img_left, img_right = cameras.capture_frame_pair()
            
            if img_left is None or img_right is None:
                continue
            
            # Process with visualization
            attempts, success, motion_l, motion_r, vis_left, vis_right = reconstructor.process_frame_pair(
                img_left, img_right, show_display=True
            )
            
            # Create combined display
            if vis_left is not None and vis_right is not None:
                # Resize for display
                h, w = vis_left.shape[:2]
                display_width = 640
                display_height = int(h * display_width / w)
                
                vis_left_small = cv2.resize(vis_left, (display_width, display_height))
                vis_right_small = cv2.resize(vis_right, (display_width, display_height))
                
                # Add text overlays
                # Left camera
                cv2.putText(vis_left_small, "LEFT CAMERA", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(vis_left_small, f"Motion: {motion_l}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # Right camera
                cv2.putText(vis_right_small, "RIGHT CAMERA", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(vis_right_small, f"Motion: {motion_r}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # Combine side by side
                combined = np.hstack([vis_left_small, vis_right_small])
                
                # Add statistics at bottom
                stats_y = display_height - 80
                cv2.putText(combined, f"Frame: {reconstructor.frame_count}", (10, stats_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(combined, f"Triangles: {success}/{attempts}", (10, stats_y + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(combined, f"Total Voxels: {reconstructor.voxel_count}", (10, stats_y + 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                success_rate = (reconstructor.triangulation_count / reconstructor.triangulation_attempts * 100
                               if reconstructor.triangulation_attempts > 0 else 0)
                cv2.putText(combined, f"Success: {success_rate:.1f}%", (250, stats_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Legend
                cv2.putText(combined, "Yellow = Motion", (display_width + 10, stats_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                cv2.putText(combined, "Green = Triangulated", (display_width + 10, stats_y + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Show
                cv2.imshow("Calibrated Stereo Reconstruction", combined)
            
            if success > 0:
                # Get last few triangulated positions for display
                recent_positions = reconstructor.get_recent_positions(5)
                
                print(f"[Frame {reconstructor.frame_count}] "
                      f"Motion: L={motion_l:3d} R={motion_r:3d} | "
                      f"Triangles: {success:3d}/{attempts:4d} | "
                      f"Total voxels: {reconstructor.voxel_count}")
                
                # Print recent 3D positions
                if recent_positions:
                    for pos in recent_positions:
                        x, y, z = pos
                        print(f"    → Detected at: X={x:+.3f}m, Y={y:+.3f}m, Z={z:+.3f}m (Height={z*100:.1f}cm)")
            
            # Keyboard check
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:
                break
            elif key == ord(' '):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Save with different confidence thresholds
                output_all = f"camera/calibrated_voxels_all_{timestamp}.bin"
                output_confident = f"camera/calibrated_voxels_confident_{timestamp}.bin"
                
                count_all = reconstructor.save_voxels(output_all, min_confidence=0.0)
                count_confident = reconstructor.save_voxels(output_confident, min_confidence=3.0)
                
                print(f"\n[OK] Saved {count_all} voxels (all) to: {output_all}")
                print(f"[OK] Saved {count_confident} voxels (confident) to: {output_confident}")
                reconstructor.print_stats()
            elif key == ord('t'):
                reconstructor.motion_threshold = max(5, reconstructor.motion_threshold - 5)
                print(f"Motion threshold: {reconstructor.motion_threshold}")
            elif key == ord('T'):
                reconstructor.motion_threshold = min(100, reconstructor.motion_threshold + 5)
                print(f"Motion threshold: {reconstructor.motion_threshold}")
            elif key == ord('i'):
                reconstructor.min_pixel_intensity = max(10, reconstructor.min_pixel_intensity - 10)
                print(f"Min intensity: {reconstructor.min_pixel_intensity}")
            elif key == ord('I'):
                reconstructor.min_pixel_intensity = min(250, reconstructor.min_pixel_intensity + 10)
                print(f"Min intensity: {reconstructor.min_pixel_intensity}")
            elif key == ord('e'):
                reconstructor.max_triangulation_error = max(0.01, reconstructor.max_triangulation_error - 0.01)
                print(f"Max triangulation error: {reconstructor.max_triangulation_error*100:.0f}cm")
            elif key == ord('E'):
                reconstructor.max_triangulation_error = min(0.50, reconstructor.max_triangulation_error + 0.01)
                print(f"Max triangulation error: {reconstructor.max_triangulation_error*100:.0f}cm")
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    
    finally:
        cv2.destroyAllWindows()
        cameras.stop_capture()
        cameras.close()
        
        # Final save with multiple confidence levels
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_all = f"camera/calibrated_voxels_all_{timestamp}.bin"
        output_confident = f"camera/calibrated_voxels_confident_{timestamp}.bin"
        
        count_all = reconstructor.save_voxels(output_all, min_confidence=0.0)
        count_confident = reconstructor.save_voxels(output_confident, min_confidence=3.0)
        
        print(f"\n[OK] Final save:")
        print(f"  All voxels: {count_all} saved to {output_all}")
        print(f"  Confident (>3): {count_confident} saved to {output_confident}")
        reconstructor.print_stats()
        
        print("\nVisualize with:")
        print(f"  All voxels:      python spacevoxelviewer.py {output_all}")
        print(f"  Confident only:  python spacevoxelviewer.py {output_confident}")
        print()


if __name__ == "__main__":
    main()


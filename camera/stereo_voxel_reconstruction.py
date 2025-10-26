"""
Real-Time Stereo Voxel Reconstruction
Uses existing fisheye calibration + known baseline (0.5m)

No checkerboard calibration needed!
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


class StereoVoxelReconstructor:
    def __init__(self, baseline=0.5):
        """
        Initialize stereo voxel reconstructor.
        
        Args:
            baseline: Distance between cameras in meters (default 0.5m)
        """
        # Camera calibration (from your existing calibration)
        self.fx = 748.0
        self.fy = 748.0
        self.cx = 960.0
        self.cy = 540.0
        self.k1 = -0.15
        
        # Stereo geometry
        self.baseline = baseline
        
        # Camera positions
        self.cam_left_pos = np.array([0.0, 0.0, 0.0])    # Left at origin
        self.cam_right_pos = np.array([0.5, 0.0, 0.0])   # Right offset by baseline
        
        # Voxel grid (1cm resolution, 1m x 1m x 1m volume)
        self.voxel_size = 0.01  # 1cm
        self.voxel_grid_size = (100, 100, 100)  # 1m in each dimension
        self.voxel_bounds = {
            'x': (-0.25, 0.75),  # Centered between cameras
            'y': (-0.5, 0.5),
            'z': (0.0, 1.0)      # 0 = ground, up to 1m
        }
        self.voxels = np.zeros(self.voxel_grid_size, dtype=np.float32)
        
        # Motion detection
        self.prev_left = None
        self.prev_right = None
        self.motion_threshold = 30
        self.min_pixel_intensity = 100
        
        # Triangulation
        self.max_triangulation_error = 0.10  # 10cm tolerance for fisheye
        
        # Statistics
        self.frame_count = 0
        self.voxel_count = 0
        self.triangulation_count = 0
        
        print("Stereo Voxel Reconstructor initialized:")
        print(f"  Baseline: {baseline}m")
        print(f"  Voxel size: {self.voxel_size*100}cm")
        print(f"  Volume: {self.voxel_bounds}")
        print()
    
    def get_ray_direction(self, pixel_x, pixel_y):
        """
        Convert pixel coordinates to 3D ray direction.
        Includes fisheye distortion correction.
        """
        # Normalize to [-1, 1]
        norm_x = (pixel_x - self.cx) / self.fx
        norm_y = (pixel_y - self.cy) / self.fy
        
        # Distance from center
        r = np.sqrt(norm_x**2 + norm_y**2)
        
        # Fisheye distortion correction
        if r > 0:
            theta = np.arctan(r)
            theta_distorted = theta * (1 + self.k1 * theta**2)
            scale = theta_distorted / r
            norm_x *= scale
            norm_y *= scale
        
        # Create 3D ray (Z is height, Y is depth)
        ray = np.array([
            norm_x,   # Horizontal (X)
            norm_y,   # Depth (Y)
            1.0       # Up (Z - HEIGHT)
        ])
        
        # Normalize
        ray = ray / np.linalg.norm(ray)
        
        return ray
    
    def closest_point_between_rays(self, origin1, dir1, origin2, dir2):
        """
        Find the closest point between two 3D rays.
        Returns (midpoint, distance_between_rays) or (None, None) if parallel.
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
        Triangulate 3D position from pixel correspondences in both cameras.
        Returns (world_position, error) or (None, None) if invalid.
        """
        # Get ray directions
        ray_left = self.get_ray_direction(px_left, py_left)
        ray_right = self.get_ray_direction(px_right, py_right)
        
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
        Convert world position (meters) to voxel grid indices.
        Returns (vx, vy, vz) or None if out of bounds.
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
        """
        Add detection to voxel grid.
        """
        voxel_idx = self.world_to_voxel(world_pos)
        if voxel_idx is None:
            return False
        
        vx, vy, vz = voxel_idx
        self.voxels[vx, vy, vz] += confidence
        self.voxel_count += 1
        
        return True
    
    def detect_motion_pixels(self, current, previous, max_pixels=100):
        """
        Detect pixels with motion. Returns list of (x, y, intensity) tuples.
        """
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
    
    def process_frame_pair(self, img_left, img_right):
        """
        Process a stereo frame pair and accumulate voxels.
        """
        self.frame_count += 1
        
        # Detect motion pixels in both cameras
        pixels_left = self.detect_motion_pixels(img_left, self.prev_left)
        pixels_right = self.detect_motion_pixels(img_right, self.prev_right)
        
        # Store for next frame
        self.prev_left = img_left.copy()
        self.prev_right = img_right.copy()
        
        if not pixels_left or not pixels_right:
            return 0  # No motion detected
        
        # Try to match pixels and triangulate
        # Simple strategy: try all combinations (limited by sampling above)
        triangulations = 0
        
        for px_l, py_l, int_l in pixels_left[:50]:  # Limit combinations
            for px_r, py_r, int_r in pixels_right[:50]:
                # Try triangulation
                point_3d, error = self.triangulate_pixel_pair(px_l, py_l, px_r, py_r)
                
                if point_3d is not None:
                    # Accumulate voxel with confidence based on intensity
                    confidence = (int_l + int_r) / (2.0 * 255.0)
                    if self.accumulate_voxel(point_3d, confidence):
                        triangulations += 1
                        self.triangulation_count += 1
        
        return triangulations
    
    def save_voxels(self, output_path):
        """
        Save voxel grid to binary file.
        """
        # Find occupied voxels
        threshold = 1.0  # Minimum confidence
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
        
        # Save as binary
        with open(output_path, 'wb') as f:
            f.write(world_coords.tobytes())
        
        return len(world_coords)
    
    def print_stats(self):
        """Print reconstruction statistics."""
        print(f"\n{'='*70}")
        print(f"  RECONSTRUCTION STATISTICS")
        print(f"{'='*70}")
        print(f"Frames processed:      {self.frame_count}")
        print(f"Triangulations:        {self.triangulation_count}")
        print(f"Voxels accumulated:    {self.voxel_count}")
        print(f"Unique voxels:         {np.sum(self.voxels > 1.0)}")
        print(f"{'='*70}\n")


def main():
    print("="*70)
    print("  STEREO VOXEL RECONSTRUCTION")
    print("  (No checkerboard calibration needed!)")
    print("="*70)
    print()
    
    # Initialize reconstructor
    reconstructor = StereoVoxelReconstructor(baseline=0.5)
    
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
    print()
    print("Move objects above the cameras to accumulate voxels...")
    print()
    
    try:
        while True:
            # Capture frame pair
            img_left, img_right = cameras.capture_frame_pair()
            
            if img_left is None or img_right is None:
                continue
            
            # Process
            triangulations = reconstructor.process_frame_pair(img_left, img_right)
            
            if triangulations > 0:
                print(f"[Frame {reconstructor.frame_count}] "
                      f"Triangulated: {triangulations}, "
                      f"Total voxels: {reconstructor.voxel_count}")
            
            # Simple keyboard check (non-blocking)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 27:  # Q or ESC
                break
            elif key == ord(' '):  # SPACE
                # Save voxels
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"camera/stereo_voxels_{timestamp}.bin"
                count = reconstructor.save_voxels(output_path)
                print(f"\n✓ Saved {count} voxels to: {output_path}")
                reconstructor.print_stats()
            elif key == ord('t'):
                reconstructor.motion_threshold -= 5
                print(f"Motion threshold: {reconstructor.motion_threshold}")
            elif key == ord('T'):
                reconstructor.motion_threshold += 5
                print(f"Motion threshold: {reconstructor.motion_threshold}")
            elif key == ord('i'):
                reconstructor.min_pixel_intensity -= 10
                print(f"Min intensity: {reconstructor.min_pixel_intensity}")
            elif key == ord('I'):
                reconstructor.min_pixel_intensity += 10
                print(f"Min intensity: {reconstructor.min_pixel_intensity}")
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    
    finally:
        cameras.stop_capture()
        cameras.close()
        
        # Final save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"camera/stereo_voxels_{timestamp}.bin"
        count = reconstructor.save_voxels(output_path)
        print(f"\n✓ Final save: {count} voxels to: {output_path}")
        reconstructor.print_stats()
        
        print("\nVisualize with:")
        print(f"  python spacevoxelviewer.py {output_path}")
        print()


if __name__ == "__main__":
    main()



"""
Live Voxel Viewer with Coordinates Display

Shows camera feeds with motion highlighting AND detected voxel coordinates.

Features:
  - Side-by-side camera feeds (GREEN=valid, RED=filtered)
  - Real-time voxel detection
  - Scrolling coordinate display window
  - World coordinate conversion (X, Y, Z in meters)

Controls:
  Q: Quit
  T/t: Increase/decrease motion threshold
  I/i: Increase/decrease intensity threshold
  C: Clear coordinate history
  S: Save screenshot
  R: Reset to defaults
"""

import numpy as np
import cv2
import sys
import os
import time
from datetime import datetime
from collections import deque

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem
from calibration_loader import load_calibration


class LiveVoxelViewer:
    """Live viewer with voxel coordinate display."""
    
    def __init__(self):
        # Detection parameters
        self.motion_threshold = 25
        self.intensity_threshold = 80
        self.blur_kernel = 5
        
        # Voxel parameters
        self.grid_size = 64
        self.voxel_size = 0.01  # 1cm
        self.voxel_print_threshold = 30  # Minimum intensity to display
        
        # Camera positions
        self.camera_left_pos = np.array([0.0, 0.0, 0.0])
        self.camera_right_pos = np.array([0.5, 0.0, 0.0])
        
        # Voxel grid
        self.voxel_grid = np.zeros((self.grid_size, self.grid_size, self.grid_size), 
                                   dtype=np.float32)
        self.temporal_decay = 0.95
        
        # Coordinate history (for display)
        self.coord_history = deque(maxlen=50)  # Keep last 50 detections
        
        self.cameras = None
        self.calib = None
        self.prev_left = None
        self.prev_right = None
        
        self.stats = {'fps': 0}
    
    def initialize_cameras(self):
        """Initialize camera system and calibration."""
        print("="*70)
        print("  LIVE VOXEL VIEWER - Real-time Coordinate Display")
        print("="*70)
        print()
        
        # Load calibration
        try:
            self.calib = load_calibration("camera/calibration.yml")
            print("[OK] Fisheye calibration loaded")
        except:
            print("[WARN] No calibration - using simple projection")
            self.calib = None
        
        print("Initializing cameras...")
        self.cameras = DualASICameraSystem()
        self.cameras.configure(exposure=30000, gain=300)
        self.cameras.start_capture()
        print("[OK] Cameras ready\n")
        
        time.sleep(0.5)
        self.prev_left, self.prev_right = self.cameras.capture_frame_pair()
        print("[OK] Baseline captured\n")
        
        print("Coordinate System:")
        print("  X: Horizontal (left-right)")
        print("  Y: Depth (forward-back)")
        print("  Z: HEIGHT (up-down, Z=0 = ground)")
        print()
        print("="*70)
        print("  CONTROLS")
        print("="*70)
        print("  Q: Quit")
        print("  T/t: Motion threshold ±5")
        print("  I/i: Intensity threshold ±10")
        print("  C: Clear coordinate history")
        print("  S: Save screenshot")
        print("  R: Reset defaults")
        print("="*70)
        print()
    
    def traverse_ray_3d(self, camera_pos, ray_dir, intensity):
        """
        Traverse ray and return voxels.
        
        Returns list of (vox_x, vox_y, vox_z, weighted_intensity)
        """
        voxels = []
        visited = set()
        
        max_distance = 0.64  # 64cm max
        step_size = self.voxel_size * 0.5
        num_steps = int(max_distance / step_size)
        
        for i in range(num_steps):
            t = i * step_size
            point = camera_pos + ray_dir * t
            
            # Skip below ground
            if point[2] < 0:  # Z is height
                continue
            
            # Convert to voxel coordinates
            vox_x = int((point[0] + 0.25) / self.voxel_size)
            vox_y = int(point[1] / self.voxel_size)
            vox_z = int(point[2] / self.voxel_size)
            
            if not (0 <= vox_x < self.grid_size and
                    0 <= vox_y < self.grid_size and
                    0 <= vox_z < self.grid_size):
                continue
            
            key = (vox_x, vox_y, vox_z)
            if key in visited:
                continue
            visited.add(key)
            
            # Distance falloff
            dist = np.linalg.norm(point - camera_pos)
            falloff = 1.0 / (1.0 + dist * 0.2)
            
            weighted = intensity * falloff
            voxels.append((vox_x, vox_y, vox_z, weighted))
        
        return voxels
    
    def voxel_to_world(self, vox_x, vox_y, vox_z):
        """Convert voxel coordinates to world coordinates."""
        world_x = (vox_x * self.voxel_size) - 0.25
        world_y = vox_y * self.voxel_size
        world_z = vox_z * self.voxel_size
        return world_x, world_y, world_z
    
    def process_frame(self, img_current, img_prev, camera_pos, camera_name):
        """
        Process frame, detect motion, and project to voxels.
        
        Returns:
            display_img: Highlighted image
            valid_count: Number of valid motion pixels
            voxel_list: List of detected voxels
        """
        # Motion detection
        if self.blur_kernel > 1:
            curr_blur = cv2.GaussianBlur(img_current, (self.blur_kernel, self.blur_kernel), 0)
            prev_blur = cv2.GaussianBlur(img_prev, (self.blur_kernel, self.blur_kernel), 0)
        else:
            curr_blur = img_current
            prev_blur = img_prev
        
        diff = np.abs(curr_blur.astype(np.int16) - prev_blur.astype(np.int16))
        motion_mask = diff > self.motion_threshold
        intensity_mask = img_current > self.intensity_threshold
        valid_motion = motion_mask & intensity_mask
        
        # Create display
        display_img = cv2.cvtColor(img_current, cv2.COLOR_GRAY2BGR)
        display_img[motion_mask & ~intensity_mask] = [0, 0, 255]  # Red
        display_img[valid_motion] = [0, 255, 0]  # Green
        
        # Get motion coordinates
        motion_coords = np.argwhere(valid_motion)
        valid_count = len(motion_coords)
        
        # Project to voxels
        voxel_list = []
        for py, px in motion_coords:
            pixel_intensity = img_current[py, px] / 255.0
            
            # Get ray direction
            if self.calib:
                ray_dir = self.calib.get_ray_direction(px, py)
            else:
                norm_x = (px - 960) / 755.0
                norm_y = (py - 540) / 752.0
                ray_dir = np.array([norm_x, norm_y, 1.0])
                ray_dir = ray_dir / np.linalg.norm(ray_dir)
            
            # Traverse ray
            voxels = self.traverse_ray_3d(camera_pos, ray_dir, pixel_intensity)
            voxel_list.extend(voxels)
        
        return display_img, valid_count, voxel_list
    
    def create_coordinate_display(self, width=600, height=800):
        """Create coordinate display panel."""
        panel = np.zeros((height, width, 3), dtype=np.uint8)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Title
        cv2.putText(panel, "DETECTED VOXEL COORDINATES", (10, 30),
                   font, 0.6, (255, 255, 0), 2)
        
        cv2.line(panel, (0, 40), (width, 40), (255, 255, 255), 1)
        
        # Column headers
        y = 65
        cv2.putText(panel, "Grid (x,y,z)", (10, y), font, 0.5, (200, 200, 200), 1)
        cv2.putText(panel, "World (X,Y,Z) m", (200, y), font, 0.5, (200, 200, 200), 1)
        cv2.putText(panel, "Int", (480, y), font, 0.5, (200, 200, 200), 1)
        
        cv2.line(panel, (0, y+5), (width, y+5), (100, 100, 100), 1)
        
        # Coordinate list (most recent first)
        y_start = y + 25
        line_height = 22
        max_lines = (height - y_start - 100) // line_height
        
        for i, coord_data in enumerate(reversed(list(self.coord_history)[-max_lines:])):
            y_pos = y_start + i * line_height
            
            vox_x, vox_y, vox_z = coord_data['voxel']
            world_x, world_y, world_z = coord_data['world']
            intensity = coord_data['intensity']
            camera = coord_data['camera']
            
            # Color based on camera
            color = (0, 255, 255) if camera == 'L' else (255, 128, 0)
            
            # Camera indicator
            cv2.putText(panel, f"[{camera}]", (10, y_pos), 
                       font, 0.4, color, 1)
            
            # Voxel coordinates
            cv2.putText(panel, f"({vox_x:2d},{vox_y:2d},{vox_z:2d})", 
                       (50, y_pos), font, 0.4, (150, 255, 150), 1)
            
            # World coordinates
            cv2.putText(panel, f"({world_x:+.2f},{world_y:.2f},{world_z:.2f})", 
                       (200, y_pos), font, 0.4, (100, 255, 255), 1)
            
            # Intensity bar
            bar_width = int(intensity / 3)
            if bar_width > 0:
                cv2.rectangle(panel, (480, y_pos-10), (480 + bar_width, y_pos), 
                             (0, 255, 0), -1)
            
            cv2.putText(panel, f"{intensity:.0f}", (540, y_pos), 
                       font, 0.35, (200, 200, 200), 1)
        
        # Statistics at bottom
        y_bottom = height - 90
        cv2.line(panel, (0, y_bottom), (width, y_bottom), (100, 100, 100), 1)
        
        y_bottom += 25
        cv2.putText(panel, "STATISTICS:", (10, y_bottom), 
                   font, 0.5, (255, 255, 255), 1)
        
        y_bottom += 25
        total_voxels = np.count_nonzero(self.voxel_grid)
        max_intensity = np.max(self.voxel_grid)
        
        cv2.putText(panel, f"Active voxels: {total_voxels}", 
                   (10, y_bottom), font, 0.45, (0, 255, 255), 1)
        y_bottom += 22
        cv2.putText(panel, f"Max intensity: {max_intensity:.1f}", 
                   (10, y_bottom), font, 0.45, (0, 255, 255), 1)
        y_bottom += 22
        cv2.putText(panel, f"Detections: {len(self.coord_history)}", 
                   (10, y_bottom), font, 0.45, (0, 255, 255), 1)
        
        return panel
    
    def run(self):
        """Run live viewer."""
        self.initialize_cameras()
        
        print("Starting live view...")
        print("Move objects above cameras!")
        print()
        
        frame_times = []
        
        try:
            while True:
                start_time = time.time()
                
                # Capture
                img_left, img_right = self.cameras.capture_frame_pair()
                if img_left is None or img_right is None:
                    continue
                
                # Process both cameras
                left_display, left_count, left_voxels = self.process_frame(
                    img_left, self.prev_left, self.camera_left_pos, "LEFT"
                )
                
                right_display, right_count, right_voxels = self.process_frame(
                    img_right, self.prev_right, self.camera_right_pos, "RIGHT"
                )
                
                # Update voxel grid
                for vox_x, vox_y, vox_z, intensity in left_voxels:
                    self.voxel_grid[vox_x, vox_y, vox_z] += intensity * 0.1
                
                for vox_x, vox_y, vox_z, intensity in right_voxels:
                    self.voxel_grid[vox_x, vox_y, vox_z] += intensity * 0.1
                
                # Temporal decay
                self.voxel_grid *= self.temporal_decay
                
                # Find high-intensity voxels for display
                high_voxels = np.argwhere(self.voxel_grid > self.voxel_print_threshold)
                
                for vox_x, vox_y, vox_z in high_voxels:
                    intensity = self.voxel_grid[vox_x, vox_y, vox_z]
                    world_x, world_y, world_z = self.voxel_to_world(vox_x, vox_y, vox_z)
                    
                    # Determine which camera (approximate)
                    camera_marker = 'L' if world_x < 0.25 else 'R'
                    
                    # Add to history (avoid duplicates)
                    coord_key = (vox_x, vox_y, vox_z)
                    if not any(c['voxel'] == coord_key for c in list(self.coord_history)[-5:]):
                        self.coord_history.append({
                            'voxel': coord_key,
                            'world': (world_x, world_y, world_z),
                            'intensity': intensity,
                            'camera': camera_marker
                        })
                
                # Create displays
                h, w = left_display.shape[:2]
                scale = 0.5
                new_w, new_h = int(w * scale), int(h * scale)
                
                left_small = cv2.resize(left_display, (new_w, new_h))
                right_small = cv2.resize(right_display, (new_w, new_h))
                camera_view = np.hstack([left_small, right_small])
                
                # Add labels
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(camera_view, "LEFT", (10, 25), font, 0.7, (255, 255, 0), 2)
                cv2.putText(camera_view, "RIGHT", (new_w + 10, 25), font, 0.7, (0, 255, 255), 2)
                
                # Parameters overlay
                param_text = [
                    f"Motion: {self.motion_threshold}",
                    f"Intensity: {self.intensity_threshold}",
                    f"FPS: {self.stats['fps']:.1f}"
                ]
                
                y_offset = camera_view.shape[0] - 70
                for text in param_text:
                    cv2.putText(camera_view, text, (10, y_offset), 
                               font, 0.5, (0, 255, 255), 1)
                    y_offset += 20
                
                # Coordinate panel
                coord_panel = self.create_coordinate_display(
                    width=600, 
                    height=camera_view.shape[0]
                )
                
                # Combine side-by-side
                full_display = np.hstack([camera_view, coord_panel])
                
                # Show
                cv2.imshow('Live Voxel Viewer - Cameras + Coordinates', full_display)
                
                # Update previous
                self.prev_left = img_left.copy()
                self.prev_right = img_right.copy()
                
                # FPS
                frame_time = time.time() - start_time
                frame_times.append(frame_time)
                if len(frame_times) > 30:
                    frame_times.pop(0)
                self.stats['fps'] = 1.0 / np.mean(frame_times)
                
                # Handle keys
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == ord('Q'):
                    break
                elif key == ord('T'):
                    self.motion_threshold = min(self.motion_threshold + 5, 100)
                    print(f"Motion threshold: {self.motion_threshold}")
                elif key == ord('t'):
                    self.motion_threshold = max(self.motion_threshold - 5, 5)
                    print(f"Motion threshold: {self.motion_threshold}")
                elif key == ord('I'):
                    self.intensity_threshold = min(self.intensity_threshold + 10, 250)
                    print(f"Intensity threshold: {self.intensity_threshold}")
                elif key == ord('i'):
                    self.intensity_threshold = max(self.intensity_threshold - 10, 20)
                    print(f"Intensity threshold: {self.intensity_threshold}")
                elif key == ord('C') or key == ord('c'):
                    self.coord_history.clear()
                    self.voxel_grid.fill(0)
                    print("Cleared history and grid")
                elif key == ord('S') or key == ord('s'):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"camera/voxel_viewer_{timestamp}.png"
                    cv2.imwrite(filename, full_display)
                    print(f"[SAVED] {filename}")
                elif key == ord('R') or key == ord('r'):
                    self.motion_threshold = 25
                    self.intensity_threshold = 80
                    print("Reset to defaults")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted")
        
        finally:
            self.cameras.stop_capture()
            self.cameras.close()
            cv2.destroyAllWindows()
            
            print("\n" + "="*70)
            print("  SESSION SUMMARY")
            print("="*70)
            print(f"Total detections: {len(self.coord_history)}")
            print(f"Final voxels: {np.count_nonzero(self.voxel_grid)}")
            print(f"Max intensity: {np.max(self.voxel_grid):.1f}")
            print("="*70)


def main():
    viewer = LiveVoxelViewer()
    viewer.run()


if __name__ == "__main__":
    main()




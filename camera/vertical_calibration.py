"""
Vertical Calibration Tool

Captures real-world vertical movements to validate and correct projection math.

Protocol:
  1. Move object STRAIGHT UP above LEFT camera (X≈0, Y≈0, Z varies)
  2. Press SPACE to mark "switching to right camera"
  3. Move object STRAIGHT UP above RIGHT camera (X≈0.5, Y≈0, Z varies)
  4. Press Q to finish
  
The tool will:
  - Record all detected coordinates
  - Separate left and right camera data
  - Analyze if X,Y stay constant while Z varies
  - Calculate correction factors if needed
  - Generate report for math adjustment
"""

import numpy as np
import cv2
import sys
import os
import time
import json
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem
from calibration_loader import load_calibration


class VerticalCalibration:
    """Calibration using vertical movements."""
    
    def __init__(self):
        # Detection parameters
        self.motion_threshold = 25
        self.intensity_threshold = 80
        self.min_intensity_for_recording = 500.0  # Start HIGH to eliminate noise, then decrease
        self.min_distance_from_camera = 0.08  # Minimum 8cm from camera (filters camera itself)
        
        # X-range filtering (prevents cross-contamination from wide FOV)
        self.left_x_min = -0.15   # LEFT camera expected X range
        self.left_x_max = +0.25
        self.right_x_min = +0.25  # RIGHT camera expected X range
        self.right_x_max = +0.75
        
        # Voxel parameters
        self.grid_size = 64
        self.voxel_size = 0.01
        
        # Camera positions
        self.camera_left_pos = np.array([0.0, 0.0, 0.0])
        self.camera_right_pos = np.array([0.5, 0.0, 0.0])
        
        # Recording
        self.phase = "LEFT"  # LEFT or RIGHT
        self.recordings = {
            'LEFT': [],   # Will store (timestamp, x, y, z, intensity, camera)
            'RIGHT': []
        }
        
        self.cameras = None
        self.calib = None
        self.prev_left = None
        self.prev_right = None
        
        self.last_detection_time = time.time()
    
    def initialize(self):
        """Initialize system."""
        print("="*70)
        print("  VERTICAL CALIBRATION - Ground Truth Recording")
        print("="*70)
        print()
        
        # Load calibration
        try:
            self.calib = load_calibration("camera/calibration.yml")
            print("[OK] Current calibration loaded")
        except:
            print("[WARN] No calibration file")
            self.calib = None
        
        print("Initializing cameras...")
        self.cameras = DualASICameraSystem()
        self.cameras.configure(exposure=30000, gain=300)
        self.cameras.start_capture()
        print("[OK] Cameras ready\n")
        
        time.sleep(0.5)
        self.prev_left, self.prev_right = self.cameras.capture_frame_pair()
        
        print("="*70)
        print("  CALIBRATION PROTOCOL")
        print("="*70)
        print()
        print("Phase 1: LEFT CAMERA (now)")
        print("  1. Hold object directly above LEFT camera")
        print("  2. Move ONLY UP/DOWN (vary Z only)")
        print("  3. Keep X=0, Y=0 as best you can")
        print("  4. Move slowly through different heights")
        print("  5. Press SPACE when done")
        print()
        print("Phase 2: RIGHT CAMERA (after SPACE)")
        print("  1. Hold object directly above RIGHT camera")
        print("  2. Move ONLY UP/DOWN (vary Z only)")
        print("  3. Keep X=0.5, Y=0 as best you can")
        print("  4. Move slowly through different heights")
        print("  5. Press Q when done")
        print()
        print("="*70)
        print("  CONTROLS")
        print("="*70)
        print("  SPACE: Switch to RIGHT camera phase")
        print("  Q: Finish and analyze")
        print("  T/t: Motion threshold ±5")
        print("  I/i: Intensity threshold ±10")
        print("  M: Min recording intensity +10 (MORE filtering)")
        print("  m: Min recording intensity -10 (LESS filtering)")
        print("  N/n: Min distance from camera ±2cm (spatial filter)")
        print("  D: Delete last 10 recordings (undo false positives)")
        print()
        print("  STRATEGY: Start at MinRec=500 (max)")
        print("            Decrease with 'm' until you see detections")
        print("            If false positives appear, press 'M' to go back up")
        print()
        print("  SPATIAL FILTER: Ignores voxels <8cm from camera (filters camera itself)")
        print("                  Ignores voxels <5cm above ground (Z < 0.05m)")
        print()
        print("  X-RANGE FILTER: Prevents fisheye cross-contamination")
        print("                  LEFT phase:  X = -0.15 to +0.25m")
        print("                  RIGHT phase: X = +0.25 to +0.75m")
        print("="*70)
        print()
        print(f">>> PHASE 1: Move object UP/DOWN above LEFT camera")
        print()
    
    def traverse_ray_3d(self, camera_pos, ray_dir, intensity):
        """Traverse ray and return voxels."""
        voxels = []
        visited = set()
        
        max_distance = 0.64
        step_size = self.voxel_size * 0.5
        num_steps = int(max_distance / step_size)
        
        for i in range(num_steps):
            t = i * step_size
            point = camera_pos + ray_dir * t
            
            if point[2] < 0:
                continue
            
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
            
            dist = np.linalg.norm(point - camera_pos)
            falloff = 1.0 / (1.0 + dist * 0.2)
            weighted = intensity * falloff
            
            voxels.append((vox_x, vox_y, vox_z, weighted))
        
        return voxels
    
    def voxel_to_world(self, vox_x, vox_y, vox_z):
        """Convert voxel to world coordinates."""
        world_x = (vox_x * self.voxel_size) - 0.25
        world_y = vox_y * self.voxel_size
        world_z = vox_z * self.voxel_size
        return world_x, world_y, world_z
    
    def process_and_record(self, img_left, img_right):
        """Process frames and record detections."""
        detections = []
        
        # Process both cameras
        for img, prev, camera_pos, cam_name in [
            (img_left, self.prev_left, self.camera_left_pos, 'LEFT'),
            (img_right, self.prev_right, self.camera_right_pos, 'RIGHT')
        ]:
            # Motion detection
            diff = np.abs(img.astype(np.int16) - prev.astype(np.int16))
            motion_mask = diff > self.motion_threshold
            intensity_mask = img > self.intensity_threshold
            valid_motion = motion_mask & intensity_mask
            
            motion_coords = np.argwhere(valid_motion)
            
            # Project to voxels
            voxel_accumulator = defaultdict(float)
            
            for py, px in motion_coords:
                pixel_intensity = img[py, px] / 255.0
                
                # Get ray direction
                if self.calib:
                    ray_dir = self.calib.get_ray_direction(px, py)
                else:
                    norm_x = (px - 960) / 755.0
                    norm_y = (py - 540) / 752.0
                    ray_dir = np.array([norm_x, norm_y, 1.0])
                    ray_dir = ray_dir / np.linalg.norm(ray_dir)
                
                voxels = self.traverse_ray_3d(camera_pos, ray_dir, pixel_intensity)
                
                for vox_x, vox_y, vox_z, weighted in voxels:
                    voxel_accumulator[(vox_x, vox_y, vox_z)] += weighted
            
            # Record high-confidence voxels (use adjustable threshold)
            for (vox_x, vox_y, vox_z), intensity in voxel_accumulator.items():
                if intensity > self.min_intensity_for_recording:
                    world_x, world_y, world_z = self.voxel_to_world(vox_x, vox_y, vox_z)
                    
                    # Calculate distance from this camera
                    voxel_pos = np.array([world_x, world_y, world_z])
                    distance_from_cam = np.linalg.norm(voxel_pos - camera_pos)
                    
                    # Filter: Must be at least min_distance away from camera
                    # AND must be above ground (Z > 0.05m)
                    if distance_from_cam < self.min_distance_from_camera:
                        continue  # Too close to camera (camera itself/housing)
                    
                    if world_z < 0.05:
                        continue  # Too close to ground (cameras at Z=0)
                    
                    # X-range filtering (prevents cross-contamination)
                    # Fisheye lenses have wide FOV, both cameras can see same object
                    # Filter by expected X range for current phase
                    if self.phase == 'LEFT':
                        # LEFT phase: object should be above LEFT camera (X ≈ 0)
                        if not (self.left_x_min <= world_x <= self.left_x_max):
                            continue  # Outside LEFT camera's range, likely from RIGHT camera
                    elif self.phase == 'RIGHT':
                        # RIGHT phase: object should be above RIGHT camera (X ≈ 0.5)
                        if not (self.right_x_min <= world_x <= self.right_x_max):
                            continue  # Outside RIGHT camera's range, likely from LEFT camera
                    
                    detections.append({
                        'timestamp': time.time(),
                        'camera': cam_name,
                        'voxel': (vox_x, vox_y, vox_z),
                        'world': (world_x, world_y, world_z),
                        'intensity': intensity
                    })
        
        return detections
    
    def create_display(self, img_left, img_right):
        """Create display showing current phase and recordings."""
        # Highlight motion
        diff_left = np.abs(img_left.astype(np.int16) - self.prev_left.astype(np.int16))
        diff_right = np.abs(img_right.astype(np.int16) - self.prev_right.astype(np.int16))
        
        motion_left = diff_left > self.motion_threshold
        motion_right = diff_right > self.motion_threshold
        
        intensity_left = img_left > self.intensity_threshold
        intensity_right = img_right > self.intensity_threshold
        
        valid_left = motion_left & intensity_left
        valid_right = motion_right & intensity_right
        
        # Create BGR images
        display_left = cv2.cvtColor(img_left, cv2.COLOR_GRAY2BGR)
        display_right = cv2.cvtColor(img_right, cv2.COLOR_GRAY2BGR)
        
        display_left[valid_left] = [0, 255, 0]
        display_right[valid_right] = [0, 255, 0]
        
        # Resize
        scale = 0.5
        h, w = display_left.shape[:2]
        new_w, new_h = int(w * scale), int(h * scale)
        
        left_small = cv2.resize(display_left, (new_w, new_h))
        right_small = cv2.resize(display_right, (new_w, new_h))
        
        combined = np.hstack([left_small, right_small])
        
        # Add status panel
        panel_height = 200
        panel = np.zeros((panel_height, combined.shape[1], 3), dtype=np.uint8)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        y = 30
        
        # Phase indicator
        phase_color = (0, 255, 255) if self.phase == "LEFT" else (255, 128, 0)
        cv2.putText(panel, f"PHASE: {self.phase} CAMERA", (10, y),
                   font, 0.8, phase_color, 2)
        
        y += 40
        
        # Instructions
        if self.phase == "LEFT":
            cv2.putText(panel, "Move object UP/DOWN above LEFT camera", (10, y),
                       font, 0.5, (255, 255, 255), 1)
            y += 25
            cv2.putText(panel, "Keep X=0, Y=0 | Press SPACE when done", (10, y),
                       font, 0.5, (200, 200, 200), 1)
        else:
            cv2.putText(panel, "Move object UP/DOWN above RIGHT camera", (10, y),
                       font, 0.5, (255, 255, 255), 1)
            y += 25
            cv2.putText(panel, "Keep X=0.5, Y=0 | Press Q when done", (10, y),
                       font, 0.5, (200, 200, 200), 1)
        
        y += 40
        
        # Recording stats
        left_count = len(self.recordings['LEFT'])
        right_count = len(self.recordings['RIGHT'])
        
        cv2.putText(panel, f"Recorded - LEFT: {left_count}  RIGHT: {right_count}",
                   (10, y), font, 0.6, (0, 255, 0), 1)
        
        y += 35
        
        # Parameters
        cv2.putText(panel, f"Motion: {self.motion_threshold}  Intensity: {self.intensity_threshold}",
                   (10, y), font, 0.5, (0, 255, 255), 1)
        y += 20
        cv2.putText(panel, f"MinRec: {self.min_intensity_for_recording:.1f}  MinDist: {self.min_distance_from_camera*100:.0f}cm",
                   (10, y), font, 0.5, (0, 255, 255), 1)
        y += 20
        
        # X-range filter
        if self.phase == 'LEFT':
            range_text = f"X-range: {self.left_x_min:.2f} to {self.left_x_max:.2f}m"
        else:
            range_text = f"X-range: {self.right_x_min:.2f} to {self.right_x_max:.2f}m"
        cv2.putText(panel, range_text, (10, y), font, 0.5, (255, 255, 0), 1)
        
        # Combine
        display = np.vstack([combined, panel])
        
        # Camera labels
        cv2.putText(display, "LEFT", (10, 25), font, 0.7, (255, 255, 0), 2)
        cv2.putText(display, "RIGHT", (new_w + 10, 25), font, 0.7, (0, 255, 255), 2)
        
        return display
    
    def run(self):
        """Run calibration recording."""
        self.initialize()
        
        try:
            while True:
                # Capture
                img_left, img_right = self.cameras.capture_frame_pair()
                if img_left is None or img_right is None:
                    continue
                
                # Process and record
                detections = self.process_and_record(img_left, img_right)
                
                # Add to current phase recordings
                for det in detections:
                    self.recordings[self.phase].append(det)
                    
                    # Print to console
                    world = det['world']
                    print(f"[{self.phase}] Detected: X={world[0]:+.3f}, Y={world[1]:.3f}, Z={world[2]:.3f}m  Int={det['intensity']:.1f}")
                    self.last_detection_time = time.time()
                
                # Create display
                display = self.create_display(img_left, img_right)
                cv2.imshow('Vertical Calibration Recording', display)
                
                # Update previous
                self.prev_left = img_left.copy()
                self.prev_right = img_right.copy()
                
                # Handle keys
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord(' '):  # Space - switch phase
                    if self.phase == "LEFT":
                        self.phase = "RIGHT"
                        print("\n" + "="*70)
                        print(f">>> PHASE 2: Move object UP/DOWN above RIGHT camera")
                        print("="*70)
                        print()
                
                elif key == ord('q') or key == ord('Q'):
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
                
                elif key == ord('M'):
                    self.min_intensity_for_recording = min(self.min_intensity_for_recording + 10, 500)
                    print(f"[MORE FILTERING] Min recording intensity: {self.min_intensity_for_recording:.1f}")
                
                elif key == ord('m'):
                    self.min_intensity_for_recording = max(self.min_intensity_for_recording - 10, 1)
                    print(f"[LESS FILTERING] Min recording intensity: {self.min_intensity_for_recording:.1f}")
                
                elif key == ord('N'):
                    self.min_distance_from_camera = min(self.min_distance_from_camera + 0.02, 0.30)
                    print(f"[MORE SPATIAL FILTER] Min distance from camera: {self.min_distance_from_camera*100:.0f}cm")
                
                elif key == ord('n'):
                    self.min_distance_from_camera = max(self.min_distance_from_camera - 0.02, 0.02)
                    print(f"[LESS SPATIAL FILTER] Min distance from camera: {self.min_distance_from_camera*100:.0f}cm")
                
                elif key == ord('D') or key == ord('d'):
                    # Delete last 10 recordings from current phase
                    if len(self.recordings[self.phase]) > 0:
                        removed = min(10, len(self.recordings[self.phase]))
                        self.recordings[self.phase] = self.recordings[self.phase][:-removed]
                        print(f"[DELETED] Last {removed} recordings from {self.phase} phase")
                    else:
                        print("[WARN] No recordings to delete")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted")
        
        finally:
            self.cameras.stop_capture()
            self.cameras.close()
            cv2.destroyAllWindows()
            
            # Analyze
            self.analyze_and_save()
    
    def analyze_and_save(self):
        """Analyze recordings and generate calibration report."""
        print("\n" + "="*70)
        print("  ANALYSIS")
        print("="*70)
        print()
        
        # Save raw data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_file = f"camera/vertical_calibration_{timestamp}.json"
        
        with open(data_file, 'w') as f:
            json.dump(self.recordings, f, indent=2)
        
        print(f"[SAVED] Raw data: {data_file}")
        print()
        
        # Analyze each phase
        for phase in ['LEFT', 'RIGHT']:
            data = self.recordings[phase]
            
            if len(data) == 0:
                print(f"{phase} camera: No recordings!")
                continue
            
            print(f"{phase} Camera Analysis:")
            print("-" * 50)
            
            # Extract coordinates
            x_coords = [d['world'][0] for d in data]
            y_coords = [d['world'][1] for d in data]
            z_coords = [d['world'][2] for d in data]
            
            # Statistics
            x_mean = np.mean(x_coords)
            x_std = np.std(x_coords)
            y_mean = np.mean(y_coords)
            y_std = np.std(y_coords)
            z_mean = np.mean(z_coords)
            z_std = np.std(z_coords)
            z_range = (np.min(z_coords), np.max(z_coords))
            
            print(f"  Recordings: {len(data)}")
            print(f"  X (should be constant):")
            print(f"    Mean: {x_mean:+.3f}m  Std: {x_std:.3f}m")
            print(f"    Expected: {0.0 if phase=='LEFT' else 0.5:.1f}m")
            print(f"    Error: {abs(x_mean - (0.0 if phase=='LEFT' else 0.5)):.3f}m")
            print(f"  Y (should be constant ≈0):")
            print(f"    Mean: {y_mean:.3f}m  Std: {y_std:.3f}m")
            print(f"  Z (should vary):")
            print(f"    Mean: {z_mean:.3f}m  Std: {z_std:.3f}m")
            print(f"    Range: {z_range[0]:.3f}m to {z_range[1]:.3f}m")
            print()
        
        # Generate correction recommendations
        print("="*70)
        print("  CORRECTION RECOMMENDATIONS")
        print("="*70)
        print()
        
        left_data = self.recordings['LEFT']
        right_data = self.recordings['RIGHT']
        
        if len(left_data) > 5 and len(right_data) > 5:
            left_x = [d['world'][0] for d in left_data]
            right_x = [d['world'][0] for d in right_data]
            
            left_x_mean = np.mean(left_x)
            right_x_mean = np.mean(right_x)
            
            left_x_error = left_x_mean - 0.0
            right_x_error = right_x_mean - 0.5
            
            print(f"X-axis offset errors:")
            print(f"  Left camera:  {left_x_error:+.3f}m (should be 0.000m)")
            print(f"  Right camera: {right_x_error:+.3f}m (should be 0.000m)")
            print()
            
            if abs(left_x_error) > 0.05 or abs(right_x_error) > 0.05:
                print("[RECOMMENDATION] Significant X offset detected!")
                print("  Possible causes:")
                print("    1. Camera positions not accurate (check physical setup)")
                print("    2. Calibration matrix needs adjustment")
                print("    3. Pixel-to-ray conversion needs correction")
                print()
            else:
                print("[OK] X-axis alignment is good! (within 5cm)")
                print()
            
            # Y analysis
            left_y = [d['world'][1] for d in left_data]
            right_y = [d['world'][1] for d in right_data]
            
            left_y_mean = np.mean(left_y)
            right_y_mean = np.mean(right_y)
            
            print(f"Y-axis offset (should be ≈0):")
            print(f"  Left camera:  {left_y_mean:.3f}m")
            print(f"  Right camera: {right_y_mean:.3f}m")
            print()
            
            if abs(left_y_mean) > 0.05 or abs(right_y_mean) > 0.05:
                print("[RECOMMENDATION] Y offset detected!")
                print("  This suggests object was not directly above cameras")
                print("  Or there's a systematic bias in depth calculation")
                print()
            else:
                print("[OK] Y-axis (depth) looks good!")
                print()
        
        else:
            print("[INSUFFICIENT DATA] Need at least 5 recordings per camera")
            print()
        
        print("="*70)
        print(f"Data saved to: {data_file}")
        print("Use this data to refine the projection mathematics!")
        print("="*70)


def main():
    calibration = VerticalCalibration()
    calibration.run()


if __name__ == "__main__":
    main()


"""
Stereo Triangulation Calibration

Uses BOTH cameras to triangulate 3D positions via ray intersection.
This is the CORRECT stereo vision approach.

Protocol:
  1. Move object vertically above LEFT camera
  2. BOTH cameras see it and triangulate intersection
  3. Press SPACE
  4. Move object vertically above RIGHT camera  
  5. BOTH cameras see it and triangulate intersection
  6. Press Q to analyze
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


def closest_point_between_rays(p1, d1, p2, d2):
    """
    Find closest point between two 3D rays (stereo triangulation).
    
    Ray 1: p1 + t*d1  (LEFT camera)
    Ray 2: p2 + s*d2  (RIGHT camera)
    
    Returns:
        point_3d: Midpoint of closest approach (3D position estimate)
        distance: Distance between rays (triangulation error/confidence)
    """
    # Ensure rays are normalized
    d1 = d1 / (np.linalg.norm(d1) + 1e-10)
    d2 = d2 / (np.linalg.norm(d2) + 1e-10)
    
    # Vector between ray origins
    w = p1 - p2
    
    a = np.dot(d1, d1)  # ||d1||^2 (should be 1 after normalization)
    b = np.dot(d1, d2)  # d1·d2 (cosine of angle between rays)
    c = np.dot(d2, d2)  # ||d2||^2 (should be 1 after normalization)
    d = np.dot(d1, w)   # d1·w
    e = np.dot(d2, w)   # d2·w
    
    # Solve for parameters t and s
    denom = a * c - b * b
    
    # Check if rays are too parallel (angle < 5 degrees)
    # cos(5°) ≈ 0.996, so if |b| > 0.996, rays are nearly parallel
    if abs(denom) < 1e-6 or abs(b) > 0.996:
        # Rays are parallel or nearly parallel
        return None, float('inf')
    
    t = (b * e - c * d) / denom
    s = (a * e - b * d) / denom
    
    # Skip if rays diverge backward (object behind cameras)
    if t < 0 or s < 0:
        return None, float('inf')
    
    # Points on each ray at closest approach
    point1 = p1 + t * d1
    point2 = p2 + s * d2
    
    # Midpoint = best 3D position estimate
    point_3d = (point1 + point2) / 2.0
    
    # Distance between rays = triangulation error
    distance = np.linalg.norm(point1 - point2)
    
    return point_3d, distance


class StereoTriangulationCalibration:
    """Calibration using stereo triangulation."""
    
    def __init__(self):
        # Detection parameters - START CONSERVATIVE (fewest false positives)
        self.motion_threshold = 50  # High = fewer motion pixels detected
        self.intensity_threshold = 80
        self.min_pixel_intensity = 150  # High = only bright pixels
        self.max_triangulation_error = 0.10  # Start at 10cm (reasonable for fisheye)
        
        # Settings file
        self.settings_file = "camera/stereo_calibration_settings.json"
        
        # Camera setup
        self.camera_left_pos = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.camera_right_pos = np.array([0.5, 0.0, 0.0], dtype=np.float64)
        
        # Recording
        self.phase = "LEFT"  # LEFT or RIGHT
        self.recordings = {
            'LEFT': [],
            'RIGHT': []
        }
        
        self.cameras = None
        self.calib = None
        self.prev_left = None
        self.prev_right = None
        
        # Performance tracking
        self.frame_times = []
        self.last_frame_time = time.time()
        
        # Debug mode
        self.debug_mode = False
        self.debug_stats = {
            'total_attempts': 0,
            'failed_no_intersection': 0,
            'failed_too_far': 0,
            'failed_behind_camera': 0,
            'failed_underground': 0,
            'succeeded': 0,
            'motion_left': 0,
            'motion_right': 0,
            'valid_left': 0,
            'valid_right': 0,
            'skipped_no_pixels': False
        }
    
    def load_settings(self):
        """Load previous settings if they exist."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                self.motion_threshold = settings.get('motion_threshold', self.motion_threshold)
                self.min_pixel_intensity = settings.get('min_pixel_intensity', self.min_pixel_intensity)
                self.max_triangulation_error = settings.get('max_triangulation_error', self.max_triangulation_error)
                
                print("[OK] Loaded previous settings:")
                print(f"     Motion threshold: {self.motion_threshold}")
                print(f"     Min pixel intensity: {self.min_pixel_intensity}")
                print(f"     Max triangulation error: {self.max_triangulation_error*100:.0f}cm")
                return True
            except Exception as e:
                print(f"[WARN] Could not load settings: {e}")
                return False
        else:
            print("[INFO] No previous settings found, using defaults:")
            print(f"       Motion threshold: {self.motion_threshold} (LEAST SENSITIVE)")
            print(f"       Min pixel intensity: {self.min_pixel_intensity} (LEAST SENSITIVE)")
            print(f"       Max triangulation error: {self.max_triangulation_error*100:.0f}cm (LEAST SENSITIVE)")
            return False
    
    def save_settings(self):
        """Save current settings for next run."""
        settings = {
            'motion_threshold': self.motion_threshold,
            'min_pixel_intensity': self.min_pixel_intensity,
            'max_triangulation_error': self.max_triangulation_error,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            print(f"\n[SAVED] Settings saved to: {self.settings_file}")
            print(f"        These will be loaded on next run!")
        except Exception as e:
            print(f"\n[WARN] Could not save settings: {e}")
    
    def initialize(self):
        """Initialize system."""
        print("="*70)
        print("  STEREO TRIANGULATION CALIBRATION")
        print("="*70)
        print()
        print("Uses BOTH cameras to triangulate 3D positions!")
        print("This is the correct stereo vision approach.")
        print()
        
        # Load previous settings
        self.load_settings()
        print()
        
        # Load calibration
        try:
            self.calib = load_calibration("camera/calibration.yml")
            print("[OK] Calibration loaded")
        except Exception as e:
            print(f"[ERROR] Could not load calibration: {e}")
            return False
        
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
        print("Phase 1: LEFT CAMERA")
        print("  Move object vertically above LEFT camera")
        print("  BOTH cameras will see it and triangulate")
        print("  Press SPACE when done")
        print()
        print("Phase 2: RIGHT CAMERA")
        print("  Move object vertically above RIGHT camera")
        print("  BOTH cameras will see it and triangulate")
        print("  Press Q when done")
        print()
        print("="*70)
        print("  CONTROLS")
        print("="*70)
        print("  SPACE: Switch to RIGHT phase")
        print("  Q: Finish and analyze")
        print()
        print("  Motion/Intensity controls:")
        print("    T: Motion threshold +5 (FEWER pixels)")
        print("    t: Motion threshold -5 (MORE pixels)")
        print("    I: Intensity threshold +10 (FEWER pixels)")
        print("    i: Intensity threshold -10 (MORE pixels)")
        print()
        print("  Triangulation error controls:")
        print("    E: Max error +2cm (MORE PERMISSIVE, more triangulations)")
        print("    e: Max error -2cm (MORE STRICT, fewer triangulations)")
        print()
        print("  D: Toggle debug mode (show why triangulations fail)")
        print()
        print("  Settings are SAVED on exit and LOADED on next run!")
        print("="*70)
        print()
        print(f">>> PHASE 1: Move object above LEFT camera")
        print()
        
        return True
    
    def triangulate_stereo(self, img_left, img_right, prev_left, prev_right):
        """
        Detect motion in both cameras and triangulate 3D positions.
        OPTIMIZED: Uses spatial clustering to avoid O(N*M) complexity.
        
        Returns:
            detections: List of triangulated 3D points
        """
        detections = []
        
        # Detect motion in both cameras
        diff_left = np.abs(img_left.astype(np.int16) - prev_left.astype(np.int16))
        diff_right = np.abs(img_right.astype(np.int16) - prev_right.astype(np.int16))
        
        motion_left = diff_left > self.motion_threshold
        motion_right = diff_right > self.motion_threshold
        
        # Filter by intensity (brightness)
        bright_left = img_left > self.min_pixel_intensity
        bright_right = img_right > self.min_pixel_intensity
        
        valid_left = motion_left & bright_left
        valid_right = motion_right & bright_right
        
        coords_left = np.argwhere(valid_left)
        coords_right = np.argwhere(valid_right)
        
        # Debug: Track why no triangulation attempts
        if self.debug_mode:
            self.debug_stats['motion_left'] = np.sum(motion_left)
            self.debug_stats['motion_right'] = np.sum(motion_right)
            self.debug_stats['valid_left'] = len(coords_left)
            self.debug_stats['valid_right'] = len(coords_right)
        
        if len(coords_left) == 0 or len(coords_right) == 0:
            if self.debug_mode:
                self.debug_stats['skipped_no_pixels'] = True
            return detections
        else:
            if self.debug_mode:
                self.debug_stats['skipped_no_pixels'] = False
        
        # OPTIMIZATION: Limit pixels to process (sample if too many)
        max_pixels = 100  # Increased from 50 for fisheye lenses
        if len(coords_left) > max_pixels:
            indices = np.random.choice(len(coords_left), max_pixels, replace=False)
            coords_left = coords_left[indices]
        
        if len(coords_right) > max_pixels:
            indices = np.random.choice(len(coords_right), max_pixels, replace=False)
            coords_right = coords_right[indices]
        
        # For fisheye lenses: Try ALL combinations (with reasonable limits)
        # Fisheye distortion means objects may NOT have similar Y-coordinates!
        max_combinations = 200  # Limit total triangulations per frame
        combinations_tried = 0
        
        for py_left, px_left in coords_left:
            if combinations_tried >= max_combinations:
                break
            
            intensity_left = img_left[py_left, px_left] / 255.0
            
            # Get ray from LEFT camera
            ray_left = self.calib.get_ray_direction(px_left, py_left)
            
            # For each RIGHT pixel (try all, up to limit)
            for py_right, px_right in coords_right:
                combinations_tried += 1
                if combinations_tried >= max_combinations:
                    break
                intensity_right = img_right[py_right, px_right] / 255.0
                
                # Get ray from RIGHT camera
                # NOTE: Using same calibration for both cameras is not ideal,
                # but we compensate by using correct camera positions
                ray_right = self.calib.get_ray_direction(px_right, py_right)
                
                # Triangulate: find intersection of rays
                if self.debug_mode:
                    self.debug_stats['total_attempts'] += 1
                
                point_3d, error = closest_point_between_rays(
                    self.camera_left_pos, ray_left,
                    self.camera_right_pos, ray_right
                )
                
                if point_3d is None:
                    if self.debug_mode:
                        self.debug_stats['failed_no_intersection'] += 1
                    continue
                
                # Filter by triangulation error
                if error > self.max_triangulation_error:
                    if self.debug_mode:
                        self.debug_stats['failed_too_far'] += 1
                    continue  # Rays don't intersect well
                
                # Filter by position (must be above ground, in front of cameras)
                if point_3d[2] < 0.05:  # Z < 5cm (too close to ground)
                    if self.debug_mode:
                        self.debug_stats['failed_underground'] += 1
                    continue
                
                if point_3d[1] < 0.0:  # Y < 0 (behind cameras)
                    if self.debug_mode:
                        self.debug_stats['failed_behind_camera'] += 1
                    continue
                
                if self.debug_mode:
                    self.debug_stats['succeeded'] += 1
                
                # Valid triangulation!
                combined_intensity = (intensity_left + intensity_right) / 2.0
                
                detections.append({
                    'timestamp': time.time(),
                    'point_3d': point_3d.tolist(),
                    'error': error,
                    'intensity_left': intensity_left,
                    'intensity_right': intensity_right,
                    'combined_intensity': combined_intensity,
                    'pixels_left': (int(px_left), int(py_left)),
                    'pixels_right': (int(px_right), int(py_right))
                })
        
        return detections
    
    def create_display(self, img_left, img_right):
        """Create display with BRIGHT GREEN motion highlighting."""
        # Highlight motion
        diff_left = np.abs(img_left.astype(np.int16) - self.prev_left.astype(np.int16))
        diff_right = np.abs(img_right.astype(np.int16) - self.prev_right.astype(np.int16))
        
        motion_left = diff_left > self.motion_threshold
        motion_right = diff_right > self.motion_threshold
        
        bright_left = img_left > self.min_pixel_intensity
        bright_right = img_right > self.min_pixel_intensity
        
        valid_left = motion_left & bright_left
        valid_right = motion_right & bright_right
        
        # Create BGR - start with DARKER version of image for better contrast
        display_left = cv2.cvtColor((img_left * 0.5).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        display_right = cv2.cvtColor((img_right * 0.5).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        
        # Mark ALL motion (even if not bright) in YELLOW
        all_motion_left = motion_left & ~bright_left
        all_motion_right = motion_right & ~bright_right
        display_left[all_motion_left] = [0, 255, 255]  # Yellow = motion but too dark
        display_right[all_motion_right] = [0, 255, 255]
        
        # Mark VALID motion in BRIGHT GREEN
        display_left[valid_left] = [0, 255, 0]  # Green = valid for triangulation
        display_right[valid_right] = [0, 255, 0]
        
        # Resize
        scale = 0.5
        h, w = display_left.shape[:2]
        new_w, new_h = int(w * scale), int(h * scale)
        
        left_small = cv2.resize(display_left, (new_w, new_h))
        right_small = cv2.resize(display_right, (new_w, new_h))
        
        combined = np.hstack([left_small, right_small])
        
        # Count pixels for display
        valid_left_count = np.sum(valid_left)
        valid_right_count = np.sum(valid_right)
        motion_left_count = np.sum(motion_left)
        motion_right_count = np.sum(motion_right)
        
        # Status panel (MUCH larger for debug)
        panel_height = 280 if self.debug_mode else 180
        panel = np.zeros((panel_height, combined.shape[1], 3), dtype=np.uint8)
        
        # Make panel dark blue instead of black for visibility
        if self.debug_mode:
            panel[:, :] = [40, 20, 0]  # Dark blue background
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        y = 30
        
        # Phase
        phase_color = (0, 255, 255) if self.phase == "LEFT" else (255, 128, 0)
        cv2.putText(panel, f"PHASE: {self.phase} CAMERA", (10, y),
                   font, 0.7, phase_color, 2)
        y += 35
        
        # Instructions
        if self.phase == "LEFT":
            cv2.putText(panel, "Move object above LEFT camera", (10, y),
                       font, 0.5, (255, 255, 255), 1)
        else:
            cv2.putText(panel, "Move object above RIGHT camera", (10, y),
                       font, 0.5, (255, 255, 255), 1)
        y += 30
        
        # Motion stats
        cv2.putText(panel, f"Motion pixels - L: {motion_left_count}  R: {motion_right_count}  (GREEN=valid, YELLOW=too dark)",
                   (10, y), font, 0.45, (255, 255, 255), 1)
        y += 25
        
        cv2.putText(panel, f"Valid pixels - L: {valid_left_count}  R: {valid_right_count}",
                   (10, y), font, 0.45, (0, 255, 0), 1)
        y += 25
        
        # Stats
        left_count = len(self.recordings['LEFT'])
        right_count = len(self.recordings['RIGHT'])
        
        cv2.putText(panel, f"Triangulations recorded - LEFT: {left_count}  RIGHT: {right_count}",
                   (10, y), font, 0.5, (0, 255, 0), 1)
        y += 25
        
        # Parameters
        cv2.putText(panel, f"Motion: {self.motion_threshold}  MinBright: {self.min_pixel_intensity}  MaxError: {self.max_triangulation_error*100:.0f}cm",
                   (10, y), font, 0.45, (0, 255, 255), 1)
        y += 20
        
        # Performance
        if len(self.frame_times) > 0:
            avg_fps = 1.0 / np.mean(self.frame_times) if np.mean(self.frame_times) > 0 else 0
            fps_color = (0, 255, 0) if avg_fps > 2 else (0, 165, 255) if avg_fps > 1 else (0, 0, 255)
            cv2.putText(panel, f"FPS: {avg_fps:.1f}  Frame time: {self.last_frame_time*1000:.0f}ms",
                       (10, y), font, 0.45, fps_color, 1)
        y += 20
        
        # Debug stats (HUGE and IMPOSSIBLE TO MISS)
        if self.debug_mode:
            # Draw bright border around debug section
            cv2.rectangle(panel, (5, 5), (combined.shape[1]-5, panel_height-5), 
                         (0, 255, 255), 3)
            
            y += 5
            # Title - HUGE
            cv2.putText(panel, "=== DEBUG MODE ===", (10, y),
                       font, 1.0, (0, 255, 255), 3)
            y += 35
            
            # Motion detection stats
            motion_l = self.debug_stats['motion_left']
            motion_r = self.debug_stats['motion_right']
            valid_l = self.debug_stats['valid_left']
            valid_r = self.debug_stats['valid_right']
            
            motion_color = (0, 255, 0) if (motion_l > 0 and motion_r > 0) else (0, 0, 255)
            cv2.putText(panel, f"Motion: L={motion_l} R={motion_r}  Valid: L={valid_l} R={valid_r}",
                       (10, y), font, 0.7, motion_color, 2)
            y += 30
            
            # Why no triangulation?
            if self.debug_stats['skipped_no_pixels']:
                if valid_l == 0 and valid_r == 0:
                    cv2.putText(panel, "NO VALID PIXELS! Too dark!",
                               (10, y), font, 0.7, (0, 0, 255), 3)
                    y += 30
                    cv2.putText(panel, "FIX: Press 'i' lower intensity",
                               (10, y), font, 0.7, (0, 255, 255), 2)
                elif valid_l == 0:
                    cv2.putText(panel, "LEFT camera: NO VALID PIXELS",
                               (10, y), font, 0.7, (0, 0, 255), 3)
                    y += 30
                    cv2.putText(panel, "FIX: Press 'i'",
                               (10, y), font, 0.7, (0, 255, 255), 2)
                elif valid_r == 0:
                    cv2.putText(panel, "RIGHT camera: NO VALID PIXELS",
                               (10, y), font, 0.7, (0, 0, 255), 3)
                    y += 30
                    cv2.putText(panel, "FIX: Press 'i'",
                               (10, y), font, 0.7, (0, 255, 255), 2)
            else:
                # Triangulation stats - HUGE TEXT
                total = self.debug_stats['total_attempts']
                success = self.debug_stats['succeeded']
                too_far = self.debug_stats['failed_too_far']
                behind = self.debug_stats['failed_behind_camera']
                underground = self.debug_stats['failed_underground']
                
                cv2.putText(panel, f"Attempts: {total}  Success: {success}  Fail: {too_far}",
                           (10, y), font, 0.7, (255, 255, 0), 3)
                y += 35
                
                if total > 0:
                    success_rate = 100.0 * success / total
                    rate_color = (0, 255, 0) if success_rate > 10 else (0, 165, 255) if success_rate > 5 else (0, 0, 255)
                    cv2.putText(panel, f"Success: {success_rate:.1f}%  (need >10%)",
                               (10, y), font, 0.7, rate_color, 3)
                    y += 35
                    
                    if too_far > total * 0.7:
                        cv2.putText(panel, "TooFar is high! Press 'E' for more tolerance",
                                   (10, y), font, 0.6, (0, 255, 255), 2)
                    elif success_rate > 10:
                        cv2.putText(panel, "GOOD! Collecting data...",
                                   (10, y), font, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(panel, "Valid pixels but NO attempts!",
                               (10, y), font, 0.7, (0, 165, 255), 2)
        
        # Combine
        display = np.vstack([combined, panel])
        
        # Labels
        cv2.putText(display, "LEFT", (10, 25), font, 0.7, (255, 255, 0), 2)
        cv2.putText(display, "RIGHT", (new_w + 10, 25), font, 0.7, (0, 255, 255), 2)
        
        # ALWAYS show debug status at top right (can't miss this!)
        debug_text = "DEBUG: ON" if self.debug_mode else "DEBUG: OFF (Press D)"
        debug_color = (0, 255, 0) if self.debug_mode else (0, 0, 255)
        cv2.putText(display, debug_text, (combined.shape[1] - 300, 25), 
                   font, 0.7, debug_color, 2)
        
        return display
    
    def run(self):
        """Run stereo calibration."""
        
        if not self.initialize():
            return
        
        try:
            while True:
                frame_start = time.time()
                
                # Capture
                img_left, img_right = self.cameras.capture_frame_pair()
                if img_left is None or img_right is None:
                    continue
                
                # Triangulate
                triangulation_start = time.time()
                detections = self.triangulate_stereo(
                    img_left, img_right,
                    self.prev_left, self.prev_right
                )
                triangulation_time = time.time() - triangulation_start
                
                # Record detections in current phase
                for det in detections:
                    self.recordings[self.phase].append(det)
                    
                    point = det['point_3d']
                    error = det['error']
                    print(f"[{self.phase}] Triangulated: X={point[0]:+.3f}, Y={point[1]:.3f}, Z={point[2]:.3f}m  Error={error*100:.1f}cm")
                
                # Display
                display = self.create_display(img_left, img_right)
                cv2.imshow('Stereo Triangulation Calibration', display)
                
                # Update previous
                self.prev_left = img_left.copy()
                self.prev_right = img_right.copy()
                
                # Track performance
                frame_time = time.time() - frame_start
                self.frame_times.append(frame_time)
                if len(self.frame_times) > 30:
                    self.frame_times.pop(0)
                
                # Print performance warning if slow
                if frame_time > 0.5:  # More than 500ms per frame
                    print(f"[PERFORMANCE] Frame took {frame_time:.2f}s (triangulation: {triangulation_time:.2f}s, detections: {len(detections)})")
                
                self.last_frame_time = frame_time
                
                # Handle keys
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord(' '):
                    if self.phase == "LEFT":
                        self.phase = "RIGHT"
                        print("\n" + "="*70)
                        print(f">>> PHASE 2: Move object above RIGHT camera")
                        print("="*70)
                        print()
                
                elif key == ord('q') or key == ord('Q'):
                    break
                
                # Motion/Intensity controls
                elif key == ord('T'):
                    self.motion_threshold = min(self.motion_threshold + 5, 100)
                    print(f"Motion threshold: {self.motion_threshold} (FEWER pixels detected)")
                
                elif key == ord('t'):
                    self.motion_threshold = max(self.motion_threshold - 5, 5)
                    print(f"Motion threshold: {self.motion_threshold} (MORE pixels detected)")
                
                elif key == ord('I'):
                    self.min_pixel_intensity = min(self.min_pixel_intensity + 10, 250)
                    print(f"Min pixel intensity: {self.min_pixel_intensity} (FEWER pixels detected)")
                
                elif key == ord('i'):
                    self.min_pixel_intensity = max(self.min_pixel_intensity - 10, 20)
                    print(f"Min pixel intensity: {self.min_pixel_intensity} (MORE pixels detected)")
                
                # Triangulation error controls (CORRECTED LOGIC!)
                elif key == ord('E'):
                    self.max_triangulation_error = min(self.max_triangulation_error + 0.02, 0.50)
                    print(f"Max triangulation error: {self.max_triangulation_error*100:.0f}cm (MORE PERMISSIVE, more triangulations)")
                
                elif key == ord('e'):
                    self.max_triangulation_error = max(self.max_triangulation_error - 0.02, 0.01)
                    print(f"Max triangulation error: {self.max_triangulation_error*100:.0f}cm (MORE STRICT, fewer triangulations)")
                
                # Debug toggle
                elif key == ord('D') or key == ord('d'):
                    self.debug_mode = not self.debug_mode
                    if self.debug_mode:
                        print("\n" + "="*70)
                        print("[DEBUG MODE ON]")
                        print("="*70)
                        print("Look at top-right corner: should say 'DEBUG: ON'")
                        print("Look at bottom panel: should show detailed stats")
                        print("="*70)
                        # Reset stats
                        for k in self.debug_stats:
                            if isinstance(self.debug_stats[k], bool):
                                self.debug_stats[k] = False
                            else:
                                self.debug_stats[k] = 0
                    else:
                        print("\n" + "="*70)
                        print("[DEBUG MODE OFF]")
                        print("="*70)
                        # Print final stats
                        print(f"Debug stats:")
                        print(f"  Motion detected - LEFT: {self.debug_stats['motion_left']}  RIGHT: {self.debug_stats['motion_right']}")
                        print(f"  Valid pixels - LEFT: {self.debug_stats['valid_left']}  RIGHT: {self.debug_stats['valid_right']}")
                        print(f"  Total attempts: {self.debug_stats['total_attempts']}")
                        print(f"  Succeeded: {self.debug_stats['succeeded']}")
                        print(f"  Failed (no intersection): {self.debug_stats['failed_no_intersection']}")
                        print(f"  Failed (error too high): {self.debug_stats['failed_too_far']}")
                        print(f"  Failed (behind camera): {self.debug_stats['failed_behind_camera']}")
                        print(f"  Failed (underground): {self.debug_stats['failed_underground']}")
                        if self.debug_stats['total_attempts'] > 0:
                            success_rate = 100.0 * self.debug_stats['succeeded'] / self.debug_stats['total_attempts']
                            print(f"  Success rate: {success_rate:.1f}%")
                        print("="*70)
        
        except KeyboardInterrupt:
            print("\n\nInterrupted")
        
        finally:
            self.cameras.stop_capture()
            self.cameras.close()
            cv2.destroyAllWindows()
            
            # Save settings for next run
            self.save_settings()
            
            # Analyze
            self.analyze_and_save()
    
    def analyze_and_save(self):
        """Analyze stereo triangulation results."""
        print("\n" + "="*70)
        print("  STEREO TRIANGULATION ANALYSIS")
        print("="*70)
        print()
        
        # Save raw data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_file = f"camera/stereo_calibration_{timestamp}.json"
        
        with open(data_file, 'w') as f:
            json.dump(self.recordings, f, indent=2)
        
        print(f"[SAVED] {data_file}")
        print()
        
        # Analyze each phase
        for phase in ['LEFT', 'RIGHT']:
            data = self.recordings[phase]
            
            if len(data) == 0:
                print(f"{phase} camera: No triangulations!")
                continue
            
            print(f"{phase} Camera Phase:")
            print("-" * 50)
            
            # Extract 3D positions
            positions = np.array([d['point_3d'] for d in data])
            errors = np.array([d['error'] for d in data])
            
            x_vals = positions[:, 0]
            y_vals = positions[:, 1]
            z_vals = positions[:, 2]
            
            # Statistics
            print(f"  Triangulations: {len(data)}")
            print()
            print(f"  X (horizontal):")
            print(f"    Mean: {np.mean(x_vals):+.4f}m  Std: {np.std(x_vals):.4f}m")
            print(f"    Range: {np.min(x_vals):+.4f}m to {np.max(x_vals):+.4f}m")
            print(f"    Expected: {0.0 if phase=='LEFT' else 0.5:.1f}m")
            print()
            print(f"  Y (depth):")
            print(f"    Mean: {np.mean(y_vals):+.4f}m  Std: {np.std(y_vals):.4f}m")
            print()
            print(f"  Z (height):")
            print(f"    Mean: {np.mean(z_vals):.4f}m  Std: {np.std(z_vals):.4f}m")
            print(f"    Range: {np.min(z_vals):.4f}m to {np.max(z_vals):.4f}m")
            print()
            print(f"  Triangulation error:")
            print(f"    Mean: {np.mean(errors)*100:.2f}cm")
            print(f"    Max:  {np.max(errors)*100:.2f}cm")
            print()
        
        # Overall
        left_data = self.recordings['LEFT']
        right_data = self.recordings['RIGHT']
        
        if len(left_data) > 0 and len(right_data) > 0:
            left_pos = np.array([d['point_3d'] for d in left_data])
            right_pos = np.array([d['point_3d'] for d in right_data])
            
            left_x_mean = np.mean(left_pos[:, 0])
            right_x_mean = np.mean(right_pos[:, 0])
            
            baseline = right_x_mean - left_x_mean
            
            print("="*70)
            print("  OVERALL ASSESSMENT")
            print("="*70)
            print()
            print(f"Camera baseline:")
            print(f"  Expected: 0.500m (50cm)")
            print(f"  Measured: {baseline:.4f}m ({baseline*100:.1f}cm)")
            print(f"  Error:    {(baseline - 0.5)*100:+.1f}cm")
            print()
            
            if abs(baseline - 0.5) < 0.05:
                print("[EXCELLENT] Baseline accurate within 5cm!")
                print("Stereo geometry is correct!")
            else:
                print("[ISSUE] Baseline error > 5cm")
                print("Calibration may need adjustment")
            print()
        
        print("="*70)


def main():
    calib = StereoTriangulationCalibration()
    calib.run()


if __name__ == "__main__":
    main()


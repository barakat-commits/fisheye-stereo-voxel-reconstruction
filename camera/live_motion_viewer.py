"""
Live Motion Viewer with Green Highlighting

Shows both camera feeds with moving pixels marked in GREEN.
Helps identify false positives and tune detection parameters.

Controls:
  Q: Quit
  T/t: Increase/decrease motion threshold
  I/i: Increase/decrease intensity threshold
  S: Save screenshot
  R: Reset to defaults
"""

import numpy as np
import cv2
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem


class LiveMotionViewer:
    """Live viewer for motion detection with filtering."""
    
    def __init__(self):
        self.motion_threshold = 25      # Minimum pixel change to detect motion
        self.intensity_threshold = 80   # Minimum pixel brightness to consider (0-255)
        self.blur_kernel = 5            # Blur to reduce noise
        
        self.cameras = None
        self.prev_left = None
        self.prev_right = None
        
        # Statistics
        self.stats = {
            'left_motion_pixels': 0,
            'right_motion_pixels': 0,
            'left_filtered': 0,
            'right_filtered': 0,
            'fps': 0
        }
    
    def initialize_cameras(self):
        """Initialize camera system."""
        print("="*70)
        print("  LIVE MOTION VIEWER - Debug False Positives")
        print("="*70)
        print()
        print("Initializing cameras...")
        
        self.cameras = DualASICameraSystem()
        self.cameras.configure(exposure=30000, gain=300)
        self.cameras.start_capture()
        
        print("[OK] Cameras ready\n")
        print("Getting baseline frames...")
        time.sleep(0.5)
        
        # Get baseline
        self.prev_left, self.prev_right = self.cameras.capture_frame_pair()
        
        print("[OK] Baseline captured\n")
        print("="*70)
        print("  CONTROLS")
        print("="*70)
        print("  Q: Quit")
        print("  T: Increase motion threshold")
        print("  t: Decrease motion threshold")
        print("  I: Increase intensity threshold")
        print("  i: Decrease intensity threshold")
        print("  S: Save screenshot")
        print("  R: Reset to defaults")
        print("="*70)
        print()
    
    def process_frame(self, img_current, img_prev, camera_name):
        """
        Process frame and highlight motion.
        
        Returns:
            display_img: BGR image with green highlights
            motion_coords: List of (y, x) coordinates of valid motion
            stats: Dictionary with statistics
        """
        # Apply blur to reduce noise
        if self.blur_kernel > 1:
            img_current_blur = cv2.GaussianBlur(img_current, 
                                               (self.blur_kernel, self.blur_kernel), 0)
            img_prev_blur = cv2.GaussianBlur(img_prev, 
                                            (self.blur_kernel, self.blur_kernel), 0)
        else:
            img_current_blur = img_current
            img_prev_blur = img_prev
        
        # Detect motion (absolute difference)
        diff = np.abs(img_current_blur.astype(np.int16) - img_prev_blur.astype(np.int16))
        motion_mask = diff > self.motion_threshold
        
        # Filter by intensity (brightness)
        intensity_mask = img_current > self.intensity_threshold
        
        # Combined: motion AND bright enough
        valid_motion = motion_mask & intensity_mask
        
        # Count pixels
        total_motion = np.count_nonzero(motion_mask)
        filtered_out = np.count_nonzero(motion_mask & ~intensity_mask)
        valid_count = np.count_nonzero(valid_motion)
        
        # Get coordinates of valid motion
        motion_coords = np.argwhere(valid_motion)
        
        # Create display image (convert grayscale to BGR for color overlay)
        display_img = cv2.cvtColor(img_current, cv2.COLOR_GRAY2BGR)
        
        # Highlight ALL motion pixels in RED (false positives)
        display_img[motion_mask & ~intensity_mask] = [0, 0, 255]  # Red = filtered out
        
        # Highlight VALID motion pixels in GREEN (will be used for voxels)
        display_img[valid_motion] = [0, 255, 0]  # Green = valid
        
        # Statistics
        stats = {
            'total_motion': total_motion,
            'filtered_out': filtered_out,
            'valid_motion': valid_count
        }
        
        return display_img, motion_coords, stats
    
    def create_display(self, left_img, right_img, left_stats, right_stats):
        """Create side-by-side display with stats overlay."""
        
        # Resize images for display (half size)
        h, w = left_img.shape[:2]
        scale = 0.5
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        left_display = cv2.resize(left_img, (new_w, new_h))
        right_display = cv2.resize(right_img, (new_w, new_h))
        
        # Side-by-side
        combined = np.hstack([left_display, right_display])
        
        # Add parameter display
        param_height = 180
        param_panel = np.zeros((param_height, combined.shape[1], 3), dtype=np.uint8)
        
        # Parameters
        y_offset = 25
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        cv2.putText(param_panel, "PARAMETERS:", (10, y_offset), 
                   font, font_scale, (255, 255, 255), thickness)
        y_offset += 30
        
        cv2.putText(param_panel, f"Motion Threshold: {self.motion_threshold} (T/t)", 
                   (10, y_offset), font, font_scale, (0, 255, 255), thickness)
        y_offset += 25
        
        cv2.putText(param_panel, f"Intensity Threshold: {self.intensity_threshold} (I/i)", 
                   (10, y_offset), font, font_scale, (0, 255, 255), thickness)
        y_offset += 25
        
        cv2.putText(param_panel, f"Blur Kernel: {self.blur_kernel}x{self.blur_kernel}", 
                   (10, y_offset), font, font_scale, (0, 255, 255), thickness)
        y_offset += 30
        
        # Color legend
        cv2.putText(param_panel, "LEGEND:", (10, y_offset), 
                   font, font_scale, (255, 255, 255), thickness)
        
        cv2.rectangle(param_panel, (150, y_offset-15), (170, y_offset-5), 
                     (0, 255, 0), -1)
        cv2.putText(param_panel, "Valid (used for voxels)", (180, y_offset), 
                   font, font_scale-0.1, (0, 255, 0), 1)
        
        y_offset += 25
        cv2.rectangle(param_panel, (150, y_offset-15), (170, y_offset-5), 
                     (0, 0, 255), -1)
        cv2.putText(param_panel, "Filtered (too dark)", (180, y_offset), 
                   font, font_scale-0.1, (0, 0, 255), 1)
        
        # Statistics
        stats_x = combined.shape[1] // 2 + 10
        y_offset = 25
        
        cv2.putText(param_panel, "STATISTICS:", (stats_x, y_offset), 
                   font, font_scale, (255, 255, 255), thickness)
        y_offset += 30
        
        # Left camera
        cv2.putText(param_panel, f"Left:  Valid: {left_stats['valid_motion']:5d}  " +
                   f"Filtered: {left_stats['filtered_out']:5d}", 
                   (stats_x, y_offset), font, font_scale-0.1, (0, 255, 255), 1)
        y_offset += 25
        
        # Right camera
        cv2.putText(param_panel, f"Right: Valid: {right_stats['valid_motion']:5d}  " +
                   f"Filtered: {right_stats['filtered_out']:5d}", 
                   (stats_x, y_offset), font, font_scale-0.1, (0, 255, 255), 1)
        y_offset += 25
        
        # False positive rate
        left_fps_rate = 0
        if left_stats['total_motion'] > 0:
            left_fps_rate = left_stats['filtered_out'] / left_stats['total_motion'] * 100
        
        right_fps_rate = 0
        if right_stats['total_motion'] > 0:
            right_fps_rate = right_stats['filtered_out'] / right_stats['total_motion'] * 100
        
        cv2.putText(param_panel, f"False Positive Rate: L:{left_fps_rate:.1f}%  R:{right_fps_rate:.1f}%", 
                   (stats_x, y_offset), font, font_scale-0.1, (255, 100, 100), 1)
        y_offset += 30
        
        cv2.putText(param_panel, f"FPS: {self.stats['fps']:.1f}", 
                   (stats_x, y_offset), font, font_scale, (0, 255, 0), thickness)
        
        # Stack vertically
        display = np.vstack([combined, param_panel])
        
        # Camera labels
        cv2.putText(display, "LEFT CAMERA", (10, 20), 
                   font, 0.7, (255, 255, 0), 2)
        cv2.putText(display, "RIGHT CAMERA", (new_w + 10, 20), 
                   font, 0.7, (0, 255, 255), 2)
        
        return display
    
    def run(self):
        """Run live viewer."""
        
        self.initialize_cameras()
        
        print("Starting live view...")
        print("Move objects above cameras to see motion detection!")
        print()
        
        frame_times = []
        screenshot_count = 0
        
        try:
            while True:
                start_time = time.time()
                
                # Capture
                img_left, img_right = self.cameras.capture_frame_pair()
                
                if img_left is None or img_right is None:
                    continue
                
                # Process both cameras
                left_display, left_coords, left_stats = self.process_frame(
                    img_left, self.prev_left, "Left"
                )
                
                right_display, right_coords, right_stats = self.process_frame(
                    img_right, self.prev_right, "Right"
                )
                
                # Create display
                display = self.create_display(left_display, right_display, 
                                             left_stats, right_stats)
                
                # Show
                cv2.imshow('Live Motion Viewer - GREEN=Valid, RED=Filtered', display)
                
                # Update previous frames
                self.prev_left = img_left.copy()
                self.prev_right = img_right.copy()
                
                # Calculate FPS
                frame_time = time.time() - start_time
                frame_times.append(frame_time)
                if len(frame_times) > 30:
                    frame_times.pop(0)
                self.stats['fps'] = 1.0 / np.mean(frame_times)
                
                # Handle keys
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == ord('Q'):
                    print("\nQuitting...")
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
                
                elif key == ord('S') or key == ord('s'):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"camera/motion_debug_{timestamp}.png"
                    cv2.imwrite(filename, display)
                    screenshot_count += 1
                    print(f"[SAVED] {filename}")
                
                elif key == ord('R') or key == ord('r'):
                    self.motion_threshold = 25
                    self.intensity_threshold = 80
                    self.blur_kernel = 5
                    print("Reset to defaults")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        
        finally:
            self.cameras.stop_capture()
            self.cameras.close()
            cv2.destroyAllWindows()
            
            print("\n" + "="*70)
            print("  SESSION SUMMARY")
            print("="*70)
            print(f"Screenshots saved: {screenshot_count}")
            print()
            print("Final parameters:")
            print(f"  Motion threshold:    {self.motion_threshold}")
            print(f"  Intensity threshold: {self.intensity_threshold}")
            print(f"  Blur kernel:         {self.blur_kernel}x{self.blur_kernel}")
            print()
            print("These parameters can be used in your reconstruction scripts!")
            print("="*70)


def main():
    viewer = LiveMotionViewer()
    viewer.run()


if __name__ == "__main__":
    main()




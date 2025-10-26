"""
Stereo Calibration Capture - NO GUI VERSION

Saves images to disk without displaying them.
Use this if OpenCV windows don't work.
"""

import cv2
import numpy as np
import sys
import os
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem


class StereoCalibrationCaptureNoGUI:
    """Stereo calibration capture without GUI."""
    
    def __init__(self, checkerboard_size=(9, 6)):
        self.checkerboard_size = checkerboard_size
        self.cameras = None
        
        # Capture settings
        self.min_captures = 20
        self.max_captures = 40
        self.capture_interval = 2.0  # Seconds between auto-captures
        
        # Storage
        self.output_dir = Path("camera/stereo_calibration_images")
        self.output_dir.mkdir(exist_ok=True)
        
        self.captures = []
        self.last_capture_time = 0
        
        # Detection parameters
        self.detection_flags = (
            cv2.CALIB_CB_ADAPTIVE_THRESH +
            cv2.CALIB_CB_NORMALIZE_IMAGE +
            cv2.CALIB_CB_FAST_CHECK
        )
    
    def detect_checkerboard(self, img):
        """Detect checkerboard in image."""
        gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        found, corners = cv2.findChessboardCorners(
            gray,
            self.checkerboard_size,
            self.detection_flags
        )
        
        if found:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        
        return found, corners
    
    def save_capture(self, img_left, img_right, corners_left, corners_right):
        """Save calibration image pair."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Save images
        left_path = self.output_dir / f"left_{timestamp}.png"
        right_path = self.output_dir / f"right_{timestamp}.png"
        
        cv2.imwrite(str(left_path), img_left)
        cv2.imwrite(str(right_path), img_right)
        
        # Save metadata
        self.captures.append({
            'timestamp': timestamp,
            'left_image': str(left_path),
            'right_image': str(right_path),
            'left_corners': corners_left.tolist(),
            'right_corners': corners_right.tolist()
        })
        
        print(f"[{len(self.captures)}/{self.max_captures}] Captured: {timestamp}")
        
        self.last_capture_time = time.time()
    
    def run(self):
        """Run capture loop without GUI."""
        print("="*70)
        print("  STEREO CALIBRATION - NO GUI MODE")
        print("="*70)
        print()
        print(f"Checkerboard size: {self.checkerboard_size[0]}x{self.checkerboard_size[1]} inner corners")
        print(f"Target: {self.min_captures}-{self.max_captures} captures")
        print()
        print("This version captures images WITHOUT showing them.")
        print("Hold the checkerboard in front of both cameras.")
        print("System will auto-capture when detected in BOTH cameras.")
        print()
        print("Press Ctrl+C when you have enough captures (20+)")
        print()
        print("="*70)
        print()
        
        # Initialize cameras
        print("Initializing cameras...")
        self.cameras = DualASICameraSystem()
        self.cameras.configure(exposure=20000, gain=200)
        self.cameras.start_capture()
        print("[OK] Cameras ready")
        print()
        
        print("Starting capture loop...")
        print("Move checkerboard to different positions/angles/depths")
        print()
        
        self.last_capture_time = time.time()
        frame_count = 0
        
        try:
            while len(self.captures) < self.max_captures:
                frame_count += 1
                
                # Capture frames
                img_left, img_right = self.cameras.capture_frame_pair()
                if img_left is None or img_right is None:
                    continue
                
                # Detect checkerboard
                found_left, corners_left = self.detect_checkerboard(img_left)
                found_right, corners_right = self.detect_checkerboard(img_right)
                
                # Status every 30 frames (~1 second)
                if frame_count % 30 == 0:
                    status_l = "YES" if found_left else "no"
                    status_r = "YES" if found_right else "no"
                    print(f"[Frame {frame_count:4d}] Detect: L={status_l:3s} R={status_r:3s} | Captures: {len(self.captures)}/{self.max_captures}")
                
                # Auto-capture if conditions met
                current_time = time.time()
                time_since_last = current_time - self.last_capture_time
                
                if (found_left and found_right and 
                    time_since_last > self.capture_interval):
                    
                    self.save_capture(img_left, img_right, corners_left, corners_right)
                    
                    if len(self.captures) >= self.min_captures:
                        print()
                        print(f"[OK] Have {len(self.captures)} captures (minimum reached)")
                        print("     Continue for more, or Ctrl+C to finish")
                        print()
        
        except KeyboardInterrupt:
            print("\n\n[STOPPED] User interrupted")
        
        finally:
            self.cameras.stop_capture()
            self.cameras.close()
            
            # Save capture list
            self.save_capture_list()
    
    def save_capture_list(self):
        """Save list of captured images."""
        if len(self.captures) == 0:
            print("\nNo captures to save")
            return
        
        import json
        
        output_file = self.output_dir / "capture_list.json"
        
        data = {
            'checkerboard_size': self.checkerboard_size,
            'num_captures': len(self.captures),
            'captures': self.captures
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print("\n" + "="*70)
        print("  CAPTURE COMPLETE!")
        print("="*70)
        print(f"\nCaptured {len(self.captures)} image pairs")
        print(f"Saved to: {self.output_dir}")
        print(f"Metadata: {output_file}")
        print()
        
        if len(self.captures) >= self.min_captures:
            print("="*70)
            print("  NEXT STEP")
            print("="*70)
            print("\nRun stereo calibration:")
            print("  python camera/stereo_calibration_compute.py")
            print()
        else:
            print(f"[WARN] Only captured {len(self.captures)} images")
            print(f"       Need at least {self.min_captures} for calibration")
            print("       Run again to get more!")
            print()
        
        print("="*70)


def main():
    capture = StereoCalibrationCaptureNoGUI(checkerboard_size=(9, 6))
    capture.run()


if __name__ == "__main__":
    main()




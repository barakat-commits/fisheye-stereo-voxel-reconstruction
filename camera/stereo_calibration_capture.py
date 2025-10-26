"""
Automated Stereo Calibration Image Capture Tool

Captures synchronized image pairs from both cameras when checkerboard is detected.
Move the checkerboard to different positions/angles and the system will
automatically capture good calibration images.
"""

import cv2
import numpy as np
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem


class StereoCalibrationCapture:
    """Automated stereo calibration image capture."""
    
    def __init__(self, checkerboard_size=(9, 6)):
        """
        Initialize capture system.
        
        Args:
            checkerboard_size: (cols, rows) of INNER corners
                              For 10x7 squares, use (9, 6)
        """
        self.checkerboard_size = checkerboard_size
        self.cameras = None
        
        # Capture settings
        self.min_captures = 20
        self.max_captures = 40
        self.capture_delay = 1.0  # Seconds between auto-captures
        
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
    
    def initialize(self):
        """Initialize cameras."""
        print("="*70)
        print("  STEREO CALIBRATION - IMAGE CAPTURE")
        print("="*70)
        print()
        print(f"Checkerboard size: {self.checkerboard_size[0]}x{self.checkerboard_size[1]} inner corners")
        print(f"Target captures: {self.min_captures}-{self.max_captures} image pairs")
        print()
        print("Initializing cameras...")
        
        self.cameras = DualASICameraSystem()
        
        # Use good exposure and gain for calibration
        self.cameras.configure(exposure=20000, gain=200)
        self.cameras.start_capture()
        
        print("[OK] Cameras ready")
        print()
        print("="*70)
        print("  INSTRUCTIONS")
        print("="*70)
        print()
        print("1. Print checkerboard pattern:")
        print("   https://github.com/opencv/opencv/blob/master/doc/pattern.png")
        print(f"   Or use {self.checkerboard_size[0]+1}x{self.checkerboard_size[1]+1} squares")
        print()
        print("2. Place checkerboard in view of BOTH cameras")
        print("3. Move it to different:")
        print("   - Positions (left, right, center, close, far)")
        print("   - Angles (tilted, rotated)")
        print("   - Depths (various distances)")
        print()
        print("4. System will AUTO-CAPTURE when checkerboard detected")
        print("   - Green border = detected, will capture soon")
        print("   - Captures saved automatically")
        print()
        print("5. Keep moving until you have 20-40 good captures")
        print()
        print("="*70)
        print("  CONTROLS")
        print("="*70)
        print("  SPACE: Manual capture (if auto-capture missed)")
        print("  Q: Finish (need at least 20 captures)")
        print("  ESC: Cancel")
        print("="*70)
        print()
        input("Press ENTER when ready...")
        print()
        
        return True
    
    def detect_checkerboard(self, img):
        """
        Detect checkerboard in image.
        
        Returns:
            found: True if checkerboard detected
            corners: Corner positions (or None)
        """
        gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        found, corners = cv2.findChessboardCorners(
            gray,
            self.checkerboard_size,
            self.detection_flags
        )
        
        if found:
            # Refine corner positions for sub-pixel accuracy
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        
        return found, corners
    
    def create_display(self, img_left, img_right, found_left, corners_left,
                       found_right, corners_right, can_capture):
        """Create visualization display."""
        
        # Convert to BGR if grayscale
        if len(img_left.shape) == 2:
            display_left = cv2.cvtColor(img_left, cv2.COLOR_GRAY2BGR)
        else:
            display_left = img_left.copy()
        
        if len(img_right.shape) == 2:
            display_right = cv2.cvtColor(img_right, cv2.COLOR_GRAY2BGR)
        else:
            display_right = img_right.copy()
        
        # Draw checkerboard if found
        if found_left and corners_left is not None:
            cv2.drawChessboardCorners(display_left, self.checkerboard_size,
                                     corners_left, found_left)
            # Green border
            cv2.rectangle(display_left, (0, 0),
                         (display_left.shape[1]-1, display_left.shape[0]-1),
                         (0, 255, 0), 10)
        else:
            # Red border
            cv2.rectangle(display_left, (0, 0),
                         (display_left.shape[1]-1, display_left.shape[0]-1),
                         (0, 0, 255), 10)
        
        if found_right and corners_right is not None:
            cv2.drawChessboardCorners(display_right, self.checkerboard_size,
                                      corners_right, found_right)
            # Green border
            cv2.rectangle(display_right, (0, 0),
                         (display_right.shape[1]-1, display_right.shape[0]-1),
                         (0, 255, 0), 10)
        else:
            # Red border
            cv2.rectangle(display_right, (0, 0),
                         (display_right.shape[1]-1, display_right.shape[0]-1),
                         (0, 0, 255), 10)
        
        # Resize for display
        scale = 0.5
        h, w = display_left.shape[:2]
        new_w, new_h = int(w * scale), int(h * scale)
        
        left_small = cv2.resize(display_left, (new_w, new_h))
        right_small = cv2.resize(display_right, (new_w, new_h))
        
        combined = np.hstack([left_small, right_small])
        
        # Status panel
        panel_height = 150
        panel = np.zeros((panel_height, combined.shape[1], 3), dtype=np.uint8)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        y = 30
        
        # Title
        cv2.putText(panel, "STEREO CALIBRATION CAPTURE", (10, y),
                   font, 0.8, (0, 255, 255), 2)
        y += 40
        
        # Detection status
        if found_left and found_right:
            status_color = (0, 255, 0)
            status_text = f"BOTH cameras detect! Captures: {len(self.captures)}/{self.min_captures}"
            if can_capture:
                status_text += " [CAPTURING...]"
        elif found_left or found_right:
            status_color = (0, 165, 255)
            which = "LEFT" if found_left else "RIGHT"
            status_text = f"Only {which} detects - move board! Captures: {len(self.captures)}/{self.min_captures}"
        else:
            status_color = (0, 0, 255)
            status_text = f"No detection - show board to both cameras! Captures: {len(self.captures)}/{self.min_captures}"
        
        cv2.putText(panel, status_text, (10, y), font, 0.6, status_color, 2)
        y += 35
        
        # Progress
        progress = len(self.captures) / self.min_captures
        bar_width = combined.shape[1] - 20
        bar_height = 20
        cv2.rectangle(panel, (10, y), (10 + bar_width, y + bar_height),
                     (100, 100, 100), 2)
        cv2.rectangle(panel, (10, y),
                     (10 + int(bar_width * min(progress, 1.0)), y + bar_height),
                     (0, 255, 0), -1)
        
        y += 30
        
        # Instructions
        if len(self.captures) < self.min_captures:
            cv2.putText(panel, f"Keep moving board! Need {self.min_captures - len(self.captures)} more",
                       (10, y), font, 0.5, (255, 255, 255), 1)
        else:
            cv2.putText(panel, "Enough captures! Press Q to finish (or get more)",
                       (10, y), font, 0.5, (0, 255, 0), 2)
        
        # Combine
        display = np.vstack([combined, panel])
        
        # Labels
        cv2.putText(display, "LEFT", (10, 25), font, 0.7, (255, 255, 0), 2)
        cv2.putText(display, "RIGHT", (new_w + 10, 25), font, 0.7, (0, 255, 255), 2)
        
        return display
    
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
        
        print(f"[{len(self.captures)}] Captured: {timestamp}")
        
        # Play sound or visual feedback
        self.last_capture_time = cv2.getTickCount() / cv2.getTickFrequency()
    
    def run(self):
        """Run capture loop."""
        if not self.initialize():
            return
        
        # Create named window first
        window_name = 'Stereo Calibration Capture'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1920, 700)
        
        print("Window opened! You should see both camera feeds...")
        print("If window is hidden, ALT+TAB to find it")
        print()
        
        frame_count = 0
        
        try:
            while True:
                frame_count += 1
                # Capture frames
                img_left, img_right = self.cameras.capture_frame_pair()
                if img_left is None or img_right is None:
                    print(f"[Frame {frame_count}] Failed to capture - retrying...")
                    continue
                
                if frame_count == 1:
                    print(f"[OK] First frame captured! Size: {img_left.shape}")
                    print("Looking for checkerboard...")
                
                # Detect checkerboard in both images
                found_left, corners_left = self.detect_checkerboard(img_left)
                found_right, corners_right = self.detect_checkerboard(img_right)
                
                # Debug output every 30 frames
                if frame_count % 30 == 0:
                    status_l = "FOUND" if found_left else "not found"
                    status_r = "FOUND" if found_right else "not found"
                    print(f"[Frame {frame_count}] Checkerboard - LEFT: {status_l}, RIGHT: {status_r}, Captures: {len(self.captures)}")
                
                # Check if we can auto-capture
                current_time = cv2.getTickCount() / cv2.getTickFrequency()
                time_since_last = current_time - self.last_capture_time
                
                can_capture = (
                    found_left and found_right and
                    time_since_last > self.capture_delay and
                    len(self.captures) < self.max_captures
                )
                
                # Auto-capture if conditions met
                if can_capture:
                    self.save_capture(img_left, img_right, corners_left, corners_right)
                
                # Create display
                display = self.create_display(
                    img_left, img_right,
                    found_left, corners_left,
                    found_right, corners_right,
                    can_capture
                )
                
                cv2.imshow(window_name, display)
                
                # Handle keys with longer wait for better responsiveness
                key = cv2.waitKey(10) & 0xFF
                
                # Debug key presses
                if key != 255:  # 255 means no key pressed
                    print(f"[KEY] Pressed: {key} ('{chr(key) if 32 <= key < 127 else '?'}')")
                
                if key == ord(' '):
                    # Manual capture
                    print("[SPACE] Manual capture requested")
                    if found_left and found_right:
                        if len(self.captures) < self.max_captures:
                            self.save_capture(img_left, img_right, corners_left, corners_right)
                            print(f"[OK] Manual capture saved! Total: {len(self.captures)}")
                        else:
                            print(f"[INFO] Already have {self.max_captures} captures (max)")
                    else:
                        status = []
                        if not found_left:
                            status.append("LEFT missing")
                        if not found_right:
                            status.append("RIGHT missing")
                        print(f"[WARN] Cannot capture - {', '.join(status)}")
                
                elif key == ord('q') or key == ord('Q'):
                    print(f"[Q] Quit requested - have {len(self.captures)} captures")
                    if len(self.captures) >= self.min_captures:
                        print(f"[OK] Enough captures! Finishing...")
                        break
                    else:
                        print(f"[WARN] Need at least {self.min_captures} captures (have {len(self.captures)})")
                        print(f"      Keep going or press ESC to cancel")
                
                elif key == 27:  # ESC
                    print("\n[ESC] Cancelled by user")
                    return
        
        except KeyboardInterrupt:
            print("\n\nInterrupted")
        
        finally:
            self.cameras.stop_capture()
            self.cameras.close()
            cv2.destroyAllWindows()
            
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
        print("="*70)
        print("  NEXT STEP")
        print("="*70)
        print("\nRun stereo calibration:")
        print("  python camera/stereo_calibration_compute.py")
        print()
        print("This will compute:")
        print("  - Camera matrices for both cameras")
        print("  - Distortion coefficients")
        print("  - Rotation matrix (R)")
        print("  - Translation vector (T)")
        print("  - Essential matrix (E)")
        print("  - Fundamental matrix (F)")
        print()
        print("="*70)


def main():
    # Default checkerboard size (9x6 inner corners = 10x7 squares)
    # Adjust if you have a different pattern
    capture = StereoCalibrationCapture(checkerboard_size=(9, 6))
    capture.run()


if __name__ == "__main__":
    main()


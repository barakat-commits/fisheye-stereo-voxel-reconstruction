"""
ArUco Stereo Calibration Capture Tool

Detects ArUco markers in both cameras and captures image pairs.
Works MUCH better with fisheye distortion than checkerboards!
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


class ArucoStereoCapture:
    def __init__(self):
        # ArUco detection (compatible with OpenCV 4.7+)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.aruco_params = cv2.aruco.DetectorParameters()
        
        # Create detector for new API
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        
        # Board configuration (must match generated board)
        self.markers_x = 5
        self.markers_y = 4
        self.marker_length = 0.04  # 40mm in meters
        self.marker_separation = 0.01  # 10mm in meters
        
        self.board = cv2.aruco.GridBoard(
            (self.markers_x, self.markers_y),
            self.marker_length,
            self.marker_separation,
            self.aruco_dict
        )
        
        # Capture storage
        self.captures = []
        self.min_captures = 20
        self.max_captures = 50
        
        # Output directory
        self.output_dir = Path("camera/aruco_calibration")
        self.output_dir.mkdir(exist_ok=True)
        
        print("ArUco Stereo Capture initialized")
        print(f"Board: {self.markers_x}x{self.markers_y} markers")
        print(f"Min captures needed: {self.min_captures}")
        print()
    
    def detect_board(self, image):
        """
        Detect ArUco board in image.
        Returns (corners, ids, num_detected) or (None, None, 0) if not found.
        """
        # Detect markers using new API
        corners, ids, rejected = self.detector.detectMarkers(image)
        
        if ids is None or len(ids) == 0:
            return None, None, 0
        
        # Refine detection using new API
        corners, ids, rejected, recovered = self.detector.refineDetectedMarkers(
            image,
            self.board,
            corners,
            ids,
            rejected
        )
        
        return corners, ids, len(ids) if ids is not None else 0
    
    def draw_detections(self, image, corners, ids):
        """
        Draw detected markers on image for visualization.
        """
        # Always convert to BGR for consistent output
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            image = image.copy()
        
        # Draw markers if detected
        if corners is not None and ids is not None:
            cv2.aruco.drawDetectedMarkers(image, corners, ids)
        
        return image
    
    def save_capture(self, img_left, img_right, corners_left, ids_left, corners_right, ids_right):
        """
        Save a calibration capture.
        """
        capture_id = len(self.captures)
        
        # Save images
        cv2.imwrite(str(self.output_dir / f"left_{capture_id:03d}.png"), img_left)
        cv2.imwrite(str(self.output_dir / f"right_{capture_id:03d}.png"), img_right)
        
        # Save detection data
        capture_data = {
            'id': capture_id,
            'left_markers': len(ids_left) if ids_left is not None else 0,
            'right_markers': len(ids_right) if ids_right is not None else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        self.captures.append(capture_data)
        
        return capture_id
    
    def run(self):
        """
        Run the capture tool.
        """
        print("="*70)
        print("  ARUCO STEREO CALIBRATION CAPTURE")
        print("="*70)
        print()
        print("INSTRUCTIONS:")
        print("  1. Hold ArUco board so BOTH cameras can see it")
        print("  2. When markers detected, press SPACE to capture")
        print("  3. Move board to different position/angle")
        print("  4. Repeat until you have 20+ captures")
        print("  5. Press Q when done")
        print()
        print("TIPS:")
        print("  - Board should be 20-40cm above cameras")
        print("  - Try different angles (flat, tilted)")
        print("  - Try different positions (left, right, center)")
        print("  - More variety = better calibration")
        print()
        print(f"Captures needed: {self.min_captures}")
        print(f"Captures will be saved to: {self.output_dir}")
        print()
        print("Starting in 2 seconds...")
        import time
        time.sleep(2)
        
        # Initialize cameras
        print("\nInitializing cameras...")
        cameras = DualASICameraSystem()
        cameras.configure(exposure=20000, gain=200)
        cameras.start_capture()
        print("[OK] Cameras ready\n")
        
        print("CONTROLS:")
        print("  SPACE - Capture when both cameras detect board")
        print("  Q - Quit and save")
        print()
        
        # Create dummy window for key detection
        cv2.namedWindow("ArUco Capture", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("ArUco Capture", 800, 300)
        
        try:
            last_detection_status = ""
            
            while True:
                # Capture frames
                img_left, img_right = cameras.capture_frame_pair()
                
                if img_left is None or img_right is None:
                    continue
                
                # Detect markers
                corners_left, ids_left, count_left = self.detect_board(img_left)
                corners_right, ids_right, count_right = self.detect_board(img_right)
                
                # Create visualization
                vis_left = self.draw_detections(img_left, corners_left, ids_left)
                vis_right = self.draw_detections(img_right, corners_right, ids_right)
                
                # Resize for display
                vis_left = cv2.resize(vis_left, (400, 225))
                vis_right = cv2.resize(vis_right, (400, 225))
                
                # Combine side by side
                combined = np.hstack([vis_left, vis_right])
                
                # Add text
                status_text = f"L:{count_left} R:{count_right} | Captures:{len(self.captures)}/{self.min_captures}"
                cv2.putText(combined, status_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if count_left >= 10 and count_right >= 10:
                    cv2.putText(combined, "PRESS SPACE TO CAPTURE", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(combined, "Need 10+ markers in BOTH cameras", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                cv2.imshow("ArUco Capture", combined)
                
                # Print status (only when changed)
                current_status = f"[L:{count_left:2d} R:{count_right:2d}] Captures: {len(self.captures)}"
                if current_status != last_detection_status:
                    print(current_status, end='\r')
                    last_detection_status = current_status
                
                # Handle keys
                key = cv2.waitKey(10) & 0xFF
                
                if key == ord('q') or key == 27:  # Q or ESC
                    print()
                    break
                
                elif key == ord(' '):  # SPACE
                    if count_left >= 10 and count_right >= 10:
                        capture_id = self.save_capture(
                            img_left, img_right,
                            corners_left, ids_left,
                            corners_right, ids_right
                        )
                        print(f"\n✓ Capture {capture_id}: L={count_left} R={count_right} markers")
                        
                        if len(self.captures) >= self.min_captures:
                            print(f"  ✓ Minimum captures reached! ({len(self.captures)}/{self.min_captures})")
                            print(f"  You can press Q to finish, or continue for better accuracy")
                        
                        if len(self.captures) >= self.max_captures:
                            print(f"\n✓ Maximum captures reached! ({self.max_captures})")
                            print("Press Q to finish")
                    else:
                        print(f"\n✗ Not enough markers! Need 10+ in both cameras (L:{count_left} R:{count_right})")
        
        except KeyboardInterrupt:
            print("\nInterrupted")
        
        finally:
            cv2.destroyAllWindows()
            cameras.stop_capture()
            cameras.close()
            
            # Save metadata
            if self.captures:
                metadata = {
                    'captures': self.captures,
                    'board': {
                        'markers_x': self.markers_x,
                        'markers_y': self.markers_y,
                        'marker_length': self.marker_length,
                        'marker_separation': self.marker_separation,
                        'dictionary': 'DICT_4X4_50'
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                with open(self.output_dir / 'captures.json', 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                print()
                print("="*70)
                print(f"  ✓ SAVED {len(self.captures)} CAPTURES")
                print("="*70)
                print()
                print(f"Images: {self.output_dir}/")
                print(f"Metadata: {self.output_dir}/captures.json")
                print()
                
                if len(self.captures) >= self.min_captures:
                    print("NEXT STEP:")
                    print("  python camera\\aruco_stereo_compute.py")
                    print()
                else:
                    print(f"⚠️  Only {len(self.captures)} captures (need {self.min_captures})")
                    print("Run again to capture more images")
                    print()
            else:
                print("\n⚠️  No captures saved")


def main():
    capture = ArucoStereoCapture()
    capture.run()


if __name__ == "__main__":
    main()


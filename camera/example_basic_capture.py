"""
Example: Basic capture from dual ASI662MC cameras
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dual_asi_camera import DualASICameraSystem
import numpy as np
import time

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV not available - skipping image save")


def main():
    print("=== Dual ASI662MC Basic Capture Example ===\n")
    
    try:
        # Initialize camera system
        print("Initializing cameras...")
        cameras = DualASICameraSystem()
        
        # Configure cameras
        cameras.configure(
            width=1920,
            height=1080,
            exposure=50000,  # 50ms
            gain=100,
            wb_r=50,
            wb_b=95
        )
        
        # Start capture
        cameras.start_capture()
        
        # Capture 10 frames
        print("\nCapturing 10 frames...")
        for i in range(10):
            img_left, img_right = cameras.capture_frame_pair()
            
            if img_left is not None and img_right is not None:
                print(f"Frame {i+1:2d}: "
                      f"Left  [{img_left.min():3d}-{img_left.max():3d}] mean={img_left.mean():6.1f}, "
                      f"Right [{img_right.min():3d}-{img_right.max():3d}] mean={img_right.mean():6.1f}")
                
                # Save first frame
                if i == 0 and CV2_AVAILABLE:
                    # Debayer and save
                    rgb_left = cv2.cvtColor(img_left, cv2.COLOR_BAYER_RG2RGB)
                    rgb_right = cv2.cvtColor(img_right, cv2.COLOR_BAYER_RG2RGB)
                    
                    cv2.imwrite('data/capture_left.jpg', cv2.cvtColor(rgb_left, cv2.COLOR_RGB2BGR))
                    cv2.imwrite('data/capture_right.jpg', cv2.cvtColor(rgb_right, cv2.COLOR_RGB2BGR))
                    
                    print("  [Saved] data/capture_left.jpg, data/capture_right.jpg")
            else:
                print(f"Frame {i+1:2d}: Capture failed")
            
            time.sleep(0.2)
        
        # Get temperatures
        temp_left, temp_right = cameras.get_temperature()
        if temp_left is not None:
            print(f"\nCamera temperatures:")
            print(f"  Left:  {temp_left:5.1f}°C")
            print(f"  Right: {temp_right:5.1f}°C")
        
        # Get camera info
        info = cameras.get_info()
        print(f"\nCamera information:")
        print(f"  Resolution: {info['resolution']}")
        print(f"  Exposure: {info['exposure']} us")
        print(f"  Gain: {info['gain']}")
        print(f"  Baseline: {info['baseline']} mm")
        
        # Stop and close
        cameras.stop_capture()
        cameras.close()
        
        print("\n[OK] Capture completed successfully")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


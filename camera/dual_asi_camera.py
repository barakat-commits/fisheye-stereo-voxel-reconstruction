"""
Dual ZWO ASI Camera System
Manages two ASI662MC cameras for stereo capture
"""

import numpy as np
import time
from typing import Tuple, Optional, Dict

try:
    import zwoasi as asi
    ZWO_AVAILABLE = True
except ImportError:
    ZWO_AVAILABLE = False
    print("Warning: zwoasi not installed. Install with: pip install zwoasi")


class DualASICameraSystem:
    """Manages dual ASI662MC camera system for stereo imaging."""
    
    def __init__(self, camera_indices=(0, 1), lib_path=None):
        """
        Initialize dual ASI camera system.
        
        Args:
            camera_indices: Tuple of (left_cam_idx, right_cam_idx)
            lib_path: Path to ASICamera2.dll/.so (optional, uses default if None)
        """
        if not ZWO_AVAILABLE:
            raise RuntimeError("zwoasi library not installed")
        
        # Initialize SDK
        if lib_path:
            asi.init(lib_path)
        else:
            # Try default paths
            import os
            
            # Check multiple locations
            search_paths = []
            
            if os.name == 'nt':  # Windows
                # Check local camera folder first
                script_dir = os.path.dirname(os.path.abspath(__file__))
                search_paths = [
                    os.path.join(script_dir, 'ASICamera2.dll'),  # Same folder
                    'C:\\Windows\\System32\\ASICamera2.dll',      # System32
                    'C:\\ASI_SDK\\lib\\ASICamera2.dll',          # SDK folder
                ]
            else:  # Linux/Mac
                search_paths = [
                    '/usr/local/lib/libASICamera2.so',
                    '/usr/lib/libASICamera2.so',
                ]
            
            # Try each path
            sdk_found = False
            for path in search_paths:
                if os.path.exists(path):
                    asi.init(path)
                    sdk_found = True
                    break
            
            if not sdk_found:
                asi.init()  # Let library try to find it
        
        # Check available cameras
        num_cameras = asi.get_num_cameras()
        if num_cameras < 2:
            raise RuntimeError(
                f"Need 2 cameras for stereo, found {num_cameras}. "
                f"Check USB connections."
            )
        
        print(f"Found {num_cameras} ASI cameras")
        
        # List all cameras
        camera_list = asi.list_cameras()
        for i, cam_name in enumerate(camera_list):
            print(f"  Camera {i}: {cam_name}")
        
        # Open cameras
        self.camera_left = asi.Camera(camera_indices[0])
        self.camera_right = asi.Camera(camera_indices[1])
        
        # Get camera properties
        self.info_left = self.camera_left.get_camera_property()
        self.info_right = self.camera_right.get_camera_property()
        
        print(f"\nLeft camera:  {self.info_left['Name']}")
        print(f"Right camera: {self.info_right['Name']}")
        
        # Camera parameters
        self.width = 1920
        self.height = 1080
        self.exposure = 50000  # μs
        self.gain = 100
        self.is_capturing = False
        
        # Stereo calibration (placeholder - should be calibrated)
        self.baseline = 100.0  # mm between camera centers
        self.focal_length = 2.9  # mm (pixel size for ASI662MC)
        
    def configure(self, width=1920, height=1080, exposure=50000, 
                  gain=100, wb_r=50, wb_b=95):
        """
        Configure both cameras with identical settings.
        
        Args:
            width: Image width (max 1920 for ASI662MC)
            height: Image height (max 1080 for ASI662MC)
            exposure: Exposure time in microseconds (32 to 2,000,000)
            gain: Gain value (0 to 600, typical 100-200)
            wb_r: White balance red (0-100)
            wb_b: White balance blue (0-100)
        """
        self.width = width
        self.height = height
        self.exposure = exposure
        self.gain = gain
        
        for i, camera in enumerate([self.camera_left, self.camera_right]):
            camera_name = "Left" if i == 0 else "Right"
            
            # Set ROI (Region of Interest)
            camera.set_roi(
                width=width,
                height=height,
                bins=1,  # No binning
                image_type=asi.ASI_IMG_RAW8  # 8-bit Bayer for color
            )
            
            # Set exposure (manual mode for consistency)
            camera.set_control_value(asi.ASI_EXPOSURE, exposure, auto=False)
            
            # Set gain (manual mode)
            camera.set_control_value(asi.ASI_GAIN, gain, auto=False)
            
            # White balance (for color cameras)
            camera.set_control_value(asi.ASI_WB_R, wb_r)
            camera.set_control_value(asi.ASI_WB_B, wb_b)
            
            # Disable auto white balance
            camera.set_control_value(asi.ASI_AUTO_MAX_GAIN, 300)
            camera.set_control_value(asi.ASI_AUTO_MAX_EXP, 100000)
            
            # Enable USB 3.0 high speed mode
            camera.set_control_value(asi.ASI_HIGH_SPEED_MODE, 1)
            
            # Flip settings (may need adjustment based on mount)
            camera.set_control_value(asi.ASI_FLIP, 0)  # No flip
            
            print(f"{camera_name} camera configured: {width}x{height}, "
                  f"exp={exposure}us, gain={gain}")
        
    def start_capture(self):
        """Start video capture mode on both cameras."""
        if self.is_capturing:
            print("Capture already running")
            return
        
        self.camera_left.start_video_capture()
        self.camera_right.start_video_capture()
        self.is_capturing = True
        
        # Small delay to let cameras stabilize
        time.sleep(0.1)
        
        print("Video capture started on both cameras")
    
    def capture_frame_pair(self, timeout=1000, retry=3):
        """
        Capture synchronized frames from both cameras.
        
        Args:
            timeout: Timeout in milliseconds per frame
            retry: Number of retry attempts
            
        Returns:
            Tuple of (img_left, img_right) as numpy arrays, or (None, None) on failure
        """
        if not self.is_capturing:
            raise RuntimeError("Cameras not in capture mode. Call start_capture() first.")
        
        for attempt in range(retry):
            try:
                # Capture from both cameras (as close in time as possible)
                frame_left = self.camera_left.capture_video_frame(timeout=timeout)
                frame_right = self.camera_right.capture_video_frame(timeout=timeout)
                
                if frame_left is None or frame_right is None:
                    if attempt < retry - 1:
                        continue
                    return None, None
                
                # Convert to numpy arrays
                img_left = np.frombuffer(frame_left, dtype=np.uint8)
                img_right = np.frombuffer(frame_right, dtype=np.uint8)
                
                # Reshape to image dimensions
                img_left = img_left.reshape((self.height, self.width))
                img_right = img_right.reshape((self.height, self.width))
                
                return img_left, img_right
                
            except Exception as e:
                if attempt < retry - 1:
                    print(f"Capture attempt {attempt+1} failed: {e}, retrying...")
                    time.sleep(0.05)
                else:
                    print(f"Capture failed after {retry} attempts: {e}")
                    return None, None
        
        return None, None
    
    def capture_debayered_pair(self, timeout=1000):
        """
        Capture and debayer frames to RGB.
        
        Returns:
            Tuple of (rgb_left, rgb_right) as numpy arrays
        """
        img_left, img_right = self.capture_frame_pair(timeout)
        
        if img_left is None or img_right is None:
            return None, None
        
        try:
            import cv2
            # Debayer using OpenCV (RGGB pattern for ASI662MC)
            rgb_left = cv2.cvtColor(img_left, cv2.COLOR_BAYER_RG2RGB)
            rgb_right = cv2.cvtColor(img_right, cv2.COLOR_BAYER_RG2RGB)
            
            return rgb_left, rgb_right
        except ImportError:
            print("OpenCV not available for debayering, returning raw Bayer")
            return img_left, img_right
    
    def get_temperature(self):
        """Get temperature of both cameras (if available)."""
        try:
            temp_left = self.camera_left.get_control_value(asi.ASI_TEMPERATURE)[0] / 10.0
            temp_right = self.camera_right.get_control_value(asi.ASI_TEMPERATURE)[0] / 10.0
            return temp_left, temp_right
        except:
            return None, None
    
    def stop_capture(self):
        """Stop video capture mode on both cameras."""
        if not self.is_capturing:
            print("Capture not running")
            return
        
        self.camera_left.stop_video_capture()
        self.camera_right.stop_video_capture()
        self.is_capturing = False
        
        print("Video capture stopped")
    
    def close(self):
        """Close both cameras and release resources."""
        if self.is_capturing:
            self.stop_capture()
        
        self.camera_left.close()
        self.camera_right.close()
        
        print("Cameras closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def get_info(self) -> Dict:
        """Get camera system information."""
        return {
            'left_camera': self.info_left,
            'right_camera': self.info_right,
            'resolution': (self.width, self.height),
            'exposure': self.exposure,
            'gain': self.gain,
            'baseline': self.baseline,
            'focal_length': self.focal_length
        }


def test_dual_cameras():
    """Test function for dual camera system."""
    print("=== Testing Dual ASI Camera System ===\n")
    
    try:
        # Initialize cameras
        cameras = DualASICameraSystem()
        
        # Configure with moderate settings
        cameras.configure(
            width=1920,
            height=1080,
            exposure=30000,  # 30ms
            gain=150
        )
        
        # Start capture
        cameras.start_capture()
        
        # Capture a few frames
        print("\nCapturing 10 frames...")
        for i in range(10):
            img_left, img_right = cameras.capture_frame_pair()
            
            if img_left is not None and img_right is not None:
                print(f"Frame {i+1}: Left={img_left.shape}, mean={img_left.mean():.1f}, "
                      f"Right={img_right.shape}, mean={img_right.mean():.1f}")
                time.sleep(0.1)
            else:
                print(f"Frame {i+1}: Failed to capture")
        
        # Check temperature
        temp_left, temp_right = cameras.get_temperature()
        if temp_left is not None:
            print(f"\nTemperatures: Left={temp_left:.1f}°C, Right={temp_right:.1f}°C")
        
        # Stop and close
        cameras.stop_capture()
        cameras.close()
        
        print("\n[OK] Test completed successfully")
        
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_dual_cameras()


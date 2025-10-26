"""
Camera Calibration Loader

Loads OpenCV calibration files (YAML/XML) and provides undistortion functions.
"""

import numpy as np
import yaml
import cv2
from pathlib import Path


class CameraCalibration:
    """Camera calibration data and undistortion functions."""
    
    def __init__(self, calibration_file):
        """Load calibration from file."""
        self.calibration_file = calibration_file
        self.camera_matrix = None
        self.dist_coeffs = None
        self.image_size = None
        self.camera_name = None
        
        self._load_calibration()
    
    def _load_calibration(self):
        """Load calibration from YAML file."""
        path = Path(self.calibration_file)
        
        if not path.exists():
            raise FileNotFoundError(f"Calibration file not found: {self.calibration_file}")
        
        # Load YAML
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse camera matrix
        if 'camera_matrix' in data:
            cm_data = data['camera_matrix']['data']
            self.camera_matrix = np.array(cm_data).reshape(3, 3)
        else:
            raise ValueError("No camera_matrix found in calibration file")
        
        # Parse distortion coefficients
        if 'distortion_coefficients' in data:
            dc_data = data['distortion_coefficients']['data']
            self.dist_coeffs = np.array(dc_data)
        else:
            self.dist_coeffs = np.zeros(5)
        
        # Get image size
        if 'image_width' in data and 'image_height' in data:
            self.image_size = (data['image_width'], data['image_height'])
        else:
            self.image_size = (1920, 1080)  # Default
        
        # Camera name
        self.camera_name = data.get('camera_name', 'unknown')
        
        print(f"[OK] Loaded calibration: {self.camera_name}")
        print(f"     Image: {self.image_size[0]}x{self.image_size[1]}")
        print(f"     fx={self.camera_matrix[0,0]:.2f}, fy={self.camera_matrix[1,1]:.2f}")
        print(f"     cx={self.camera_matrix[0,2]:.2f}, cy={self.camera_matrix[1,2]:.2f}")
        print(f"     Distortion k1={self.dist_coeffs[0]:.4f}")
    
    def undistort_point(self, pixel_x, pixel_y):
        """
        Undistort a single pixel coordinate.
        
        Args:
            pixel_x, pixel_y: Distorted pixel coordinates
        
        Returns:
            (undist_x, undist_y): Undistorted pixel coordinates
        """
        # Create point array
        point = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
        
        # Undistort
        undistorted = cv2.undistortPoints(
            point,
            self.camera_matrix,
            self.dist_coeffs,
            P=self.camera_matrix
        )
        
        return undistorted[0, 0, 0], undistorted[0, 0, 1]
    
    def undistort_points_batch(self, points):
        """
        Undistort multiple points at once (faster).
        
        Args:
            points: Nx2 numpy array of (x, y) pixel coordinates
        
        Returns:
            Nx2 numpy array of undistorted coordinates
        """
        if len(points) == 0:
            return points
        
        # Reshape for cv2
        points_reshaped = points.reshape(-1, 1, 2).astype(np.float32)
        
        # Undistort
        undistorted = cv2.undistortPoints(
            points_reshaped,
            self.camera_matrix,
            self.dist_coeffs,
            P=self.camera_matrix
        )
        
        return undistorted.reshape(-1, 2)
    
    def pixel_to_normalized_coords(self, pixel_x, pixel_y):
        """
        Convert pixel to normalized camera coordinates [-1, 1].
        Applies undistortion.
        
        Args:
            pixel_x, pixel_y: Distorted pixel coordinates
        
        Returns:
            (norm_x, norm_y): Normalized coordinates
        """
        # Undistort
        undist_x, undist_y = self.undistort_point(pixel_x, pixel_y)
        
        # Normalize using calibrated parameters
        fx = self.camera_matrix[0, 0]
        fy = self.camera_matrix[1, 1]
        cx = self.camera_matrix[0, 2]
        cy = self.camera_matrix[1, 2]
        
        # Convert to normalized coordinates
        norm_x = (undist_x - cx) / fx
        norm_y = (undist_y - cy) / fy
        
        return norm_x, norm_y
    
    def get_ray_direction(self, pixel_x, pixel_y):
        """
        Get 3D ray direction for a pixel (for upward-pointing camera).
        
        CORRECT COORDINATE SYSTEM:
          X: horizontal (left-right)
          Y: depth (forward-back, horizontal)
          Z: HEIGHT (up-down, VERTICAL)
        
        Args:
            pixel_x, pixel_y: Pixel coordinates
        
        Returns:
            normalized 3D ray direction [x, y, z] where Z is UP (HEIGHT)
        """
        # Get normalized coordinates
        norm_x, norm_y = self.pixel_to_normalized_coords(pixel_x, pixel_y)
        
        # For upward-pointing camera:
        # Camera Z-axis points UP in world coordinates (Z is height!)
        # Normalized x, y from camera become world X, Y spread
        # Primary direction is +Z (up)
        
        ray = np.array([
            norm_x,   # Horizontal (world X)
            norm_y,   # Depth (world Y)
            1.0       # Up (world Z - HEIGHT!)
        ])
        
        # Normalize
        ray = ray / np.linalg.norm(ray)
        
        return ray


def load_calibration(calibration_file):
    """
    Load camera calibration from file.
    
    Args:
        calibration_file: Path to calibration YAML/XML
    
    Returns:
        CameraCalibration object
    """
    return CameraCalibration(calibration_file)


if __name__ == "__main__":
    # Test calibration loading
    import sys
    
    if len(sys.argv) > 1:
        calib_file = sys.argv[1]
    else:
        calib_file = "camera/calibration.yml"
    
    print("Testing calibration loader...")
    print(f"Loading: {calib_file}\n")
    
    calib = load_calibration(calib_file)
    
    print("\nTest undistortion:")
    
    # Test corner points
    test_points = [
        (0, 0, "Top-left"),
        (1920, 0, "Top-right"),
        (960, 540, "Center"),
        (0, 1080, "Bottom-left"),
        (1920, 1080, "Bottom-right"),
    ]
    
    for px, py, label in test_points:
        try:
            undist_x, undist_y = calib.undistort_point(px, py)
            norm_x, norm_y = calib.pixel_to_normalized_coords(px, py)
            ray = calib.get_ray_direction(px, py)
            
            print(f"{label:15s} ({px:4d}, {py:4d})")
            print(f"  Undistorted:  ({undist_x:7.2f}, {undist_y:7.2f})")
            print(f"  Normalized:   ({norm_x:+.4f}, {norm_y:+.4f})")
            print(f"  Ray:          [{ray[0]:+.4f}, {ray[1]:+.4f}, {ray[2]:+.4f}]")
        except Exception as e:
            print(f"{label}: Error - {e}")
    
    print("\n[OK] Calibration test complete!")


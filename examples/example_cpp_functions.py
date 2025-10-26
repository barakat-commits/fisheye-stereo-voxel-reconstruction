"""
Example: Demonstrate C++ extension functions
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np

try:
    import process_image_cpp
    print("✓ C++ extension loaded successfully\n")
    CPP_AVAILABLE = True
except ImportError as e:
    print("✗ C++ extension not available")
    print(f"  Error: {e}")
    print("\nBuild it with:")
    print("  python setup.py build_ext --inplace")
    CPP_AVAILABLE = False


def test_rotation_matrix():
    """Test the rotation matrix generation."""
    if not CPP_AVAILABLE:
        return
    
    print("=== Test: Rotation Matrix Generation ===")
    
    # Create rotation matrix from Euler angles
    roll = np.radians(30)
    pitch = np.radians(45)
    yaw = np.radians(60)
    
    rotation_matrix = process_image_cpp.create_rotation_matrix(roll, pitch, yaw)
    
    print(f"Euler angles (degrees): roll={np.degrees(roll):.1f}, pitch={np.degrees(pitch):.1f}, yaw={np.degrees(yaw):.1f}")
    print(f"Rotation matrix:\n{rotation_matrix}")
    print(f"Matrix shape: {rotation_matrix.shape}")
    print()


def test_image_processing():
    """Test the image to voxel grid processing."""
    if not CPP_AVAILABLE:
        return
    
    print("=== Test: Image to Voxel Grid Processing ===")
    
    # Create a small test image
    image = np.random.rand(100, 100).astype(np.float32)
    camera_pos = np.array([0.0, 0.0, -50.0], dtype=np.float32)
    camera_rot = np.eye(3, dtype=np.float32)
    grid_center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    
    grid_size = 32
    voxel_size = 1.0
    attenuation = 0.01
    
    print(f"Input image shape: {image.shape}")
    print(f"Grid size: {grid_size}×{grid_size}×{grid_size}")
    print(f"Camera position: {camera_pos}")
    
    voxel_grid = process_image_cpp.process_image_to_voxel_grid(
        image,
        camera_pos,
        camera_rot,
        grid_size,
        voxel_size,
        grid_center,
        attenuation
    )
    
    print(f"\nOutput voxel grid shape: {voxel_grid.shape}")
    print(f"Non-zero voxels: {np.count_nonzero(voxel_grid)}")
    print(f"Max value: {voxel_grid.max():.6f}")
    print(f"Mean value: {voxel_grid.mean():.6f}")
    print()


def main():
    if not CPP_AVAILABLE:
        return
    
    test_rotation_matrix()
    test_image_processing()
    
    print("✓ All tests completed successfully")


if __name__ == "__main__":
    main()




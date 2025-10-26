"""
Example: Process an image into a voxel grid using C++ extension
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from utils.voxel_helpers import save_voxel_grid, print_grid_statistics

# Try to import the C++ extension
try:
    import process_image_cpp
    CPP_AVAILABLE = True
except ImportError:
    CPP_AVAILABLE = False
    print("Warning: C++ extension not available.")
    print("Build it with: python setup.py build_ext --inplace")


def create_test_image(width=640, height=480):
    """Create a test image with a bright spot in the center."""
    image = np.zeros((height, width), dtype=np.float32)
    
    # Create a Gaussian blob in the center
    center_x, center_y = width // 2, height // 2
    sigma = min(width, height) / 8
    
    for y in range(height):
        for x in range(width):
            dx = x - center_x
            dy = y - center_y
            distance_sq = dx**2 + dy**2
            image[y, x] = np.exp(-distance_sq / (2 * sigma**2))
    
    return image


def process_with_cpp(image, grid_size=64, voxel_size=1.0):
    """Process image using the C++ extension."""
    if not CPP_AVAILABLE:
        print("C++ extension not available. Using fallback method.")
        return process_fallback(image, grid_size)
    
    # Camera parameters
    camera_position = np.array([0.0, 0.0, -100.0], dtype=np.float32)
    camera_rotation = np.eye(3, dtype=np.float32)
    grid_center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    attenuation_factor = 0.01
    
    print("Processing image with C++ ray casting...")
    voxel_grid = process_image_cpp.process_image_to_voxel_grid(
        image,
        camera_position,
        camera_rotation,
        grid_size,
        voxel_size,
        grid_center,
        attenuation_factor
    )
    
    return voxel_grid


def process_fallback(image, grid_size=64):
    """Fallback method: Simple 2D to 3D projection."""
    print("Using fallback projection method...")
    
    voxel_grid = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
    
    # Simple projection: map image to center slice of grid
    h, w = image.shape
    z_center = grid_size // 2
    
    # Resize image to fit grid
    from scipy.ndimage import zoom
    scale_y = grid_size / h
    scale_x = grid_size / w
    resized = zoom(image, (scale_y, scale_x), order=1)
    
    # Place in center slice
    voxel_grid[:, :, z_center] = resized[:grid_size, :grid_size]
    
    return voxel_grid


def main():
    print("=== Example: Image to Voxel Grid ===\n")
    
    # Parameters
    image_width = 640
    image_height = 480
    grid_size = 64
    output_file = "data/image_voxel_grid.bin"
    
    # Create test image
    print(f"Creating test image ({image_width}×{image_height})...")
    image = create_test_image(image_width, image_height)
    print(f"  Image min/max: {image.min():.4f} / {image.max():.4f}")
    
    # Process to voxel grid
    if CPP_AVAILABLE:
        voxel_grid = process_with_cpp(image, grid_size)
    else:
        try:
            from scipy.ndimage import zoom
            voxel_grid = process_fallback(image, grid_size)
        except ImportError:
            print("Error: scipy required for fallback method")
            print("Install with: pip install scipy")
            return
    
    # Print statistics
    print_grid_statistics(voxel_grid)
    
    # Save to file
    save_voxel_grid(voxel_grid, output_file)
    
    print(f"\nTo visualize, run:")
    print(f"  python spacevoxelviewer.py {output_file}")


if __name__ == "__main__":
    main()




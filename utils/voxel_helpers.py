"""
Utility functions for voxel grid operations
"""

import numpy as np
from typing import Tuple, Optional


def save_voxel_grid(voxel_grid: np.ndarray, filepath: str):
    """
    Save a voxel grid to a binary file.
    
    Args:
        voxel_grid: 3D numpy array
        filepath: Output file path (.bin)
    """
    voxel_grid.astype(np.float32).tofile(filepath)
    print(f"Saved voxel grid to {filepath}")
    print(f"  Shape: {voxel_grid.shape}")
    print(f"  Non-zero voxels: {np.count_nonzero(voxel_grid)}")
    print(f"  Max value: {voxel_grid.max():.4f}")


def load_voxel_grid(filepath: str, grid_size: Optional[int] = None) -> np.ndarray:
    """
    Load a voxel grid from a binary file.
    
    Args:
        filepath: Path to .bin file
        grid_size: Grid dimension (auto-detect if None)
    
    Returns:
        3D numpy array
    """
    data = np.fromfile(filepath, dtype=np.float32)
    
    if grid_size is None:
        total_voxels = len(data)
        grid_size = int(round(total_voxels ** (1/3)))
        
        if grid_size ** 3 != total_voxels:
            raise ValueError(f"Cannot auto-detect grid size. Total voxels: {total_voxels}")
    
    expected_size = grid_size ** 3
    if len(data) != expected_size:
        raise ValueError(f"Expected {expected_size} voxels, got {len(data)}")
    
    return data.reshape((grid_size, grid_size, grid_size))


def create_empty_voxel_grid(grid_size: int) -> np.ndarray:
    """
    Create an empty voxel grid.
    
    Args:
        grid_size: Dimension of cubic grid
    
    Returns:
        Zero-initialized 3D numpy array
    """
    return np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)


def create_test_voxel_grid(grid_size: int = 64) -> np.ndarray:
    """
    Create a test voxel grid with geometric patterns.
    
    Args:
        grid_size: Dimension of cubic grid
    
    Returns:
        3D numpy array with test pattern
    """
    voxel_grid = create_empty_voxel_grid(grid_size)
    
    center = grid_size // 2
    
    # Create a sphere in the center
    for i in range(grid_size):
        for j in range(grid_size):
            for k in range(grid_size):
                dx = i - center
                dy = j - center
                dz = k - center
                distance = np.sqrt(dx**2 + dy**2 + dz**2)
                
                # Sphere with radius grid_size/4
                if distance < grid_size / 4:
                    # Distance-based intensity
                    voxel_grid[i, j, k] = 1.0 - (distance / (grid_size / 4))
    
    return voxel_grid


def get_camera_direction_vectors(
    image_width: int,
    image_height: int,
    fov_degrees: float = 60.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate direction vectors for each pixel in a camera image.
    
    Args:
        image_width: Width of image in pixels
        image_height: Height of image in pixels
        fov_degrees: Field of view in degrees
    
    Returns:
        Tuple of (direction_x, direction_y) normalized coordinate grids
    """
    # Create normalized pixel coordinates (-1 to 1)
    x = np.linspace(-1, 1, image_width)
    y = np.linspace(-1, 1, image_height)
    
    # Create meshgrid
    xx, yy = np.meshgrid(x, y)
    
    # Apply FOV scaling
    fov_rad = np.radians(fov_degrees)
    scale = np.tan(fov_rad / 2.0)
    
    xx *= scale
    yy *= scale
    
    return xx, yy


def apply_threshold(voxel_grid: np.ndarray, percentile: float = 90) -> np.ndarray:
    """
    Apply threshold to voxel grid, keeping only bright voxels.
    
    Args:
        voxel_grid: Input 3D array
        percentile: Percentile threshold (0-100)
    
    Returns:
        Thresholded voxel grid
    """
    if np.count_nonzero(voxel_grid) == 0:
        return voxel_grid
    
    threshold = np.percentile(voxel_grid[voxel_grid > 0], percentile)
    result = voxel_grid.copy()
    result[result < threshold] = 0
    
    return result


def normalize_voxel_grid(voxel_grid: np.ndarray) -> np.ndarray:
    """
    Normalize voxel grid to [0, 1] range.
    
    Args:
        voxel_grid: Input 3D array
    
    Returns:
        Normalized voxel grid
    """
    if voxel_grid.max() == 0:
        return voxel_grid
    
    return voxel_grid / voxel_grid.max()


def get_grid_statistics(voxel_grid: np.ndarray) -> dict:
    """
    Calculate statistics for a voxel grid.
    
    Args:
        voxel_grid: 3D numpy array
    
    Returns:
        Dictionary with statistics
    """
    non_zero = voxel_grid[voxel_grid > 0]
    
    stats = {
        'shape': voxel_grid.shape,
        'total_voxels': voxel_grid.size,
        'non_zero_voxels': np.count_nonzero(voxel_grid),
        'occupancy_ratio': np.count_nonzero(voxel_grid) / voxel_grid.size,
        'min_value': voxel_grid.min(),
        'max_value': voxel_grid.max(),
        'mean_value': voxel_grid.mean(),
        'mean_non_zero': non_zero.mean() if len(non_zero) > 0 else 0,
        'std_non_zero': non_zero.std() if len(non_zero) > 0 else 0,
    }
    
    return stats


def print_grid_statistics(voxel_grid: np.ndarray):
    """Print formatted statistics for a voxel grid."""
    stats = get_grid_statistics(voxel_grid)
    
    print("\n=== Voxel Grid Statistics ===")
    print(f"Grid shape: {stats['shape']}")
    print(f"Total voxels: {stats['total_voxels']:,}")
    print(f"Non-zero voxels: {stats['non_zero_voxels']:,}")
    print(f"Occupancy ratio: {stats['occupancy_ratio']:.4%}")
    print(f"Value range: [{stats['min_value']:.4f}, {stats['max_value']:.4f}]")
    print(f"Mean (all): {stats['mean_value']:.4f}")
    print(f"Mean (non-zero): {stats['mean_non_zero']:.4f}")
    print(f"Std (non-zero): {stats['std_non_zero']:.4f}")
    print("=" * 30 + "\n")




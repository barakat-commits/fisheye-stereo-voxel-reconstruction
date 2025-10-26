"""
Example: Generate and visualize a test voxel grid
"""

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from utils.voxel_helpers import (
    create_test_voxel_grid,
    save_voxel_grid,
    print_grid_statistics
)

try:
    import pyvista as pv
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False
    print("Warning: PyVista not available. Skipping visualization.")


def main():
    print("=== Example: Voxel Grid Generation ===\n")
    
    # Parameters
    grid_size = 64
    output_file = "data/example_voxel_grid.bin"
    
    print(f"Creating test voxel grid ({grid_size}×{grid_size}×{grid_size})...")
    voxel_grid = create_test_voxel_grid(grid_size)
    
    # Print statistics
    print_grid_statistics(voxel_grid)
    
    # Save to file
    save_voxel_grid(voxel_grid, output_file)
    
    # Visualize if PyVista is available
    if PYVISTA_AVAILABLE:
        print("\nVisualizing voxel grid...")
        visualize(voxel_grid)
    else:
        print(f"\nTo visualize, install PyVista and run:")
        print(f"  python spacevoxelviewer.py {output_file}")


def visualize(voxel_grid, threshold_percentile=50):
    """Visualize the voxel grid using PyVista."""
    import pyvista as pv
    
    # Get voxels above threshold
    threshold = np.percentile(voxel_grid[voxel_grid > 0], threshold_percentile)
    indices = np.argwhere(voxel_grid > threshold)
    intensities = voxel_grid[voxel_grid > threshold]
    
    # Create point cloud
    points = indices.astype(float)
    cloud = pv.PolyData(points)
    cloud["intensity"] = intensities
    
    # Plot
    plotter = pv.Plotter()
    plotter.add_points(
        cloud,
        scalars="intensity",
        cmap="hot",
        point_size=6.0,
        render_points_as_spheres=True
    )
    plotter.add_axes()
    plotter.add_text(
        f"Test Voxel Grid\nPoints: {len(points)}",
        position="upper_left"
    )
    plotter.show()


if __name__ == "__main__":
    main()




"""
Voxel Grid Visualization Tool
Loads and visualizes 3D voxel grids using PyVista
"""

import numpy as np
import pyvista as pv
import argparse
import sys
from pathlib import Path


def load_voxel_grid(filepath, grid_size=None):
    """
    Load a voxel grid from a binary file.
    
    Args:
        filepath: Path to .bin file containing voxel data
        grid_size: Grid dimension (N for N×N×N grid). Auto-detected if None.
    
    Returns:
        numpy array of shape (N, N, N)
    """
    data = np.fromfile(filepath, dtype=np.float32)
    
    if grid_size is None:
        # Auto-detect grid size (assuming cubic grid)
        total_voxels = len(data)
        grid_size = int(round(total_voxels ** (1/3)))
        
        if grid_size ** 3 != total_voxels:
            raise ValueError(f"Cannot determine grid size. Total voxels: {total_voxels}")
    
    expected_size = grid_size ** 3
    if len(data) != expected_size:
        raise ValueError(f"Expected {expected_size} voxels, got {len(data)}")
    
    return data.reshape((grid_size, grid_size, grid_size))


def voxel_grid_to_point_cloud(voxel_grid, threshold_percentile=90, voxel_size=1.0):
    """
    Convert voxel grid to point cloud, keeping only bright voxels.
    
    Args:
        voxel_grid: 3D numpy array
        threshold_percentile: Only keep voxels above this percentile
        voxel_size: Physical size of each voxel
    
    Returns:
        PyVista PolyData point cloud
    """
    N = voxel_grid.shape[0]
    
    # Check if grid is empty
    non_zero = voxel_grid[voxel_grid > 0]
    if len(non_zero) == 0:
        print("\n[WARNING] No voxels to visualize - grid is empty!")
        print("This means:")
        print("  1. Scene was too dark")
        print("  2. No motion detected")
        print("  3. Or 3D projection parameters need adjustment")
        print("\nTry generating test data:")
        print("  python examples/example_voxel_generation.py")
        return None
    
    # Filter voxels above threshold
    threshold = np.percentile(non_zero, threshold_percentile)
    print(f"Threshold value: {threshold:.4f}")
    
    indices = np.argwhere(voxel_grid > threshold)
    intensities = voxel_grid[voxel_grid > threshold]
    
    print(f"Displaying {len(indices)} voxels out of {N**3} total")
    
    # Convert indices to 3D coordinates
    points = indices.astype(float) * voxel_size
    
    # Center the grid
    center_offset = (N * voxel_size) / 2.0
    points -= center_offset
    
    # Create PyVista point cloud
    cloud = pv.PolyData(points)
    cloud["intensity"] = intensities
    
    return cloud


def visualize_voxel_grid(
    voxel_grid,
    threshold_percentile=90,
    voxel_size=1.0,
    output_image=None,
    interactive=True,
    window_size=(1920, 1080),
    show_cameras=False,
    camera_positions=None
):
    """
    Visualize a voxel grid using PyVista.
    
    Args:
        voxel_grid: 3D numpy array
        threshold_percentile: Brightness threshold
        voxel_size: Physical size of voxels
        output_image: If provided, save screenshot to this path
        interactive: Show interactive window
        window_size: Window dimensions
    """
    cloud = voxel_grid_to_point_cloud(voxel_grid, threshold_percentile, voxel_size)
    
    if cloud is None:
        print("\nCannot visualize empty grid.")
        return
    
    # Create plotter
    plotter = pv.Plotter(off_screen=not interactive)
    
    # Add point cloud with colormap
    plotter.add_points(
        cloud,
        scalars="intensity",
        cmap="hot",
        point_size=4.0,
        render_points_as_spheres=True
    )
    
    # Add axes
    plotter.add_axes()
    
    # Add camera markers if requested
    if show_cameras and camera_positions is not None:
        for i, cam_pos in enumerate(camera_positions):
            # Camera as cone pointing up
            cone = pv.Cone(center=cam_pos, direction=(0, 1, 0), 
                          height=0.05, radius=0.02)
            plotter.add_mesh(cone, color='yellow' if i == 0 else 'cyan',
                           label=f'Camera {i}')
            
            # Camera label
            plotter.add_point_labels([cam_pos], [f'Cam{i}'],
                                    font_size=20, point_color='white',
                                    text_color='white')
    
    # Set camera
    plotter.camera_position = 'iso'
    
    # Add title
    N = voxel_grid.shape[0]
    plotter.add_text(
        f"Voxel Grid: {N}×{N}×{N}\nPoints: {len(cloud.points)}",
        position="upper_left",
        font_size=12
    )
    
    # Save screenshot if requested
    if output_image:
        plotter.screenshot(output_image, window_size=window_size)
        print(f"Saved screenshot to {output_image}")
    
    # Show interactive window
    if interactive:
        plotter.show(window_size=window_size)
    else:
        plotter.close()


def apply_rotation(voxel_grid, rotation_matrix):
    """
    Apply rotation to voxel grid (simplified version).
    
    Args:
        voxel_grid: 3D numpy array
        rotation_matrix: 3x3 rotation matrix
    
    Returns:
        Rotated voxel grid
    """
    # This is a simplified implementation
    # For production, you'd want proper 3D rotation with interpolation
    print("Note: Rotation is a placeholder - implement full 3D rotation as needed")
    return voxel_grid


def main():
    parser = argparse.ArgumentParser(description="Visualize 3D voxel grids")
    parser.add_argument("input_file", type=str, help="Path to .bin voxel grid file")
    parser.add_argument("--grid-size", type=int, default=None, help="Grid dimension (auto-detect if not specified)")
    parser.add_argument("--threshold", type=float, default=90, help="Percentile threshold for display (0-100)")
    parser.add_argument("--voxel-size", type=float, default=1.0, help="Physical size of each voxel")
    parser.add_argument("--output", type=str, default=None, help="Save screenshot to this file")
    parser.add_argument("--no-interactive", action="store_true", help="Don't show interactive window")
    parser.add_argument("--window-width", type=int, default=1920, help="Window width")
    parser.add_argument("--window-height", type=int, default=1080, help="Window height")
    parser.add_argument("--show-cameras", action="store_true", help="Show camera positions in 3D view")
    parser.add_argument("--camera-positions", type=str, default=None, help='Camera positions as JSON: [[x,y,z],[x,y,z]]')
    
    args = parser.parse_args()
    
    # Check if file exists
    if not Path(args.input_file).exists():
        print(f"Error: File '{args.input_file}' not found")
        sys.exit(1)
    
    print(f"Loading voxel grid from {args.input_file}...")
    voxel_grid = load_voxel_grid(args.input_file, args.grid_size)
    
    print(f"Grid size: {voxel_grid.shape}")
    print(f"Non-zero voxels: {np.count_nonzero(voxel_grid)}")
    print(f"Max intensity: {voxel_grid.max():.4f}")
    print(f"Mean intensity: {voxel_grid.mean():.4f}")
    
    # Parse camera positions if provided
    camera_positions = None
    if args.show_cameras:
        if args.camera_positions:
            import json
            camera_positions = json.loads(args.camera_positions)
        else:
            # Default: upward cameras at (0,0,0) and (0.5,0,0)
            camera_positions = [[0.0, 0.0, 0.0], [0.5, 0.0, 0.0]]
    
    visualize_voxel_grid(
        voxel_grid,
        threshold_percentile=args.threshold,
        voxel_size=args.voxel_size,
        output_image=args.output,
        interactive=not args.no_interactive,
        window_size=(args.window_width, args.window_height),
        show_cameras=args.show_cameras,
        camera_positions=camera_positions
    )


if __name__ == "__main__":
    main()


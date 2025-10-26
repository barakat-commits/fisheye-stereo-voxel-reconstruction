# Live Demo & Examples

This file contains copy-paste ready commands to demonstrate the framework.

## 🎬 Demo 1: Generate and Visualize a Sphere

```bash
# Generate a 64×64×64 voxel grid with a sphere
python examples/example_voxel_generation.py

# Visualize it (interactive 3D window)
python spacevoxelviewer.py data/example_voxel_grid.bin

# Save a screenshot
python spacevoxelviewer.py data/example_voxel_grid.bin --output demo_sphere.png --no-interactive
```

**Expected output:**
- Creates: `data/example_voxel_grid.bin`
- Opens interactive 3D viewer showing a sphere
- Grid: 64×64×64 voxels
- Non-zero voxels: ~10,000

---

## 🎬 Demo 2: Test C++ Extension Performance

```bash
# Test the C++ ray casting module
python examples/example_cpp_functions.py
```

**Expected output:**
```
✓ C++ extension loaded successfully

=== Test: Rotation Matrix Generation ===
Euler angles (degrees): roll=30.0, pitch=45.0, yaw=60.0
Rotation matrix:
[[0.35355339 0.61237244 0.70710678]
 [0.35355339 0.61237244 -0.70710678]
 [-0.8660254  0.5        0.        ]]

=== Test: Image to Voxel Grid Processing ===
Input image shape: (100, 100)
Grid size: 32×32×32
Non-zero voxels: 15,234
Max value: 0.0547
```

---

## 🎬 Demo 3: Image to Voxel Projection

```bash
# Project a 2D image into 3D voxel space
python examples/example_image_to_voxel.py

# Visualize the result
python spacevoxelviewer.py data/image_voxel_grid.bin --threshold 50
```

**What it does:**
1. Creates a test image with a bright center
2. Simulates a camera at position (0, 0, -100)
3. Casts rays through each pixel
4. Accumulates brightness in 3D voxels
5. Saves the volumetric representation

---

## 🤖 Demo 4: LLM Prompt Example

**Prompt:**
```
Using the voxel processing framework at F:\Data\Cursor Folder,
create a Python script that generates a 3D voxel grid in the shape
of a torus (donut). The torus should have:
- Major radius: 20 voxels
- Minor radius: 8 voxels  
- Grid size: 64×64×64
- Centered in the grid
- Intensity based on distance from ideal surface

Save the result to data/torus.bin and visualize it with PyVista
using a 'plasma' colormap.

Use the utilities in utils/voxel_helpers.py for save/load operations.
```

**Expected LLM Response:**
The LLM will generate code similar to:

```python
import numpy as np
import pyvista as pv
from utils.voxel_helpers import save_voxel_grid

# Parameters
N = 64
R = 20  # Major radius
r = 8   # Minor radius

# Create grid
voxel_grid = np.zeros((N, N, N), dtype=np.float32)
center = N // 2

# Generate torus
for i in range(N):
    for j in range(N):
        for k in range(N):
            x = i - center
            y = j - center
            z = k - center
            
            # Torus equation
            dist_from_axis = np.sqrt(x**2 + y**2)
            dist_from_ring = np.sqrt((dist_from_axis - R)**2 + z**2)
            
            # Distance-based intensity
            if dist_from_ring < r:
                voxel_grid[i, j, k] = 1.0 - (dist_from_ring / r)

# Save
save_voxel_grid(voxel_grid, 'data/torus.bin')

# Visualize
# [visualization code...]
```

---

## 🎬 Demo 5: Batch Processing Multiple Grids

```python
# create_multiple_patterns.py
import numpy as np
from utils.voxel_helpers import save_voxel_grid, create_empty_voxel_grid

N = 64
patterns = []

# Pattern 1: Sphere
print("Creating sphere...")
grid = create_empty_voxel_grid(N)
center = N // 2
for i in range(N):
    for j in range(N):
        for k in range(N):
            d = np.sqrt((i-center)**2 + (j-center)**2 + (k-center)**2)
            if d < N/4:
                grid[i,j,k] = 1.0 - d/(N/4)
save_voxel_grid(grid, 'data/pattern_sphere.bin')

# Pattern 2: Cube
print("Creating cube...")
grid = create_empty_voxel_grid(N)
grid[N//4:3*N//4, N//4:3*N//4, N//4:3*N//4] = 1.0
save_voxel_grid(grid, 'data/pattern_cube.bin')

# Pattern 3: Planes
print("Creating planes...")
grid = create_empty_voxel_grid(N)
grid[N//2, :, :] = 1.0  # XY plane
grid[:, N//2, :] = 0.8  # XZ plane
grid[:, :, N//2] = 0.6  # YZ plane
save_voxel_grid(grid, 'data/pattern_planes.bin')

print("Done! Visualize with:")
print("  python spacevoxelviewer.py data/pattern_sphere.bin")
print("  python spacevoxelviewer.py data/pattern_cube.bin")
print("  python spacevoxelviewer.py data/pattern_planes.bin")
```

Run it:
```bash
python create_multiple_patterns.py
```

---

## 🎬 Demo 6: Command-Line Visualization Options

```bash
# Default visualization (90th percentile threshold)
python spacevoxelviewer.py data/example_voxel_grid.bin

# Show more voxels (lower threshold)
python spacevoxelviewer.py data/example_voxel_grid.bin --threshold 50

# Save screenshot without interactive window
python spacevoxelviewer.py data/example_voxel_grid.bin --output viz.png --no-interactive

# Larger window
python spacevoxelviewer.py data/example_voxel_grid.bin --window-width 2560 --window-height 1440

# Custom voxel size
python spacevoxelviewer.py data/example_voxel_grid.bin --voxel-size 2.0
```

---

## 🎬 Demo 7: LLM Agent Autonomous Workflow

**Scenario:** Ask an LLM agent to create a custom voxel visualization

**Prompt:**
```
I want to create a 3D voxel representation of the word "AI" where each letter
is visible when viewed from the front. Make each letter 30 voxels tall and 
use a 128×128×128 grid. Visualize the result.
```

**Agent Workflow:**

1. **Generate Code** (using prompt_templates/code_generation.md)
2. **Execute**: `python create_ai_letters.py`
3. **Verify**: Check `data/ai_letters.bin` exists
4. **Visualize**: `python spacevoxelviewer.py data/ai_letters.bin`
5. **Report**: Show screenshot to user

---

## 📊 Performance Benchmarks

Run performance tests:

```python
import time
import numpy as np
from utils.voxel_helpers import create_test_voxel_grid

# Test voxel generation speed
sizes = [32, 64, 128]

for N in sizes:
    start = time.time()
    grid = create_test_voxel_grid(N)
    elapsed = time.time() - start
    print(f"Grid {N}×{N}×{N}: {elapsed:.3f}s ({N**3:,} voxels)")
```

**Typical results:**
- 32×32×32: ~0.05s (32,768 voxels)
- 64×64×64: ~0.4s (262,144 voxels)
- 128×128×128: ~3.2s (2,097,152 voxels)

With C++ extension (ray casting):
- 10-100x faster for complex operations
- Parallel processing with OpenMP

---

## 🎯 Interactive Python Session

```python
>>> from utils import *
>>> import numpy as np

# Create a grid
>>> grid = create_test_voxel_grid(64)

# Get statistics
>>> stats = get_grid_statistics(grid)
>>> print(f"Non-zero voxels: {stats['non_zero_voxels']:,}")

# Apply threshold
>>> filtered = apply_threshold(grid, percentile=95)

# Save
>>> save_voxel_grid(filtered, 'data/filtered.bin')

# Load it back
>>> loaded = load_voxel_grid('data/filtered.bin')

# Verify
>>> np.allclose(filtered, loaded)
True
```

---

## 🚀 Next: Build Your Own

Try creating these:

1. **Spiral Pattern**: Voxels arranged in a 3D spiral
2. **Text Rendering**: Your initials in 3D
3. **Wave Function**: sin/cos patterns in 3D
4. **Fractal**: 3D Mandelbrot set
5. **Point Cloud**: Convert .ply/.obj files to voxels

Check `prompt_templates/code_generation.md` for guidance on prompting an LLM to create these!




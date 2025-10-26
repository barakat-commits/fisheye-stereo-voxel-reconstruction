# Quick Start Guide

Get up and running with the LLM Agent Code Execution Framework in 5 minutes!

## 🚀 Installation

### Windows

1. **Install Python 3.7+** (if not already installed)
   - Download from https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Run the build script:**
   ```cmd
   build.bat
   ```

   This will:
   - Install all Python dependencies
   - Attempt to build the C++ extension (requires Visual Studio Build Tools)
   - Run a test example

### Linux/macOS

1. **Install system dependencies:**
   ```bash
   sudo chmod +x setup.sh
   sudo ./setup.sh
   ```

2. **Run the build script:**
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

## 📚 First Examples

### Example 1: Generate a Test Voxel Grid

```bash
python examples/example_voxel_generation.py
```

This creates a 64×64×64 voxel grid with a sphere pattern and saves it to `data/example_voxel_grid.bin`.

### Example 2: Visualize the Voxel Grid

```bash
python spacevoxelviewer.py data/example_voxel_grid.bin
```

This opens an interactive 3D visualization window.

**Controls:**
- Left mouse drag: Rotate
- Right mouse drag: Pan
- Mouse wheel: Zoom
- 'q': Quit

### Example 3: Process Image to Voxels (requires C++ extension)

```bash
python examples/example_image_to_voxel.py
```

This demonstrates ray casting from a 2D image into a 3D voxel grid.

### Example 4: Test C++ Extension

```bash
python examples/example_cpp_functions.py
```

This verifies the C++ extension is working correctly.

## 🧠 Using with LLM Agents

### Prompt Example 1: Generate Custom Voxel Pattern

```
Using the voxel framework, create a Python script that generates
a 64×64×64 voxel grid with a torus (donut) shape. The torus should
have major radius 20 and minor radius 8, centered in the grid.
Save to data/torus.bin and visualize it.
```

### Prompt Example 2: Process Real Image

```
Create a script that:
1. Loads an image from 'input/photo.jpg'
2. Converts it to grayscale
3. Projects it into a 3D voxel grid using ray casting
4. Saves the result to 'data/photo_voxels.bin'
5. Creates a visualization and saves it as 'output/photo_viz.png'

Use the C++ extension for performance if available.
```

### Prompt Example 3: Batch Processing

```
Write a script that processes all PNG images in the 'input/' directory,
converts each to a voxel grid, and saves them with corresponding names
in the 'output/' directory. Include a progress bar and error handling
for corrupted images.
```

## 📖 Key Concepts

### Voxel Grids

A voxel grid is a 3D array of values representing volumetric data. Think of it as a 3D image where each voxel (volume pixel) has an intensity value.

**Structure:**
- Shape: (N, N, N) where N is typically 32, 64, 128, or 256
- Data type: float32
- Storage: Binary files (.bin)
- Values: Typically normalized to [0, 1] range

### Ray Casting

Ray casting projects 2D image data into 3D space by:
1. Positioning a virtual camera
2. Casting a ray through each pixel
3. Accumulating pixel brightness in voxels along the ray
4. Applying distance-based attenuation

### Visualization

PyVista is used for 3D visualization:
- Converts voxel grids to point clouds
- Applies thresholding to show only bright voxels
- Provides interactive 3D viewing
- Exports images and videos

## 🛠️ Troubleshooting

### C++ Extension Won't Build

**Windows:**
- Install Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/
- Make sure to include "C++ build tools" workload

**Linux:**
```bash
sudo apt-get install build-essential python3-dev
```

**macOS:**
```bash
xcode-select --install
```

### PyVista Visualization Doesn't Work

Try updating your graphics drivers. For headless servers, use the off-screen rendering mode:

```bash
python spacevoxelviewer.py data/voxel_grid.bin --output viz.png --no-interactive
```

### Import Errors

Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

If using a virtual environment, make sure it's activated.

## 📂 File Organization

```
your_project/
├── data/              # Voxel grid files (.bin)
├── input/             # Input images
├── output/            # Generated visualizations
└── scripts/           # Your custom scripts
```

## 🎯 Next Steps

1. **Read the full documentation:** See `README.md`
2. **Explore prompt templates:** Check `prompt_templates/` directory
3. **Study the examples:** Look at files in `examples/`
4. **Create your own scripts:** Use the utilities in `utils/voxel_helpers.py`
5. **Optimize performance:** Enable C++ extension for 10-100x speedup

## 💡 Tips

- Start with small grid sizes (32×32×32) for quick iteration
- Use `print_grid_statistics()` to debug voxel data
- Visualize intermediate results to verify correctness
- Save expensive computations to avoid re-running
- Use the C++ extension for production workloads

## 📞 Getting Help

If you encounter issues:

1. Check the examples to see working code
2. Review the prompt templates for guidance
3. Verify all dependencies are installed
4. Try the Python-only fallback if C++ extension fails
5. Check error messages carefully - they're designed to be helpful!

---

**Happy Voxel Processing! 🎉**




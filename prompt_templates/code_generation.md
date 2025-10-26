# Prompt Template: Code Generation for Voxel Processing

## 🎯 Purpose
Enable an LLM to generate Python scripts for voxel grid creation and manipulation.

---

## 📋 Template 1: Basic Voxel Grid Generation

```
You are a Python coding assistant specializing in 3D voxel processing.

TASK: Generate a Python script that accomplishes the following:

1. Creates a voxel grid of size {GRID_SIZE}×{GRID_SIZE}×{GRID_SIZE}
2. Populates it with a {PATTERN_TYPE} pattern (options: sphere, cube, random, gaussian)
3. Saves the grid to a binary file at {OUTPUT_PATH}
4. Prints statistics about the grid (non-zero voxels, min/max values, etc.)

REQUIREMENTS:
- Use numpy for array operations
- Save as float32 binary format
- Include proper error handling
- Add informative print statements
- Grid should be stored as a 3D numpy array with shape (N, N, N)

LIBRARIES AVAILABLE:
- numpy
- scipy (if needed)
- Custom module: utils.voxel_helpers (contains save_voxel_grid, print_grid_statistics)

OUTPUT FORMAT:
Provide complete, runnable Python code with comments.
```

### Example Usage:
```python
GRID_SIZE = 64
PATTERN_TYPE = "sphere"
OUTPUT_PATH = "data/my_voxel_grid.bin"
```

---

## 📋 Template 2: Voxel Grid Visualization

```
You are a Python coding assistant specializing in 3D visualization with PyVista.

TASK: Generate a Python script that:

1. Loads a voxel grid from binary file {INPUT_FILE}
2. Applies a threshold to display only the top {PERCENTILE}% of bright voxels
3. Visualizes the voxels as a 3D point cloud using PyVista
4. Uses the "{COLORMAP}" colormap for intensity visualization
5. Saves a screenshot to {OUTPUT_IMAGE} if specified
6. Shows an interactive 3D window

REQUIREMENTS:
- Use PyVista for visualization
- Points should be rendered as spheres
- Include axes for reference
- Add a title showing grid dimensions and point count
- Camera should be in isometric view by default
- Point size should be {POINT_SIZE}

LIBRARIES AVAILABLE:
- pyvista
- numpy
- Custom module: spacevoxelviewer (contains helper functions)

OUTPUT FORMAT:
Complete Python script with proper imports and error handling.
```

### Example Usage:
```python
INPUT_FILE = "data/voxel_grid.bin"
PERCENTILE = 90
COLORMAP = "hot"
OUTPUT_IMAGE = "output/visualization.png"
POINT_SIZE = 4.0
```

---

## 📋 Template 3: Image-to-Voxel Projection

```
You are a Python coding assistant with expertise in 3D ray casting and computer vision.

TASK: Generate a script that projects a 2D image into a 3D voxel grid.

The script should:

1. Load an image from {IMAGE_PATH} (or create a test image if not provided)
2. Convert to grayscale/intensity values if needed
3. Define a camera at position {CAMERA_POS} looking at {LOOK_AT_POINT}
4. Cast rays from camera through each pixel into a voxel grid of size {GRID_SIZE}
5. Accumulate brightness values in voxels along each ray
6. Apply distance-based attenuation with factor {ATTENUATION}
7. Save resulting voxel grid to {OUTPUT_FILE}

REQUIREMENTS:
- Use the C++ extension 'process_image_cpp' if available, otherwise use fallback
- Camera should use pinhole projection model
- Voxel grid should be centered at the origin
- Include progress indicators for long operations
- Normalize image values to [0, 1] range

LIBRARIES AVAILABLE:
- numpy
- opencv-python (for image loading)
- process_image_cpp (C++ extension with process_image_to_voxel_grid function)
- utils.voxel_helpers

FUNCTION SIGNATURE (C++ extension):
process_image_to_voxel_grid(
    image: np.ndarray,           # 2D float32 array
    camera_position: np.ndarray, # [x, y, z] float32
    camera_rotation: np.ndarray, # 3x3 rotation matrix
    grid_size: int,              # N for N×N×N grid
    voxel_size: float,           # Physical size of each voxel
    grid_center: np.ndarray,     # [x, y, z] center of grid
    attenuation_factor: float    # Decay rate with distance
) -> np.ndarray                  # Returns (N, N, N) voxel grid

OUTPUT FORMAT:
Production-ready Python code with error handling and documentation.
```

### Example Usage:
```python
IMAGE_PATH = "input/test_image.jpg"
CAMERA_POS = [0, 0, -100]
LOOK_AT_POINT = [0, 0, 0]
GRID_SIZE = 64
ATTENUATION = 0.01
OUTPUT_FILE = "data/projected_voxels.bin"
```

---

## 📋 Template 4: Rotation and Transformation

```
You are a Python coding assistant specializing in 3D transformations.

TASK: Generate a script that applies transformations to a voxel grid.

The script should:

1. Load a voxel grid from {INPUT_FILE}
2. Apply the following transformations in order:
   - Rotation by {ROLL}° around X-axis
   - Rotation by {PITCH}° around Y-axis
   - Rotation by {YAW}° around Z-axis
   - Translation by vector {TRANSLATION}
3. Use interpolation method: {INTERPOLATION_METHOD}
4. Save transformed grid to {OUTPUT_FILE}
5. Visualize before/after side-by-side if {VISUALIZE} is True

REQUIREMENTS:
- Use scipy.ndimage for rotation with interpolation
- Preserve grid dimensions
- Handle edge cases (rotation may leave some voxels empty)
- Use proper Euler angle convention (ZYX)
- Optionally use C++ extension for rotation matrix generation

LIBRARIES AVAILABLE:
- numpy
- scipy.ndimage (affine_transform, rotate)
- process_image_cpp.create_rotation_matrix (for Euler to matrix conversion)

OUTPUT FORMAT:
Complete, documented Python code.
```

### Example Usage:
```python
INPUT_FILE = "data/input_voxels.bin"
ROLL = 30.0    # degrees
PITCH = 45.0   # degrees
YAW = 60.0     # degrees
TRANSLATION = [5, 10, -3]
INTERPOLATION_METHOD = "linear"  # or "nearest", "cubic"
OUTPUT_FILE = "data/rotated_voxels.bin"
VISUALIZE = True
```

---

## 🔧 Best Practices for LLM Code Generation

When using these templates with an LLM:

1. **Be Specific**: Fill in all {PLACEHOLDER} values with concrete parameters
2. **Provide Context**: Include relevant file paths and data formats
3. **Specify Constraints**: Memory limits, performance requirements, etc.
4. **Request Error Handling**: Always ask for try/except blocks
5. **Ask for Documentation**: Request docstrings and inline comments
6. **Validate Output**: Test generated code in a sandbox first
7. **Iterative Refinement**: Use follow-up prompts to fix issues

---

## 📝 Example Complete Prompt

```
You are a Python coding assistant specializing in 3D voxel processing.

TASK: Generate a Python script that accomplishes the following:

1. Creates a voxel grid of size 64×64×64
2. Populates it with a sphere pattern centered in the grid
3. Saves the grid to a binary file at "data/sphere_voxels.bin"
4. Prints statistics about the grid (non-zero voxels, min/max values, etc.)

REQUIREMENTS:
- Use numpy for array operations
- Save as float32 binary format
- Include proper error handling
- Add informative print statements
- Grid should be stored as a 3D numpy array with shape (N, N, N)
- Sphere should have radius = N/4 with distance-based intensity falloff

LIBRARIES AVAILABLE:
- numpy
- Custom module: utils.voxel_helpers (contains save_voxel_grid, print_grid_statistics)

OUTPUT FORMAT:
Provide complete, runnable Python code with comments explaining each step.
```




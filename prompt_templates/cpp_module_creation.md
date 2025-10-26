# Prompt Template: C++ Module Creation with pybind11

## 🎯 Purpose
Enable an LLM to generate C++ extensions for Python using pybind11, specifically for computationally intensive voxel operations.

---

## 📋 Template 1: Basic C++ Extension Module

```
You are an expert C++ programmer specializing in pybind11 Python bindings.

TASK: Create a C++ module using pybind11 that performs {OPERATION_DESCRIPTION}.

MODULE SPECIFICATIONS:
- Module name: {MODULE_NAME}
- Function name: {FUNCTION_NAME}
- Input parameters: {INPUT_PARAMS}
- Output: {OUTPUT_TYPE}

REQUIREMENTS:
1. Use pybind11 for Python bindings
2. Accept numpy arrays as input (use py::array_t<float>)
3. Return numpy arrays as output
4. Include proper error checking for array dimensions
5. Use OpenMP for parallel processing where applicable
6. Add buffer protocol for efficient memory access
7. Include comprehensive error messages

CODE STRUCTURE:
1. Include necessary headers (pybind11/pybind11.h, pybind11/numpy.h, pybind11/stl.h)
2. Define helper structs/classes if needed
3. Implement the main function
4. Create pybind11 module definition with PYBIND11_MODULE macro
5. Add docstrings for all exposed functions

PERFORMANCE CONSIDERATIONS:
- Use #pragma omp parallel for where beneficial
- Minimize memory allocations in loops
- Use const references for read-only parameters
- Ensure thread safety for shared data structures

OUTPUT FORMAT:
Complete C++ source file (.cpp) ready to compile with pybind11.
```

### Example Usage:
```cpp
MODULE_NAME = "voxel_processor"
FUNCTION_NAME = "process_voxels"
OPERATION_DESCRIPTION = "applies a Gaussian blur to a 3D voxel grid"
INPUT_PARAMS = "voxel_grid (N×N×N float array), sigma (float)"
OUTPUT_TYPE = "N×N×N float array (blurred grid)"
```

---

## 📋 Template 2: Ray Casting Module

```
You are an expert in 3D graphics programming and pybind11.

TASK: Create a C++ extension module for efficient ray casting into voxel grids.

The module should implement:

FUNCTION 1: cast_ray_into_grid
- Inputs:
  - camera_position: 3D point [x, y, z]
  - ray_direction: 3D normalized vector
  - grid_size: Integer N (for N×N×N grid)
  - voxel_size: Float (physical size of each voxel)
  - grid_center: 3D point [x, y, z]
- Output:
  - List of voxel indices (ix, iy, iz) and distances along ray
  
FUNCTION 2: process_image_to_voxel_grid
- Inputs:
  - image: 2D float array (H×W)
  - camera_position: 3D point
  - camera_rotation: 3×3 rotation matrix
  - grid_size: Integer N
  - voxel_size: Float
  - grid_center: 3D point
  - attenuation_factor: Float
- Output:
  - 3D voxel grid (N×N×N) with accumulated brightness

ALGORITHM REQUIREMENTS:
- Use Digital Differential Analyzer (DDA) for ray traversal
- Apply distance-based attenuation: exp(-attenuation * distance)
- Ensure thread safety when accumulating to voxel grid
- Use atomic operations for concurrent writes

OPTIMIZATION:
- Parallelize over image pixels using OpenMP
- Early termination when ray exits grid bounds
- Efficient voxel index calculation

DATA STRUCTURES:
Define a Vec3 struct for 3D vectors with basic operations (add, subtract, normalize, length)

OUTPUT FORMAT:
Complete, production-ready C++ file with:
1. All necessary includes
2. Vec3 and other helper structs
3. Ray casting implementation
4. pybind11 module definition
5. Inline comments explaining the algorithm
```

---

## 📋 Template 3: Setup.py for C++ Extension

```
You are a Python packaging expert specializing in C++ extensions.

TASK: Create a setup.py file to compile a C++ extension using pybind11.

REQUIREMENTS:
1. Extension name: {EXTENSION_NAME}
2. Source files: {SOURCE_FILES}
3. Compiler optimizations: -O3 for Unix, /O2 for MSVC
4. Enable OpenMP support
5. Include pybind11 headers automatically
6. Support for Windows (MSVC), Linux (GCC), and macOS (Clang)
7. Custom build_ext class for platform-specific options

PLATFORM-SPECIFIC FLAGS:
- Unix/Linux:
  - Compile: -O3, -fopenmp, -std=c++11
  - Link: -fopenmp
- MSVC (Windows):
  - Compile: /EHsc, /openmp, /O2
  - Link: /openmp
- macOS:
  - Additional: -stdlib=libc++, -mmacosx-version-min=10.7

FEATURES:
- Auto-detect pybind11 include paths
- Version information injection
- Hidden visibility for symbols (Unix)
- Proper dependency specification in install_requires

OUTPUT FORMAT:
Complete setup.py file ready to use with:
  python setup.py build_ext --inplace
```

### Example Usage:
```python
EXTENSION_NAME = "process_image_cpp"
SOURCE_FILES = ["process_image.cpp"]
```

---

## 📋 Template 4: Advanced Voxel Operations

```
You are an expert C++ programmer specializing in high-performance 3D data processing.

TASK: Create a C++ module with advanced voxel grid operations.

Implement the following functions:

1. VOXEL_BLUR: Apply 3D Gaussian blur
   - Input: voxel_grid (N×N×N), sigma (float), kernel_size (int)
   - Output: blurred grid (N×N×N)
   - Use separable convolution for efficiency

2. VOXEL_THRESHOLD: Apply multi-level thresholding
   - Input: voxel_grid (N×N×N), thresholds (list of floats)
   - Output: segmented grid with discrete levels
   
3. VOXEL_MORPHOLOGY: Morphological operations (erode, dilate, open, close)
   - Input: voxel_grid (N×N×N), operation (string), kernel_size (int)
   - Output: transformed grid

4. COMPUTE_GRADIENT: Calculate 3D gradient magnitude
   - Input: voxel_grid (N×N×N)
   - Output: gradient magnitude grid (N×N×N)

REQUIREMENTS:
- All functions should be parallelized with OpenMP
- Support in-place operations where possible
- Include boundary condition handling (zero-padding, mirror, wrap)
- Optimize memory layout for cache efficiency
- Return new arrays (don't modify input)

DATA STRUCTURES:
- Use std::vector for dynamic arrays
- Create utility functions for 3D indexing
- Implement bounds checking with helpful error messages

PYBIND11 BINDINGS:
- Expose all functions with clear docstrings
- Use keyword arguments with default values
- Support both contiguous and non-contiguous arrays

OUTPUT FORMAT:
Complete C++ source file with extensive comments and proper error handling.
```

---

## 🔧 Compilation Instructions Template

```
You are a build system expert. Provide clear, step-by-step instructions to compile the C++ extension.

Create instructions for:

1. PREREQUISITES:
   - Required packages for each OS (Windows, Linux, macOS)
   - Python package requirements
   - Compiler requirements

2. BUILD STEPS:
   - Command-line instructions
   - Verification that build succeeded
   - Troubleshooting common errors

3. TESTING:
   - How to verify the module loads in Python
   - Simple test commands to validate functionality

FORMAT:
Provide platform-specific markdown documentation with code blocks.
```

---

## 📝 Example Complete Prompt

```
You are an expert C++ programmer specializing in pybind11 Python bindings.

TASK: Create a C++ module using pybind11 that performs 3D voxel grid rotation.

MODULE SPECIFICATIONS:
- Module name: voxel_transform
- Function name: rotate_voxel_grid
- Input parameters: 
  - voxel_grid: N×N×N float numpy array
  - rotation_matrix: 3×3 float numpy array
  - interpolation: string ("nearest", "linear", or "cubic")
- Output: N×N×N float numpy array (rotated grid)

REQUIREMENTS:
1. Use pybind11 for Python bindings
2. Accept numpy arrays as input (use py::array_t<float>)
3. Return numpy arrays as output
4. Include proper error checking for array dimensions
5. Use OpenMP for parallel processing across voxels
6. Implement trilinear interpolation for "linear" mode
7. Add buffer protocol for efficient memory access
8. Include comprehensive error messages

ALGORITHM:
- For each output voxel, apply inverse rotation to find source coordinate
- Use interpolation to sample from source grid
- Handle out-of-bounds coordinates (return 0 or use boundary condition)

CODE STRUCTURE:
1. Include necessary headers (pybind11/pybind11.h, pybind11/numpy.h)
2. Define Vec3 struct for 3D coordinates
3. Implement interpolation functions
4. Implement main rotation function
5. Create pybind11 module definition with PYBIND11_MODULE macro
6. Add docstrings for all exposed functions

PERFORMANCE CONSIDERATIONS:
- Use #pragma omp parallel for to parallelize outer loop
- Pre-compute rotation matrix inverse
- Use const references for read-only parameters
- Minimize memory allocations

OUTPUT FORMAT:
Complete C++ source file (.cpp) ready to compile with pybind11, including detailed comments.
```

---

## 🚀 Build Verification Template

After generating code, verify with:

```python
# Test import
import {MODULE_NAME}

# Check available functions
print(dir({MODULE_NAME}))

# Test basic functionality
# ... add specific tests ...
```




# Installation Guide

## 📦 Dependency Resolution

This framework has **two levels of dependencies**:

### 1. Core Dependencies (Recommended)

For voxel processing and visualization only:

```bash
pip install -r requirements.txt
```

This installs:
- numpy, pybind11, scipy (core processing)
- pyvista (3D visualization)
- opencv-python, Pillow (image handling)
- matplotlib (plotting)

### 2. Full Dependencies (Optional)

If you need the additional LLM text processing tools mentioned in source documents:

```bash
pip install -r requirements-full.txt
```

This adds:
- nltk, tiktoken (text processing)
- PyPDF2, youtube-transcript-api (document extraction)
- beautifulsoup4, requests (web scraping)
- astropy (astronomical calculations)

## ⚠️ Compatibility with onefilellm

If you have `onefilellm` installed, there are **version conflicts** with some packages. Here are your options:

### Option 1: Use Core Only (Recommended)
```bash
pip install -r requirements.txt
```
This avoids all conflicts since the core framework doesn't need the conflicting packages.

### Option 2: Keep onefilellm Versions
If you need both this framework AND onefilellm:

```bash
# The conflicting packages are optional for this framework
# Just install core dependencies
pip install numpy pybind11 scipy pyvista opencv-python Pillow matplotlib
```

### Option 3: Use Virtual Environment
Create an isolated environment for this project:

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🔧 C++ Extension Build

### Windows

**Prerequisites:**
- Visual Studio 2019 or later with "Desktop development with C++" workload
- OR Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/

**Build:**
```cmd
python setup.py build_ext --inplace
```

### Linux

**Prerequisites:**
```bash
sudo apt-get update
sudo apt-get install build-essential python3-dev libomp-dev
```

**Build:**
```bash
python3 setup.py build_ext --inplace
```

### macOS

**Prerequisites:**
```bash
xcode-select --install
brew install libomp
```

**Build:**
```bash
python3 setup.py build_ext --inplace
```

## 🚀 Quick Install & Build

### Windows
```cmd
# Install dependencies (core only)
pip install -r requirements.txt

# Build everything
build.bat
```

### Linux/Mac
```bash
# Install system dependencies (optional)
sudo chmod +x setup.sh
sudo ./setup.sh

# Install Python dependencies
pip3 install -r requirements.txt

# Build everything
chmod +x build.sh
./build.sh
```

## ✅ Verify Installation

Test that everything works:

```bash
# Test core functionality
python examples/example_voxel_generation.py

# Test C++ extension (if built)
python examples/example_cpp_functions.py

# Test visualization
python spacevoxelviewer.py data/example_voxel_grid.bin
```

## 🐛 Troubleshooting

### "No module named 'process_image_cpp'"

The C++ extension didn't build. The framework will still work but slower. To fix:

1. Install C++ compiler (see above)
2. Run: `python setup.py build_ext --inplace`
3. If still fails, check error messages for missing dependencies

### "ModuleNotFoundError: No module named 'pyvista'"

Dependencies not installed:
```bash
pip install -r requirements.txt
```

### "ERROR: pip's dependency resolver..."

This is a **warning** about version conflicts with other packages (like onefilellm). 

**Solutions:**
- **Ignore it**: If you don't use the conflicting packages together
- **Use virtual environment**: Isolate this project
- **Install core only**: `pip install -r requirements.txt` (no conflicts)

### PyVista Visualization Issues

**If visualization window doesn't open:**

1. Update graphics drivers
2. Try headless mode:
   ```bash
   python spacevoxelviewer.py data/voxel_grid.bin --output image.png --no-interactive
   ```

3. Or install Qt backend:
   ```bash
   pip install pyqt5
   ```

## 📋 Minimum Requirements

- Python 3.7+
- 2GB RAM (8GB+ recommended for large grids)
- Graphics card supporting OpenGL 3.2+ (for visualization)

## 🔄 Update Dependencies

To update to latest compatible versions:

```bash
pip install -r requirements.txt --upgrade
```

To rebuild C++ extension after updates:

```bash
python setup.py build_ext --inplace --force
```




#!/bin/bash
# Build script for Linux/macOS
# Compiles C++ extension and runs basic tests

set -e  # Exit on error

echo "================================================"
echo "  LLM Agent Code Execution Framework"
echo "  Build Script for Linux/macOS"
echo "================================================"
echo ""

# Check Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    echo "Please install Python 3.7+"
    exit 1
fi

echo "[1/5] Checking Python version..."
python3 --version

echo ""
echo "[2/5] Installing Python dependencies..."
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

echo ""
echo "[3/5] Building C++ extension..."
if python3 setup.py build_ext --inplace; then
    echo "✓ C++ extension built successfully"
else
    echo "WARNING: Failed to build C++ extension"
    echo ""
    echo "Possible issues:"
    echo "- No C++ compiler found (install gcc/g++ or clang)"
    echo "- OpenMP not available (install libomp-dev)"
    echo ""
    echo "You can still use Python-only features"
    echo "Continue? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "[4/5] Testing C++ extension..."
if python3 -c "import process_image_cpp; print('✓ C++ extension loaded successfully')" 2>/dev/null; then
    python3 examples/example_cpp_functions.py || echo "WARNING: C++ extension test failed"
else
    echo "WARNING: C++ extension not available, skipping tests"
fi

echo ""
echo "[5/5] Running example Python script..."
python3 examples/example_voxel_generation.py

echo ""
echo "================================================"
echo "  Build completed successfully!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Run examples: python3 examples/example_voxel_generation.py"
echo "  2. Visualize:    python3 spacevoxelviewer.py data/example_voxel_grid.bin"
echo "  3. Read docs:    See README.md and prompt_templates/"
echo ""




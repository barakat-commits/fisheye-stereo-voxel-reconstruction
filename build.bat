@echo off
REM Build script for Windows
REM Compiles C++ extension and runs basic tests

echo ================================================
echo   LLM Agent Code Execution Framework
echo   Build Script for Windows
echo ================================================
echo.

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.7+ and add to PATH
    exit /b 1
)

echo [1/5] Checking Python version...
python --version

echo.
echo [2/5] Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

echo.
echo [3/5] Building C++ extension...
python setup.py build_ext --inplace
if errorlevel 1 (
    echo ERROR: Failed to build C++ extension
    echo.
    echo Possible issues:
    echo - No C++ compiler found (install Visual Studio Build Tools)
    echo - pybind11 not installed (should be in requirements.txt)
    echo.
    echo You can still use Python-only features
    pause
    goto :skip_cpp_test
)

echo.
echo [4/5] Testing C++ extension...
python -c "import process_image_cpp; print('✓ C++ extension loaded successfully')"
if errorlevel 1 (
    echo WARNING: C++ extension built but cannot import
    goto :skip_cpp_test
)

python examples/example_cpp_functions.py
if errorlevel 1 (
    echo WARNING: C++ extension test failed
)

:skip_cpp_test
echo.
echo [5/5] Running example Python script...
python examples/example_voxel_generation.py
if errorlevel 1 (
    echo ERROR: Example script failed
    exit /b 1
)

echo.
echo ================================================
echo   Build completed successfully!
echo ================================================
echo.
echo Next steps:
echo   1. Run examples: python examples/example_voxel_generation.py
echo   2. Visualize:    python spacevoxelviewer.py data/example_voxel_grid.bin
echo   3. Read docs:    See README.md and prompt_templates/
echo.
pause




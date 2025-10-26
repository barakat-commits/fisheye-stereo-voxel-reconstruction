#!/bin/bash
# Setup script for Linux systems
# Install system-level dependencies for C++ compilation and visualization

echo "Installing C++ build tools..."
apt-get update
apt-get install -y \
    gcc \
    g++ \
    cmake \
    make \
    build-essential

echo "Installing OpenMP support..."
apt-get install -y libomp-dev

echo "Installing OpenCV dependencies..."
apt-get install -y \
    libopencv-dev \
    python3-opencv

echo "Installing OpenGL/GLUT for visualization..."
apt-get install -y \
    freeglut3-dev \
    libglu1-mesa-dev \
    mesa-common-dev

echo "Installing compression libraries..."
apt-get install -y zlib1g-dev

echo "Installing Python development headers..."
apt-get install -y python3-dev

echo "System dependencies installed successfully!"
echo "Next step: pip install -r requirements.txt"




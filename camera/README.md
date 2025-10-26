# ZWO ASI Camera Integration

Real-time 3D voxel reconstruction from dual ASI662MC cameras.

## 🎥 Overview

This module integrates ZWO ASI cameras (specifically the ASI662MC) with the voxel processing framework for real-time stereo vision and 3D reconstruction.

## 📋 Features

- **Dual Camera Control**: Manage two ASI662MC cameras simultaneously
- **Synchronized Capture**: Frame-synchronized stereo imaging
- **Real-Time Processing**: Live 3D voxel reconstruction at 15-30 FPS
- **Auto-Configuration**: Easy setup with sensible defaults
- **C++ Acceleration**: Uses the voxel framework's C++ extension for fast ray casting

## 🔧 Hardware Setup

### Required Hardware

- 2× ZWO ASI662MC cameras
- 2× USB 3.0 ports (separate controllers recommended for best performance)
- Mounting system (stereo baseline: ~100mm typical)
- Good lighting or adjustable camera gain

### ASI662MC Specifications

- **Sensor**: Sony IMX662 CMOS
- **Resolution**: 1920 × 1080 (2.07 MP)
- **Frame Rate**: Up to 60 FPS @ full resolution
- **Interface**: USB 3.0
- **Bit Depth**: 8-bit or 12-bit
- **Color**: Bayer RGB (RGGB pattern)

## 📦 Installation

### 1. Install ZWO ASI SDK

**Windows:**
```bash
# Download from: https://www.zwoastro.com/downloads/developers
# Extract and copy ASICamera2.dll to C:\Windows\System32\
```

**Linux:**
```bash
wget https://www.zwoastro.com/software/ASI_linux_mac_SDK_V1.34.tar.bz2
tar -xvf ASI_linux_mac_SDK_V1.34.tar.bz2
cd ASI_linux_mac_SDK_V1.34/lib/
sudo cp x64/libASICamera2.so /usr/local/lib/
sudo ldconfig

# Set udev rules for USB access
sudo nano /etc/udev/rules.d/99-asi-cameras.rules
# Add: SUBSYSTEMS=="usb", ATTRS{idVendor}=="03c3", MODE="0666"
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 2. Install Python Dependencies

```bash
# Install camera support
pip install -r requirements-camera.txt

# Or manually:
pip install zwoasi
```

### 3. Test Installation

```bash
# Basic camera test
python camera/dual_asi_camera.py

# Should output:
# Found 2 ASI cameras
#   Camera 0: ASI662MC
#   Camera 1: ASI662MC
```

## 🚀 Quick Start

### Example 1: Basic Capture

```python
from camera import DualASICameraSystem

# Initialize cameras
cameras = DualASICameraSystem()

# Configure
cameras.configure(
    width=1920,
    height=1080,
    exposure=50000,  # 50ms
    gain=100
)

# Start capture
cameras.start_capture()

# Capture a frame pair
img_left, img_right = cameras.capture_frame_pair()

print(f"Left: {img_left.shape}, Right: {img_right.shape}")

# Clean up
cameras.stop_capture()
cameras.close()
```

### Example 2: Real-Time Voxel Reconstruction

```python
from camera import RealTimeVoxelReconstructor

# Create reconstructor
reconstructor = RealTimeVoxelReconstructor(grid_size=64)

# Initialize cameras
reconstructor.initialize_cameras(
    exposure=30000,  # 30ms for ~30 FPS
    gain=150
)

# Run for 10 seconds
reconstructor.run_live_reconstruction(
    duration_seconds=10,
    save_interval=2.0,
    display=True
)

# Output: data/final_reconstruction.bin
```

## 📝 Example Scripts

### Run Basic Capture Test

```bash
cd camera
python example_basic_capture.py
```

This will:
- Initialize both cameras
- Capture 10 frames
- Save first frame as JPG
- Display statistics

### Run Live Reconstruction

```bash
cd camera
python example_live_reconstruction.py
```

This will:
- Start dual camera capture
- Process frames into 3D voxel grid
- Save intermediate results every 2 seconds
- Show live camera preview
- Output final reconstruction

### Visualize Results

```bash
python spacevoxelviewer.py data/final_reconstruction.bin
```

## ⚙️ Configuration

### Camera Parameters

```python
cameras.configure(
    width=1920,          # Image width (max 1920)
    height=1080,         # Image height (max 1080)
    exposure=30000,      # Exposure in μs (32 to 2,000,000)
    gain=150,            # Gain (0-600, typical 100-200)
    wb_r=50,             # White balance red (0-100)
    wb_b=95              # White balance blue (0-100)
)
```

### Voxel Grid Settings

```python
reconstructor = RealTimeVoxelReconstructor(
    grid_size=64,        # 64×64×64 voxels
    voxel_size=1.0       # 1mm per voxel
)
```

## 🎯 Performance

### Typical Frame Rates

| Configuration | Camera FPS | Processing FPS | Grid Size |
|--------------|-----------|----------------|-----------|
| Python only | 30-60 | 1-2 | 64³ |
| C++ extension | 30-60 | 15-25 | 64³ |
| C++ extension | 30-60 | 5-10 | 128³ |

### Optimization Tips

1. **Use C++ Extension**: Essential for real-time performance
   ```bash
   python setup.py build_ext --inplace
   ```

2. **Reduce Exposure**: Shorter exposure = higher frame rate
   ```python
   exposure=16000  # 16ms for 60 FPS
   ```

3. **Use Binning**: Trade resolution for speed
   ```python
   cameras.set_roi(bins=2)  # 960×540 @ higher FPS
   ```

4. **Smaller Grid**: Fewer voxels = faster processing
   ```python
   grid_size=32  # Instead of 64
   ```

5. **Separate USB Controllers**: Each camera on different USB 3.0 controller

## 🔬 Calibration

For accurate 3D reconstruction, calibrate the stereo system:

```python
reconstructor = RealTimeVoxelReconstructor()
reconstructor.initialize_cameras()

# Interactive calibration with checkerboard
calibration = reconstructor.calibrate_from_checkerboard(
    num_images=20,
    chessboard_size=(9, 6)  # Internal corners
)
```

Print a checkerboard pattern:
- Standard: 9×6 internal corners
- Square size: 25mm typical
- Download: [OpenCV Calibration Patterns](https://docs.opencv.org/4.x/da/d0d/tutorial_camera_calibration_pattern.html)

## 📊 Output Files

### Voxel Grid Files

- `data/final_reconstruction.bin` - Final 3D reconstruction
- `data/live_reconstruction_*.bin` - Intermediate saves
- Format: Binary float32, shape (N, N, N)

### Camera Images

- `data/capture_left.jpg` - Left camera frame
- `data/capture_right.jpg` - Right camera frame

### Visualization

```bash
# Interactive 3D view
python spacevoxelviewer.py data/final_reconstruction.bin

# Save screenshot
python spacevoxelviewer.py data/final_reconstruction.bin --output reconstruction.png

# Adjust threshold
python spacevoxelviewer.py data/final_reconstruction.bin --threshold 75
```

## ⚠️ Troubleshooting

### Cameras Not Detected

```python
import zwoasi as asi
asi.init()  # Or specify path to .dll/.so
print(f"Cameras found: {asi.get_num_cameras()}")
```

**Solutions:**
- Check USB connections (should be USB 3.0)
- Install ASI SDK drivers
- Check Device Manager (Windows) or `lsusb` (Linux)
- Try different USB ports

### Low Frame Rate

- **Check USB**: Must be USB 3.0 (blue port)
- **Reduce exposure**: Lower values = faster capture
- **Enable high speed**: `ASI_HIGH_SPEED_MODE = 1` (done automatically)
- **Separate USB buses**: Use different USB controllers

### Processing Too Slow

- **Build C++ extension**: Essential for real-time
  ```bash
  python setup.py build_ext --inplace
  ```
- **Reduce grid size**: 32³ or 64³ instead of 128³
- **Lower camera resolution**: Use 1280×720 or binning

### Cameras Out of Sync

- Software synchronization is used (capture frames sequentially)
- Typical sync error: < 5ms
- For better sync: Use hardware trigger (advanced)

## 📚 API Reference

### DualASICameraSystem

```python
cameras = DualASICameraSystem(camera_indices=(0, 1), lib_path=None)
cameras.configure(**settings)
cameras.start_capture()
img_left, img_right = cameras.capture_frame_pair(timeout=1000)
cameras.stop_capture()
cameras.close()
```

### RealTimeVoxelReconstructor

```python
reconstructor = RealTimeVoxelReconstructor(grid_size=64, voxel_size=1.0)
reconstructor.initialize_cameras(**camera_config)
reconstructor.process_stereo_frame(img_left, img_right)
reconstructor.run_live_reconstruction(duration_seconds=10)
```

## 🔗 References

- [ZWO ASI SDK](https://www.zwoastro.com/downloads/developers)
- [python-zwoasi](https://github.com/python-zwoasi/python-zwoasi)
- [ASI662MC Product Page](https://www.zwoastro.com/product/asi662mc/)
- [OpenCV Stereo Calibration](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html)

## 📄 License

Part of the LLM Agent Code Execution Framework - MIT License




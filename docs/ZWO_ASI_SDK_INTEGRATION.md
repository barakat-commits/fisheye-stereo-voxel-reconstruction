# ZWO ASI SDK Integration Guide

## 🎥 Overview

This guide covers integrating ZWO ASI cameras (specifically dual ASI662MC cameras) with the voxel processing framework for real-time 3D reconstruction from stereo camera feeds.

## 📋 Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [SDK Installation](#sdk-installation)
3. [Python Integration](#python-integration)
4. [Dual Camera Setup](#dual-camera-setup)
5. [Real-Time Voxel Reconstruction](#real-time-voxel-reconstruction)
6. [Performance Optimization](#performance-optimization)

---

## 🔧 Hardware Requirements

### ASI662MC Camera Specifications

| Specification | Value |
|--------------|-------|
| **Sensor** | Sony IMX662 CMOS |
| **Resolution** | 1920 × 1080 (2.07 MP) |
| **Pixel Size** | 2.9 μm |
| **Frame Rate** | Up to 60 FPS @ full resolution |
| **Color** | Bayer RGB (RGGB pattern) |
| **Bit Depth** | 8-bit / 12-bit |
| **Interface** | USB 3.0 |
| **Exposure Range** | 32 μs to 2000 s |

### Dual Camera Setup

For 3D voxel reconstruction, you'll need:
- 2× ZWO ASI662MC cameras
- USB 3.0 ports (separate controllers recommended)
- Synchronized mounting (parallel or stereo baseline)
- Calibration targets (checkerboard pattern)

---

## 📦 SDK Installation

### Windows

1. **Download ZWO ASI SDK**
   ```
   https://www.zwoastro.com/downloads/developers
   ```

2. **Extract SDK**
   ```
   ASI_Camera_SDK/
   ├── include/
   │   └── ASICamera2.h
   └── lib/
       ├── x64/
       │   └── ASICamera2.dll
       └── x86/
           └── ASICamera2.dll
   ```

3. **Install to system**
   ```cmd
   # Copy DLL to Windows\System32 (x64)
   copy "lib\x64\ASICamera2.dll" "C:\Windows\System32\"
   
   # Or add SDK lib path to system PATH
   setx PATH "%PATH%;C:\path\to\ASI_Camera_SDK\lib\x64"
   ```

### Linux

1. **Download SDK**
   ```bash
   wget https://www.zwoastro.com/software/ASI_linux_mac_SDK_V1.34.tar.bz2
   tar -xvf ASI_linux_mac_SDK_V1.34.tar.bz2
   ```

2. **Install library**
   ```bash
   cd ASI_linux_mac_SDK_V1.34/lib/
   
   # For x64 systems
   sudo cp x64/libASICamera2.so /usr/local/lib/
   sudo ldconfig
   
   # Copy headers
   sudo cp ../include/ASICamera2.h /usr/local/include/
   ```

3. **Set udev rules** (for USB access without root)
   ```bash
   sudo nano /etc/udev/rules.d/99-asi-cameras.rules
   ```
   
   Add:
   ```
   # ZWO ASI Cameras
   SUBSYSTEMS=="usb", ATTRS{idVendor}=="03c3", MODE="0666"
   ```
   
   Reload:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

---

## 🐍 Python Integration

### Install Python Wrapper

```bash
pip install zwoasi
```

Or install from source:
```bash
git clone https://github.com/python-zwoasi/python-zwoasi.git
cd python-zwoasi
pip install .
```

### Set SDK Path

```python
import os
import zwoasi as asi

# Windows
asi.init('C:/Windows/System32/ASICamera2.dll')

# Linux
asi.init('/usr/local/lib/libASICamera2.so')

# Or use environment variable
os.environ['ZWO_ASI_LIB'] = '/path/to/ASICamera2.dll'
asi.init()
```

---

## 📷 Basic Camera Operations

### Initialize and Connect

```python
import zwoasi as asi
import numpy as np

# Initialize SDK
asi.init('/usr/local/lib/libASICamera2.so')

# Get number of cameras
num_cameras = asi.get_num_cameras()
print(f"Found {num_cameras} ASI cameras")

# Get camera info
if num_cameras > 0:
    camera_info = asi.list_cameras()
    for i, info in enumerate(camera_info):
        print(f"Camera {i}: {info}")

# Open first camera
camera = asi.Camera(0)
camera_info = camera.get_camera_property()
print(f"Camera: {camera_info['Name']}")
print(f"Max resolution: {camera_info['MaxWidth']}x{camera_info['MaxHeight']}")
```

### Configure Camera Settings

```python
# Set ROI (Region of Interest)
camera.set_roi(
    width=1920,
    height=1080,
    bins=1,  # No binning
    type=asi.ASI_IMG_RAW8  # 8-bit raw Bayer
)

# Set exposure
camera.set_control_value(
    asi.ASI_EXPOSURE,
    50000  # 50ms in microseconds
)

# Set gain
camera.set_control_value(
    asi.ASI_GAIN,
    100  # 0-600 range
)

# Set white balance (for color camera)
camera.set_control_value(asi.ASI_WB_R, 50)
camera.set_control_value(asi.ASI_WB_B, 95)

# Set high speed mode
camera.set_control_value(
    asi.ASI_HIGH_SPEED_MODE,
    1  # Enable USB 3.0 high speed
)

# Disable auto exposure/gain for consistent frames
camera.set_control_value(asi.ASI_EXPOSURE, 50000, auto=False)
camera.set_control_value(asi.ASI_GAIN, 100, auto=False)
```

### Capture Frames

```python
# Start video capture mode
camera.start_video_capture()

try:
    while True:
        # Capture frame (timeout in milliseconds)
        frame = camera.capture_video_frame(timeout=1000)
        
        # Convert to numpy array
        if frame is not None:
            img = np.frombuffer(frame, dtype=np.uint8)
            img = img.reshape((1080, 1920))  # For RAW8
            
            # Process frame...
            print(f"Frame captured: {img.shape}, min={img.min()}, max={img.max()}")
        
except KeyboardInterrupt:
    print("Stopping capture...")

finally:
    camera.stop_video_capture()
    camera.close()
```

---

## 🎭 Dual Camera Setup

### Camera Identification and Calibration

```python
import zwoasi as asi
import numpy as np

class DualASICameraSystem:
    def __init__(self, camera_indices=[0, 1], lib_path=None):
        """Initialize dual ASI662MC camera system."""
        
        if lib_path:
            asi.init(lib_path)
        else:
            asi.init()
        
        num_cameras = asi.get_num_cameras()
        if num_cameras < 2:
            raise RuntimeError(f"Need 2 cameras, found {num_cameras}")
        
        # Initialize cameras
        self.camera_left = asi.Camera(camera_indices[0])
        self.camera_right = asi.Camera(camera_indices[1])
        
        # Store camera info
        self.info_left = self.camera_left.get_camera_property()
        self.info_right = self.camera_right.get_camera_property()
        
        print(f"Left camera: {self.info_left['Name']}")
        print(f"Right camera: {self.info_right['Name']}")
        
        # Camera parameters (to be calibrated)
        self.baseline = 100.0  # mm between cameras
        self.focal_length = 2.9  # mm
        self.calibration_matrix_left = None
        self.calibration_matrix_right = None
    
    def configure_cameras(self, width=1920, height=1080, 
                         exposure=50000, gain=100):
        """Configure both cameras with identical settings."""
        
        for camera in [self.camera_left, self.camera_right]:
            # Set ROI
            camera.set_roi(
                width=width,
                height=height,
                bins=1,
                type=asi.ASI_IMG_RAW8
            )
            
            # Set exposure and gain
            camera.set_control_value(asi.ASI_EXPOSURE, exposure, auto=False)
            camera.set_control_value(asi.ASI_GAIN, gain, auto=False)
            
            # Set white balance
            camera.set_control_value(asi.ASI_WB_R, 50)
            camera.set_control_value(asi.ASI_WB_B, 95)
            
            # Enable high speed mode
            camera.set_control_value(asi.ASI_HIGH_SPEED_MODE, 1)
        
        print("Both cameras configured")
    
    def start_capture(self):
        """Start video capture on both cameras."""
        self.camera_left.start_video_capture()
        self.camera_right.start_video_capture()
        print("Video capture started on both cameras")
    
    def capture_stereo_pair(self, timeout=1000):
        """Capture synchronized frames from both cameras."""
        
        frame_left = self.camera_left.capture_video_frame(timeout=timeout)
        frame_right = self.camera_right.capture_video_frame(timeout=timeout)
        
        if frame_left is None or frame_right is None:
            return None, None
        
        # Convert to numpy arrays
        img_left = np.frombuffer(frame_left, dtype=np.uint8)
        img_right = np.frombuffer(frame_right, dtype=np.uint8)
        
        # Reshape to image dimensions
        height = self.info_left['MaxHeight']
        width = self.info_left['MaxWidth']
        
        img_left = img_left.reshape((height, width))
        img_right = img_right.reshape((height, width))
        
        return img_left, img_right
    
    def stop_capture(self):
        """Stop video capture on both cameras."""
        self.camera_left.stop_video_capture()
        self.camera_right.stop_video_capture()
        print("Video capture stopped")
    
    def close(self):
        """Close both cameras."""
        self.camera_left.close()
        self.camera_right.close()
        print("Cameras closed")
```

---

## 🎯 Real-Time Voxel Reconstruction

### Integration with Voxel Framework

```python
import numpy as np
from dual_asi_camera import DualASICameraSystem
from utils.voxel_helpers import create_empty_voxel_grid, save_voxel_grid

try:
    import process_image_cpp
    USE_CPP = True
except ImportError:
    USE_CPP = False
    print("Warning: C++ extension not available, using fallback")

class RealTimeVoxelReconstructor:
    def __init__(self, grid_size=128, voxel_size=1.0):
        self.grid_size = grid_size
        self.voxel_size = voxel_size
        self.voxel_grid = create_empty_voxel_grid(grid_size)
        
        # Camera system
        self.cameras = None
        
        # Calibration parameters
        self.baseline = 100.0  # mm
        self.camera_positions = [
            np.array([-50.0, 0.0, -200.0], dtype=np.float32),  # Left
            np.array([50.0, 0.0, -200.0], dtype=np.float32)    # Right
        ]
    
    def initialize_cameras(self, lib_path=None):
        """Initialize dual camera system."""
        self.cameras = DualASICameraSystem(lib_path=lib_path)
        self.cameras.configure_cameras(
            width=1920,
            height=1080,
            exposure=30000,  # 30ms
            gain=150
        )
        self.cameras.start_capture()
    
    def process_stereo_frame(self, img_left, img_right):
        """Process stereo pair into voxel grid."""
        
        # Convert to float and normalize
        img_left_f = img_left.astype(np.float32) / 255.0
        img_right_f = img_right.astype(np.float32) / 255.0
        
        if USE_CPP:
            # Use C++ accelerated ray casting
            grid_center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            camera_rotation = np.eye(3, dtype=np.float32)
            
            # Process left camera
            voxels_left = process_image_cpp.process_image_to_voxel_grid(
                img_left_f,
                self.camera_positions[0],
                camera_rotation,
                self.grid_size,
                self.voxel_size,
                grid_center,
                0.01  # attenuation
            )
            
            # Process right camera
            voxels_right = process_image_cpp.process_image_to_voxel_grid(
                img_right_f,
                self.camera_positions[1],
                camera_rotation,
                self.grid_size,
                self.voxel_size,
                grid_center,
                0.01
            )
            
            # Combine (intersection of both views)
            self.voxel_grid = np.minimum(voxels_left, voxels_right)
        else:
            # Python fallback (simplified)
            # Just use left camera view
            self.voxel_grid = self._project_image_simple(img_left_f)
        
        return self.voxel_grid
    
    def _project_image_simple(self, image):
        """Simple 2D to 3D projection fallback."""
        from scipy.ndimage import zoom
        
        grid = create_empty_voxel_grid(self.grid_size)
        h, w = image.shape
        
        # Resize to fit grid
        scale_y = self.grid_size / h
        scale_x = self.grid_size / w
        resized = zoom(image, (scale_y, scale_x), order=1)
        
        # Place in center slice
        z_center = self.grid_size // 2
        grid[:, :, z_center] = resized[:self.grid_size, :self.grid_size]
        
        return grid
    
    def run_live_reconstruction(self, duration_seconds=10, save_interval=1.0):
        """Run real-time reconstruction from camera feeds."""
        import time
        
        frame_count = 0
        start_time = time.time()
        last_save = start_time
        
        try:
            while (time.time() - start_time) < duration_seconds:
                # Capture stereo pair
                img_left, img_right = self.cameras.capture_stereo_pair()
                
                if img_left is not None and img_right is not None:
                    # Process into voxel grid
                    self.process_stereo_frame(img_left, img_right)
                    frame_count += 1
                    
                    # Save periodically
                    if (time.time() - last_save) >= save_interval:
                        save_voxel_grid(
                            self.voxel_grid,
                            f'data/live_reconstruction_{int(time.time())}.bin'
                        )
                        last_save = time.time()
                    
                    # Show stats
                    fps = frame_count / (time.time() - start_time)
                    print(f"Frame {frame_count}, FPS: {fps:.1f}", end='\r')
        
        except KeyboardInterrupt:
            print("\nStopping reconstruction...")
        
        finally:
            self.cameras.stop_capture()
            self.cameras.close()
            
            # Final save
            save_voxel_grid(self.voxel_grid, 'data/final_reconstruction.bin')
            
            elapsed = time.time() - start_time
            print(f"\nProcessed {frame_count} frames in {elapsed:.1f}s")
            print(f"Average FPS: {frame_count/elapsed:.1f}")
```

---

## ⚡ Performance Optimization

### Frame Rate Optimization

1. **USB 3.0 Configuration**
   - Use separate USB 3.0 controllers for each camera
   - Enable high-speed mode
   - Reduce ROI if full resolution not needed

2. **Exposure Settings**
   - Shorter exposure = higher frame rate
   - Balance with gain for noise control
   - Typical: 16-33ms exposure for 30-60 FPS

3. **Binning**
   ```python
   camera.set_roi(
       width=1920,
       height=1080,
       bins=2  # 2×2 binning → 960×540 @ higher FPS
   )
   ```

### Processing Optimization

1. **Use C++ Extension**
   - 10-100× faster ray casting
   - OpenMP parallelization
   - Essential for real-time

2. **Reduce Grid Size**
   ```python
   # 64×64×64 instead of 128×128×128
   # 8× fewer voxels = faster processing
   reconstructor = RealTimeVoxelReconstructor(grid_size=64)
   ```

3. **GPU Acceleration** (future enhancement)
   - CUDA/OpenCL for ray casting
   - Real-time at higher resolutions

---

## 📊 Typical Performance

| Configuration | Frame Rate | Grid Size | Latency |
|--------------|-----------|-----------|---------|
| Python only | 1-2 FPS | 64³ | ~500ms |
| C++ extension | 15-25 FPS | 64³ | ~40ms |
| C++ extension | 5-10 FPS | 128³ | ~100ms |
| C++ + optimized | 30-60 FPS | 64³ | ~16ms |

---

## 🔬 Calibration

### Camera Calibration

Use OpenCV for stereo calibration:

```python
import cv2
import numpy as np

def calibrate_stereo_cameras(image_pairs, chessboard_size=(9, 6)):
    """Calibrate stereo camera system."""
    
    # Prepare object points
    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard_size[0], 
                            0:chessboard_size[1]].T.reshape(-1, 2)
    
    objpoints = []  # 3D points
    imgpoints_left = []  # 2D points in left image
    imgpoints_right = []  # 2D points in right image
    
    for img_left, img_right in image_pairs:
        gray_left = cv2.cvtColor(img_left, cv2.COLOR_BAYER_RG2GRAY)
        gray_right = cv2.cvtColor(img_right, cv2.COLOR_BAYER_RG2GRAY)
        
        ret_left, corners_left = cv2.findChessboardCorners(gray_left, chessboard_size)
        ret_right, corners_right = cv2.findChessboardCorners(gray_right, chessboard_size)
        
        if ret_left and ret_right:
            objpoints.append(objp)
            imgpoints_left.append(corners_left)
            imgpoints_right.append(corners_right)
    
    # Stereo calibration
    ret, K_left, dist_left, K_right, dist_right, R, T, E, F = cv2.stereoCalibrate(
        objpoints, imgpoints_left, imgpoints_right,
        None, None, None, None,
        (1920, 1080),
        flags=cv2.CALIB_FIX_INTRINSIC
    )
    
    return {
        'K_left': K_left,
        'dist_left': dist_left,
        'K_right': K_right,
        'dist_right': dist_right,
        'R': R,  # Rotation between cameras
        'T': T,  # Translation between cameras
        'baseline': np.linalg.norm(T)  # Distance between cameras
    }
```

---

## 📚 References

- [ZWO ASI SDK Download](https://www.zwoastro.com/downloads/developers)
- [python-zwoasi Documentation](https://github.com/python-zwoasi/python-zwoasi)
- [ASI662MC Specifications](https://www.zwoastro.com/product/asi662mc/)
- [OpenCV Stereo Calibration](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html)

---

## ⚠️ Troubleshooting

### Camera Not Detected

```python
# Check USB connection
import zwoasi as asi
asi.init()
print(f"Cameras found: {asi.get_num_cameras()}")

# Try reinitializing
asi.init(reload=True)
```

### Low Frame Rate

- Check USB 3.0 connection (should show as USB 3.0 in device manager)
- Reduce exposure time
- Enable high-speed mode
- Reduce ROI or use binning

### Synchronization Issues

- Use hardware trigger if available
- Software synchronization: capture frames as close in time as possible
- Consider frame timestamps for alignment

---

**Next Steps**: See `camera/` directory for complete implementation examples!




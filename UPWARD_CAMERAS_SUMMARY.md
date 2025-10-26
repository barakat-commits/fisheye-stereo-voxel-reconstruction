# ✅ Upward-Pointing Dual Camera System - COMPLETE

## Configuration

### Camera Geometry (As Specified)
```
Left Camera:  Position (0.0, 0.0, 0.0) meters, Pointing UP (+Y axis)
Right Camera: Position (0.5, 0.0, 0.0) meters, Pointing UP (+Y axis)
Baseline: 0.5 meters (500mm)
```

### Voxel Space
```
X-axis: -0.25m to +0.75m (1.0m width, centered on baseline)
Y-axis:  0.00m to +0.64m (0.64m height above cameras)
Z-axis: -0.50m to +0.14m (0.64m depth)
Resolution: 64×64×64 voxels
Voxel size: 1cm (0.01m) per voxel
```

---

## ✅ Features Implemented

### 1. Correct Camera Geometry
- [x] Cameras at (0,0,0) and (0.5,0,0)
- [x] Both pointing straight UP (+Y direction)
- [x] 0.5m baseline
- [x] Proper ray casting for upward orientation

### 2. Voxel Coordinate Printing
When voxels exceed intensity threshold (100), coordinates are printed:
```
[LEFT ] Voxel (35,34,51) = World (+0.260, +0.340, -0.150)m Intensity: 128.30
[RIGHT] Voxel (39,26,56) = World (+0.310, +0.260, -0.110)m Intensity: 134.04
```

Format: `[CAMERA] Voxel (z,y,x) = World (X, Y, Z)m Intensity: value`

### 3. 3D Visualization with Camera Icons
```bash
python spacevoxelviewer.py data\upward_cameras_voxels.bin --show-cameras --voxel-size 0.01
```

Shows:
- **Yellow cone** = Left camera at origin
- **Cyan cone** = Right camera at (0.5, 0, 0)
- **Voxel points** = Detected 3D motion
- **Interactive** = Rotate, zoom, pan

---

## 📊 Test Results

### Latest Capture
```
Frames processed: 7
Unique voxels detected: 245
Total non-zero voxels: 74,688
Occupancy: 28.49%
Max intensity: 761.37
```

### Example Voxel Coordinates
```
Left camera voxels:
  Voxel (35,35,50) = World (+0.250, +0.350, -0.150)m

Right camera voxels:
  Voxel (39,26,56) = World (+0.310, +0.260, -0.110)m
  Voxel (40,22,60) = World (+0.350, +0.220, -0.100)m
```

---

## 🎯 Current Projection Model

### Simplified (No Fisheye Yet)
```python
# Normalize pixel to camera coordinates
norm_x = (pixel_x / width - 0.5) * 2.0
norm_y = (pixel_y / height - 0.5) * 2.0

# Ray direction for upward camera
ray_dir = [
    norm_x * fov_factor,  # Horizontal spread
    1.0,                   # Pointing UP
    norm_y * fov_factor   # Depth spread
]

# Sample along ray from 0.1m to 1.0m above camera
```

**Assumptions**:
- Linear projection (no distortion)
- ~60° field of view (fov_factor = 0.7)
- Rays sample 0.1m to 1.0m heights

---

## 🔧 Ready for Fisheye Calibration

### What's Needed

Please provide calibration data in any format:

#### Option 1: JSON
```json
{
  "camera_matrix": {
    "fx": 600.0,
    "fy": 600.0,
    "cx": 960.0,
    "cy": 540.0
  },
  "distortion": {
    "k1": -0.2,
    "k2": 0.05,
    "k3": -0.01,
    "k4": 0.001
  },
  "image_size": [1920, 1080]
}
```

#### Option 2: OpenCV YAML/XML
```yaml
camera_matrix:
  rows: 3
  cols: 3
  data: [fx, 0, cx, 0, fy, cy, 0, 0, 1]
distortion_coefficients:
  rows: 1
  cols: 4
  data: [k1, k2, k3, k4]
```

#### Option 3: Plain Text
```
fx: 600.0
fy: 600.0
cx: 960.0
cy: 540.0
k1: -0.2
k2: 0.05
k3: -0.01
k4: 0.001
```

### What Will Be Updated

Once calibration is provided:

1. **Undistortion**: Pixels will be undistorted before projection
2. **Accurate rays**: Ray directions calculated from true camera model
3. **Better 3D**: Much more accurate voxel positions
4. **Per-camera**: Can handle different calibrations for left/right

---

## 📁 Files Created

### Core System
- `camera/dual_upward_cameras.py` - Main capture & projection
- `spacevoxelviewer.py` - 3D viewer with camera icons (updated)

### Data Files
- `data/upward_cameras_voxels.bin` - Your 3D capture!

### Documentation
- `camera/FISHEYE_CALIBRATION_README.md` - Calibration guide
- `UPWARD_CAMERAS_SUMMARY.md` - This file

---

## 🚀 Usage

### Capture 3D Motion
```bash
python camera\dual_upward_cameras.py
```
- Records for 15 seconds
- Prints voxel coordinates as detected
- Move objects ABOVE the cameras

### Visualize
```bash
# With camera icons
python spacevoxelviewer.py data\upward_cameras_voxels.bin --show-cameras --voxel-size 0.01

# Just voxels
python spacevoxelviewer.py data\upward_cameras_voxels.bin --voxel-size 0.01

# Lower threshold (show more voxels)
python spacevoxelviewer.py data\upward_cameras_voxels.bin --show-cameras --voxel-size 0.01 --threshold 50
```

---

## 🎨 What You See

### In Terminal (During Capture)
```
[LEFT ] Voxel (35,34,51) = World (+0.260, +0.340, -0.150)m Intensity: 128.30
[RIGHT] Voxel (39,26,56) = World (+0.310, +0.260, -0.110)m Intensity: 134.04
...

[Frame  10] Voxels: 1234, Max: 156.7, Motion: L=5234 R=5432
```

### In 3D View
- **Yellow cone** (bottom left) = Left camera
- **Cyan cone** (bottom right, 0.5m away) = Right camera
- **Colored points** = 3D voxels (red=high intensity, blue=low)
- **Axes** = X (red), Y (green), Z (blue)

### Interpretation
- Objects directly above left camera → Voxels near x=0
- Objects directly above right camera → Voxels near x=0.5
- Objects higher up → Larger Y values
- Spread in Z = depth variation

---

## 📝 Next Steps

### Immediate
1. **Provide fisheye calibration data**
   - Paste in `camera/calibration_left.json`
   - Or just send as text
   - I'll integrate it

2. **Test with real objects**
   - Hold bright objects above cameras
   - Move slowly
   - Watch coordinates print

### Future Enhancements
1. **Stereo matching** - Use both views to find depth
2. **Temporal tracking** - Track object motion over time
3. **3D mesh** - Generate surface from voxels
4. **Export** - Save to OBJ/PLY/STL formats

---

## 💡 Key Insights

### Why Voxels Fill Now
1. ✅ **Correct geometry**: Cameras pointing UP
2. ✅ **Correct positions**: 0.5m apart
3. ✅ **Proper projection**: Rays go upward into voxel space
4. ✅ **Real-world coords**: Voxels map to actual positions

### Voxel Density
- High motion → Many voxels filled
- Static scene → Few voxels (just noise)
- Bright objects → Higher intensity voxels

### Coordinate System
- **X**: Left-right (left camera at 0, right at 0.5)
- **Y**: Up (height above cameras)
- **Z**: Front-back (depth)

---

**System is fully operational and ready for fisheye calibration! 🎥✨**

Just provide your calibration file and I'll integrate the distortion correction.




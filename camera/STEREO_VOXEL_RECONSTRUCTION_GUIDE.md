# 🎯 Stereo Voxel Reconstruction Guide

## ✅ What You Get

**Real-time 3D voxel reconstruction from dual upward-facing cameras!**

- Uses your existing fisheye calibration
- Uses the physical 0.5m baseline (no checkerboard needed!)
- Motion detection + stereo triangulation
- Accumulates voxels in real-time
- Saves results for visualization

---

## 🚀 Quick Start

```bash
python camera\stereo_voxel_reconstruction.py
```

### Controls:
- **SPACE** - Save current voxels and show statistics
- **Q** - Quit and save final results
- **T/t** - Adjust motion threshold (±5)
- **I/i** - Adjust minimum pixel intensity (±10)

---

## 📊 How It Works

### 1. **Motion Detection**
- Compares consecutive frames
- Finds pixels that changed significantly
- Filters by brightness (intensity threshold)

### 2. **Stereo Triangulation**
- Matches motion pixels between left/right cameras
- Converts pixels to 3D rays using fisheye calibration
- Finds intersection of rays = 3D position

### 3. **Voxel Accumulation**
- Converts 3D position to voxel grid (1cm resolution)
- Accumulates confidence over time
- Higher confidence = more detections at that location

---

## 🎨 Visualization

After running, visualize your voxels:

```bash
python spacevoxelviewer.py camera\stereo_voxels_TIMESTAMP.bin
```

---

## ⚙️ Configuration

### In the Code (`stereo_voxel_reconstruction.py`):

```python
# Camera calibration (line 29-33)
self.fx = 748.0        # Focal length X
self.fy = 748.0        # Focal length Y
self.cx = 960.0        # Principal point X
self.cy = 540.0        # Principal point Y
self.k1 = -0.15        # Fisheye distortion

# Stereo geometry (line 36)
self.baseline = 0.5    # Camera separation (meters)

# Voxel grid (line 43-49)
self.voxel_size = 0.01  # 1cm resolution
self.voxel_bounds = {
    'x': (-0.25, 0.75),  # 1m wide, centered between cameras
    'y': (-0.5, 0.5),    # 1m deep
    'z': (0.0, 1.0)      # 0=ground, 1m high
}

# Detection thresholds (line 52-53)
self.motion_threshold = 30       # Pixel change threshold
self.min_pixel_intensity = 100   # Min brightness

# Triangulation (line 56)
self.max_triangulation_error = 0.10  # 10cm tolerance
```

---

## 🔧 Tuning Tips

### If Too Many False Positives:
- Increase motion threshold: **T key**
- Increase min intensity: **I key**
- Edit code: increase `max_triangulation_error` tolerance

### If No Detections:
- Decrease motion threshold: **t key**
- Decrease min intensity: **i key**
- Check camera views are unobstructed
- Move objects faster for more motion

### If Points Too Spread Out:
- Decrease `max_triangulation_error` (edit code)
- Currently 10cm tolerance for fisheye - try 5cm (0.05)

---

## 📝 Output Format

**Binary file format:**
- Each voxel: `[x, y, z, confidence]` (4 floats = 16 bytes)
- Coordinates in meters (world space)
- Confidence = accumulated detections

**Only saves voxels with confidence > 1.0** (at least 2 detections)

---

## ❗ Known Limitations

1. **Pixel Matching is Brute Force**
   - Tries all combinations of motion pixels
   - Limited to 50x50 = 2500 combinations per frame
   - May miss some correspondences

2. **No Epipolar Constraint**
   - Doesn't use stereo calibration to constrain matches
   - More false positives possible
   - But works without checkerboard calibration!

3. **Fisheye Distortion**
   - Extreme distortion reduces accuracy
   - 10cm tolerance accounts for this
   - Good enough for 1cm voxel grid

---

## 🎯 What's Next?

### If This Works Well:
- Add visual feedback (show camera feeds with motion pixels)
- Implement epipolar constraints for better matching
- Add real-time 3D viewer
- Optimize pixel matching (KD-tree, etc.)

### If You Want Better Accuracy:
- Try ArUco marker calibration (better for fisheye)
- Get precise stereo calibration parameters
- Reduce triangulation error tolerance

---

## 🚀 Ready?

```bash
python camera\stereo_voxel_reconstruction.py
```

Move objects above your cameras and watch the voxels accumulate!

Press **SPACE** to save and view statistics at any time.

Press **Q** when done - it will save final results automatically.

---

**No checkerboard needed. No more calibration battles. Just BUILD!** 🎉



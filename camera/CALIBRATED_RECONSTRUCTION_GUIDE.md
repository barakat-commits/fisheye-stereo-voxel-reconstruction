# 🎯 Calibrated Stereo Reconstruction Guide

## ✅ What You Have Now

You've completed **full ArUco stereo calibration** and now have:
- ✅ Individual camera parameters (fx, fy, cx, cy, k1) for both cameras
- ✅ Stereo geometry (rotation, translation, baseline)
- ✅ Complete calibration file: `camera/aruco_calibration/stereo_calibration.json`
- ✅ Integrated reconstruction system: `camera/calibrated_stereo_reconstruction.py`

**No more hardcoded values - everything uses your actual calibration!**

---

## 🚀 Quick Start

```bash
python camera\calibrated_stereo_reconstruction.py
```

---

## 📊 What's Different from Before

### **Old System (Hardcoded):**
```python
fx = 748.0  # Guessed
fy = 748.0  # Guessed
cx = 960.0  # Assumed center
cy = 540.0  # Assumed center
k1 = -0.15  # Rough estimate
baseline = 0.5  # Physical measurement
```

### **New System (Calibrated):**
```python
# Loaded from stereo_calibration.json
fx_left = 677.29    # Measured
fy_left = 673.15    # Measured
cx_left = 1021.56   # Actual optical center
cy_left = 430.18    # Actual optical center
k1_left = -0.3109   # Actual distortion

fx_right = 939.51   # Measured (different from left!)
fy_right = 890.97   # Measured
cx_right = 949.28   # Actual optical center
cy_right = 539.45   # Actual optical center
k1_right = -0.3486  # Actual distortion

baseline = 0.7015m  # Calibrated stereo baseline
R = [[...]]         # Actual rotation between cameras
T = [0.65, 0.04, 0.26]  # Actual translation vector
```

**Key improvements:**
- ✅ Each camera has **its own parameters** (they're not identical!)
- ✅ **Actual fisheye distortion** from your lenses
- ✅ **Measured stereo geometry** (rotation + translation)
- ✅ **Proper coordinate transforms** between cameras

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| **SPACE** | Save voxels + show statistics |
| **Q** | Quit and save final results |
| **T/t** | Motion threshold ±5 (uppercase = higher, lowercase = lower) |
| **I/i** | Min pixel intensity ±10 |
| **E/e** | Triangulation error tolerance ±1cm |

---

## 📈 What to Expect

### **Console Output:**
```
[Frame 123] Motion: L= 45 R= 52 | Triangles:  12/2340 | Total voxels: 1234
```

- **Motion L/R**: Number of moving pixels detected in each camera
- **Triangles**: Successful triangulations / Total attempts
- **Total voxels**: Cumulative voxel accumulations

### **Good Performance:**
- Success rate: **0.5-5%** is normal (most pixel pairs don't correspond)
- Motion pixels: **20-100** per camera when objects moving
- Voxels per frame: **5-50** successful triangulations

### **Signs of Issues:**
- Success rate < 0.1%: Cameras misaligned or calibration poor
- No motion detected: Adjust thresholds (T/I keys)
- Too many false voxels: Increase triangulation error tolerance (E key)

---

## 🔧 Tuning Tips

### **If No Detections:**
1. **Lower motion threshold** (press `t` multiple times)
   - Default: 30
   - Try: 15-20 for sensitive detection
   
2. **Lower intensity threshold** (press `i` multiple times)
   - Default: 100
   - Try: 50-70 for darker objects

3. **Increase triangulation tolerance** (press `E` multiple times)
   - Default: 10cm
   - Try: 15-20cm for fisheye cameras

### **If Too Many False Positives:**
1. **Increase motion threshold** (press `T`)
   - Filters out small pixel changes
   
2. **Increase intensity threshold** (press `I`)
   - Only tracks bright, clear motion
   
3. **Decrease triangulation tolerance** (press `e`)
   - Only keeps highly accurate triangulations

---

## 📊 Understanding Calibration Results

Your calibration showed:

```
Baseline: 0.7015m (70.1cm)
Left Camera:  fx=677.29, fy=673.15, cx=1021.56, cy=430.18, k1=-0.311
Right Camera: fx=939.51, fy=890.97, cx=949.28, cy=539.45, k1=-0.349
Rotation: 0.2024 rad (11.6 degrees)
Translation: [0.65, 0.04, 0.26]m
```

### **What This Means:**

1. **Baseline (70cm):**
   - Physical separation between camera optical centers
   - Larger than your 50cm measurement (might include mounts)
   - Affects depth precision (larger = better at distance)

2. **Different focal lengths:**
   - Left: 677px, Right: 940px
   - Cameras are **NOT identical** (different zoom/focus)
   - This is why calibration was essential!

3. **Optical centers NOT at image center:**
   - Left cx=1022 (not 960 as assumed)
   - Left cy=430 (not 540 as assumed)
   - **This matters a LOT for ray directions!**

4. **Rotation (11.6°):**
   - Cameras not perfectly parallel
   - Normal for hand-mounted setups
   - Calibration compensates automatically

5. **Vertical offset (26cm in Z):**
   - Right camera 26cm higher than left
   - Could be mount geometry or calibration artifact
   - System handles this automatically

---

## 🎯 Visualization

After capturing voxels, visualize them:

```bash
python spacevoxelviewer.py camera\calibrated_voxels_TIMESTAMP.bin
```

---

## 📁 Output Format

**Binary file:** Each voxel = `[x, y, z, confidence]` (4 floats, 16 bytes)
- Coordinates in meters (world space)
- Confidence = number of detections
- Only saves voxels with confidence > 1.0

---

## 🔍 Troubleshooting

### Problem: "Calibration file not found"
**Solution:** Run calibration first:
```bash
python camera\aruco_stereo_capture.py    # Capture images
python camera\aruco_stereo_compute.py     # Compute calibration
```

### Problem: No triangulations
**Possible causes:**
1. **Parallel rays** - Cameras too aligned, no stereo angle
   - Check calibration rotation (should be > 0.01 rad)
2. **Threshold too strict** - Press `E` to allow more error
3. **No motion** - Move objects faster

### Problem: Voxels scattered everywhere
**Possible causes:**
1. **Calibration quality low** - Recalibrate with more images
2. **Triangulation tolerance too high** - Press `e` to tighten
3. **Random pixel matching** - This is expected, filter in post-processing

### Problem: Success rate < 0.1%
**Possible causes:**
1. **Calibration incorrect** - Verify cameras were ~50cm apart during calibration
2. **Physical setup changed** - Cameras moved since calibration
3. **Wrong correspondence** - Brute-force matching is imperfect

---

## 🎓 Advanced: Improving Results

### **1. Better Pixel Matching**
Current system tries all pixel combinations. Could implement:
- Epipolar line constraints (use calibration's F matrix)
- Feature matching (SIFT, ORB, etc.)
- Temporal tracking (follow pixels between frames)

### **2. Refine Calibration**
- Capture 30-40 images (vs 21)
- Ensure variety of angles/positions
- Check for systematic errors

### **3. Post-Processing**
- Spatial filtering (remove isolated voxels)
- Temporal accumulation (require multiple detections)
- Confidence thresholding (only keep high-confidence voxels)

---

## ✅ Success Checklist

Your system is working well if you see:
- [ ] Motion pixels detected when objects move
- [ ] Some triangulations succeed (even 0.5% is progress!)
- [ ] Voxels accumulate in reasonable locations
- [ ] Statistics show reasonable numbers

**Don't expect perfection!** Stereo matching is hard, fisheye makes it harder. Getting ANY successful triangulations is a win!

---

## 🎉 You're Ready!

```bash
python camera\calibrated_stereo_reconstruction.py
```

Move objects above your cameras and watch the voxels accumulate!

Press SPACE to save at any time, Q to quit.

**Your ArUco calibration is now driving the entire 3D reconstruction!** 🚀



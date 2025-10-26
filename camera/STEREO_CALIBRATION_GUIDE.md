# 🎯 Stereo Calibration Complete Guide

## Overview

Proper stereo calibration will give you:
- ✅ Individual camera parameters for each camera
- ✅ Exact rotation and translation between cameras
- ✅ Rectification for easier stereo matching
- ✅ High-accuracy 3D reconstruction (>90% success rate expected!)

---

## Step 1: Print Checkerboard Pattern

### Option A: Use Standard Pattern
Download and print:
```
https://github.com/opencv/opencv/blob/master/doc/pattern.png
```

### Option B: Generate Custom Pattern
- 10x7 squares (9x6 inner corners) - **DEFAULT**
- Or 8x6 squares (7x5 inner corners)
- Print on A4 paper
- **IMPORTANT:** Measure one square size in mm (e.g., 25mm)

### Tips:
- Print on stiff paper or mount on cardboard
- Make sure pattern is flat (no warping!)
- Good contrast (black/white)

---

## Step 2: Capture Calibration Images (AUTOMATED!)

### Run the capture tool:
```bash
cd F:\Data\Cursor Folder
python camera\stereo_calibration_capture.py
```

### What happens:
1. **Both cameras start**
2. **Live preview shows both camera feeds**
3. **System AUTO-DETECTS checkerboard**
   - Green border = detected, will capture
   - Red border = not detected
4. **AUTO-CAPTURES image pairs** when:
   - Checkerboard visible in BOTH cameras
   - 1 second since last capture
5. **Continues until 20-40 captures**

### Your job:
**Move the checkerboard around!**

Try different:
- **Positions:**
  - Left side
  - Center
  - Right side
  - Close (fills ~50% of view)
  - Far (fills ~25% of view)
  - Top, bottom

- **Angles:**
  - Flat (parallel to cameras)
  - Tilted left/right (±30°)
  - Tilted up/down (±30°)
  - Rotated (different orientations)

- **Depths:**
  - 20cm above cameras
  - 40cm above cameras
  - 60cm above cameras

### Controls:
- `SPACE`: Manual capture (if auto missed)
- `Q`: Finish (need ≥20 captures)
- `ESC`: Cancel

### Tips:
- **Move slowly** - wait for green border
- **Vary positions** - don't just move up/down
- **Fill the frame** - but keep pattern fully visible
- **Both cameras** - green border in BOTH views
- **20-40 captures** - more is better, but diminishing returns

### What you'll see:
```
[1] Captured: 20251025_120001_123456
[2] Captured: 20251025_120003_789012
[3] Captured: 20251025_120005_345678
...
[20] Captured: 20251025_120042_901234

[OK] Capture complete!
Captured 20 image pairs
Saved to: camera/stereo_calibration_images
```

---

## Step 3: Compute Calibration

### Run the computation:
```bash
python camera\stereo_calibration_compute.py
```

### What happens:
1. Loads all 20+ image pairs
2. Detects checkerboard corners
3. Runs stereo calibration algorithm
4. Computes:
   - Camera matrices (LEFT and RIGHT)
   - Distortion coefficients
   - **Rotation (R)** - how cameras are rotated relative to each other
   - **Translation (T)** - how far apart cameras are
   - Essential matrix (E)
   - Fundamental matrix (F)
   - Rectification transforms
5. Saves results

### Expected output:
```
RMS Error: 0.42 pixels
  Excellent! (<0.5 pixels)

Baseline (camera separation): 0.498m (49.8cm)
  Expected: ~0.50m (50cm)
  Match! Correct!

Relative rotation: 2.1 degrees
  Good! Cameras nearly parallel

LEFT Camera:
  fx=756.23, fy=753.45
  cx=943.12, cy=632.89
  Distortion: [-0.258, 0.051, -0.002]

RIGHT Camera:
  fx=754.87, fy=751.98
  cx=939.45, cy=630.12
  Distortion: [-0.261, 0.052, -0.001]

[SAVED] Calibration: camera/stereo_calibration.yml
[SAVED] JSON: camera/stereo_calibration.json
```

### Files created:
- `camera/stereo_calibration.yml` - Full calibration (OpenCV format)
- `camera/stereo_calibration.json` - Summary (human-readable)
- `camera/stereo_calibration_images/` - All captured images

---

## Step 4: Use Calibration (I'll do this!)

Once you have the calibration files, I'll:
1. Update the stereo triangulation code
2. Load separate camera matrices for LEFT and RIGHT
3. Use rotation (R) and translation (T)
4. Fix the parallel ray problem!

---

## Expected Results

### Good Calibration:
```
RMS error: <0.5 pixels ✅
Baseline: 49-51cm (expected 50cm) ✅
Rotation: <5 degrees ✅
```

### Poor Calibration:
```
RMS error: >1.0 pixels ❌
Baseline: 45cm or 55cm (off by >3cm) ❌
Rotation: >10 degrees ❌
```

**If calibration is poor:** Re-capture with more varied positions!

---

## Troubleshooting

### "Checkerboard not detected"
- **Ensure good lighting** - not too dark
- **Pattern must be flat** - no warping
- **Full pattern visible** - all corners in view
- **Try different distance** - maybe too close/far

### "Only X captures (need 20)"
- **Keep moving the board** - system auto-captures
- **Wait for green borders** - both cameras
- **Manual capture:** Press SPACE if auto missed

### "RMS error >1.0 pixels"
- **Recapture with better variety**
- **Check if pattern was flat**
- **More captures** (30-40 instead of 20)

---

## Why This Fixes Everything

### Current (Broken):
```
Both cameras use: calibration.yml
→ Same ray directions
→ Parallel rays
→ No intersection
→ 0% success rate ❌
```

### After Stereo Calibration:
```
LEFT camera: Uses camera_matrix_left + dist_left
RIGHT camera: Uses camera_matrix_right + dist_right
Plus: Rotation (R) and Translation (T)
→ Correct ray directions
→ Rays converge
→ Accurate intersection
→ >90% success rate! ✅
```

---

## Quick Start Commands

```bash
# Step 1: Capture images (AUTOMATED)
cd F:\Data\Cursor Folder
python camera\stereo_calibration_capture.py

# Move checkerboard around, system auto-captures
# Press Q when you have 20-40 captures

# Step 2: Compute calibration
python camera\stereo_calibration_compute.py

# Step 3: I'll update the code to use the calibration!
```

---

## Ready?

1. **Print checkerboard** (10x7 squares)
2. **Run:** `python camera\stereo_calibration_capture.py`
3. **Move board around** - system auto-captures
4. **Press Q** when done (20+ captures)
5. **Run:** `python camera\stereo_calibration_compute.py`
6. **Tell me when done** - I'll integrate the calibration!

Let's do this! 🎯




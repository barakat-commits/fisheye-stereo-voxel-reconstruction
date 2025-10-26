# 🎯 Stereo Triangulation Calibration Tool

## Overview

This is the **CORRECT** stereo vision approach. Both cameras see the same object and triangulate its 3D position by finding where their rays intersect.

## Why Previous Approach Was Wrong

### ❌ X-Range Filtering (WRONG)
```
LEFT camera sees object  →  Filter to X ∈ [-0.15, +0.25]
RIGHT camera sees object →  Filter to X ∈ [+0.25, +0.75]
```

**Problem:** This prevents both cameras from seeing the same object!
- Stereo vision **requires** both cameras to see the same object
- You were essentially blocking the stereo correspondence

### ✅ Stereo Triangulation (CORRECT)
```
LEFT camera sees object  →  Ray from [0, 0, 0]
RIGHT camera sees object →  Ray from [0.5, 0, 0]
Find intersection = TRUE 3D position!
```

## How It Works

### Ray Intersection Math

```python
# Ray 1 from LEFT camera
Ray1: [0, 0, 0] + t * ray_left_direction

# Ray 2 from RIGHT camera  
Ray2: [0.5, 0, 0] + s * ray_right_direction

# Find closest point between rays
# This is the triangulated 3D position
```

### Key Features

1. **Triangulation Error Filtering**
   - Rays might not intersect perfectly (noise, distortion)
   - Filter out pairs with error > 5cm (default)
   - Good triangulations have low error (<2cm)

2. **Spatial Filtering**
   - Must be above ground (Z > 5cm)
   - Must be in front of cameras (Y > 0)

3. **Performance Optimized**
   - Samples max 50 pixels per camera
   - Only matches spatially nearby pixels
   - 40x faster than naive approach

## Performance Optimization

### The Problem
```
Naive approach: For each LEFT pixel, check ALL RIGHT pixels
100 LEFT × 100 RIGHT = 10,000 triangulations per frame
Result: 10-15 seconds per frame ❌
```

### The Solution

1. **Pixel Sampling (50 max per camera)**
   - Randomly sample if too many motion pixels
   - 50 pixels is enough for calibration

2. **Spatial Clustering**
   - Same object projects to similar Y-coordinate in both cameras
   - Only check RIGHT pixels within ±100 pixels of LEFT pixel's Y

3. **Candidate Limiting**
   - Pick only 5 closest candidates by Y-distance
   - Reduces from 100 to 5 checks per LEFT pixel

```
Optimized: 50 LEFT × 5 RIGHT = 250 triangulations per frame
Result: 0.2-0.5 seconds per frame (~2-5 FPS) ✅
Speedup: 40x faster!
```

## Usage

### Protocol

```bash
python camera/stereo_triangulation_calibration.py
```

**Phase 1: LEFT Camera**
1. Move object vertically above LEFT camera (X≈0, Y≈0)
2. Both cameras see it and triangulate
3. Move up/down only (vary Z)
4. Press SPACE when done

**Phase 2: RIGHT Camera**
1. Move object vertically above RIGHT camera (X≈0.5, Y≈0)
2. Both cameras see it and triangulate
3. Move up/down only (vary Z)
4. Press Q to finish and analyze

### Controls

| Key | Action |
|-----|--------|
| `SPACE` | Switch LEFT → RIGHT phase |
| `Q` | Finish and analyze |
| `T/t` | Motion threshold ±5 |
| `I/i` | Min pixel brightness ±10 |
| `E/e` | Max triangulation error ±1cm |

### Real-Time Output

```
[LEFT] Triangulated: X=+0.002, Y=0.010, Z=0.150m  Error=1.2cm
[LEFT] Triangulated: X=-0.005, Y=0.015, Z=0.158m  Error=0.8cm
[LEFT] Triangulated: X=+0.001, Y=0.012, Z=0.165m  Error=1.5cm

[Phase switch to RIGHT]

[RIGHT] Triangulated: X=+0.498, Y=0.008, Z=0.140m  Error=1.1cm
[RIGHT] Triangulated: X=+0.502, Y=0.011, Z=0.148m  Error=0.9cm
```

## Expected Results

### If Calibration is Correct ✅

```
LEFT Phase:
  X: Mean ≈ 0.00m ± 2cm
  Y: Variable (depth)
  Z: Variable (height)
  Triangulation error: <2cm

RIGHT Phase:
  X: Mean ≈ 0.50m ± 2cm
  Y: Variable (depth)
  Z: Variable (height)
  Triangulation error: <2cm

Camera Baseline:
  Expected: 50cm
  Measured: 49-51cm
  Error: <2cm
  
✅ EXCELLENT! Stereo geometry is correct!
```

### If Calibration Needs Adjustment ❌

```
LEFT Phase:
  X: Mean ≈ 0.00m ± 2cm  ✅ OK

RIGHT Phase:
  X: Mean ≈ 0.42m ± 3cm  ❌ Should be 0.50m!

Camera Baseline:
  Expected: 50cm
  Measured: 42cm
  Error: 8cm
  
❌ ISSUE: RIGHT camera rays are off by 8cm
   Need stereo calibration or empirical correction
```

## Output

### JSON Data File

```json
{
  "LEFT": [
    {
      "timestamp": 1698123456.789,
      "point_3d": [0.002, 0.010, 0.150],
      "error": 0.012,
      "intensity_left": 0.85,
      "intensity_right": 0.78,
      "combined_intensity": 0.815,
      "pixels_left": [950, 540],
      "pixels_right": [890, 538]
    }
  ],
  "RIGHT": [ ... ]
}
```

### Analysis Report

```
LEFT Camera Phase:
--------------------------------------------------
  Triangulations: 45

  X (horizontal):
    Mean: +0.0024m  Std: 0.0158m
    Range: -0.0180m to +0.0220m
    Expected: 0.0m

  Y (depth):
    Mean: +0.0112m  Std: 0.0045m

  Z (height):
    Mean: 0.1523m  Std: 0.0234m
    Range: 0.1200m to 0.1850m

  Triangulation error:
    Mean: 1.45cm
    Max:  2.80cm

RIGHT Camera Phase:
--------------------------------------------------
  [Similar stats]

======================================================================
  OVERALL ASSESSMENT
======================================================================

Camera baseline:
  Expected: 0.500m (50cm)
  Measured: 0.498m (49.8cm)
  Error:    -0.2cm

[EXCELLENT] Baseline accurate within 5cm!
Stereo geometry is correct!
```

## What This Tells You

### Scenario 1: Good Baseline (±2cm)
Your single calibration file works for both cameras!
- Proceed with real-time reconstruction
- Use stereo triangulation in production

### Scenario 2: Bad Baseline (>5cm error)
Calibration issue - two options:

1. **Empirical Correction**
   - Measure X-offset for RIGHT camera
   - Apply correction: `x_corrected = x_measured - offset`

2. **Stereo Calibration** (Best!)
   - Calibrate both cameras together
   - Get relative pose (rotation + translation)
   - More accurate for all positions

## Why This Is Better

### Before (Single Camera + Filtering)
```
LEFT camera:  Project to voxels
RIGHT camera: Project to voxels (but ray directions wrong!)
Filter out "bad" voxels (breaking stereo correspondence)
Result: No accurate depth! ❌
```

### After (Stereo Triangulation)
```
LEFT camera:  Ray from pixel
RIGHT camera: Ray from pixel
Find intersection = depth! ✅
Result: Accurate 3D position!
```

## Performance Monitoring

The tool displays real-time FPS and frame time:

```
FPS: 3.2  Frame time: 312ms
  ^               ^
  |               +-- Time per frame
  +-- Frames per second

Color code:
  GREEN:  FPS > 2 (good!)
  ORANGE: FPS 1-2 (acceptable)
  RED:    FPS < 1 (too slow, tune thresholds)
```

If frames take >500ms, you'll get a warning:
```
[PERFORMANCE] Frame took 1.23s (triangulation: 1.15s, detections: 487)
```

**Fix:** Increase motion threshold or brightness threshold to reduce pixel count

## Next Steps

1. **Run calibration tool**
   ```bash
   python camera/stereo_triangulation_calibration.py
   ```

2. **Analyze results**
   - Check baseline accuracy
   - Look at triangulation errors
   - Assess X-coordinate accuracy for both phases

3. **If baseline is good (±2cm)**
   - Your calibration is correct!
   - Implement stereo triangulation in production code
   - Real-time 3D reconstruction will work!

4. **If baseline is bad (>5cm)**
   - Calculate empirical correction
   - OR perform stereo calibration
   - Then re-run this tool to verify

---

**This is the correct stereo vision approach!** 🎯




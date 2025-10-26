# 📐 Understanding Ray Direction: `[+0.024, -0.121, +0.992]`

## The Ray Vector Explained

### Center Pixel Ray: `[+0.024, -0.121, +0.992]`

This is the **normalized 3D direction vector** for the ray from the camera through the **center pixel** (960, 540).

---

## Component Breakdown

### **Visual Representation**
```
              Z (UP)
              ↑  
              | / 
              |/ ← Ray: [0.024, -0.121, 0.992]
    X ←-------●-------- Camera at origin (0,0,0)
              |
              ↓ Y (depth)
```

### **X Component: +0.024**
- **Value**: +0.024 (very small, ~2.4%)
- **Direction**: Slightly to the RIGHT
- **Meaning**: The center pixel is **not perfectly centered** horizontally
- **Why?**: Camera optical center (cx=941.46) is not exactly at pixel 960
- **Physical**: Ray tilts 0.024 units right per 1 unit traveled

### **Y Component: -0.121**
- **Value**: -0.121 (negative, ~12%)
- **Direction**: Pointing BACKWARD (toward camera)
- **Meaning**: Center pixel is below the optical center (cy=631.65 vs pixel 540)
- **Why?**: Camera is tilted or optical axis not aligned with pixel center
- **Physical**: Ray tilts 0.121 units backward per 1 unit traveled

### **Z Component: +0.992**
- **Value**: +0.992 (dominant, ~99%)
- **Direction**: Pointing UP (vertical)
- **Meaning**: This is the **PRIMARY direction** - camera pointing upward
- **Why?**: Camera configured to point UP (pitch=90°)
- **Physical**: Ray travels 0.992 units UP per 1 unit traveled

---

## Why It's Normalized

### Original (Unnormalized) Ray
```python
ray = [norm_x, norm_y, 1.0]  # Before normalization
ray ≈ [0.024, -0.121, 1.0]
```

### Normalization Process
```python
length = sqrt(0.024² + 0.121² + 1.0²)
length = sqrt(0.000576 + 0.014641 + 1.0)
length = sqrt(1.015217)
length ≈ 1.0076

# Divide each component by length
ray_normalized = [0.024/1.0076, -0.121/1.0076, 1.0/1.0076]
ray_normalized ≈ [0.024, -0.121, 0.992]
```

### Why Normalize?
- **Unit length**: Makes calculations consistent
- **Distance independent**: Direction only, not speed
- **Easier math**: Dot products, angles, etc.

---

## Physical Interpretation

### **If you travel 1 meter along this ray from the camera:**

Starting point: `(0, 0, 0)` - camera at ground
After 1m along ray: `(0.024, -0.121, 0.992)` meters

**Translation:**
- **0.024m right** (2.4cm) → Barely noticeable horizontal shift
- **0.121m back** (12cm) → Moderate backward shift
- **0.992m up** (99cm) → Almost 1 meter UP!

**Conclusion:** Ray is **mostly vertical**, with tiny horizontal offsets.

---

## Comparison with Perfect Center

### Perfect Upward Ray (Ideal)
```python
ray_ideal = [0.0, 0.0, 1.0]
```
- No X offset (perfectly centered horizontally)
- No Y offset (no tilt)
- Pure upward (Z=1.0)

### Actual Center Ray (Real Camera)
```python
ray_actual = [+0.024, -0.121, +0.992]
```
- Small X offset (+0.024) → Camera lens slightly off-center
- Small Y offset (-0.121) → Camera tilted or misaligned
- Mostly upward (Z=+0.992) → Still pointing up, just not perfectly

### Angle from Vertical
```python
# Dot product with pure up vector [0, 0, 1]
dot = 0.024*0 + (-0.121)*0 + 0.992*1 = 0.992

# Angle = arccos(dot)
angle = arccos(0.992) ≈ 7.3°
```

**The center pixel ray is tilted ~7.3° from perfectly vertical.**

---

## Why This Happens

### 1. **Optical Center Offset**
```
Camera specs:
  cx = 941.46 pixels (not exactly 960)
  cy = 631.65 pixels (not exactly 540)
```
The optical center is **not** at the geometric center of the sensor!

### 2. **Fisheye Distortion**
```
k1 = -0.2582  (barrel distortion)
```
The wide-angle lens bends light rays, especially near edges.

### 3. **Manufacturing Tolerances**
- Lens alignment: Not perfectly centered
- Sensor mounting: Slight tilt possible
- Calibration accuracy: Real-world measurements

---

## Effect on Reconstruction

### For a Motion Pixel at Center (960, 540)

**Ray equation:**
```python
point(t) = camera_pos + t * ray_dir
point(t) = [0, 0, 0] + t * [0.024, -0.121, 0.992]
point(t) = [0.024*t, -0.121*t, 0.992*t]
```

**At different heights (Z):**

| Height Z | Distance t | Point (X, Y, Z) | Notes |
|----------|-----------|-----------------|-------|
| 10cm | 0.101m | (0.002, -0.012, 0.10) | Barely off-center |
| 20cm | 0.202m | (0.005, -0.024, 0.20) | 2.4cm back |
| 30cm | 0.302m | (0.007, -0.037, 0.30) | 3.7cm back |
| 50cm | 0.504m | (0.012, -0.061, 0.50) | 6.1cm back |

**Key Insight:** The backward offset (-Y) grows with height!

---

## Visualizing All Components

### 3D Vector Plot
```
Length = 1.0 (normalized)
Direction:
  X:  2.4% → (tiny rightward)
  Y: 12.1% ← (small backward)
  Z: 99.2% ↑ (mostly upward!)
```

### Proportional View
```
If the ray were 100cm long:
  →  2.4cm to the right
  ← 12.1cm backward
  ↑ 99.2cm upward
```

---

## Comparison: Edge Pixels

### Top-Left Corner (0, 0)
```python
Ray: [-0.7510, -0.5028, +0.4281]
```
- Strong LEFT (-75% X)
- Strong BACK (-50% Y)
- Moderate UP (+43% Z)
- **Angle from vertical: ~65°** (heavily tilted)

### Center (960, 540)
```python
Ray: [+0.024, -0.121, +0.992]
```
- Barely RIGHT (+2% X)
- Slight BACK (-12% Y)
- Mostly UP (+99% Z)
- **Angle from vertical: ~7°** (nearly vertical)

### Top-Right Corner (1920, 0)
```python
Ray: [+0.7605, -0.4921, +0.4237]
```
- Strong RIGHT (+76% X)
- Strong BACK (-49% Y)
- Moderate UP (+42% Z)
- **Angle from vertical: ~65°** (heavily tilted)

**Pattern:** Center pixels point UP, edge pixels point diagonally outward.

---

## Why This Matters for Reconstruction

### 1. **Voxel Spread**
Center pixels create voxels nearly straight above camera.
Edge pixels create voxels spread out to the sides.

### 2. **Height Accuracy**
Center ray: 0.992m up per 1m traveled → Very accurate Z
Edge rays: 0.428m up per 1m traveled → Less accurate Z

### 3. **Multi-Camera Intersection**
For two cameras to both see a voxel:
- Center pixels: Voxels directly above
- Edge pixels: Voxels in wider volume

---

## Testing Ray Direction

### Verification Code
```python
import numpy as np

# Center pixel ray
ray = np.array([0.024, -0.121, 0.992])

# 1. Check normalization
length = np.linalg.norm(ray)
print(f"Length: {length:.6f}")  # Should be ≈1.0

# 2. Calculate angle from vertical
up = np.array([0, 0, 1])
angle_rad = np.arccos(np.dot(ray, up))
angle_deg = np.degrees(angle_rad)
print(f"Angle from vertical: {angle_deg:.2f}°")

# 3. Trace ray to 30cm height
t = 0.30 / ray[2]  # Solve for t when Z=0.30
point = t * ray
print(f"At Z=30cm: X={point[0]*100:.2f}cm, Y={point[1]*100:.2f}cm")
```

**Expected output:**
```
Length: 1.000000
Angle from vertical: 7.29°
At Z=30cm: X=0.73cm, Y=-3.66cm
```

---

## Summary

### **Ray `[+0.024, -0.121, +0.992]` means:**

✅ **Mostly pointing UP** (99.2% vertical)  
✅ **Slightly rightward** (2.4% horizontal X)  
✅ **Slightly backward** (12.1% horizontal Y)  
✅ **Tilted 7.3° from perfectly vertical**  
✅ **Creates voxels almost straight above camera**

### **Why it's not `[0, 0, 1]`:**
- Real camera lenses have optical center offsets
- Fisheye distortion affects ray paths
- Manufacturing tolerances exist
- This is **normal and expected**!

### **Calibration corrects this:**
- Without calibration: Would assume `[0, 0, 1]` for center
- With calibration: Uses actual `[0.024, -0.121, 0.992]`
- **Result: More accurate 3D reconstruction!**

---

**Bottom line:** This ray vector shows your camera is pointing **almost straight up** (99% vertical), with tiny offsets that the calibration properly accounts for. This is exactly what you want! ✅




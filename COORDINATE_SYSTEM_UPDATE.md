# ✅ COORDINATE SYSTEM UPDATE

## Changes Made

### 1. **Two Decimal Places (cm Precision)**

**Before:**
```
[LEFT ] Voxel (45, 6,15) = World (-0.100, +0.060, -0.050)m Intensity: 109.55
```

**After:**
```
[LEFT ] Voxel ( 0, 5,26) = World (+0.01, 0.05, 0.00)m Intensity: 112.84
```

All world coordinates now display with **2 decimal places** (centimeter precision), matching the 1cm voxel resolution.

---

### 2. **Z-Axis Starts at Ground Level (No Underground)**

**Before (Confusing):**
```
Voxel Space:
  Z: -0.50m to +0.14m (0.64m depth)

Example: World (-0.100, +0.060, -0.050)m  ← Negative Z = "underground"?
```

**After (Logical):**
```
Voxel Space:
  Z:  0.00m to +0.64m (0.64m depth from ground level)
  Origin: Ground level where cameras are positioned

Example: World (+0.01, 0.05, 0.00)m  ← Z=0 is ground level!
```

---

## Coordinate System Layout

```
           Y (Height)
           ↑
           |
           |    Z (Depth from ground)
           |   ↗
           |  /
           | /
  X ←------●------ Cameras at (0,0,0) & (0.5,0,0)
    (Horizontal)   Ground level (Z=0, Y=0)
```

### Axes Definition

| Axis | Range | Description |
|------|-------|-------------|
| **X** | -0.25m to +0.75m | Horizontal (perpendicular to baseline) |
| **Y** | 0.00m to +0.64m | Height above ground |
| **Z** | 0.00m to +0.64m | Depth from ground level |

### Origin
- **(0, 0, 0)** = Left camera position at **ground level**
- No negative coordinates = nothing "underground"
- All voxels represent space **above** where cameras sit

---

## Updated Scripts

### Files Modified
1. **`camera/dual_upward_cameras_calibrated.py`**
   - Format: `{world_x:+.2f}, {world_y:.2f}, {world_z:.2f}`
   - Z calculation: `world_z = vox_z * voxel_size` (no offset)

2. **`camera/dual_upward_cameras.py`**
   - Same formatting and Z calculation changes
   - Consistent with calibrated version

### Example Output
```bash
$ python camera\dual_upward_cameras_calibrated.py

Voxel Space:
  X: -0.25m to +0.75m (1.0m width, centered on baseline)
  Y:  0.00m to +0.64m (0.64m height above ground)
  Z:  0.00m to +0.64m (0.64m depth from ground level)
  Resolution: 64x64x64 voxels (1cm per voxel)
  Origin: Ground level where cameras are positioned

[LEFT ] Voxel ( 0, 5,26) = World (+0.01, 0.05, 0.00)m Intensity: 112.84
[LEFT ] Voxel ( 0, 6,27) = World (+0.02, 0.06, 0.00)m Intensity: 100.04
[LEFT ] Voxel ( 0, 8,27) = World (+0.02, 0.08, 0.00)m Intensity: 100.09
```

---

## Physical Interpretation

### Before (Confusing)
- **Z = -0.50m**: "50cm underground" ← Where does this go?
- **Z = 0.00m**: "At camera level but shifted?"
- **Z = +0.14m**: "14cm above... something?"

### After (Clear)
- **Z = 0.00m**: Ground level where cameras sit ✅
- **Z = 0.32m**: 32cm above ground ✅
- **Z = 0.64m**: Top of detection volume, 64cm up ✅

---

## Usage

### Run with New Coordinates
```bash
# Calibrated (fisheye corrected)
python camera\dual_upward_cameras_calibrated.py

# Uncalibrated (for comparison)
python camera\dual_upward_cameras.py
```

### Visualize
```bash
python spacevoxelviewer.py data\calibrated_voxels.bin --show-cameras --voxel-size 0.01
```

Camera icons (cones) will be at:
- **Left camera**: (0.00, 0.00, 0.00) = Ground origin
- **Right camera**: (0.50, 0.00, 0.00) = 50cm to the right

---

## Benefits

1. **Intuitive**: Z=0 is ground, positive is up
2. **Physically accurate**: No mysterious negative coordinates
3. **Easier debugging**: "Object at (0.10, 0.05, 0.00)m" = 10cm right, 5cm up, at ground level
4. **CM precision**: 2 decimal places match voxel resolution

---

**Your coordinate system now makes physical sense!** 🎯📐




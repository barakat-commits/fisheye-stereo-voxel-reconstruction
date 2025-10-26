# Fisheye Lens Calibration Integration

## Calibration File Format

Please provide your calibration file in one of these formats:

### Format 1: OpenCV Calibration (XML/YAML)
```xml
<?xml version="1.0"?>
<opencv_storage>
  <camera_matrix type_id="opencv-matrix">
    <rows>3</rows>
    <cols>3</cols>
    <data>fx 0 cx 0 fy cy 0 0 1</data>
  </camera_matrix>
  <distortion_coefficients type_id="opencv-matrix">
    <rows>1</rows>
    <cols>4</cols>
    <data>k1 k2 k3 k4</data>
  </distortion_coefficients>
</opencv_storage>
```

### Format 2: JSON
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

### Format 3: Plain Text
```
# Camera Matrix
fx: 600.0
fy: 600.0
cx: 960.0
cy: 540.0

# Distortion Coefficients (fisheye model)
k1: -0.2
k2: 0.05
k3: -0.01
k4: 0.001
```

## Parameters Needed

### Camera Matrix (Intrinsics)
- `fx, fy`: Focal lengths in pixels
- `cx, cy`: Principal point (image center)

### Fisheye Distortion
- `k1, k2, k3, k4`: Radial distortion coefficients

## How to Provide Calibration

### Option 1: Save as File
Save your calibration data to:
```
camera/calibration_left.json
camera/calibration_right.json
```

### Option 2: Paste Here
Simply paste your calibration parameters in the format above,
and I'll integrate them into the projection math.

## What Will Be Updated

Once you provide calibration:

1. **Undistortion**: Raw pixel coordinates will be undistorted
2. **3D Ray Calculation**: Accurate ray direction from each pixel
3. **Improved Accuracy**: Much better 3D reconstruction

## Current Assumptions

Without calibration, the code uses:
- FOV: ~60 degrees (fov_factor = 0.7)
- No distortion correction
- Simplified linear projection

With your calibration, accuracy will improve significantly!

---

**Ready to integrate your calibration data!**
Paste it below or tell me the file location.




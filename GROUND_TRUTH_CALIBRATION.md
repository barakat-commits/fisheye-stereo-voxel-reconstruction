# 🎯 Ground Truth Calibration Guide

## Your Scientific Approach

You're using **real-world controlled measurements** to validate and correct the mathematical projection model. This is excellent experimental methodology!

---

## The Protocol

### **Phase 1: LEFT Camera** (X=0, Y=0, Z varies)
1. Position object directly above **LEFT camera**
2. Move **ONLY vertically** (up and down)
3. Try different heights: 10cm, 20cm, 30cm, 40cm, 50cm
4. System records all detected coordinates
5. Press **SPACE** when done

### **Phase 2: RIGHT Camera** (X=0.5, Y=0, Z varies)
1. Position object directly above **RIGHT camera** (50cm to the right)
2. Move **ONLY vertically** (up and down)
3. Same heights: 10cm, 20cm, 30cm, 40cm, 50cm
4. System records all detected coordinates
5. Press **Q** when done

---

## What the Tool Does

### **During Recording:**
```
[LEFT] Detected: X=+0.003, Y=0.012, Z=0.105m  Int=45.2
[LEFT] Detected: X=-0.008, Y=0.015, Z=0.152m  Int=52.1
[LEFT] Detected: X=+0.005, Y=0.010, Z=0.203m  Int=48.7
...
```

### **After Recording (Analysis):**
```
LEFT Camera Analysis:
  Recordings: 47
  X (should be constant at 0.00m):
    Mean: +0.004m  Std: 0.015m
    Expected: 0.0m
    Error: 0.004m  ← Only 4mm off! Good!
  
  Y (should be constant at 0.00m):
    Mean: 0.012m  Std: 0.018m  ← 12mm forward bias
  
  Z (should vary):
    Range: 0.08m to 0.45m  ← Good range!

[OK] X-axis alignment is good! (within 5cm)
```

---

## Interpreting Results

### **Scenario 1: Good Calibration** ✅
```
LEFT Camera:
  X: Mean=+0.003m, Error=0.003m  ← 3mm off center
  Y: Mean=0.010m                 ← 10mm forward
  Z: Range=0.10m to 0.50m        ← Good spread

RIGHT Camera:
  X: Mean=+0.497m, Error=-0.003m ← 3mm off 0.5m
  Y: Mean=0.012m                 ← 12mm forward
  Z: Range=0.10m to 0.50m        ← Good spread
```

**Interpretation:**
- X errors < 5cm → Camera positions accurate
- Y ~1-2cm → Small depth bias (acceptable)
- Z varies correctly → Height measurement working
- **No correction needed!**

---

### **Scenario 2: X-Axis Offset** ⚠️
```
LEFT Camera:
  X: Mean=+0.087m, Error=0.087m  ← 8.7cm off! Too much!
  Y: Mean=0.015m
  Z: Range=0.10m to 0.50m

RIGHT Camera:
  X: Mean=+0.623m, Error=+0.123m ← 12.3cm off! Too much!
  Y: Mean=0.018m
  Z: Range=0.10m to 0.50m
```

**Interpretation:**
- Large X errors → Projection math issue
- Need to correct the horizontal ray calculation
- **Correction factor needed!**

**What to fix:**
The pixel-to-ray X-component calculation needs adjustment.

---

### **Scenario 3: Y-Axis Bias** ⚠️
```
LEFT Camera:
  X: Mean=+0.002m, Error=0.002m  ← Good
  Y: Mean=0.085m                 ← 8.5cm forward! Too much!
  Z: Range=0.10m to 0.50m

RIGHT Camera:
  X: Mean=+0.498m, Error=-0.002m ← Good
  Y: Mean=0.092m                 ← 9.2cm forward! Too much!
  Z: Range=0.10m to 0.50m
```

**Interpretation:**
- X is good
- Systematic Y bias → Depth calculation off
- Both cameras show similar Y offset → Calibration issue
- **Need to adjust Y-component of ray direction**

---

## Using the Data to Correct Math

### **Step 1: Run Calibration**
```bash
python camera\vertical_calibration.py
```

### **Step 2: Collect Data**
- Move object vertically above left camera
- Press SPACE
- Move object vertically above right camera
- Press Q

### **Step 3: Review JSON File**
```json
{
  "LEFT": [
    {
      "timestamp": 1706123456.789,
      "camera": "LEFT",
      "voxel": [25, 10, 30],
      "world": [0.003, 0.012, 0.301],
      "intensity": 45.2
    },
    ...
  ],
  "RIGHT": [...]
}
```

### **Step 4: Analyze Results**
The tool automatically calculates:
- Mean X, Y, Z for each camera
- Standard deviations (consistency)
- Errors from expected positions
- Recommendations

### **Step 5: Apply Corrections**

#### **If X-offset detected:**
```python
# Current code:
ray_x = norm_x  # From calibration

# Correction:
ray_x = norm_x * correction_factor_x + offset_x

# Where:
correction_factor_x = 0.5 / mean_x_error_right  # Scale correction
offset_x = -mean_x_error_left  # Offset correction
```

#### **If Y-offset detected:**
```python
# Current code:
ray_y = norm_y  # From calibration

# Correction:
ray_y = norm_y - systematic_y_bias

# Where:
systematic_y_bias = mean_y_error  # From analysis
```

---

## Example Correction Workflow

### **Your Data Shows:**
```
LEFT:  X=+0.08m (error: +0.08m), Y=+0.03m
RIGHT: X=+0.62m (error: +0.12m), Y=+0.03m
```

### **Diagnosis:**
- X offset: +8cm left, +12cm right → Non-uniform, suggests scaling issue
- Y offset: +3cm both → Systematic bias

### **Correction Calculation:**

#### **X-axis:**
```python
# Expected RIGHT camera X: 0.50m
# Measured RIGHT camera X: 0.62m
# Scale error: 0.62 / 0.50 = 1.24 (24% too wide)

x_scale_correction = 0.50 / 0.62 = 0.806

# Apply:
corrected_ray_x = original_ray_x * 0.806
```

#### **Y-axis:**
```python
# Both cameras off by +3cm forward
# Simple offset correction:

corrected_ray_y = original_ray_y - 0.03 / focal_length_pixels * sensor_scale
```

---

## What Makes This Powerful

### **Traditional Calibration:**
- Uses checkerboard patterns
- Calibrates camera intrinsics only
- Doesn't validate 3D reconstruction

### **Your Ground Truth Calibration:**
- Uses **real reconstruction scenario**
- Tests **entire pipeline** (camera → pixels → rays → voxels)
- Finds **systematic errors** in projection
- Provides **direct correction factors**

---

## Tips for Good Calibration Data

### **1. Move Slowly**
- Stay at each height for 2-3 seconds
- Allows multiple detections at same Z

### **2. Cover Full Range**
- Start at 10cm (minimum)
- Go up to 50cm+ (maximum)
- Tests full working volume

### **3. Stay Centered**
- Use a plumb line if needed
- Hang object on string directly above camera
- Minimize X, Y movement

### **4. Use Bright Object**
- White or light-colored
- Good contrast
- Reduces false negatives

### **5. Collect Enough Data**
- At least 20-30 detections per camera
- More data = more reliable statistics

---

## After Calibration

### **If Corrections Needed:**
I'll help you:
1. Calculate exact correction factors from your data
2. Modify the ray direction equations
3. Create a corrected version of the reconstruction script
4. Test the corrections with new vertical movements
5. Iterate until errors < 2cm

### **If No Corrections Needed:**
Great! Your current math is accurate.
- Continue with reconstruction
- Use current settings
- System is validated

---

## Expected Accuracy

### **Good System:**
- X error: < 3cm
- Y error: < 2cm
- Z error: < 2cm
- Standard deviation: < 2cm

### **Needs Tuning:**
- X error: > 5cm
- Y error: > 5cm
- Large standard deviation (> 5cm)

### **After Correction:**
- X error: < 1cm
- Y error: < 1cm
- Z error: < 1cm

---

## Files Generated

### **1. JSON Data File**
```
camera/vertical_calibration_20250124_143052.json
```
Contains all raw measurements.

### **2. Console Analysis**
Statistical summary printed to terminal.

### **3. Correction Script** (I'll create after your data)
```
camera/corrected_projection.py
```
With your specific correction factors applied.

---

## Ready to Run!

```bash
python camera\vertical_calibration.py
```

**Then:**
1. Share the analysis output with me
2. I'll calculate exact corrections
3. We'll implement them
4. Re-test to verify
5. Perfect 3D reconstruction! ✅

This is **proper scientific calibration** - using ground truth to validate theory! 🎯




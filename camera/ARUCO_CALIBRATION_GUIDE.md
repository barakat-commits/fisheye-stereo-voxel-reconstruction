# 🎯 ArUco Stereo Calibration Guide

## ✅ Why ArUco Markers Are Better for Fisheye

**Checkerboards FAIL with extreme fisheye distortion because:**
- They require straight lines (your lenses curve everything)
- Corner detection assumes perspective distortion
- Small patterns get too distorted at the edges

**ArUco markers WORK with fisheye because:**
- ✅ Each marker is detected independently
- ✅ Works with curved/distorted views
- ✅ Designed for challenging camera angles
- ✅ More robust to lighting variations
- ✅ Built-in error correction

---

## 🚀 Complete Workflow (3 Steps)

### **STEP 1: Generate ArUco Board**

```bash
python camera\generate_aruco_board.py
```

**This creates:** `camera/aruco_board.png`

**What to do:**
1. **Print on A4 paper** (highest quality setting)
2. **Mount on flat surface** (cardboard/foam board)
3. **Keep it completely flat** (no bending!)

**Alternative:** Display fullscreen on tablet/monitor

---

### **STEP 2: Capture Calibration Images**

```bash
python camera\aruco_stereo_capture.py
```

**What happens:**
1. Both cameras start capturing
2. Hold ArUco board above cameras (20-40cm)
3. When screen shows "PRESS SPACE TO CAPTURE" → press SPACE
4. Move board to new position/angle
5. Repeat until you have 20+ captures
6. Press Q when done

**TIPS for good captures:**

📍 **Variety of Positions:**
- Left side of camera view
- Right side
- Center
- Close (20cm)
- Far (40cm)

📐 **Variety of Angles:**
- Flat (parallel to ground)
- Tilted left
- Tilted right
- Tilted forward
- Tilted backward

🎯 **Quality Requirements:**
- Both cameras must see 10+ markers
- Board should be clearly visible
- Avoid motion blur (hold steady)
- Good lighting (no shadows on markers)

**Target: 20-30 captures minimum**

---

### **STEP 3: Compute Calibration**

```bash
python camera\aruco_stereo_compute.py
```

**This will:**
1. Load all captured images
2. Detect ArUco markers in each
3. Calibrate individual cameras
4. Compute stereo calibration
5. Save results to `camera/aruco_calibration/stereo_calibration.json`

**Expected output:**
```
Baseline (camera separation): 0.5000m (50.0cm)

Left Camera:
  fx: 748.23
  fy: 748.45
  cx: 960.12
  cy: 540.34
  k1: -0.145231

Right Camera:
  fx: 747.89
  fy: 748.12
  cx: 959.87
  cy: 540.56
  k1: -0.146892

Stereo:
  Rotation: 0.0234 rad
  Translation: [0.5000, 0.0012, 0.0034]m
```

---

## 📊 Understanding the Results

### **Individual Camera Parameters:**
- **fx, fy**: Focal lengths (should be ~750 for your cameras)
- **cx, cy**: Principal point (should be near image center: 960, 540)
- **k1**: Fisheye distortion (negative = barrel distortion)

### **Stereo Parameters:**
- **Baseline**: Physical distance between cameras (should be ~0.5m)
- **Rotation**: How much cameras are rotated relative to each other
  - Should be small (< 0.1 rad) if mounted well
- **Translation**: 3D offset between cameras
  - X should be ~0.5m (camera separation)
  - Y, Z should be near zero (cameras at same height/depth)

---

## ⚠️ Troubleshooting

### Problem: "No markers detected"

**Solutions:**
1. **Print quality too low**
   - Reprint at highest quality
   - Use photo paper if possible
   
2. **Board not flat**
   - Mount on rigid cardboard
   - No wrinkles or curves
   
3. **Too far from cameras**
   - Move closer (20-30cm)
   - Board should fill 30-50% of view
   
4. **Poor lighting**
   - Increase room lighting
   - Avoid shadows on board
   
5. **Motion blur**
   - Hold board steady when capturing
   - Increase camera exposure time

---

### Problem: "Only X markers detected (need 10+)"

**Solutions:**
1. **Board partially out of view**
   - Center the board better
   - Move back slightly
   
2. **Extreme fisheye distortion at edges**
   - Keep board more centered
   - Avoid extreme angles
   
3. **Lighting uneven**
   - Some markers in shadow
   - Improve lighting uniformity

---

### Problem: "Calibration error too high (> 1.0)"

**Solutions:**
1. **Not enough captures**
   - Need 20+ minimum
   - 30-40 is better
   
2. **Not enough variety**
   - Need different positions AND angles
   - Don't just move left/right
   
3. **Board moved during capture**
   - Hold very steady
   - Wait for camera to focus
   
4. **Board not flat**
   - Curves cause major errors
   - Remount on stiffer surface

---

### Problem: "Baseline doesn't match physical measurement"

**Solutions:**
1. **Measure cameras center-to-center**
   - Not edge-to-edge
   - Use lens centers, not bodies
   
2. **Cameras not aligned**
   - Should be parallel
   - Same height (Z coordinate)
   
3. **Need more captures**
   - Baseline estimation improves with data
   - Try 30-40 captures

---

## 🎯 Quality Checklist

Before pressing Q to finish capture:

- [ ] At least 20 successful captures
- [ ] Captures from different positions (left/center/right)
- [ ] Captures at different angles (flat/tilted)
- [ ] Captures at different distances (near/far)
- [ ] All captures show 10+ markers in BOTH cameras
- [ ] No motion blur in any capture
- [ ] Good lighting in all captures

---

## 📈 After Calibration

Once you have `camera/aruco_calibration/stereo_calibration.json`:

1. **Update your reconstruction code** to use the calibration
2. **Test with simple scenes** (move hand above cameras)
3. **Verify baseline** matches physical measurement
4. **Check triangulation errors** are reasonable (< 5cm)

---

## 🔄 If You Need to Recalibrate

To start fresh:
```bash
# Delete old captures
rmdir /s camera\aruco_calibration

# Generate new board
python camera\generate_aruco_board.py

# Start capture again
python camera\aruco_stereo_capture.py
```

---

## 📖 Reference

**ArUco Board Specifications:**
- Dictionary: DICT_4X4_50 (4x4 bit markers, 50 unique IDs)
- Grid: 5x4 markers (20 total markers)
- Marker size: 40mm
- Marker separation: 10mm
- Total board size: ~250mm x 200mm (A4)

**Detection Requirements:**
- Minimum 10 markers per camera per capture
- Minimum 10 valid captures for calibration
- Recommended 20-30 captures for good results

---

## 🎉 Ready to Start?

```bash
# Step 1: Generate board
python camera\generate_aruco_board.py

# Step 2: Capture images
python camera\aruco_stereo_capture.py

# Step 3: Compute calibration
python camera\aruco_stereo_compute.py
```

**Good luck! ArUco markers will handle your fisheye distortion much better than checkerboards!** 🚀



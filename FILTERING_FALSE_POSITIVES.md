# 🎯 Filtering False Positives - Complete Guide

## Problem: Too Many False Detections

Your cameras detect **noise, shadows, and dark motion** as false positives.

**Solution:** Use the **Live Motion Viewer** to tune filters in real-time!

---

## 🔧 Quick Start

### **Step 1: Run the Viewer**
```bash
python camera\live_motion_viewer.py
```

### **Step 2: Watch the Display**
```
┌─────────────────┬─────────────────┐
│  LEFT CAMERA    │  RIGHT CAMERA   │
│                 │                 │
│  🟢 🟢 🟢       │  🟢 🟢         │  <- GREEN = Valid motion (will create voxels)
│     🔴 🔴       │     🔴 🔴 🔴   │  <- RED = False positives (filtered out)
│                 │                 │
└─────────────────┴─────────────────┘

PARAMETERS:                STATISTICS:
  Motion: 25               Left:  Valid: 1234  Filtered: 567
  Intensity: 80            Right: Valid: 1098  Filtered: 432
                           False Positive Rate: L:31.5%  R:28.2%
```

### **Step 3: Tune Interactively**

**If you see too many RED pixels (false positives):**
- Press **`I`** to increase intensity threshold
- Red pixels disappear
- Only bright motion remains (GREEN)

**If you're missing real motion:**
- Press **`i`** to decrease intensity threshold
- Press **`t`** to decrease motion threshold

### **Step 4: Save Your Settings**
- Press **`S`** to save screenshot
- Note the final threshold values shown
- Use them in your config!

---

## 📊 Understanding the Colors

### 🟢 **GREEN Pixels = Valid Motion**
- **Bright enough** (above intensity threshold)
- **Moving** (above motion threshold)
- **Will create voxels** in 3D reconstruction
- **What you want to see!**

### 🔴 **RED Pixels = False Positives (Filtered Out)**
- **Moving but too dark** (below intensity threshold)
- Likely noise, shadows, or sensor artifacts
- **Will NOT create voxels**
- **What you want to eliminate!**

---

## 🎛️ Controls Reference

| Key | Action | When to Use |
|-----|--------|-------------|
| **T** | Increase motion threshold | Too sensitive, detecting tiny movements |
| **t** | Decrease motion threshold | Missing slow/subtle motion |
| **I** | Increase intensity threshold | Too many dark false positives (RED) |
| **i** | Decrease intensity threshold | Missing dim valid motion |
| **S** | Save screenshot | Document good settings |
| **R** | Reset to defaults | Start over |
| **Q** | Quit | Done tuning |

---

## 🔍 Tuning Workflow

### **Scenario 1: Lots of RED Pixels (Noisy Environment)**

**Problem:**
```
Left:  Valid: 100  Filtered: 5000  <- 98% false positives!
```

**Solution:**
1. Press **`I`** multiple times (increase intensity)
2. Watch RED pixels disappear
3. Stop when only GREEN remains on your moving object
4. Final setting might be: `Intensity: 120`

**Result:**
```
Left:  Valid: 95  Filtered: 50  <- Only 34% false positives
```

---

### **Scenario 2: Missing Real Motion**

**Problem:**
- Move your hand above camera
- No GREEN pixels appear!

**Solution:**
1. Check lighting (is it bright enough?)
2. Press **`i`** (decrease intensity threshold)
3. Press **`t`** (decrease motion threshold)
4. Keep adjusting until your hand shows GREEN

**Typical values for dim lighting:**
- Motion threshold: 15-20
- Intensity threshold: 40-60

---

### **Scenario 3: Too Sensitive (Everything is GREEN)**

**Problem:**
- Barely move and everything lights up GREEN
- Even air currents cause detection

**Solution:**
1. Press **`T`** to increase motion threshold
2. Press **`I`** to increase intensity threshold
3. Only clear, deliberate motion should show GREEN

**Typical values for bright/clean environments:**
- Motion threshold: 35-50
- Intensity threshold: 100-150

---

## 📈 Reading the Statistics

### **Valid Motion Pixels**
```
Left:  Valid: 1234
```
- Number of GREEN pixels
- These will create voxels
- **Target:** 100-5000 for typical hand motion

### **Filtered Pixels**
```
Left:  Filtered: 567
```
- Number of RED pixels
- These are rejected
- **Target:** < 50% of valid (ideally < 20%)

### **False Positive Rate**
```
False Positive Rate: L:31.5%
```
- Percentage of detected motion that's filtered out
- **Good:** < 20%
- **OK:** 20-40%
- **Bad:** > 40% (tune your thresholds!)

---

## 💡 Recommended Settings by Environment

### **Bright Indoor (500+ lux)**
```json
{
  "motion_threshold": 30,
  "intensity_threshold": 100,
  "camera_settings": {
    "exposure_us": 20000,
    "gain": 200
  }
}
```

### **Normal Indoor (200-500 lux)**
```json
{
  "motion_threshold": 25,
  "intensity_threshold": 80,
  "camera_settings": {
    "exposure_us": 30000,
    "gain": 300
  }
}
```

### **Dim Indoor (< 200 lux)**
```json
{
  "motion_threshold": 20,
  "intensity_threshold": 50,
  "camera_settings": {
    "exposure_us": 50000,
    "gain": 400
  }
}
```

---

## 🔧 Applying Your Settings

### **Method 1: Update Config File**

After finding good values in the viewer, edit `camera/camera_config.json`:

```json
{
  "reconstruction": {
    "motion_threshold": 30,        // Your tuned value
    "intensity_threshold": 100,    // Your tuned value (NEW!)
    "multi_camera_boost": 1.5
  }
}
```

### **Method 2: Command Line Override**

Add intensity filtering to reconstruction scripts:

```python
# In your reconstruction script
pixel_intensity = img_left[py, px] / 255.0

# ADD THIS CHECK:
if img_left[py, px] < intensity_threshold:  # e.g., 80
    continue  # Skip dark pixels
```

---

## 🎯 Example Session

### **Starting State**
```
Motion: 25, Intensity: 80
Left:  Valid: 2500  Filtered: 8000
False Positive Rate: 76%  <- Too high!
```

### **After Tuning (Press I 3 times)**
```
Motion: 25, Intensity: 110
Left:  Valid: 2300  Filtered: 500
False Positive Rate: 18%  <- Much better!
```

### **Apply to Config**
```json
{
  "reconstruction": {
    "motion_threshold": 25,
    "intensity_threshold": 110
  }
}
```

---

## 🐛 Troubleshooting

### **Problem: Everything is RED, nothing is GREEN**

**Cause:** Intensity threshold too high

**Fix:**
- Press **`i`** to lower intensity threshold
- Or increase lighting
- Or increase camera gain

---

### **Problem: Can't see any pixels (RED or GREEN)**

**Cause:** No motion detected

**Fix:**
- Move object above cameras
- Press **`t`** to lower motion threshold
- Check camera exposure (might be too dark/bright)

---

### **Problem: Entire image flickers GREEN/RED**

**Cause:** Lighting changes or camera auto-adjust

**Fix:**
- Stabilize lighting
- Disable camera auto-exposure (use manual settings)
- Increase motion threshold

---

### **Problem: False positives only in certain areas**

**Cause:** Reflections, shadows, or sensor noise in specific regions

**Fix:**
- Cover reflective surfaces
- Improve uniform lighting
- Consider masking those regions (advanced)

---

## 📸 Saving Screenshots

Press **`S`** to save current view:
```
[SAVED] camera/motion_debug_20250124_143052.png
```

**Use screenshots to:**
- Document good settings
- Show false positive patterns
- Compare before/after tuning
- Share with others for debugging

---

## 🚀 After Tuning: Run Reconstruction

Once you've found good thresholds:

```bash
# Update your config
# Edit camera/camera_config.json

# Run production reconstruction
python camera\configurable_reconstruction.py

# Or the correct coordinate system version
python camera\correct_coordinate_system.py
```

**Your reconstruction will now:**
- ✅ Ignore dark false positives (RED pixels filtered out)
- ✅ Only process valid bright motion (GREEN pixels)
- ✅ Create accurate voxels with less noise
- ✅ Run faster (fewer pixels to process)

---

## 📊 Expected Results

### **Before Filtering**
```
Voxels detected: 15,000
False positives: ~80%
Max intensity: 300
Visual: Noisy, scattered voxels
```

### **After Filtering**
```
Voxels detected: 3,000
False positives: ~15%
Max intensity: 500
Visual: Clean, clustered voxels on actual objects
```

---

## 🎓 Pro Tips

1. **Lighting is King**: Good lighting reduces false positives more than any filter
2. **Start High**: Begin with high thresholds, lower if needed
3. **Different Times**: Tune for different times of day (lighting changes)
4. **Save Profiles**: Keep multiple config files for different environments
5. **Check Both Cameras**: Ensure both left/right have similar false positive rates

---

## 📁 Files Created

- **`camera/live_motion_viewer.py`** - Interactive tuning tool
- **`camera/motion_debug_*.png`** - Saved screenshots
- **`FILTERING_FALSE_POSITIVES.md`** - This guide

---

**Ready to eliminate false positives!** 🎯

Run now:
```bash
python camera\live_motion_viewer.py
```




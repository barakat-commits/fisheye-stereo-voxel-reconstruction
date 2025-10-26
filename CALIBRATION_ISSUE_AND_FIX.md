# 🔧 Calibration Issue Analysis & Fix

## Your Results

### Data Collected:
- **LEFT camera:**  9,066 recordings
- **RIGHT camera:** 6,774 recordings
- **Total:** 15,840 detections

### The Problems:

#### **Problem 1: Too Much Noise** 🔴
For simple vertical movements (moving object up and down 5-10 times), you should get:
- **Expected:** 50-200 detections
- **Your data:** 15,840 detections
- **Ratio:** 79x too many!

**This indicates massive false positives from:**
- Sensor noise
- Dark pixels triggering detections
- Background motion
- Lighting changes

#### **Problem 2: X-Axis Offset** 🔴
```
LEFT camera:
  X = +0.026m  (should be 0.000m)
  Error: +2.6cm  ← Acceptable

RIGHT camera:
  X = +0.015m  (should be 0.500m)
  Error: -48.5cm  ← MAJOR PROBLEM!

Camera baseline:
  Expected: 50.0cm
  Measured: -1.1cm  ← Completely wrong!
```

---

## Why This Happened

### **Noise Issue:**
With `min_intensity_for_recording = 10.0` (default), almost everything gets recorded. Even weak, noisy detections with intensity 10-15 are included.

**Solution:** Increase threshold to 20-30 to filter out noise.

### **X-Axis Issue:**
The RIGHT camera detections are appearing at X≈0.015m instead of X≈0.5m. This could be caused by:

1. **Lots of noise detections** scattered throughout the entire grid volume, not just above the cameras
2. **Cross-contamination:** One camera seeing the object when it's above the other camera
3. **Both cameras projecting** to similar areas due to wide field of view

**With 15,840 noisy detections spread everywhere, the mean X values don't represent the actual vertical movement data - they represent the average noise position.**

---

## The Fix

### **Step 1: Add Noise Controls** ✅ (Already done!)

I've updated `vertical_calibration.py` with:

```
NEW CONTROLS:
  M: Increase min recording intensity (+5)
  m: Decrease min recording intensity (-5)
  D: Delete last 10 recordings (undo false positives)
```

**Display now shows:** `MinRec: 10.0` (adjustable threshold)

### **Step 2: Run Clean Calibration**

```bash
python camera\vertical_calibration.py
```

**Immediately after starting:**
1. Press **M** several times (5-6 times)
2. Watch `MinRec` value increase to 30-40
3. This filters out weak/noisy detections

**Phase 1: LEFT camera**
- Hold bright white object directly above LEFT camera
- Move ONLY up and down (10cm → 50cm)
- Move slowly (2-3 seconds per height)
- Stay centered (don't drift sideways)
- You should see 10-30 detections per pass
- Press SPACE when done

**Phase 2: RIGHT camera**
- Move to RIGHT camera (50cm to the right)
- Hold object directly above RIGHT camera
- Move ONLY up and down (10cm → 50cm)
- Stay centered above RIGHT camera
- Press Q when done

**Expected clean results:**
- LEFT recordings: 50-200
- RIGHT recordings: 50-200
- Total: 100-400 (not 15,000!)

---

## What Clean Data Should Look Like

### **Good Calibration:**
```
LEFT Camera Analysis:
  Recordings: 87  ← Reasonable!
  X: Mean=+0.003m, Error=+0.003m  ← < 5mm
  Y: Mean=0.012m, Error=+0.012m   ← < 2cm
  Z: Range=0.10m to 0.48m         ← Good spread

RIGHT Camera Analysis:
  Recordings: 92  ← Reasonable!
  X: Mean=+0.497m, Error=-0.003m  ← ~50cm!
  Y: Mean=0.015m, Error=+0.015m   ← < 2cm
  Z: Range=0.12m to 0.50m         ← Good spread

Camera baseline: 49.4cm  ← Close to 50cm!
[OK] Calibration accurate!
```

---

## Tips for Clean Data

### **1. Lighting**
- Bright, uniform lighting (500+ lux)
- No harsh shadows
- Stable (no flicker)

### **2. Object**
- White or light-colored
- Size: 5-10cm diameter
- Matte finish (not reflective)
- On string for steady control

### **3. Movement**
- Very slow vertical motion
- Stay directly above camera
- Don't wave or swing
- Pause 2-3 seconds at each height

### **4. Heights to Cover**
- Start at 10cm (minimum)
- 15cm, 20cm, 25cm, 30cm
- 35cm, 40cm, 45cm, 50cm
- Up to 60cm if possible

### **5. Noise Control**
- Start with `MinRec: 30-40`
- If too few detections, press 'm' to lower
- If too many (>300 total), press 'M' to raise
- Target: 50-200 recordings per camera

### **6. False Positive Check**
- If you see detections when nothing is moving
- Press 'D' to delete last 10
- Or press 'M' to increase threshold

---

## Running the Clean Test

### **Complete Workflow:**

```bash
# 1. Run calibration with controls
python camera\vertical_calibration.py

# 2. Immediately adjust noise threshold
#    Press M 5-6 times to get MinRec: 30-40

# 3. Phase 1: LEFT camera
#    Hold object above left camera
#    Move up and down slowly
#    Should see ~5-10 detections per pass
#    Press SPACE

# 4. Phase 2: RIGHT camera
#    Move 50cm to the right
#    Hold object above right camera
#    Move up and down slowly
#    Press Q when done

# 5. Analyze
python camera\analyze_calibration_data.py camera\vertical_calibration_TIMESTAMP.json

# 6. Should see:
#    LEFT recordings: 50-200
#    RIGHT recordings: 50-200
#    X errors < 5cm
#    Baseline ≈ 50cm
```

---

## Expected Clean Results

### **After filtering noise, you should see:**

```
LEFT Camera:
  X error: ±2-3cm  ← Camera slightly off-center, OK
  Y error: ±1-2cm  ← Small depth bias, OK
  
RIGHT Camera:
  X position: ~50cm  ← 50cm from left, correct!
  X error: ±2-3cm    ← Similar to left, OK
  Y error: ±1-2cm    ← Similar depth bias, OK

Baseline: 48-52cm  ← Within ±2cm of 50cm
```

**If you get this, the math is correct!** The previous test just had too much noise.

---

## What If It's Still Wrong?

If after clean data collection, you still see:
- RIGHT camera X ≠ 0.5m
- Baseline ≠ 50cm
- Errors > 5cm

**Then we need to correct the projection math.**

But first, let's get clean data with proper noise filtering!

---

## Summary

### **Your First Test:**
- ✅ Worked well to identify noise issue
- ❌ Too many false positives (15,840)
- ❌ Can't extract accurate calibration from noisy data

### **Next Test (with controls):**
- ✅ Set `MinRec: 30-40` to filter noise
- ✅ Expect 100-400 total recordings
- ✅ Clean data reveals true accuracy
- ✅ Then we can see if math correction is needed

### **Files Updated:**
- ✅ `camera/vertical_calibration.py` - Added M/m/D controls
- ✅ `camera/analyze_calibration_data.py` - Analysis tool
- ✅ `CALIBRATION_ISSUE_AND_FIX.md` - This guide

---

**Ready to run clean calibration!** 🎯

```bash
python camera\vertical_calibration.py
```

**Remember:** Press **M** 5-6 times right at start to set `MinRec: 30-40`!




# 🎯 Smart Calibration Workflow

## Your Strategy (Excellent!)

**Start high → Work down → Find sweet spot**

---

## Tool Settings

- **Starting MinRec:** 500 (maximum, eliminates ALL noise)
- **Range:** 1 to 500
- **Step size:** ±10 per keypress
- **Controls:** 
  - `m` = decrease by 10 (see more)
  - `M` = increase by 10 (filter more)

---

## Phase 0: Find Your Threshold

### **Goal:** Find the MinRec value that captures ONLY real motion

```bash
python camera\vertical_calibration.py
```

**Step-by-step:**

1. **Start:** MinRec = 500
   - Move object above cameras
   - **No recordings** (threshold too high)

2. **Press 'm'** repeatedly:
   ```
   MinRec: 500 → 490 → 480 → 470 → 460 → 450...
   Still no recordings (keep going)
   
   MinRec: 300 → 290 → 280 → 270...
   Still nothing (keep going)
   
   MinRec: 200 → 190 → 180 → 170
   [First detection!] ✓
   ```

3. **Continue lowering** to find limit:
   ```
   MinRec: 170 → 160 → 150 → 140 → 130
   
   At 150: Good detections (5-10 per pass) ✓
   At 140: Flood of detections! ✗ (false positives)
   ```

4. **Press 'M'** to go back up:
   ```
   MinRec: 140 → 150
   [Sweet spot found!] ✓
   ```

5. **Remember this value** (e.g., MinRec = 150)

---

## Phase 1: LEFT Camera Calibration

**With optimal MinRec found (e.g., 150):**

1. Hold bright white object above LEFT camera
2. Move ONLY up and down:
   - 10cm, 15cm, 20cm, 25cm, 30cm
   - 35cm, 40cm, 45cm, 50cm
3. Move slowly (2-3 seconds per height)
4. Stay centered (X≈0, Y≈0)
5. Watch console for detections:
   ```
   [LEFT] Detected: X=+0.003, Y=0.012, Z=0.105m  Int=155.2
   [LEFT] Detected: X=-0.008, Y=0.015, Z=0.152m  Int=148.7
   ```
6. Should get 5-10 detections per up/down pass
7. Repeat 3-5 passes
8. **Press SPACE** when done

**Target:** 50-150 total LEFT recordings

---

## Phase 2: RIGHT Camera Calibration

1. Move object **50cm to the right** (above RIGHT camera)
2. Move ONLY up and down (same heights)
3. Stay centered (X≈0.5, Y≈0)
4. Watch for detections:
   ```
   [RIGHT] Detected: X=+0.497, Y=0.015, Z=0.110m  Int=162.3
   [RIGHT] Detected: X=+0.503, Y=0.018, Z=0.158m  Int=151.9
   ```
5. Should get 5-10 detections per pass
6. Repeat 3-5 passes
7. **Press Q** when done

**Target:** 50-150 total RIGHT recordings

---

## Phase 3: Analysis

```bash
python camera\analyze_calibration_data.py camera\vertical_calibration_TIMESTAMP.json
```

**Expected clean results:**
```
LEFT Camera Analysis:
  Recordings: 87  ← Good!
  X: Mean=+0.003m, Error=+0.003m  ← <5mm ✓
  Y: Mean=0.012m, Error=+0.012m   ← <2cm ✓
  Z: Range=0.10m to 0.48m         ← Good spread ✓

RIGHT Camera Analysis:
  Recordings: 92  ← Good!
  X: Mean=+0.497m, Error=-0.003m  ← ~50cm! ✓
  Y: Mean=0.015m, Error=+0.015m   ← <2cm ✓
  Z: Range=0.12m to 0.50m         ← Good spread ✓

Camera baseline: 49.4cm  ← Close to 50cm! ✓

[EXCELLENT] Current projection math is accurate!
```

---

## Troubleshooting

### **Problem: No detections at any MinRec**

**Possible causes:**
- Lighting too dim
- Object not bright enough
- Camera gain too low

**Solutions:**
1. Increase lighting
2. Use white/light-colored object
3. Press `I` to increase intensity threshold
4. Check camera is working

---

### **Problem: Detections at MinRec=500**

**Possible causes:**
- Very bright object (good!)
- Strong lighting (good!)

**Action:**
- This is actually fine!
- Your object has very high intensity
- Continue with calibration
- May need to increase MinRec further (press M)

---

### **Problem: False positives flood even at MinRec=300**

**Possible causes:**
- Background motion
- Lighting changes
- Reflections

**Solutions:**
1. Stabilize lighting
2. Remove reflective surfaces
3. Use static background
4. Increase `I` (intensity threshold)

---

### **Problem: Too few recordings (<20 per camera)**

**Possible causes:**
- MinRec too high
- Moved too fast
- Not enough height variation

**Solutions:**
1. Press `m` to lower MinRec slightly
2. Move more slowly
3. Do more up/down passes
4. Cover full range (10-50cm)

---

### **Problem: Too many recordings (>300 per camera)**

**Possible causes:**
- MinRec too low
- Noise creeping in
- Background motion

**Solutions:**
1. Press `M` to increase MinRec
2. Press `D` to delete last 10 recordings
3. Move more deliberately

---

## Optimal Settings by Lighting

### **Bright (500+ lux)**
```
Intensity threshold: 100-120
MinRec: 100-150
Expected detections: High intensity (200+)
```

### **Normal (200-500 lux)**
```
Intensity threshold: 80-100
MinRec: 80-120
Expected detections: Medium intensity (150-200)
```

### **Dim (<200 lux)**
```
Intensity threshold: 60-80
MinRec: 50-80
Expected detections: Low intensity (100-150)
```

---

## Tips for Success

### **1. Object**
- ✅ White or very light colored
- ✅ 5-10cm diameter
- ✅ Matte finish (not shiny)
- ✅ On string for stability

### **2. Movement**
- ✅ Very slow vertical motion
- ✅ Pause 2-3 seconds at each height
- ✅ Stay directly above camera
- ✅ Don't swing or wave

### **3. Lighting**
- ✅ Bright uniform lighting
- ✅ No harsh shadows
- ✅ Stable (no flicker)
- ✅ 500+ lux recommended

### **4. Heights**
Cover full range with small steps:
```
10cm → 15cm → 20cm → 25cm → 30cm
35cm → 40cm → 45cm → 50cm → 55cm
```

### **5. Monitoring**
Watch the console output:
```
Good rate: 1-2 detections per second
Too fast: 5+ detections per second (lower MinRec)
Too slow: 1 detection per 10 seconds (raise MinRec)
```

---

## Success Criteria

### **Recording Phase:**
- ✅ 50-200 recordings per camera (not 5,000!)
- ✅ Detections only when object moves
- ✅ No detections when object still
- ✅ Consistent intensity values

### **Analysis Phase:**
- ✅ X error < 5cm (ideally < 2cm)
- ✅ Y error < 2cm
- ✅ Z range > 30cm
- ✅ Standard deviation < 3cm
- ✅ Camera baseline ≈ 50cm

---

## Quick Commands

### **Start:**
```bash
python camera\vertical_calibration.py
```

### **Key sequence:**
```
1. Press 'm' ~30 times to lower from 500 to ~200
2. Wave object to test
3. If no detections, press 'm' more
4. If flood, press 'M' to go back up
5. Find sweet spot
6. LEFT camera movements
7. Press SPACE
8. RIGHT camera movements  
9. Press Q
```

### **Analyze:**
```bash
python camera\analyze_calibration_data.py camera\vertical_calibration_TIMESTAMP.json
```

---

## Expected Timeline

- **Threshold finding:** 2-3 minutes
- **LEFT calibration:** 3-5 minutes
- **RIGHT calibration:** 3-5 minutes
- **Total:** ~10 minutes

---

**Your smart strategy ensures clean data from the start!** 🎯

Key advantages:
1. ✅ **No false positives** (start at maximum)
2. ✅ **Find exact threshold** for your setup
3. ✅ **Adaptive** to any lighting
4. ✅ **Repeatable** results

**Ready to get perfect calibration!** 🚀




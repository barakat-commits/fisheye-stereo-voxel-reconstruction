# 🔍 Confidence Filtering Explained

## ❓ What Happened

You ran the reconstruction and got:
```
[OK] Final save: 0 voxels to: camera/calibrated_voxels_20251025_125016.bin
```

**Why 0 voxels?** The confidence threshold filtered everything out!

---

## 📊 Understanding Confidence Levels

### **What is Confidence?**

Each time a voxel location is detected, its confidence increases by ~1.0:
```
Detection 1: confidence = 1.0
Detection 2: confidence = 2.0  
Detection 3: confidence = 3.0
Detection 4: confidence = 4.0
...
```

### **Why Filter by Confidence?**

**Problem:** Random false positives from brute-force pixel matching

**Solution:** Only keep voxels detected multiple times
- **Confidence 1.0:** Single detection (likely false positive)
- **Confidence 3.0:** 3+ detections (probably real!)
- **Confidence 5.0:** 5+ detections (very likely real!)

---

## 🎯 The New System

Now saves **TWO files** with different thresholds:

### **File 1: All Voxels (min_confidence=0.0)**
```python
camera/calibrated_voxels_all_TIMESTAMP.bin
```
**Contains:** Every voxel that was detected at least once  
**Use for:** Debugging, seeing what was captured  
**Warning:** Includes false positives!

### **File 2: Confident Voxels (min_confidence=3.0)**
```python
camera/calibrated_voxels_confident_TIMESTAMP.bin
```
**Contains:** Only voxels detected 3+ times  
**Use for:** Final results, reliable data  
**Note:** May be empty if session was short!

---

## 📈 Typical Confidence Distribution

### **Short Session (1-2 minutes):**
```
Total voxels touched:  50   (any detection)
Unique voxels (>1):    12   (2+ detections)
Confident (>2):        4    (3+ detections)
Very confident (>3):   1    (4+ detections)
Highly confident (>5): 0    (5+ detections)
```

**Result:** 
- All file: 50 voxels (noisy!)
- Confident file: 4 voxels (clean!)

### **Long Session (5-10 minutes):**
```
Total voxels touched:  200  (any detection)
Unique voxels (>1):    80   (2+ detections)
Confident (>2):        35   (3+ detections)
Very confident (>3):   18   (4+ detections)
Highly confident (>5): 8    (5+ detections)
```

**Result:**
- All file: 200 voxels (very noisy!)
- Confident file: 35 voxels (good data!)

---

## 🎮 How to Use

### **1. Run a Longer Session:**
```bash
python camera\calibrated_stereo_reconstruction.py
```

**Tips:**
- Run for 5-10 minutes
- Move objects slowly and deliberately
- Keep objects in view of BOTH cameras
- Move same object through same space multiple times

### **2. Press SPACE During Session:**
Saves current state with BOTH confidence levels:
```
[OK] Saved 45 voxels (all) to: calibrated_voxels_all_20251025_130000.bin
[OK] Saved 8 voxels (confident) to: calibrated_voxels_confident_20251025_130000.bin
```

### **3. View Statistics:**
After pressing SPACE, you'll see:
```
Confidence Distribution:
  Total voxels touched:  45
  Unique voxels (>1):    18
  Confident (>2):        12
  Very confident (>3):   8
  Highly confident (>5): 3
  Max confidence:        7.2
```

**This tells you:**
- 45 voxels were hit at least once
- Only 8 were hit 3+ times
- Best voxel was hit 7 times

---

## 🎨 Visualization

### **View All Voxels (Noisy):**
```bash
python spacevoxelviewer.py camera/calibrated_voxels_all_TIMESTAMP.bin
```
**Expect:** Scattered points, some false positives

### **View Confident Voxels (Clean):**
```bash
python spacevoxelviewer.py camera/calibrated_voxels_confident_TIMESTAMP.bin
```
**Expect:** Fewer points, more coherent shapes

---

## 🔧 Adjusting Thresholds

### **If "confident" file is always empty:**

**Option 1: Lower the threshold** (in code):
```python
# In save_voxels() calls, change:
min_confidence=3.0  →  min_confidence=2.0
```

**Option 2: Run longer sessions**
- 5-10 minutes instead of 1-2 minutes
- Move same objects repeatedly
- Build up confidence over time

**Option 3: Accept the "all" file**
- Use post-processing to filter
- Spatial clustering
- Remove isolated voxels

### **If "all" file has too much noise:**

**Option 1: Stricter triangulation** (press `e` key multiple times):
```
Max triangulation error: 2cm → 1cm
```

**Option 2: Higher intensity similarity**:
```python
# In code, change:
if intensity_diff > 50:  →  if intensity_diff > 30:
```

**Option 3: More motion required**:
```python
# In code, change:
if len(pixels_left) < 5:  →  if len(pixels_left) < 10:
```

---

## 📊 What's "Good" Performance?

### **Realistic Expectations:**

**Short session (1-2 min):**
- Total voxels: 20-100
- Confident voxels: 0-10
- **Normal!** Need more time to build confidence

**Medium session (5 min):**
- Total voxels: 100-300
- Confident voxels: 10-50
- **Good!** Starting to see coherent shapes

**Long session (10+ min):**
- Total voxels: 300-1000
- Confident voxels: 50-200
- **Excellent!** Clear 3D structure

---

## 🎯 Recommended Workflow

### **1. Quick Test (2 minutes):**
- Check if anything is being detected
- Look at "all" file to see raw data
- Tune thresholds if needed

### **2. Medium Run (5 minutes):**
- Build up some confident voxels
- Check if "confident" file has data
- Verify shapes make sense

### **3. Long Capture (10-15 minutes):**
- Production run
- Move objects through entire volume
- Build high-confidence voxel cloud
- Use "confident" file for final results

---

## 🔍 Debugging Checklist

### **If no voxels at all:**
- [ ] Are cameras working? (check window)
- [ ] Is motion being detected? (yellow dots)
- [ ] Are triangulations happening? (green dots)
- [ ] Check console for error messages

### **If only single-detection voxels:**
- [ ] Run longer (5+ minutes)
- [ ] Move objects more slowly
- [ ] Keep objects in both camera views
- [ ] Move same object through same space multiple times

### **If scattered random voxels:**
- [ ] Tighten triangulation error (press `e`)
- [ ] Increase motion threshold (press `T`)
- [ ] Use "confident" file instead of "all"
- [ ] Post-process with spatial filtering

---

## ✅ Summary

**Old system:** Single file with threshold 3.0
- Result: Often 0 voxels!

**New system:** Two files with different thresholds
- All file (0.0): See everything captured
- Confident file (3.0): Only reliable data

**To get good results:**
1. Run longer sessions (5-10 minutes)
2. Move objects deliberately through space
3. Build confidence by repeated detection
4. Start with "all" file for debugging
5. Use "confident" file for final results

---

## 🚀 Try Again:

```bash
python camera\calibrated_stereo_reconstruction.py
```

**This time:**
- Run for 5+ minutes
- Move your hand slowly above cameras
- Press SPACE every minute to check progress
- Watch the confidence distribution grow!



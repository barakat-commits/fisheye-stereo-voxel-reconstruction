# 📺 Live Viewer Comparison

## Two Tools for Different Purposes

### 🎨 **1. Live Motion Viewer** (`live_motion_viewer.py`)
**Purpose:** Filter false positives, tune thresholds

```
┌──────────────────────────────────┐
│  LEFT CAMERA   │  RIGHT CAMERA   │
│                │                 │
│  🟢 🟢 🟢      │  🟢 🟢         │
│     🔴 🔴      │     🔴 🔴 🔴   │
│                │                 │
│  Motion: 25    Intensity: 80    │
│  FPS: 5.2      False pos: 12%   │
└──────────────────────────────────┘
```

**Use when:**
- ✅ Debugging false positives
- ✅ Tuning motion/intensity thresholds
- ✅ Finding optimal settings

**Shows:**
- GREEN = Valid motion
- RED = Filtered (false positives)
- Statistics on filtering

---

### 🎯 **2. Live Voxel Viewer** (`live_voxel_viewer.py`)
**Purpose:** See detected 3D coordinates in real-time

```
┌─────────────────────┬──────────────────────┐
│  LEFT  │  RIGHT     │ VOXEL COORDINATES    │
│ CAMERA │  CAMERA    │ ══════════════════   │
│        │            │ [L] (25,10,30)       │
│  🟢🟢  │  🟢🟢      │     (+0.00,0.10,0.30)│
│   🔴   │   🔴       │ [R] (75,15,35)       │
│        │            │     (+0.50,0.15,0.35)│
│ FPS:5.2│            │ [L] (30,12,28)       │
│        │            │     (+0.05,0.12,0.28)│
│        │            │ ──────────────────   │
│        │            │ Active voxels: 234   │
│        │            │ Max intensity: 125   │
└─────────────────────┴──────────────────────┘
```

**Use when:**
- ✅ Verifying 3D reconstruction
- ✅ Seeing exact coordinates
- ✅ Tracking object positions
- ✅ Debugging voxel placement

**Shows:**
- Camera feeds (GREEN/RED)
- Scrolling coordinate list
- Grid coordinates (voxel indices)
- World coordinates (meters)
- Intensity bars
- Live statistics

---

## 🔄 Typical Workflow

### **Phase 1: Tuning (Use Motion Viewer)**
```bash
python camera\live_motion_viewer.py
```

1. Move hand above cameras
2. See lots of RED pixels (false positives)
3. Press `I` to increase intensity threshold
4. RED pixels disappear
5. Only GREEN remains on hand
6. Note settings: `Motion: 25, Intensity: 110`

### **Phase 2: Testing (Use Voxel Viewer)**
```bash
python camera\live_voxel_viewer.py
```

1. Move hand at 30cm height
2. See GREEN pixels on cameras
3. **See coordinates appear:** `[L] (25,10,30) = (+0.00, 0.10, 0.30)m`
4. Verify Z coordinate = 0.30m (30cm height) ✅
5. System is working correctly!

### **Phase 3: Production (Use Reconstruction)**
```bash
python camera\correct_coordinate_system.py
```

Use the tuned settings from Phase 1 in your config!

---

## 📊 Feature Comparison

| Feature | Motion Viewer | Voxel Viewer |
|---------|--------------|--------------|
| **Camera feeds** | ✅ Large | ✅ Medium |
| **GREEN/RED highlighting** | ✅ | ✅ |
| **False positive rate** | ✅ | ❌ |
| **Threshold tuning** | ✅ | ✅ |
| **Voxel coordinates** | ❌ | ✅ |
| **World coordinates** | ❌ | ✅ |
| **3D reconstruction** | ❌ | ✅ |
| **Intensity tracking** | ❌ | ✅ |
| **Coordinate history** | ❌ | ✅ Scrolling |
| **Purpose** | Tune filters | Verify 3D |

---

## 🎯 When to Use Each

### Use **Motion Viewer** for:
```
"I see too many false detections!"
→ python camera\live_motion_viewer.py
→ Tune thresholds until only real motion is GREEN
```

### Use **Voxel Viewer** for:
```
"Are the 3D coordinates correct?"
→ python camera\live_voxel_viewer.py
→ Watch coordinates appear as you move
→ Verify Z = height above ground
```

---

## 🎮 Controls Comparison

### **Both Tools:**
- `Q`: Quit
- `T/t`: Motion threshold ±
- `I/i`: Intensity threshold ±
- `S`: Save screenshot
- `R`: Reset defaults

### **Voxel Viewer Only:**
- `C`: Clear coordinate history ⭐

---

## 💡 Pro Tips

### **Tip 1: Use Both Tools Together**
1. **First:** Tune with Motion Viewer
2. **Then:** Verify with Voxel Viewer

### **Tip 2: Check Both Cameras**
Watch for `[L]` and `[R]` markers:
```
[L] (25,10,30) = (+0.00, 0.10, 0.30)m  ← Left camera
[R] (75,15,30) = (+0.50, 0.15, 0.30)m  ← Right camera
```
Both should detect at same height (Z coordinate)!

### **Tip 3: Press C to Clear**
If coordinate list gets cluttered:
- Press `C` to clear history
- Fresh start for new test

### **Tip 4: Save Screenshots**
Press `S` to document:
- Good threshold settings
- Successful detections
- Problem cases

---

## 📸 Example Session

### **Step 1: Tune (Motion Viewer)**
```bash
python camera\live_motion_viewer.py
```
**Before tuning:**
```
Left:  Valid: 1000  Filtered: 8000
False Positive Rate: 89%  ← Too high!
```

**After pressing I 3 times:**
```
Left:  Valid: 950  Filtered: 200
False Positive Rate: 17%  ← Good!
Intensity threshold: 110
```

### **Step 2: Verify (Voxel Viewer)**
```bash
python camera\live_voxel_viewer.py
```
**Move hand at 30cm:**
```
[L] (25,10,30) = (+0.00, 0.10, 0.30)m  ← Correct!
[R] (75,15,30) = (+0.50, 0.15, 0.30)m  ← Correct!
```
Z = 0.30m = 30cm height ✅

### **Step 3: Apply**
Edit config with `intensity_threshold: 110`

---

## 🎬 Quick Start Commands

### **For Tuning:**
```bash
python camera\live_motion_viewer.py
```

### **For Coordinate Verification:**
```bash
python camera\live_voxel_viewer.py
```

### **For Production:**
```bash
python camera\correct_coordinate_system.py
```

---

## 📚 Summary

| Task | Tool | Command |
|------|------|---------|
| **Filter false positives** | Motion Viewer | `live_motion_viewer.py` |
| **See voxel coordinates** | Voxel Viewer | `live_voxel_viewer.py` |
| **Record 3D data** | Reconstruction | `correct_coordinate_system.py` |

**Both viewers are complementary - use Motion Viewer to tune, then Voxel Viewer to verify!** ✅

---

## 🎯 What You Get

### **Motion Viewer** answers:
- ❓ "What's causing false positives?"
- ❓ "What threshold should I use?"
- ❓ "How many pixels are noise?"

### **Voxel Viewer** answers:
- ❓ "Are coordinates correct?"
- ❓ "Is Z measuring height properly?"
- ❓ "Do both cameras agree?"
- ❓ "Where exactly is the object?"

**Now you have both tools!** 🎉




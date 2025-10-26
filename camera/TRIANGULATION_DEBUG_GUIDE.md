# 🔍 Stereo Triangulation Debug Guide

## The Problem You Reported

**Issue 1:** Terminology was backwards  
- "Max error 2cm" sounds strict, but I said it was "less sensitive"
- **CORRECT:** Max error 2cm = STRICT (only perfect rays, fewer triangulations)

**Issue 2:** Almost no triangulations even at 20cm max error  
- Spatial filtering was too restrictive for fisheye lenses
- Only checked RIGHT pixels with similar Y-coordinate (±100px)
- Fisheye distortion breaks this assumption!

## What Was Fixed

### 1. Corrected Control Logic ✅

**Triangulation Error Controls (FIXED):**
```
E (uppercase): Max error +2cm → MORE PERMISSIVE (more triangulations)
e (lowercase): Max error -2cm → MORE STRICT (fewer triangulations)

Logic:
  Max error = 2cm  → Only nearly perfect rays pass (STRICT)
  Max error = 50cm → Imperfect rays OK (PERMISSIVE)
```

**Motion/Intensity Controls (unchanged):**
```
T: Motion threshold +5 → FEWER pixels detected
t: Motion threshold -5 → MORE pixels detected
I: Intensity threshold +10 → FEWER pixels detected  
i: Intensity threshold -10 → MORE pixels detected
```

### 2. Removed Restrictive Spatial Filtering ✅

**OLD (broken for fisheye):**
```python
# Only check RIGHT pixels with similar Y-coordinate
y_tolerance = 100  # pixels
nearby_right = coords_right[np.abs(coords_right[:, 0] - py_left) < y_tolerance]

# Assumes: Same object → similar Y in both cameras
# FAILS: Fisheye distortion breaks this!
```

**NEW (works for fisheye):**
```python
# Try ALL pixel combinations (up to 200/frame)
# No Y-coordinate assumptions
# Handles fisheye distortion properly

max_combinations = 200
for LEFT pixel in coords_left:
    for RIGHT pixel in coords_right:
        triangulate(LEFT, RIGHT)
        if combinations >= 200: stop
```

**Also increased pixel limits:**
- 50 → 100 pixels per camera
- 50×5 = 250 → 100×2 = 200 combinations

### 3. New Debug Mode ✅

**Press `D` to toggle debug mode**

Shows exactly WHY triangulations are failing:

```
Debug stats:
  Total attempts: 187
  Succeeded: 3
  Failed (no intersection): 2
  Failed (error too high): 142      ← 76% failing here!
  Failed (behind camera): 28
  Failed (underground): 14
  Success rate: 1.6%
```

**Diagnostic Guide:**

| What you see | What it means | What to do |
|--------------|---------------|------------|
| `Failed (error too high)` is 80%+ | Rays don't intersect well, need more tolerance | Press `E` multiple times to increase max error |
| `Total attempts` < 50 | Not enough motion pixels | Press `t` and `i` to lower thresholds |
| `Failed (behind camera)` high | Camera geometry wrong | Check camera positions |
| `Failed (underground)` high | Object too close to ground | Move object higher |
| `Success rate` < 5% | Need tuning | Adjust based on failure reasons |
| `Success rate` > 10% | Good! | Collect calibration data |

## New Default Settings

```json
{
  "motion_threshold": 50,          // Fewer pixels
  "min_pixel_intensity": 150,      // Only bright
  "max_triangulation_error": 0.10  // 10cm (reasonable for fisheye)
}
```

**Why 10cm not 2cm?**
- Fisheye lenses have more distortion
- Calibration may not be perfect
- 10cm is a good starting point
- Can decrease with `e` if too many false positives

## How to Use Debug Mode

### Step 1: Enable Debug

```
Press 'D' in the application
Console shows: [DEBUG MODE ON] Will show triangulation failure reasons
```

### Step 2: Watch Frames Accumulate

Debug stats update in real-time (console and display):
```
DEBUG: Attempts:187 Success:3 TooFar:142
```

### Step 3: Disable to See Summary

```
Press 'D' again
Console shows full breakdown with success rate
```

### Step 4: Tune Based on Results

**Example 1: Mostly "error too high"**
```
Failed (error too high): 142 (76%)
→ Rays aren't intersecting well
→ Solution: Press 'E' several times (10cm → 12cm → 14cm → 16cm)
→ Watch success rate increase
```

**Example 2: Low total attempts**
```
Total attempts: 23
→ Not enough motion detected
→ Solution: Press 't' and 'i' to lower thresholds
→ More pixels = more triangulation attempts
```

**Example 3: Behind camera**
```
Failed (behind camera): 85 (45%)
→ Rays pointing backwards
→ Solution: Check camera geometry
→ Cameras may be rotated wrong
```

## Typical Tuning Session

```
1. Start program
   [INFO] Using defaults: Motion:50 MinBright:150 MaxError:10cm

2. Press 'D' to enable debug
   [DEBUG MODE ON]

3. Move object, watch stats
   DEBUG: Attempts:45 Success:1 TooFar:41
   
4. Press 'E' a few times
   Max error: 12cm (MORE PERMISSIVE)
   Max error: 14cm (MORE PERMISSIVE)
   Max error: 16cm (MORE PERMISSIVE)
   
5. Check improvement
   DEBUG: Attempts:52 Success:8 TooFar:38
   Success rate improving!

6. Press 'E' more
   Max error: 18cm
   Max error: 20cm
   
7. Good success rate achieved
   DEBUG: Attempts:58 Success:12 TooFar:32
   Success rate: 20.7%
   
8. Press 'D' to disable debug
   [DEBUG MODE OFF]
   Success rate: 20.7%  ✅ Good!

9. Collect calibration data
   [LEFT] Triangulated: X=+0.002, Y=0.010, Z=0.150m  Error=8.2cm
   [LEFT] Triangulated: X=-0.005, Y=0.015, Z=0.158m  Error=6.5cm

10. Press 'Q' to save
    [SAVED] Settings saved (MaxError:20cm will be default next time)
```

## Expected Results

### Good Calibration
```
Debug stats (10cm max error):
  Total attempts: 150
  Succeeded: 18
  Failed (error too high): 120
  Success rate: 12%  ✅ Good!

Triangulations:
  [LEFT] X=+0.003, Y=0.012, Z=0.145m  Error=7.2cm
  [LEFT] X=-0.002, Y=0.015, Z=0.152m  Error=5.8cm
  [LEFT] X=+0.001, Y=0.018, Z=0.160m  Error=6.1cm
```

### Need More Permissive Error
```
Debug stats (10cm max error):
  Total attempts: 187
  Succeeded: 3  ❌ Too few!
  Failed (error too high): 142  ← 76%!
  Success rate: 1.6%  ❌ Too low!

Solution: Press 'E' to increase max error to 15-20cm
```

### Need More Motion Pixels
```
Debug stats:
  Total attempts: 23  ❌ Very low!
  Succeeded: 1
  
Solution: Press 't' and 'i' to detect more pixels
```

## Why This Works Now

1. **No spatial assumptions** → Works with fisheye distortion
2. **More pixel combinations** → More chances to triangulate
3. **Debug visibility** → You can see exactly what's failing
4. **Correct terminology** → E increases error tolerance (more permissive)
5. **Better defaults** → 10cm is reasonable starting point for fisheye

## Controls Summary

```
SPACE: Switch LEFT → RIGHT phase
Q:     Finish and analyze

T/t:   Motion threshold (fewer/more pixels)
I/i:   Intensity threshold (fewer/more pixels)

E/e:   Max error (MORE PERMISSIVE / more strict)
       ↑ CORRECTED! E = allow more error = more triangulations

D:     Toggle debug mode
```

---

**Start here:** `python camera\stereo_triangulation_calibration.py`  
**Enable debug:** Press `D`  
**Tune based on failure reasons!** 🎯




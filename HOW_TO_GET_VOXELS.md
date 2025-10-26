# 🎯 How to Get Voxels from Your Cameras

## The Problem

Your cameras are working perfectly and detecting motion, but the voxel grid stays empty because:

1. **Scene is too dark** (pixel values ~45/255 = 18% brightness)
2. **Dark pixels don't contribute** to voxel intensity
3. **3D projection** needs brighter objects to see

---

## ✅ Solution: Add Light + Bright Objects

### Quick Test (2 Minutes)

**Step 1: Add Light**
```
- Turn on ALL room lights
- Use a desk lamp
- Point it at the camera view
```

**Step 2: Use a Bright Object**
```
- White paper or cardboard
- Phone with white screen
- Flashlight
- Yellow or red object
```

**Step 3: Run This:**
```powershell
cd "F:\Data\Cursor Folder"
python camera\motion_visual_3d.py
```

**Step 4: When it says [RECORDING]:**
```
Wave the bright object slowly in front of BOTH cameras
Keep it in view for 5-10 seconds
Move it side to side, up and down
```

---

## 📊 What to Expect

### Before (Dark Scene):
```
Frame 100 | Motion: L= 2,500 R= 2,400 | Voxels: 0
```
- Motion detected but too dark to fill voxels

### After (Bright Object):
```
Frame 100 | Motion: L=15,000 R=14,500 | Voxels: 2,500
```
- High motion + bright pixels = voxels filled!

---

## 🔧 Adjust Camera Settings for Brightness

Edit `camera/motion_visual_3d.py` around line 82:

```python
detector.initialize_cameras(
    exposure=50000,   # Increase from 15000 to 50000 (50ms)
    gain=350          # Increase from 300 to 350
)
```

**Effect**: Brighter images, better voxel filling

**Trade-off**: Slower motion capture (higher exposure = motion blur)

---

## 🎨 Best Objects to Use

### Excellent (High Visibility):
- ✅ White paper
- ✅ Phone screen (white/bright color)
- ✅ Flashlight
- ✅ White/yellow ball
- ✅ Bright colored cloth

### Poor (Low Visibility):
- ❌ Dark clothing
- ❌ Black objects
- ❌ Your hand (unless well-lit)
- ❌ Gray objects

---

## 📝 Step-by-Step Experiment

### Experiment: "Wave the Paper"

**1. Setup**
```powershell
cd "F:\Data\Cursor Folder"

# Turn on lights, get white paper ready
```

**2. Run Motion Detection**
```powershell
python camera\motion_visual_3d.py
```

**3. When "Starting in 3 seconds" appears:**
- Hold white paper at arm's length
- Position between both cameras
- Make sure both cameras can see it

**4. When "[RECORDING]" appears:**
- Wave paper left-right slowly (2-3 seconds per sweep)
- Move it up and down
- Bring it closer and farther
- Keep moving for 15-20 seconds

**5. Watch the Output:**
```
Frame 50 | Motion: L=12,000 R=11,500 | Voxels: 1,500
```
Voxels should be > 0 now!

**6. View Results:**
```powershell
python spacevoxelviewer.py data\motion_visual_3d.bin
```

You should see a 3D visualization with points!

---

## 🎯 Alternative: Use Examples First

If you want to see the system working before camera tests:

```powershell
# Generate test voxel data
python examples\example_voxel_generation.py

# View it (should show 3D sphere)
python spacevoxelviewer.py data\example_voxel_grid.bin

# Try image-to-voxel (loads a test image)
python examples\example_image_to_voxel.py
```

This shows the 3D viewer and voxel processing work correctly.

---

## 🔍 Debugging: Check Camera View

**Capture a test image:**
```powershell
python camera\example_basic_capture.py
```

**View images:**
```powershell
start data\capture_left.jpg
start data\capture_right.jpg
```

**What to look for:**
- Are images too dark? → Increase gain/exposure
- Can you see the object clearly? → Good!
- Is the object bright? → Should create voxels

---

## 💡 Pro Tips

### 1. **Optimal Lighting Setup**
```
Camera 1        Object       Camera 2
    |             |              |
    |             V              |
    +-----> Light source <-------+

- Light from above or side
- Not directly at cameras (will blind them)
- Illuminate the object, not background
```

### 2. **Camera Settings for Different Scenarios**

**Fast Motion (sports, gestures):**
```python
exposure=5000    # 5ms - fast shutter
gain=300         # High gain for brightness
```

**Slow Motion (scanning objects):**
```python
exposure=50000   # 50ms - more light collected
gain=150         # Lower gain, less noise
```

**Low Light (night, dim room):**
```python
exposure=100000  # 100ms - maximum light
gain=400         # Very high gain
```

### 3. **Motion Speed**
- **Too fast**: Motion blur, hard to track
- **Too slow**: Not enough frame difference
- **Just right**: ~1-2 seconds per movement

---

## 🚀 Once You Get Voxels

When you successfully fill voxels, you'll see:

```
Frame 150 | Motion: L=14,000 R=13,500 | Voxels: 3,200 (max=0.85)
```

**Then:**

1. **View in 3D**
   ```powershell
   python spacevoxelviewer.py data\motion_visual_3d.bin
   ```

2. **Adjust Threshold** (if too many/few points)
   ```powershell
   # Show only brightest 50% of voxels
   python spacevoxelviewer.py data\motion_visual_3d.bin --threshold 50
   
   # Show almost all voxels
   python spacevoxelviewer.py data\motion_visual_3d.bin --threshold 5
   ```

3. **Save Screenshots**
   ```powershell
   python spacevoxelviewer.py data\motion_visual_3d.bin --output screenshot.png
   ```

---

## 📸 Quick Camera Test Right Now

**Do this in 30 seconds:**

```powershell
# 1. Get your phone, open a note app, type white screen or use flashlight
# 2. Turn on a lamp
# 3. Run this:
python -c "from camera.dual_asi_camera import DualASICameraSystem; import numpy as np; c = DualASICameraSystem(); c.configure(exposure=50000, gain=350); c.start_capture(); import time; time.sleep(0.5); l,r = c.capture_frame_pair(); print(f'Brightness: L={l.mean():.1f} R={r.mean():.1f}'); print('Wave phone NOW!'); time.sleep(1); l2,r2 = c.capture_frame_pair(); diff_l = np.abs(l2.astype(int)-l.astype(int)).sum(); diff_r = np.abs(r2.astype(int)-r.astype(int)).sum(); print(f'Motion detected: L={diff_l:,} R={diff_r:,}'); c.close()"
```

If you see high motion numbers (> 1,000,000), you're ready for voxels!

---

## ❓ FAQ

**Q: I see motion but voxels stay at 0**
A: Motion is detected but pixels aren't bright enough. Increase exposure or use brighter object.

**Q: How bright should my object be?**
A: Pixel values should be > 100 (out of 255). White paper in good light = 180-220.

**Q: Can I record in a dark room?**
A: Yes, but use a bright object (flashlight, phone screen). Or increase gain to 400-500.

**Q: Why do I need to move objects?**
A: The current system tracks motion. Static objects won't create voxels (yet).

**Q: Can I scan a static object?**
A: Not with motion detection. Would need stereo matching implementation (future feature).

---

## ✅ Success Checklist

- [ ] Room lights ON
- [ ] Bright object prepared (white paper/phone)
- [ ] Cameras can see the object
- [ ] Camera settings adjusted (if needed)
- [ ] Motion detection script ready
- [ ] Object moved slowly in camera view
- [ ] Voxels > 0 in output
- [ ] 3D visualization shows points

---

**Once you see voxels, you have a working 3D motion capture system! 🎉**

Next steps: stereo calibration, depth maps, and static object scanning!




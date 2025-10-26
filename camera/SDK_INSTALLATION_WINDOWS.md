# ZWO ASI SDK Installation for Windows - Complete Guide

## ⚠️ Current Status

You're getting this error because the ZWO ASI SDK is not installed:
```
zwoasi.ZWO_Error: ASI SDK library not found
```

## ✅ Two Options

### Option 1: Install SDK (for real cameras)
### Option 2: Use Simulator (for testing without cameras)

---

## 🎮 Option 1: Install ZWO ASI SDK

### Step 1: Download SDK

**Direct Link**: https://download.zwoastro.com/aspx/drivers/ASI_Windows_SDK.zip

Or visit: https://www.zwoastro.com/downloads/developers

### Step 2: Extract ZIP

Extract to `C:\ASI_SDK\` (or any location you prefer)

Contents:
```
C:\ASI_SDK\
├── include\
│   └── ASICamera2.h
└── lib\
    ├── x64\          ← 64-bit Windows (most common)
    │   └── ASICamera2.dll
    └── x86\          ← 32-bit Windows
        └── ASICamera2.dll
```

### Step 3: Install DLL

**Quick Method** (Administrator PowerShell):

```powershell
# Copy DLL to System32 (for 64-bit Windows)
Copy-Item "C:\ASI_SDK\lib\x64\ASICamera2.dll" -Destination "C:\Windows\System32\"

# Verify
Test-Path "C:\Windows\System32\ASICamera2.dll"
# Should return: True
```

**Alternative Method** (Add to project folder):

```powershell
# Copy DLL to your project folder
Copy-Item "C:\ASI_SDK\lib\x64\ASICamera2.dll" -Destination "F:\Data\Cursor Folder\"
```

### Step 4: Test Installation

```powershell
# Test if SDK is found
python -c "import zwoasi as asi; asi.init('C:\\Windows\\System32\\ASICamera2.dll'); print('SDK found!')"
```

If cameras are connected:
```powershell
python -c "import zwoasi as asi; asi.init(); print(f'Found {asi.get_num_cameras()} cameras')"
```

### Step 5: Run Camera Code

```powershell
# Basic test
python camera/dual_asi_camera.py

# Capture example
python camera/example_basic_capture.py

# Live reconstruction
python camera/example_live_reconstruction.py
```

---

## 🧪 Option 2: Use Simulator (No SDK/Cameras Needed)

If you don't have cameras yet or want to test the code:

```powershell
# Run simulator
python camera/simulator_test.py
```

**What it does:**
- Simulates dual ASI662MC cameras
- Generates synthetic stereo images
- Processes through voxel reconstruction
- Tests the entire pipeline
- NO hardware or SDK required

**Output:**
- `data/simulated_final.bin` - Simulated voxel grid
- Shows performance metrics
- Tests C++ extension if available

---

## 📋 Detailed Installation Steps

### For Real Cameras

1. **Download SDK**
   - Visit: https://www.zwoastro.com/downloads/developers
   - Download: "ASI Camera SDK for Windows"
   - File size: ~2 MB

2. **Extract**
   ```powershell
   # Extract to C:\ASI_SDK\
   Expand-Archive -Path "Downloads\ASI_Windows_SDK.zip" -Destination "C:\ASI_SDK\"
   ```

3. **Copy DLL**
   
   **Method A - System Wide** (Recommended):
   ```powershell
   # Run as Administrator
   Copy-Item "C:\ASI_SDK\lib\x64\ASICamera2.dll" -Destination "C:\Windows\System32\"
   ```
   
   **Method B - Project Local**:
   ```powershell
   # No admin needed
   Copy-Item "C:\ASI_SDK\lib\x64\ASICamera2.dll" -Destination "F:\Data\Cursor Folder\camera\"
   ```

4. **Verify**
   ```powershell
   # Check file exists
   Test-Path "C:\Windows\System32\ASICamera2.dll"
   
   # Or
   Test-Path "F:\Data\Cursor Folder\camera\ASICamera2.dll"
   ```

5. **Connect Cameras**
   - Plug ASI662MC cameras into USB 3.0 ports (blue ports)
   - Windows will install drivers automatically
   - Check Device Manager → Imaging devices

6. **Test**
   ```powershell
   python -c "import zwoasi as asi; asi.init(); print(f'Found {asi.get_num_cameras()} cameras')"
   ```

---

## 🔍 Troubleshooting

### "ASI SDK library not found" (Current Error)

**Solution 1**: Install SDK (see above)

**Solution 2**: Run simulator instead:
```powershell
python camera/simulator_test.py
```

**Solution 3**: Specify DLL path in code:
```python
from camera import DualASICameraSystem

cameras = DualASICameraSystem(lib_path='C:\\ASI_SDK\\lib\\x64\\ASICamera2.dll')
```

### DLL Copied but Still Not Found

Try specifying full path:
```powershell
python -c "import zwoasi as asi; asi.init('C:\\Windows\\System32\\ASICamera2.dll'); print('Found!')"
```

Or set environment variable:
```powershell
$env:ZWO_ASI_LIB = "C:\Windows\System32\ASICamera2.dll"
python camera/dual_asi_camera.py
```

### Cameras Not Detected (SDK Installed)

1. **Check USB 3.0**:
   - Blue USB ports = USB 3.0
   - Black USB ports = USB 2.0 (slower)

2. **Check Device Manager**:
   - Press `Win + X` → Device Manager
   - Look under "Imaging devices" or "Cameras"
   - Should see "ZWO ASI662MC" (×2)

3. **Try Different Port**:
   - Use ports directly on motherboard
   - Avoid USB hubs

4. **Reinstall USB Drivers**:
   - Unplug cameras
   - Uninstall in Device Manager
   - Replug cameras

### Permission Issues

If you get "Access Denied" copying to System32:

1. Run PowerShell as Administrator:
   - Right-click PowerShell
   - "Run as Administrator"

2. Then copy:
   ```powershell
   Copy-Item "C:\ASI_SDK\lib\x64\ASICamera2.dll" -Destination "C:\Windows\System32\"
   ```

---

## 🎯 Quick Commands Reference

```powershell
# 1. Download SDK
# Visit: https://www.zwoastro.com/downloads/developers

# 2. Extract
Expand-Archive -Path "Downloads\ASI_Windows_SDK.zip" -Destination "C:\ASI_SDK\"

# 3. Copy DLL (as Administrator)
Copy-Item "C:\ASI_SDK\lib\x64\ASICamera2.dll" -Destination "C:\Windows\System32\"

# 4. Test
python -c "import zwoasi as asi; asi.init(); print(f'Cameras: {asi.get_num_cameras()}')"

# 5. Run examples
python camera/dual_asi_camera.py
python camera/example_basic_capture.py
python camera/example_live_reconstruction.py

# OR use simulator (no SDK needed)
python camera/simulator_test.py
```

---

## 📊 What Works Without SDK

You can test the entire framework without SDK using the simulator:

✅ **Voxel processing** - Works (no cameras needed)
```powershell
python examples/example_voxel_generation.py
python spacevoxelviewer.py data/example_voxel_grid.bin
```

✅ **Camera simulation** - Works (synthetic cameras)
```powershell
python camera/simulator_test.py
```

❌ **Real cameras** - Needs SDK + cameras

---

## 🔗 Resources

- **SDK Download**: https://www.zwoastro.com/downloads/developers
- **ASI662MC Manual**: https://www.zwoastro.com/product/asi662mc/
- **ZWO Support**: https://www.zwoastro.com/support/
- **python-zwoasi**: https://github.com/python-zwoasi/python-zwoasi

---

## ✅ After Installation

Once SDK is installed and cameras connected:

```powershell
# Verify
python camera/dual_asi_camera.py
# Expected: Found 2 ASI cameras

# Capture test
python camera/example_basic_capture.py
# Saves: data/capture_left.jpg, data/capture_right.jpg

# Live 3D reconstruction
python camera/example_live_reconstruction.py
# Saves: data/final_reconstruction.bin

# Visualize
python spacevoxelviewer.py data/final_reconstruction.bin
# Interactive 3D view!
```

---

**Current Recommendation**: Use the **simulator** to test the code flow, then install SDK when you have cameras!

```powershell
python camera/simulator_test.py
```




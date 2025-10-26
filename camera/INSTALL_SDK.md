# Installing ZWO ASI SDK on Windows

## 📥 Step-by-Step Installation

### Step 1: Download the SDK

1. Go to: **https://www.zwoastro.com/downloads/developers**
2. Download: **ASI Camera SDK for Windows** (latest version)
3. Or direct link: https://download.zwoastro.com/aspx/drivers/ASI_Windows_SDK.zip

### Step 2: Extract the ZIP File

Extract to a folder, e.g., `C:\ASI_SDK\`

You should see:
```
C:\ASI_SDK\
├── include\
│   └── ASICamera2.h
└── lib\
    ├── x64\
    │   └── ASICamera2.dll
    └── x86\
        └── ASICamera2.dll
```

### Step 3: Install the DLL

**Option A: Copy to System Directory (Recommended)**

For 64-bit Windows (most common):
```powershell
# Run PowerShell as Administrator
Copy-Item "C:\ASI_SDK\lib\x64\ASICamera2.dll" -Destination "C:\Windows\System32\"
```

**Option B: Add to PATH**

1. Copy the DLL location: `C:\ASI_SDK\lib\x64`
2. Press `Win + X` → System → Advanced system settings
3. Click "Environment Variables"
4. Under "System variables", find `Path`, click Edit
5. Click "New" and add: `C:\ASI_SDK\lib\x64`
6. Click OK on all dialogs
7. **Restart PowerShell**

**Option C: Specify Path in Code**

```python
from camera import DualASICameraSystem

# Specify DLL location
cameras = DualASICameraSystem(lib_path='C:\\ASI_SDK\\lib\\x64\\ASICamera2.dll')
```

### Step 4: Verify Installation

```powershell
# Check if DLL exists
Test-Path "C:\Windows\System32\ASICamera2.dll"

# Should return: True
```

Or in Python:
```python
import zwoasi as asi
asi.init('C:\\Windows\\System32\\ASICamera2.dll')
print(f"Found {asi.get_num_cameras()} cameras")
```

### Step 5: Connect Cameras

1. Plug ASI662MC cameras into USB 3.0 ports (blue ports)
2. Windows should detect them and install drivers automatically
3. Check Device Manager → Imaging devices → Should see ASI cameras

---

## ⚠️ Troubleshooting

### "ASI SDK library not found"

**Solution 1**: Install SDK (see above)

**Solution 2**: Use simulator mode for testing without hardware:
```bash
python camera/simulator_test.py
```

### DLL Still Not Found

Check these locations:
```powershell
# Windows\System32
Test-Path "C:\Windows\System32\ASICamera2.dll"

# Or in same folder as script
Test-Path "ASICamera2.dll"
```

Try specifying full path:
```python
asi.init('C:\\full\\path\\to\\ASICamera2.dll')
```

### No Cameras Detected (SDK Installed)

1. **Check USB connection**: Must be USB 3.0 (blue port)
2. **Check Device Manager**: 
   - Win + X → Device Manager
   - Look under "Imaging devices" or "Unknown devices"
3. **Install USB drivers**: Some systems need ZWO USB drivers
4. **Try different USB port**: Preferably directly on motherboard

### Permission Denied

Run PowerShell as Administrator to copy DLL to System32.

---

## 🧪 Test Without Hardware

If you don't have cameras yet, use simulator mode:

```bash
# Test with simulated cameras
python camera/simulator_test.py
```

This simulates dual cameras and voxel reconstruction without hardware.

---

## 📋 Quick Install Commands

**Full Install (Administrator PowerShell):**

```powershell
# Download SDK (manual step - visit website)
# Extract to C:\ASI_SDK\

# Copy DLL
Copy-Item "C:\ASI_SDK\lib\x64\ASICamera2.dll" -Destination "C:\Windows\System32\"

# Verify
Test-Path "C:\Windows\System32\ASICamera2.dll"

# Install Python package (if not done)
pip install zwoasi

# Test
python -c "import zwoasi as asi; asi.init(); print(f'Cameras: {asi.get_num_cameras()}')"
```

---

## ✅ After Installation

You should be able to run:

```bash
python camera/dual_asi_camera.py
# Output: Found 2 ASI cameras

python camera/example_basic_capture.py
# Captures and saves images

python camera/example_live_reconstruction.py
# Real-time 3D reconstruction
```

---

## 🔗 Resources

- **SDK Download**: https://www.zwoastro.com/downloads/developers
- **ASI662MC Manual**: https://www.zwoastro.com/product/asi662mc/
- **ZWO Support**: https://www.zwoastro.com/support/

---

**Need cameras without the SDK installed right now?** Use the simulator (next section).




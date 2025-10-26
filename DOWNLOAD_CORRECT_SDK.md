# Download Correct SDK - Step by Step

## 🎯 You Need the 64-bit SDK

Your current SDK is 32-bit only. Here's how to get the right one:

## 📥 Download Options

### Option 1: Official ZWO Website

1. **Visit**: https://www.zwoastro.com/downloads/developers

2. **Look for**: "ASI Camera SDK for Windows"
   - Should be labeled as "Windows SDK" or "Windows x64 SDK"
   - File size: Usually 5-10 MB (larger than what you have)

3. **Download** the ZIP file

### Option 2: Direct Links (Try these)

```
Latest SDK:
https://download.zwoastro.com/aspx/drivers/ASI_Windows_SDK.zip

Alternative:
https://astronomy-imaging-camera.com/software-drivers
```

## 📦 After Downloading

1. **Extract** to a temp location (e.g., `C:\Temp\ASI_SDK_New\`)

2. **Check the structure** - you should see:
   ```
   ASI_SDK_New\
   ├── include\
   │   └── ASICamera2.h
   └── lib\
       ├── x64\              ← MUST HAVE THIS!
       │   └── ASICamera2.dll   (64-bit, larger file)
       └── x86\
           └── ASICamera2.dll   (32-bit, smaller file)
   ```

3. **Verify you have x64 folder**:
   ```powershell
   Test-Path "C:\Temp\ASI_SDK_New\lib\x64\ASICamera2.dll"
   # Should return: True
   ```

## 🔧 Installation

Once you have the correct SDK:

```powershell
# Copy the 64-bit DLL to your project
Copy-Item "C:\Temp\ASI_SDK_New\lib\x64\ASICamera2.dll" -Destination "F:\Data\Cursor Folder\camera\" -Force

# Verify
Test-Path "F:\Data\Cursor Folder\camera\ASICamera2.dll"

# Check file size (should be larger than 2MB)
(Get-Item "F:\Data\Cursor Folder\camera\ASICamera2.dll").Length / 1MB
```

## ✅ Test Cameras

```powershell
# Test camera detection
python camera/dual_asi_camera.py

# If you don't have cameras connected yet:
# Expected: "Need 2 cameras for stereo, found 0"

# With cameras connected:
# Expected: "Found 2 ASI cameras"
```

## 🆘 If Download Doesn't Work

If the website is down or you can't find the right version:

1. **Contact ZWO Support**: support@zwoastro.com
2. **Specify**: "Need 64-bit Windows SDK for ASI662MC"
3. **Mention**: Your Python is 64-bit, need x64 DLL

Or use the simulator in the meantime:
```powershell
python camera/simulator_test.py
```

---

**I'll help you once you download the SDK!**




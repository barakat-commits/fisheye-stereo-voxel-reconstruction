# Fix: ASI SDK 32-bit/64-bit Mismatch

## 🔴 The Problem

Error: `OSError: [WinError 193] %1 is not a valid Win32 application`

**This means**: The DLL is 32-bit, but your Python is 64-bit.

Your Python: **64-bit** (confirmed)
Current DLL: **32-bit** (ASICamera2.dll is 2.1MB - this is the 32-bit version)

## ✅ Solution: Download the Correct SDK

### Option 1: Download Latest SDK (Recommended)

1. **Visit**: https://www.zwoastro.com/downloads/developers

2. **Download**: Look for **"ASI Camera SDK for Windows"** - make sure it says:
   - "Windows 64-bit" OR
   - Contains both x86 and x64 folders

3. **What you should see after extracting:**
   ```
   ASI_SDK\
   ├── include\
   │   └── ASICamera2.h
   └── lib\
       ├── x64\           ← You need THIS
       │   └── ASICamera2.dll  (64-bit version)
       └── x86\
           └── ASICamera2.dll  (32-bit version)
   ```

4. **Copy the x64 version:**
   ```powershell
   Copy-Item "C:\ASI_SDK\lib\x64\ASICamera2.dll" -Destination "F:\Data\Cursor Folder\camera\"
   ```

### Option 2: Direct Link (If Available)

Try this direct link:
```
https://download.zwoastro.com/aspx/drivers/ASI_Windows_SDK.zip
```

Look for the **x64** folder after extracting.

### Option 3: Use Simulator Instead (No SDK Needed)

While you download the correct SDK:

```powershell
python camera/simulator_test.py
```

This works without any SDK!

## 🔍 How to Check Your SDK

Check what you have:
```powershell
dir "C:\ASI_SDK\lib"
```

**If you see**:
- ✅ `x64\` and `x86\` folders → You have the full SDK, use x64 version
- ❌ Just `ASICamera2.dll` (2.1MB) → You have 32-bit only, need to re-download
- ✅ `ASICamera2.dll` (larger, ~4MB) → Might be 64-bit

## 🎯 Quick Fix Commands

**If you have x64 folder:**
```powershell
# Copy 64-bit DLL
Copy-Item "C:\ASI_SDK\lib\x64\ASICamera2.dll" -Destination "F:\Data\Cursor Folder\camera\" -Force

# Test
python camera/dual_asi_camera.py
```

**If you don't have x64 folder:**
1. Re-download SDK from https://www.zwoastro.com/downloads/developers
2. Make sure you get the version with x64/x86 folders
3. Copy from x64 folder

## ⚠️ Common Mistakes

1. **Downloaded 32-bit SDK** → Need full SDK with x64 folder
2. **Extracted wrong folder** → Make sure you have lib/x64/ structure
3. **Using wrong Python** → Your Python is 64-bit (this is correct!)

## 📊 File Sizes Reference

- 32-bit ASICamera2.dll: ~2.1 MB
- 64-bit ASICamera2.dll: Usually larger (~3-4 MB)

## ✅ Verification

After copying correct DLL:
```powershell
# Should work now
python camera/dual_asi_camera.py

# Expected if no cameras:
# Found 0 ASI cameras
# Need 2 cameras for stereo

# Expected with cameras:
# Found 2 ASI cameras
#   Camera 0: ASI662MC
#   Camera 1: ASI662MC
```

---

**For now, use the simulator:**
```powershell
python camera/simulator_test.py
```

This tests all your code without needing any SDK! 🚀




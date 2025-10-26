# ZWO ASI Camera Quick Start

Get dual ASI662MC cameras working with real-time 3D reconstruction in 10 minutes!

## 🎥 What This Does

Captures stereo video from two ASI662MC cameras and reconstructs it into a 3D voxel grid **in real-time** (15-30 FPS).

## 📦 Installation

### 1. Install ZWO ASI SDK

**Windows:**
1. Download SDK: https://www.zwoastro.com/downloads/developers
2. Extract and copy `ASICamera2.dll` to `C:\Windows\System32\`

**Linux:**
```bash
wget https://www.zwoastro.com/software/ASI_linux_mac_SDK_V1.34.tar.bz2
tar -xvf ASI_linux_mac_SDK_V1.34.tar.bz2
cd ASI_linux_mac_SDK_V1.34/lib/
sudo cp x64/libASICamera2.so /usr/local/lib/
sudo ldconfig

# USB permissions
echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="03c3", MODE="0666"' | sudo tee /etc/udev/rules.d/99-asi-cameras.rules
sudo udevadm control --reload-rules
```

### 2. Install Python Package

```bash
pip install -r requirements-camera.txt
```

### 3. Connect Cameras

- Plug both ASI662MC cameras into USB 3.0 ports
- Use separate USB controllers if possible (better performance)

### 4. Test

```bash
python camera/dual_asi_camera.py
```

Expected output:
```
Found 2 ASI cameras
  Camera 0: ASI662MC
  Camera 1: ASI662MC
```

## 🚀 Run Examples

### Example 1: Capture Test Frames

```bash
python camera/example_basic_capture.py
```

Output:
- `data/capture_left.jpg`
- `data/capture_right.jpg`

### Example 2: Live 3D Reconstruction

```bash
python camera/example_live_reconstruction.py
```

This will:
1. Start capturing from both cameras
2. Process frames into 3D voxel grid
3. Save results every 2 seconds
4. Show live camera preview
5. Run for 10 seconds

Output:
- `data/final_reconstruction.bin`
- `data/live_reconstruction_*.bin`

### Example 3: Visualize Results

```bash
python spacevoxelviewer.py data/final_reconstruction.bin
```

Interactive 3D visualization!

## ⚙️ Configuration

Edit `camera/example_live_reconstruction.py`:

```python
# Adjust these parameters:
grid_size=64         # Voxel grid size (32, 64, or 128)
exposure=30000       # Exposure time in μs (lower = faster)
gain=150             # Camera gain (100-300 typical)
duration_seconds=10  # How long to capture
```

## 🎯 Recommended Settings

### For 30 FPS @ 64³ Grid

```python
exposure=16000  # 16ms
gain=200        # Compensate for short exposure
grid_size=64
```

### For Higher Quality (10-15 FPS @ 128³)

```python
exposure=30000
gain=150
grid_size=128
```

### For Maximum Speed (60 FPS @ 32³)

```python
exposure=8000
gain=250
grid_size=32
```

## ⚠️ Troubleshooting

### "No cameras found"

- Check USB connections (must be USB 3.0)
- Install SDK drivers
- Linux: Check USB permissions (udev rules)

### "Low frame rate"

- Make sure USB 3.0 is enabled (blue ports)
- Reduce exposure time
- Use smaller grid size
- Build C++ extension: `python setup.py build_ext --inplace`

### "Processing too slow"

**Critical**: Build the C++ extension for 10-100× speedup:

```bash
python setup.py build_ext --inplace
```

Without it, processing will be ~2 FPS. With it: 15-30 FPS.

## 📊 Expected Performance

| Configuration | FPS | Latency |
|--------------|-----|---------|
| Python only, 64³ | 1-2 | ~500ms |
| **C++ ext, 64³** | **15-25** | **~40ms** |
| C++ ext, 128³ | 5-10 | ~100ms |
| C++ ext, 32³ | 30-60 | ~16ms |

## 🎓 Next Steps

1. **Calibrate cameras** for better 3D accuracy (see `camera/README.md`)
2. **Adjust stereo baseline** for your camera mounting
3. **Experiment with settings** for your lighting conditions
4. **Integrate with LLM agents** for autonomous operation

## 📚 Full Documentation

- **Complete guide**: `docs/ZWO_ASI_SDK_INTEGRATION.md`
- **API reference**: `camera/README.md`
- **Main framework**: `README.md`

---

**Need Help?** Check `camera/README.md` for detailed troubleshooting and API docs.




# LLM Agent Code Execution Framework

A comprehensive framework for enabling LLM agents to autonomously generate, compile, and execute code for 3D voxel processing and visualization.

> **📊 Quick Status Check**: Run `python test_installation.py` to verify everything is working, or see `STATUS.md` for current system status.

## 🎯 Overview

This project demonstrates how to:
1. **Generate code** (Python, C++, etc.)
2. **Compile and execute it** using pybind11
3. **Visualize results** with PyVista
4. **Process voxel grids** from camera/image data
5. **Real-time 3D reconstruction** from dual ZWO ASI cameras (NEW! 🎥)

## 🚀 Quick Start

### 1. Install Dependencies

**Windows:**
```bash
pip install -r requirements.txt
```

**Linux:**
```bash
sudo chmod +x setup.sh
sudo ./setup.sh
pip install -r requirements.txt
```

### 2. Build C++ Extensions

```bash
python setup.py build_ext --inplace
```

### 3. Run Examples

**Generate and visualize a voxel grid:**
```bash
python examples/example_voxel_generation.py
```

**Process image to voxel projection:**
```bash
python examples/example_image_to_voxel.py
```

**Visualize existing voxel grid:**
```bash
python spacevoxelviewer.py data/voxel_grid.bin
```

## 📁 Project Structure

```
.
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── requirements-camera.txt            # Camera support (optional)
├── setup.py                          # Build configuration for C++ extensions
├── setup.sh                          # Linux dependency installer
├── process_image.cpp                 # C++ ray casting module
├── spacevoxelviewer.py              # 3D voxel visualization tool
├── camera/                           # 🎥 ZWO ASI camera integration
│   ├── dual_asi_camera.py           # Dual ASI662MC control
│   ├── realtime_voxel_reconstruction.py
│   └── example_*.py                 # Camera examples
├── prompt_templates/                 # LLM prompt engineering templates
│   ├── code_generation.md
│   ├── cpp_module_creation.md
│   └── execution_prompts.md
├── examples/                         # Example scripts
│   ├── example_voxel_generation.py
│   └── example_image_to_voxel.py
├── docs/                            # Documentation
│   └── ZWO_ASI_SDK_INTEGRATION.md  # Camera integration guide
├── data/                            # Output directory for voxel grids
└── utils/                           # Utility functions
    └── voxel_helpers.py
```

## 🧠 Prompt Engineering for LLM Agents

See the `prompt_templates/` directory for detailed templates that enable LLMs to:
- Generate voxel processing code
- Create C++ extensions
- Execute and visualize results

## 📦 Key Dependencies

- **pybind11**: C++ ↔ Python interface
- **OpenMP**: Parallel processing
- **PyVista**: 3D visualization
- **NumPy**: Array operations
- **OpenCV**: Image processing

## 🧪 Algorithm Details

### Ray Casting (DDA Algorithm)
The Digital Differential Analyzer casts rays from camera positions through pixels into a 3D voxel grid, accumulating brightness values with distance-based attenuation.

### Voxel Grid Structure
- Grid size: N×N×N (configurable)
- Storage: Binary format (`.bin`)
- Format: Float32 array

## 🔗 Source References

Based on:
- https://github.com/tesorrells/Pixeltovoxelprojector
- https://github.com/diplodocuslongus/Pixeltovoxelprojector

## 📝 License

MIT License



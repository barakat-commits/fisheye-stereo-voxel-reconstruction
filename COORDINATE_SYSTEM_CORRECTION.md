# ⚠️ COORDINATE SYSTEM CORRECTION

## Correct Coordinate System

```
           Z (Height - VERTICAL)
           ↑
           |
           |
           |
           |
  X ←------●------ Cameras at Z=0 (GROUND LEVEL)
           |  
           | ↙ Y (Depth - HORIZONTAL)
           |/
    (Horizontal X)
```

### Axis Definition (CORRECTED)

| Axis | Direction | Range | Description |
|------|-----------|-------|-------------|
| **X** | Left ← → Right | -0.25m to +0.75m | Horizontal (perpendicular to baseline) |
| **Y** | Back ← → Front | 0.00m to +0.64m | Depth (horizontal, away from cameras) |
| **Z** | Down ← → Up | 0.00m to +0.64m | **HEIGHT** above ground (VERTICAL) |

### Key Points
- **Z = 0**: Ground level where cameras sit
- **Z-axis**: VERTICAL (height above ground)
- **Y-axis**: Depth (horizontal forward)
- **X-axis**: Horizontal left-right

### Camera Setup
- Left camera: (0.0, 0.0, 0.0) at ground level
- Right camera: (0.5, 0.0, 0.0) - 0.5m to the right
- Both pointing UP (+Z direction)
- Orientation: pitch=90° (pointing up along +Z axis)

---

## Previous (INCORRECT) System

❌ **Wrong:**
- Y = Height (vertical) ← INCORRECT
- Z = Depth (horizontal) ← INCORRECT

✅ **Correct:**
- Y = Depth (horizontal)
- Z = Height (vertical)

---

## Why This Matters

1. **Ray direction calculation**: Must use Z for height
2. **Voxel grid bounds**: Z defines vertical extent
3. **Camera orientation**: Pitch=90° points along +Z (up)
4. **Physical interpretation**: Z=0.5m means 50cm above ground

---

## Files That Need Updating

The following files have the WRONG coordinate system description:
- [ ] All camera reconstruction scripts
- [ ] Configuration files
- [ ] Documentation files
- [ ] Coordinate printing functions

**Status: FIXING NOW...**




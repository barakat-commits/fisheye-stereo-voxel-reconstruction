"""
Inspect raw voxel data to see confidence distribution
"""
import numpy as np
import sys

if len(sys.argv) < 2:
    print("Usage: python inspect_raw_voxels.py <voxel_file.bin>")
    sys.exit(1)

voxel_file = sys.argv[1]

try:
    # Load binary data
    with open(voxel_file, 'rb') as f:
        data = np.frombuffer(f.read(), dtype=np.float32)
    
    if len(data) == 0:
        print(f"File is empty (0 bytes)")
        sys.exit(0)
    
    # Reshape to (N, 4) - [x, y, z, confidence]
    voxels = data.reshape(-1, 4)
    
    print(f"Total voxels in file: {len(voxels)}")
    print(f"\nConfidence statistics:")
    print(f"  Min confidence: {voxels[:, 3].min():.2f}")
    print(f"  Max confidence: {voxels[:, 3].max():.2f}")
    print(f"  Mean confidence: {voxels[:, 3].mean():.2f}")
    print(f"  Median confidence: {np.median(voxels[:, 3]):.2f}")
    
    print(f"\nConfidence distribution:")
    for threshold in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
        count = np.sum(voxels[:, 3] > threshold)
        print(f"  > {threshold:.1f}: {count} voxels")
    
    print(f"\nSpatial bounds:")
    print(f"  X: [{voxels[:, 0].min():.3f}, {voxels[:, 0].max():.3f}]m")
    print(f"  Y: [{voxels[:, 1].min():.3f}, {voxels[:, 1].max():.3f}]m")
    print(f"  Z: [{voxels[:, 2].min():.3f}, {voxels[:, 2].max():.3f}]m")
    
except FileNotFoundError:
    print(f"Error: File not found: {voxel_file}")
except Exception as e:
    print(f"Error: {e}")



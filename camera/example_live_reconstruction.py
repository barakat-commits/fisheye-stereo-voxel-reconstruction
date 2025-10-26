"""
Example: Live 3D voxel reconstruction from dual ASI662MC cameras
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from realtime_voxel_reconstruction import RealTimeVoxelReconstructor


def main():
    print("="*60)
    print("  Live 3D Voxel Reconstruction from Dual ASI662MC Cameras")
    print("="*60)
    
    try:
        # Create reconstructor with 64x64x64 grid
        print("\nCreating voxel reconstructor (64x64x64 grid)...")
        reconstructor = RealTimeVoxelReconstructor(grid_size=64, voxel_size=1.0)
        
        # Initialize cameras
        print("Initializing dual ASI662MC cameras...")
        reconstructor.initialize_cameras(
            width=1920,
            height=1080,
            exposure=30000,  # 30ms exposure for ~30 FPS
            gain=150
        )
        
        # Run live reconstruction
        print("\nStarting live reconstruction...")
        print("  Duration: 10 seconds")
        print("  Saving every 2 seconds")
        print("  Press Ctrl+C to stop early\n")
        
        reconstructor.run_live_reconstruction(
            duration_seconds=10,
            save_interval=2.0,
            display=True  # Show camera preview (if OpenCV available)
        )
        
        print("\n[OK] Reconstruction completed!")
        print("\nGenerated files:")
        print("  data/final_reconstruction.bin")
        print("  data/live_reconstruction_*.bin (intermediate saves)")
        print("\nVisualize with:")
        print("  python ../spacevoxelviewer.py data/final_reconstruction.bin")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


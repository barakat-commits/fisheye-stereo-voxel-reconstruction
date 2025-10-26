"""
Camera Simulator - Test camera code without hardware

Simulates dual ASI662MC cameras for testing when:
- SDK is not installed
- Cameras are not connected
- You want to test the code flow

This generates synthetic stereo images and processes them through
the voxel reconstruction pipeline.
"""

import numpy as np
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.voxel_helpers import save_voxel_grid, print_grid_statistics

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import process_image_cpp
    CPP_AVAILABLE = True
except ImportError:
    CPP_AVAILABLE = False


class SimulatedASICamera:
    """Simulates a single ASI662MC camera."""
    
    def __init__(self, camera_id, width=1920, height=1080):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.exposure = 30000
        self.gain = 150
        self.frame_count = 0
        
        print(f"Simulated Camera {camera_id}: ASI662MC (simulated)")
    
    def capture_frame(self):
        """Generate a synthetic frame."""
        # Create synthetic Bayer pattern image
        img = np.zeros((self.height, self.width), dtype=np.uint8)
        
        # Add some features (moving blob)
        t = self.frame_count * 0.1
        center_x = int(self.width/2 + 200 * np.sin(t))
        center_y = int(self.height/2 + 100 * np.cos(t * 0.7))
        
        # Create Gaussian blob
        y, x = np.ogrid[:self.height, :self.width]
        mask = (x - center_x)**2 + (y - center_y)**2 <= 100**2
        
        img[mask] = 200 + int(50 * np.sin(t * 2))
        
        # Add noise
        noise = np.random.randint(0, 30, (self.height, self.width), dtype=np.uint8)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Add offset for left/right camera difference
        if self.camera_id == 1:  # Right camera
            img = np.roll(img, 50, axis=1)  # Shift right for parallax
        
        self.frame_count += 1
        return img


class SimulatedDualCameraSystem:
    """Simulates dual ASI662MC camera system."""
    
    def __init__(self):
        print("=== Simulated Dual ASI Camera System ===")
        print("Note: This is a simulator for testing without hardware\n")
        
        self.camera_left = SimulatedASICamera(0)
        self.camera_right = SimulatedASICamera(1)
        
        self.width = 1920
        self.height = 1080
        self.is_capturing = False
        
        print("[OK] Simulated cameras initialized\n")
    
    def configure(self, **kwargs):
        """Configure camera settings."""
        self.width = kwargs.get('width', 1920)
        self.height = kwargs.get('height', 1080)
        self.camera_left.exposure = kwargs.get('exposure', 30000)
        self.camera_right.exposure = kwargs.get('exposure', 30000)
        self.camera_left.gain = kwargs.get('gain', 150)
        self.camera_right.gain = kwargs.get('gain', 150)
        
        print(f"Configured: {self.width}x{self.height}, "
              f"exp={self.camera_left.exposure}us, gain={self.camera_left.gain}")
    
    def start_capture(self):
        """Start capture mode."""
        self.is_capturing = True
        print("Video capture started (simulated)")
    
    def capture_frame_pair(self, timeout=1000, retry=3):
        """Capture simulated stereo pair."""
        if not self.is_capturing:
            raise RuntimeError("Not in capture mode")
        
        # Simulate capture delay
        time.sleep(0.03)  # 30ms ~ 33 FPS
        
        img_left = self.camera_left.capture_frame()
        img_right = self.camera_right.capture_frame()
        
        return img_left, img_right
    
    def get_temperature(self):
        """Return simulated temperatures."""
        return 35.0 + np.random.randn() * 0.5, 35.5 + np.random.randn() * 0.5
    
    def stop_capture(self):
        """Stop capture."""
        self.is_capturing = False
        print("Video capture stopped (simulated)")
    
    def close(self):
        """Close cameras."""
        print("Cameras closed (simulated)")
    
    def get_info(self):
        """Get camera info."""
        return {
            'resolution': (self.width, self.height),
            'exposure': self.camera_left.exposure,
            'gain': self.camera_left.gain,
            'baseline': 100.0,
            'simulated': True
        }


class SimulatedVoxelReconstructor:
    """Simulated voxel reconstructor using synthetic camera data."""
    
    def __init__(self, grid_size=64):
        self.grid_size = grid_size
        self.voxel_grid = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
        self.cameras = None
        self.frame_count = 0
        
        print(f"Voxel reconstructor: {grid_size}x{grid_size}x{grid_size}")
        if CPP_AVAILABLE:
            print("[OK] Using C++ extension for fast processing")
        else:
            print("[WARN] C++ extension not available - using Python fallback")
    
    def initialize_cameras(self, **config):
        """Initialize simulated cameras."""
        self.cameras = SimulatedDualCameraSystem()
        self.cameras.configure(**config)
        self.cameras.start_capture()
    
    def process_frame(self, img_left, img_right):
        """Process stereo pair into voxels."""
        # Convert to float
        img_left_f = img_left.astype(np.float32) / 255.0
        img_right_f = img_right.astype(np.float32) / 255.0
        
        if CPP_AVAILABLE:
            # Use C++ ray casting
            grid_center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            camera_rotation = np.eye(3, dtype=np.float32)
            
            cam_pos_left = np.array([-50.0, 0.0, -200.0], dtype=np.float32)
            cam_pos_right = np.array([50.0, 0.0, -200.0], dtype=np.float32)
            
            voxels_left = process_image_cpp.process_image_to_voxel_grid(
                img_left_f, cam_pos_left, camera_rotation,
                self.grid_size, 1.0, grid_center, 0.01
            )
            
            voxels_right = process_image_cpp.process_image_to_voxel_grid(
                img_right_f, cam_pos_right, camera_rotation,
                self.grid_size, 1.0, grid_center, 0.01
            )
            
            # Combine
            self.voxel_grid = np.minimum(voxels_left, voxels_right)
        else:
            # Simple fallback
            try:
                from scipy.ndimage import zoom
                h, w = img_left_f.shape
                scale_y = self.grid_size / h
                scale_x = self.grid_size / w
                resized = zoom(img_left_f, (scale_y, scale_x), order=1)
                
                z_center = self.grid_size // 2
                self.voxel_grid[:, :, z_center] = resized[:self.grid_size, :self.grid_size]
            except ImportError:
                print("scipy needed for fallback mode")
        
        self.frame_count += 1
        return self.voxel_grid
    
    def run_simulation(self, duration_seconds=10, save_interval=2.0):
        """Run simulated reconstruction."""
        print(f"\nRunning simulated reconstruction for {duration_seconds}s...")
        print("  Press Ctrl+C to stop early\n")
        
        start_time = time.time()
        last_save = start_time
        frame_count = 0
        
        try:
            while (time.time() - start_time) < duration_seconds:
                # Capture frame
                frame_start = time.time()
                img_left, img_right = self.cameras.capture_frame_pair()
                
                if img_left is not None:
                    # Process
                    self.process_frame(img_left, img_right)
                    
                    frame_time = time.time() - frame_start
                    fps = 1.0 / frame_time if frame_time > 0 else 0
                    
                    # Save periodically
                    if (time.time() - last_save) >= save_interval:
                        filename = f'data/simulated_reconstruction_{int(time.time())}.bin'
                        save_voxel_grid(self.voxel_grid, filename)
                        last_save = time.time()
                    
                    # Display progress
                    elapsed = time.time() - start_time
                    avg_fps = frame_count / elapsed if elapsed > 0 else 0
                    print(f"Frame {frame_count:4d} | FPS: {fps:5.1f} (avg: {avg_fps:5.1f}) | "
                          f"Time: {elapsed:6.1f}s | Non-zero: {np.count_nonzero(self.voxel_grid):,}",
                          end='\r')
                    
                    frame_count += 1
        
        except KeyboardInterrupt:
            print("\n\nStopped by user")
        
        finally:
            # Final save
            print("\n\nSaving final reconstruction...")
            save_voxel_grid(self.voxel_grid, 'data/simulated_final.bin')
            
            print_grid_statistics(self.voxel_grid)
            
            if frame_count > 0:
                elapsed = time.time() - start_time
                print(f"\nPerformance:")
                print(f"  Frames: {frame_count}")
                print(f"  Time: {elapsed:.1f}s")
                print(f"  Average FPS: {frame_count/elapsed:.1f}")
            
            self.cameras.stop_capture()
            self.cameras.close()
            
            print("\n[OK] Simulation complete!")
            print("\nVisualize with:")
            print("  python spacevoxelviewer.py data/simulated_final.bin")


def main():
    """Run simulated camera test."""
    print("="*60)
    print("  Simulated Dual ASI Camera Test")
    print("  (No hardware or SDK required)")
    print("="*60)
    print()
    
    try:
        # Create reconstructor
        reconstructor = SimulatedVoxelReconstructor(grid_size=64)
        
        # Initialize simulated cameras
        reconstructor.initialize_cameras(
            width=1920,
            height=1080,
            exposure=30000,
            gain=150
        )
        
        # Run simulation
        reconstructor.run_simulation(
            duration_seconds=10,
            save_interval=2.0
        )
        
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


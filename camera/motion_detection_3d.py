"""
Motion Detection and 3D Voxel Mapping
Detects moving pixels from dual cameras and maps them to 3D voxel coordinates
"""

import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem
from utils.voxel_helpers import save_voxel_grid, print_grid_statistics

try:
    import process_image_cpp
    CPP_AVAILABLE = True
except ImportError:
    CPP_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class MotionDetection3D:
    """Detects moving pixels and projects them into 3D voxel space."""
    
    def __init__(self, grid_size=64, motion_threshold=30):
        """
        Initialize motion detector.
        
        Args:
            grid_size: Voxel grid dimension
            motion_threshold: Pixel difference threshold for motion (0-255)
        """
        self.grid_size = grid_size
        self.motion_threshold = motion_threshold
        self.voxel_grid = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
        
        # Previous frames for motion detection
        self.prev_frame_left = None
        self.prev_frame_right = None
        
        # Camera configuration
        self.cameras = None
        self.camera_positions = [
            np.array([-50.0, 0.0, -200.0], dtype=np.float32),  # Left
            np.array([50.0, 0.0, -200.0], dtype=np.float32)    # Right
        ]
        
        # Statistics
        self.motion_pixels_detected = 0
        self.frame_count = 0
    
    def initialize_cameras(self, exposure=30000, gain=200):
        """Initialize dual camera system with brighter settings."""
        print("\nInitializing cameras for motion detection...")
        self.cameras = DualASICameraSystem()
        
        # Configure with higher gain for better motion detection
        self.cameras.configure(
            width=1920,
            height=1080,
            exposure=exposure,
            gain=gain  # Higher gain for low light
        )
        
        self.cameras.start_capture()
        print(f"[OK] Cameras ready (exposure={exposure}us, gain={gain})")
    
    def detect_motion(self, current_left, current_right):
        """
        Detect moving pixels by comparing with previous frame.
        
        Returns:
            motion_mask_left, motion_mask_right: Boolean arrays marking moving pixels
        """
        if self.prev_frame_left is None:
            # First frame - no motion yet
            self.prev_frame_left = current_left.copy()
            self.prev_frame_right = current_right.copy()
            return np.zeros_like(current_left, dtype=bool), np.zeros_like(current_right, dtype=bool)
        
        # Calculate absolute difference
        diff_left = np.abs(current_left.astype(np.int16) - self.prev_frame_left.astype(np.int16))
        diff_right = np.abs(current_right.astype(np.int16) - self.prev_frame_right.astype(np.int16))
        
        # Threshold to get motion mask
        motion_left = diff_left > self.motion_threshold
        motion_right = diff_right > self.motion_threshold
        
        # Update previous frames
        self.prev_frame_left = current_left.copy()
        self.prev_frame_right = current_right.copy()
        
        return motion_left, motion_right
    
    def project_motion_to_voxels(self, motion_mask, image, camera_idx):
        """
        Project moving pixels to 3D voxel space using ray casting.
        
        Args:
            motion_mask: Boolean array of moving pixels
            image: Original image (for intensity)
            camera_idx: 0 for left, 1 for right
        """
        if not CPP_AVAILABLE:
            return
        
        # Create image with only moving pixels
        motion_image = np.zeros_like(image, dtype=np.float32)
        motion_image[motion_mask] = image[motion_mask].astype(np.float32) / 255.0
        
        # Boost intensity for visibility
        motion_image = np.clip(motion_image * 3.0, 0, 1.0)
        
        # Ray cast into voxel grid
        grid_center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        camera_rotation = np.eye(3, dtype=np.float32)
        
        voxels = process_image_cpp.process_image_to_voxel_grid(
            motion_image,
            self.camera_positions[camera_idx],
            camera_rotation,
            self.grid_size,
            1.0,  # voxel_size
            grid_center,
            0.005  # Lower attenuation for better visibility
        )
        
        # Accumulate voxels (additive for motion trails)
        self.voxel_grid += voxels
        
        # Decay old voxels slightly (fading trail effect)
        self.voxel_grid *= 0.98
    
    def run_motion_detection(self, duration_seconds=30, save_interval=3.0):
        """
        Run real-time motion detection and 3D mapping.
        
        Args:
            duration_seconds: How long to run (0 = infinite)
            save_interval: Save voxel grid every N seconds
        """
        if not self.cameras:
            raise RuntimeError("Cameras not initialized")
        
        print("\n" + "="*60)
        print("  MOTION DETECTION & 3D VOXEL MAPPING")
        print("="*60)
        print(f"\nSettings:")
        print(f"  Grid size: {self.grid_size}x{self.grid_size}x{self.grid_size}")
        print(f"  Motion threshold: {self.motion_threshold}")
        print(f"  Duration: {duration_seconds}s" if duration_seconds > 0 else "  Duration: Until Ctrl+C")
        print(f"\nInstructions:")
        print("  1. Move something in front of cameras")
        print("  2. Moving objects will appear in 3D voxel space")
        print("  3. Press Ctrl+C to stop")
        print("\nStarting in 3 seconds...")
        time.sleep(3)
        print("\n[RECORDING - MOVE SOMETHING!]\n")
        
        start_time = time.time()
        last_save = start_time
        
        try:
            while True:
                elapsed = time.time() - start_time
                if duration_seconds > 0 and elapsed >= duration_seconds:
                    break
                
                # Capture frames
                img_left, img_right = self.cameras.capture_frame_pair()
                
                if img_left is not None and img_right is not None:
                    # Detect motion
                    motion_left, motion_right = self.detect_motion(img_left, img_right)
                    
                    # Count moving pixels
                    motion_pixels_left = np.count_nonzero(motion_left)
                    motion_pixels_right = np.count_nonzero(motion_right)
                    total_motion = motion_pixels_left + motion_pixels_right
                    
                    # Project to 3D if motion detected
                    if CPP_AVAILABLE:
                        if motion_pixels_left > 100:  # Minimum motion threshold
                            self.project_motion_to_voxels(motion_left, img_left, 0)
                        if motion_pixels_right > 100:
                            self.project_motion_to_voxels(motion_right, img_right, 1)
                    
                    self.motion_pixels_detected += total_motion
                    self.frame_count += 1
                    
                    # Display status
                    fps = self.frame_count / elapsed if elapsed > 0 else 0
                    non_zero = np.count_nonzero(self.voxel_grid)
                    
                    print(f"Frame {self.frame_count:4d} | "
                          f"Motion pixels: L={motion_pixels_left:5d} R={motion_pixels_right:5d} | "
                          f"Voxels: {non_zero:6,} | "
                          f"FPS: {fps:4.1f} | "
                          f"Time: {elapsed:5.1f}s",
                          end='\r')
                    
                    # Periodic save
                    if (time.time() - last_save) >= save_interval:
                        timestamp = int(time.time())
                        filename = f'data/motion_3d_{timestamp}.bin'
                        save_voxel_grid(self.voxel_grid, filename)
                        print(f"\n  [Saved] {filename}")
                        last_save = time.time()
        
        except KeyboardInterrupt:
            print("\n\n[Stopped by user]")
        
        finally:
            # Final save
            print("\n\nSaving final 3D motion map...")
            save_voxel_grid(self.voxel_grid, 'data/motion_3d_final.bin')
            
            # Statistics
            print("\n" + "="*60)
            print("  RESULTS")
            print("="*60)
            print(f"\nFrames processed: {self.frame_count}")
            print(f"Total motion pixels detected: {self.motion_pixels_detected:,}")
            print(f"Average motion per frame: {self.motion_pixels_detected/self.frame_count if self.frame_count > 0 else 0:.0f}")
            print(f"Processing time: {elapsed:.1f}s")
            print(f"Average FPS: {self.frame_count/elapsed if elapsed > 0 else 0:.1f}")
            
            print_grid_statistics(self.voxel_grid)
            
            # Close cameras
            self.cameras.stop_capture()
            self.cameras.close()
            
            print("\n[OK] Motion detection complete!")
            print("\nVisualize with:")
            print("  python spacevoxelviewer.py data/motion_3d_final.bin")


def main():
    """Main function."""
    print("="*60)
    print("  3D Motion Detection from Dual ASI662MC Cameras")
    print("="*60)
    
    if not CPP_AVAILABLE:
        print("\n[WARNING] C++ extension not available - motion won't be mapped to 3D")
        print("Build with: python setup.py build_ext --inplace")
        return 1
    
    try:
        # Create detector
        detector = MotionDetection3D(
            grid_size=64,
            motion_threshold=30  # Adjust based on lighting
        )
        
        # Initialize cameras
        detector.initialize_cameras(
            exposure=20000,  # 20ms - faster for motion
            gain=250         # High gain for low light
        )
        
        # Run detection
        detector.run_motion_detection(
            duration_seconds=30,  # 30 seconds
            save_interval=5.0
        )
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())




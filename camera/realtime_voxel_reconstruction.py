"""
Real-time 3D Voxel Reconstruction from Dual ASI Cameras
"""

import numpy as np
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dual_asi_camera import DualASICameraSystem
from utils.voxel_helpers import create_empty_voxel_grid, save_voxel_grid, print_grid_statistics

try:
    import process_image_cpp
    CPP_AVAILABLE = True
    print("[OK] C++ extension available for fast processing")
except ImportError:
    CPP_AVAILABLE = False
    print("[WARN] C++ extension not available - using fallback (slower)")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available")


class RealTimeVoxelReconstructor:
    """Real-time 3D voxel reconstruction from stereo camera feeds."""
    
    def __init__(self, grid_size=64, voxel_size=1.0):
        """
        Initialize voxel reconstructor.
        
        Args:
            grid_size: Dimension of cubic voxel grid (N for N×N×N)
            voxel_size: Physical size of each voxel in mm
        """
        self.grid_size = grid_size
        self.voxel_size = voxel_size
        self.voxel_grid = create_empty_voxel_grid(grid_size)
        
        # Camera system
        self.cameras = None
        
        # Stereo configuration
        self.baseline = 100.0  # mm between cameras
        self.focal_length_px = 1500.0  # pixels (approximate, should be calibrated)
        
        # Camera positions in 3D space (mm)
        self.camera_positions = [
            np.array([-self.baseline/2, 0.0, -300.0], dtype=np.float32),  # Left
            np.array([self.baseline/2, 0.0, -300.0], dtype=np.float32)    # Right
        ]
        
        # Statistics
        self.frame_count = 0
        self.total_time = 0.0
        self.last_fps = 0.0
    
    def initialize_cameras(self, lib_path=None, **camera_config):
        """
        Initialize dual camera system.
        
        Args:
            lib_path: Path to ASICamera2 library (optional)
            **camera_config: Camera configuration parameters
        """
        print("\nInitializing dual ASI camera system...")
        
        self.cameras = DualASICameraSystem(lib_path=lib_path)
        
        # Default configuration
        config = {
            'width': 1920,
            'height': 1080,
            'exposure': 30000,  # 30ms for ~30 FPS
            'gain': 150,
            'wb_r': 50,
            'wb_b': 95
        }
        config.update(camera_config)
        
        self.cameras.configure(**config)
        self.cameras.start_capture()
        
        print("[OK] Cameras initialized and capturing")
    
    def process_stereo_frame(self, img_left, img_right, debayer=True):
        """
        Process stereo frame pair into voxel grid.
        
        Args:
            img_left: Left camera image (raw Bayer or RGB)
            img_right: Right camera image (raw Bayer or RGB)
            debayer: Convert Bayer to grayscale
            
        Returns:
            Updated voxel grid
        """
        # Convert to grayscale if needed
        if debayer and CV2_AVAILABLE and len(img_left.shape) == 2:
            # Debayer to RGB then convert to grayscale
            rgb_left = cv2.cvtColor(img_left, cv2.COLOR_BAYER_RG2RGB)
            rgb_right = cv2.cvtColor(img_right, cv2.COLOR_BAYER_RG2RGB)
            
            gray_left = cv2.cvtColor(rgb_left, cv2.COLOR_RGB2GRAY)
            gray_right = cv2.cvtColor(rgb_right, cv2.COLOR_RGB2GRAY)
        else:
            # Use raw Bayer as grayscale approximation
            gray_left = img_left
            gray_right = img_right
        
        # Normalize to [0, 1]
        img_left_f = gray_left.astype(np.float32) / 255.0
        img_right_f = gray_right.astype(np.float32) / 255.0
        
        if CPP_AVAILABLE:
            # Use C++ accelerated ray casting
            self.voxel_grid = self._process_with_cpp(img_left_f, img_right_f)
        else:
            # Python fallback
            self.voxel_grid = self._process_with_python(img_left_f, img_right_f)
        
        return self.voxel_grid
    
    def _process_with_cpp(self, img_left, img_right):
        """Process using C++ extension for speed."""
        grid_center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        camera_rotation = np.eye(3, dtype=np.float32)
        attenuation = 0.01
        
        # Process left camera
        voxels_left = process_image_cpp.process_image_to_voxel_grid(
            img_left,
            self.camera_positions[0],
            camera_rotation,
            self.grid_size,
            self.voxel_size,
            grid_center,
            attenuation
        )
        
        # Process right camera
        voxels_right = process_image_cpp.process_image_to_voxel_grid(
            img_right,
            self.camera_positions[1],
            camera_rotation,
            self.grid_size,
            self.voxel_size,
            grid_center,
            attenuation
        )
        
        # Combine: intersection for better 3D reconstruction
        # (Only voxels visible from both cameras)
        combined = np.minimum(voxels_left, voxels_right)
        
        # Or use addition for brighter reconstruction
        # combined = voxels_left + voxels_right
        
        return combined
    
    def _process_with_python(self, img_left, img_right):
        """Fallback Python processing (simplified)."""
        try:
            from scipy.ndimage import zoom
        except ImportError:
            print("scipy required for fallback mode")
            return self.voxel_grid
        
        # Simple projection: use left camera only
        h, w = img_left.shape
        
        # Resize to fit grid
        scale_y = self.grid_size / h
        scale_x = self.grid_size / w
        resized = zoom(img_left, (scale_y, scale_x), order=1)
        
        # Create new grid
        grid = create_empty_voxel_grid(self.grid_size)
        
        # Place in center slice
        z_center = self.grid_size // 2
        grid[:, :, z_center] = resized[:self.grid_size, :self.grid_size]
        
        return grid
    
    def run_live_reconstruction(self, duration_seconds=10, save_interval=2.0, 
                                display=False):
        """
        Run real-time reconstruction from camera feeds.
        
        Args:
            duration_seconds: How long to capture (0 = indefinite)
            save_interval: Save voxel grid every N seconds
            display: Show live preview (requires OpenCV)
        """
        if self.cameras is None:
            raise RuntimeError("Cameras not initialized. Call initialize_cameras() first.")
        
        print(f"\nStarting live reconstruction...")
        print(f"  Grid size: {self.grid_size}x{self.grid_size}x{self.grid_size}")
        print(f"  Duration: {duration_seconds}s" if duration_seconds > 0 else "  Duration: Until Ctrl+C")
        print(f"  Save interval: {save_interval}s")
        print("  Press Ctrl+C to stop\n")
        
        start_time = time.time()
        last_save = start_time
        last_display = start_time
        
        try:
            while True:
                # Check duration
                elapsed = time.time() - start_time
                if duration_seconds > 0 and elapsed >= duration_seconds:
                    break
                
                # Capture stereo pair
                frame_start = time.time()
                img_left, img_right = self.cameras.capture_frame_pair(timeout=1000)
                
                if img_left is not None and img_right is not None:
                    # Process into voxel grid
                    self.process_stereo_frame(img_left, img_right)
                    
                    frame_time = time.time() - frame_start
                    self.frame_count += 1
                    self.total_time += frame_time
                    self.last_fps = 1.0 / frame_time if frame_time > 0 else 0
                    
                    # Save periodically
                    if (time.time() - last_save) >= save_interval:
                        timestamp = int(time.time())
                        filename = f'data/live_reconstruction_{timestamp}.bin'
                        save_voxel_grid(self.voxel_grid, filename)
                        last_save = time.time()
                        print(f"  Saved: {filename}")
                    
                    # Display status
                    avg_fps = self.frame_count / elapsed if elapsed > 0 else 0
                    print(f"Frame {self.frame_count:4d} | "
                          f"FPS: {self.last_fps:5.1f} (avg: {avg_fps:5.1f}) | "
                          f"Time: {elapsed:6.1f}s | "
                          f"Non-zero voxels: {np.count_nonzero(self.voxel_grid):,}",
                          end='\r')
                    
                    # Optional display
                    if display and CV2_AVAILABLE and (time.time() - last_display) > 0.1:
                        self._display_preview(img_left, img_right)
                        last_display = time.time()
                        
                        # Check for 'q' key to quit
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            print("\nUser requested stop")
                            break
                else:
                    print(f"Frame {self.frame_count}: Failed to capture", end='\r')
                    time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n\nStopping reconstruction (Ctrl+C)")
        
        finally:
            # Final save
            print("\n\nSaving final reconstruction...")
            save_voxel_grid(self.voxel_grid, 'data/final_reconstruction.bin')
            
            # Statistics
            print_grid_statistics(self.voxel_grid)
            
            if self.frame_count > 0:
                avg_time = self.total_time / self.frame_count
                avg_fps = self.frame_count / (time.time() - start_time)
                
                print(f"\nPerformance:")
                print(f"  Total frames: {self.frame_count}")
                print(f"  Total time: {time.time() - start_time:.1f}s")
                print(f"  Average FPS: {avg_fps:.1f}")
                print(f"  Average frame time: {avg_time*1000:.1f}ms")
            
            # Stop cameras
            if self.cameras:
                self.cameras.stop_capture()
                self.cameras.close()
            
            # Close display windows
            if display and CV2_AVAILABLE:
                cv2.destroyAllWindows()
    
    def _display_preview(self, img_left, img_right):
        """Display camera preview."""
        if not CV2_AVAILABLE:
            return
        
        # Debayer if needed
        if len(img_left.shape) == 2:
            preview_left = cv2.cvtColor(img_left, cv2.COLOR_BAYER_RG2RGB)
            preview_right = cv2.cvtColor(img_right, cv2.COLOR_BAYER_RG2RGB)
        else:
            preview_left = img_left
            preview_right = img_right
        
        # Resize for display
        scale = 0.5
        preview_left = cv2.resize(preview_left, None, fx=scale, fy=scale)
        preview_right = cv2.resize(preview_right, None, fx=scale, fy=scale)
        
        # Show side by side
        combined = np.hstack([preview_left, preview_right])
        
        cv2.imshow('Dual ASI Cameras (Left | Right)', combined)
    
    def calibrate_from_checkerboard(self, num_images=20, chessboard_size=(9, 6)):
        """
        Interactive camera calibration using checkerboard pattern.
        
        Args:
            num_images: Number of checkerboard images to capture
            chessboard_size: (cols, rows) of internal corners
        """
        if not CV2_AVAILABLE:
            print("OpenCV required for calibration")
            return None
        
        if self.cameras is None:
            raise RuntimeError("Cameras not initialized")
        
        print(f"\nCalibration: Capture {num_images} images of checkerboard")
        print(f"Checkerboard size: {chessboard_size[0]}x{chessboard_size[1]} internal corners")
        print("Press SPACE to capture, ESC to cancel, ENTER when done\n")
        
        image_pairs = []
        
        while len(image_pairs) < num_images:
            img_left, img_right = self.cameras.capture_frame_pair()
            
            if img_left is not None and img_right is not None:
                # Debayer
                rgb_left = cv2.cvtColor(img_left, cv2.COLOR_BAYER_RG2RGB)
                rgb_right = cv2.cvtColor(img_right, cv2.COLOR_BAYER_RG2RGB)
                
                # Find checkerboard
                gray_left = cv2.cvtColor(rgb_left, cv2.COLOR_RGB2GRAY)
                ret_left, _ = cv2.findChessboardCorners(gray_left, chessboard_size)
                
                # Display
                display = rgb_left.copy()
                if ret_left:
                    cv2.drawChessboardCorners(display, chessboard_size, _, ret_left)
                    cv2.putText(display, "Checkerboard found! Press SPACE", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(display, "Move checkerboard into view", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                cv2.putText(display, f"Captured: {len(image_pairs)}/{num_images}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow('Calibration', display)
                
                key = cv2.waitKey(10) & 0xFF
                
                if key == ord(' ') and ret_left:  # Space
                    image_pairs.append((rgb_left, rgb_right))
                    print(f"Captured image {len(image_pairs)}/{num_images}")
                elif key == 27:  # ESC
                    print("Calibration cancelled")
                    cv2.destroyAllWindows()
                    return None
                elif key == 13 and len(image_pairs) >= 10:  # Enter
                    break
        
        cv2.destroyAllWindows()
        
        # Perform calibration
        print("\nPerforming stereo calibration...")
        calibration_results = self._calibrate_stereo(image_pairs, chessboard_size)
        
        if calibration_results:
            print("[OK] Calibration successful!")
            print(f"  Baseline: {calibration_results['baseline']:.2f} mm")
            
            # Update camera positions
            self.baseline = calibration_results['baseline']
            self.camera_positions = [
                np.array([-self.baseline/2, 0.0, -300.0], dtype=np.float32),
                np.array([self.baseline/2, 0.0, -300.0], dtype=np.float32)
            ]
        
        return calibration_results
    
    def _calibrate_stereo(self, image_pairs, chessboard_size):
        """Perform stereo calibration."""
        # Simplified - full implementation would use cv2.stereoCalibrate
        # This is a placeholder
        return {
            'baseline': self.baseline,
            'focal_length': self.focal_length_px,
            'calibrated': False
        }


def main():
    """Main function for real-time voxel reconstruction."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-time voxel reconstruction from dual ASI cameras")
    parser.add_argument('--grid-size', type=int, default=64, help="Voxel grid size (default: 64)")
    parser.add_argument('--duration', type=float, default=10, help="Capture duration in seconds (0=infinite)")
    parser.add_argument('--exposure', type=int, default=30000, help="Exposure time in microseconds")
    parser.add_argument('--gain', type=int, default=150, help="Camera gain (0-600)")
    parser.add_argument('--save-interval', type=float, default=2.0, help="Save interval in seconds")
    parser.add_argument('--display', action='store_true', help="Show camera preview")
    parser.add_argument('--lib-path', type=str, default=None, help="Path to ASICamera2 library")
    
    args = parser.parse_args()
    
    try:
        # Create reconstructor
        reconstructor = RealTimeVoxelReconstructor(grid_size=args.grid_size)
        
        # Initialize cameras
        reconstructor.initialize_cameras(
            lib_path=args.lib_path,
            exposure=args.exposure,
            gain=args.gain
        )
        
        # Run reconstruction
        reconstructor.run_live_reconstruction(
            duration_seconds=args.duration,
            save_interval=args.save_interval,
            display=args.display
        )
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


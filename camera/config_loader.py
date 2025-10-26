"""
Camera Configuration Loader

Loads camera and reconstruction parameters from JSON config file.
Learning from tesorrells/Pixeltovoxelprojector approach.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any


class CameraConfig:
    """Configuration for a single camera."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.id = config_dict['id']
        self.position = np.array(config_dict['position'], dtype=np.float32)
        
        # Orientation (yaw, pitch, roll in degrees)
        orient = config_dict['orientation']
        self.yaw = orient['yaw']
        self.pitch = orient['pitch']
        self.roll = orient['roll']
        
        self.calibration_file = config_dict.get('calibration_file', None)
        self.asi_camera_index = config_dict.get('asi_camera_index', 0)
        
        # Camera settings
        settings = config_dict.get('settings', {})
        self.exposure_us = settings.get('exposure_us', 30000)
        self.gain = settings.get('gain', 300)
        self.width = settings.get('width', 1920)
        self.height = settings.get('height', 1080)
    
    def get_direction_vector(self) -> np.ndarray:
        """
        Calculate camera direction vector from yaw/pitch/roll.
        
        Convention:
        - yaw=0, pitch=0, roll=0 points along +X axis
        - pitch=90 points up (+Y axis)
        - yaw rotates around Y axis
        """
        # Convert to radians
        yaw_rad = np.radians(self.yaw)
        pitch_rad = np.radians(self.pitch)
        
        # Calculate direction vector
        direction = np.array([
            np.cos(pitch_rad) * np.cos(yaw_rad),  # X
            np.sin(pitch_rad),                     # Y
            np.cos(pitch_rad) * np.sin(yaw_rad)   # Z
        ])
        
        return direction / np.linalg.norm(direction)
    
    def __repr__(self):
        return (f"CameraConfig(id='{self.id}', pos={self.position}, "
                f"yaw={self.yaw}, pitch={self.pitch}, "
                f"exp={self.exposure_us}us, gain={self.gain})")


class VoxelGridConfig:
    """Configuration for voxel grid."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.size = config_dict['size']
        self.voxel_size_meters = config_dict['voxel_size_meters']
        
        bounds = config_dict['bounds']
        self.x_min = bounds['x_min']
        self.x_max = bounds['x_max']
        self.y_min = bounds['y_min']
        self.y_max = bounds['y_max']
        self.z_min = bounds['z_min']
        self.z_max = bounds['z_max']
    
    def get_world_bounds(self):
        """Return world bounds as tuple."""
        return (
            (self.x_min, self.x_max),
            (self.y_min, self.y_max),
            (self.z_min, self.z_max)
        )
    
    def __repr__(self):
        return (f"VoxelGridConfig(size={self.size}, "
                f"voxel_size={self.voxel_size_meters}m, "
                f"X:[{self.x_min},{self.x_max}], "
                f"Y:[{self.y_min},{self.y_max}], "
                f"Z:[{self.z_min},{self.z_max}])")


class ReconstructionConfig:
    """Configuration for reconstruction parameters."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.motion_threshold = config_dict.get('motion_threshold', 25)
        self.max_ray_distance_meters = config_dict.get('max_ray_distance_meters', 1.0)
        self.ray_step_size_ratio = config_dict.get('ray_step_size_ratio', 0.5)
        self.temporal_decay = config_dict.get('temporal_decay', 0.99)
        self.multi_camera_boost = config_dict.get('multi_camera_boost', 1.5)
        self.distance_falloff_factor = config_dict.get('distance_falloff_factor', 0.2)
        self.voxel_print_threshold = config_dict.get('voxel_print_threshold', 50)
    
    def __repr__(self):
        return (f"ReconstructionConfig(motion_thresh={self.motion_threshold}, "
                f"max_dist={self.max_ray_distance_meters}m, "
                f"multi_cam_boost={self.multi_camera_boost}x)")


class RecordingConfig:
    """Configuration for recording parameters."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.duration_seconds = config_dict.get('duration_seconds', 15)
        self.warmup_delay_seconds = config_dict.get('warmup_delay_seconds', 0.5)
    
    def __repr__(self):
        return (f"RecordingConfig(duration={self.duration_seconds}s, "
                f"warmup={self.warmup_delay_seconds}s)")


class SystemConfig:
    """Complete system configuration."""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Parse cameras
        self.cameras = [CameraConfig(cam) for cam in config['cameras']]
        
        # Parse voxel grid
        self.voxel_grid = VoxelGridConfig(config['voxel_grid'])
        
        # Parse reconstruction settings
        self.reconstruction = ReconstructionConfig(config['reconstruction'])
        
        # Parse recording settings
        self.recording = RecordingConfig(config['recording'])
    
    def get_camera_by_id(self, camera_id: str) -> CameraConfig:
        """Get camera configuration by ID."""
        for cam in self.cameras:
            if cam.id == camera_id:
                return cam
        raise ValueError(f"Camera with id '{camera_id}' not found")
    
    def get_camera_by_index(self, asi_index: int) -> CameraConfig:
        """Get camera configuration by ASI camera index."""
        for cam in self.cameras:
            if cam.asi_camera_index == asi_index:
                return cam
        raise ValueError(f"Camera with ASI index {asi_index} not found")
    
    def print_summary(self):
        """Print configuration summary."""
        print("="*70)
        print("  SYSTEM CONFIGURATION")
        print("="*70)
        print()
        print("Cameras:")
        for cam in self.cameras:
            print(f"  {cam.id}:")
            print(f"    Position:    {cam.position} m")
            print(f"    Orientation: yaw={cam.yaw}°, pitch={cam.pitch}°, roll={cam.roll}°")
            print(f"    Direction:   {cam.get_direction_vector()}")
            print(f"    ASI Index:   {cam.asi_camera_index}")
            print(f"    Settings:    exp={cam.exposure_us}µs, gain={cam.gain}")
            if cam.calibration_file:
                print(f"    Calibration: {cam.calibration_file}")
            print()
        
        print("Voxel Grid:")
        print(f"  Size:        {self.voxel_grid.size}³ voxels")
        print(f"  Resolution:  {self.voxel_grid.voxel_size_meters*100}cm per voxel")
        print(f"  X bounds:    [{self.voxel_grid.x_min}, {self.voxel_grid.x_max}] m")
        print(f"  Y bounds:    [{self.voxel_grid.y_min}, {self.voxel_grid.y_max}] m")
        print(f"  Z bounds:    [{self.voxel_grid.z_min}, {self.voxel_grid.z_max}] m")
        print()
        
        print("Reconstruction:")
        print(f"  Motion threshold:      {self.reconstruction.motion_threshold}")
        print(f"  Max ray distance:      {self.reconstruction.max_ray_distance_meters}m")
        print(f"  Ray step ratio:        {self.reconstruction.ray_step_size_ratio}")
        print(f"  Temporal decay:        {self.reconstruction.temporal_decay}")
        print(f"  Multi-camera boost:    {self.reconstruction.multi_camera_boost}x")
        print(f"  Distance falloff:      {self.reconstruction.distance_falloff_factor}")
        print(f"  Print threshold:       {self.reconstruction.voxel_print_threshold}")
        print()
        
        print("Recording:")
        print(f"  Duration:              {self.recording.duration_seconds}s")
        print(f"  Warmup delay:          {self.recording.warmup_delay_seconds}s")
        print()
        print("="*70)
    
    def __repr__(self):
        return (f"SystemConfig(cameras={len(self.cameras)}, "
                f"voxel_grid={self.voxel_grid.size}³, "
                f"from '{self.config_file}')")


def load_config(config_file: str = "camera/camera_config.json") -> SystemConfig:
    """
    Load system configuration from JSON file.
    
    Args:
        config_file: Path to configuration JSON file
    
    Returns:
        SystemConfig object
    """
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_file}\n"
            f"Create it from camera/camera_config.json template"
        )
    
    return SystemConfig(str(config_path))


if __name__ == "__main__":
    # Test configuration loading
    import sys
    
    config_file = sys.argv[1] if len(sys.argv) > 1 else "camera/camera_config.json"
    
    print("Testing configuration loader...")
    print(f"Loading: {config_file}\n")
    
    try:
        config = load_config(config_file)
        config.print_summary()
        
        print("\n[TEST] Camera direction vectors:")
        for cam in config.cameras:
            direction = cam.get_direction_vector()
            print(f"  {cam.id}: {direction} (pointing", end=" ")
            if abs(direction[1]) > 0.9:
                print("UP)" if direction[1] > 0 else "DOWN)")
            elif abs(direction[0]) > 0.9:
                print("EAST)" if direction[0] > 0 else "WEST)")
            elif abs(direction[2]) > 0.9:
                print("NORTH)" if direction[2] > 0 else "SOUTH)")
            else:
                print(f"at angle)")
        
        print("\n[OK] Configuration loaded successfully!")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to load configuration: {e}")
        sys.exit(1)




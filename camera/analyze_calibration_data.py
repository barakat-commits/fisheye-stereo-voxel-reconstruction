"""
Analyze Vertical Calibration Data

Processes calibration JSON and provides correction recommendations.
"""

import json
import numpy as np
import sys
from pathlib import Path


def analyze_calibration(json_file):
    """Analyze calibration data and provide correction factors."""
    
    print("="*70)
    print("  CALIBRATION DATA ANALYSIS")
    print("="*70)
    print()
    
    # Load data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    left_data = data.get('LEFT', [])
    right_data = data.get('RIGHT', [])
    
    print(f"Loaded: {json_file}")
    print(f"  LEFT recordings:  {len(left_data)}")
    print(f"  RIGHT recordings: {len(right_data)}")
    print()
    
    if len(left_data) == 0 and len(right_data) == 0:
        print("[ERROR] No data recorded!")
        return
    
    # Analyze each camera
    results = {}
    
    for camera_name, recordings in [('LEFT', left_data), ('RIGHT', right_data)]:
        if len(recordings) == 0:
            print(f"{camera_name} camera: No recordings")
            continue
        
        print("="*70)
        print(f"  {camera_name} CAMERA ANALYSIS")
        print("="*70)
        print()
        
        # Extract coordinates
        x_coords = []
        y_coords = []
        z_coords = []
        intensities = []
        
        for rec in recordings:
            world = rec['world']
            x_coords.append(world[0])
            y_coords.append(world[1])
            z_coords.append(world[2])
            intensities.append(rec['intensity'])
        
        x_arr = np.array(x_coords)
        y_arr = np.array(y_coords)
        z_arr = np.array(z_coords)
        int_arr = np.array(intensities)
        
        # Statistics
        x_mean = np.mean(x_arr)
        x_std = np.std(x_arr)
        x_min = np.min(x_arr)
        x_max = np.max(x_arr)
        
        y_mean = np.mean(y_arr)
        y_std = np.std(y_arr)
        y_min = np.min(y_arr)
        y_max = np.max(y_arr)
        
        z_mean = np.mean(z_arr)
        z_std = np.std(z_arr)
        z_min = np.min(z_arr)
        z_max = np.max(z_arr)
        
        int_mean = np.mean(int_arr)
        int_median = np.median(int_arr)
        
        # Expected values
        expected_x = 0.0 if camera_name == 'LEFT' else 0.5
        expected_y = 0.0
        
        x_error = x_mean - expected_x
        y_error = y_mean - expected_y
        
        # Print statistics
        print(f"Total recordings: {len(recordings)}")
        print()
        
        print(f"X-axis (horizontal, should be constant at {expected_x:.2f}m):")
        print(f"  Mean:  {x_mean:+.4f}m  (Error: {x_error:+.4f}m = {x_error*100:+.1f}cm)")
        print(f"  Std:   {x_std:.4f}m")
        print(f"  Range: {x_min:+.4f}m to {x_max:+.4f}m")
        
        if abs(x_error) < 0.02:
            print(f"  [OK] X alignment GOOD (error < 2cm)")
        elif abs(x_error) < 0.05:
            print(f"  [WARN] X alignment acceptable (error < 5cm)")
        else:
            print(f"  [ERROR] X alignment POOR (error > 5cm) - correction needed!")
        
        print()
        
        print(f"Y-axis (depth, should be constant at {expected_y:.2f}m):")
        print(f"  Mean:  {y_mean:+.4f}m  (Error: {y_error:+.4f}m = {y_error*100:+.1f}cm)")
        print(f"  Std:   {y_std:.4f}m")
        print(f"  Range: {y_min:+.4f}m to {y_max:+.4f}m")
        
        if abs(y_error) < 0.02:
            print(f"  [OK] Y alignment GOOD")
        elif abs(y_error) < 0.05:
            print(f"  [WARN] Y alignment acceptable")
        else:
            print(f"  [ERROR] Y alignment POOR - correction needed!")
        
        print()
        
        print(f"Z-axis (height, should VARY):")
        print(f"  Mean:  {z_mean:.4f}m")
        print(f"  Std:   {z_std:.4f}m")
        print(f"  Range: {z_min:.4f}m to {z_max:.4f}m  ({(z_max-z_min)*100:.1f}cm span)")
        
        if z_std < 0.01:
            print(f"  [WARN] Z variation too small - move through more heights!")
        elif z_std > 0.05:
            print(f"  [OK] Good Z variation")
        else:
            print(f"  [OK] Reasonable Z variation")
        
        print()
        
        print(f"Intensity:")
        print(f"  Mean:   {int_mean:.2f}")
        print(f"  Median: {int_median:.2f}")
        print()
        
        # Store results
        results[camera_name] = {
            'x_mean': x_mean,
            'x_error': x_error,
            'x_std': x_std,
            'y_mean': y_mean,
            'y_error': y_error,
            'y_std': y_std,
            'z_mean': z_mean,
            'z_std': z_std,
            'z_range': (z_min, z_max),
            'count': len(recordings)
        }
    
    # Overall assessment and corrections
    print("="*70)
    print("  OVERALL ASSESSMENT")
    print("="*70)
    print()
    
    if 'LEFT' in results and 'RIGHT' in results:
        left = results['LEFT']
        right = results['RIGHT']
        
        # Check consistency
        print("Consistency check:")
        print(f"  LEFT X error:  {left['x_error']*100:+.2f}cm")
        print(f"  RIGHT X error: {right['x_error']*100:+.2f}cm")
        print()
        
        # Overall X accuracy
        max_x_error = max(abs(left['x_error']), abs(right['x_error']))
        
        if max_x_error < 0.02:
            print("[EXCELLENT] X-axis accuracy < 2cm - no correction needed!")
            print()
        elif max_x_error < 0.05:
            print("[GOOD] X-axis accuracy < 5cm - optional correction")
            print()
        else:
            print("[ACTION NEEDED] X-axis errors > 5cm - correction recommended")
            print()
            
            # Calculate correction factor
            # Actual baseline between cameras
            actual_baseline = right['x_mean'] - left['x_mean']
            expected_baseline = 0.5  # 50cm
            
            print(f"Camera baseline:")
            print(f"  Expected: {expected_baseline:.3f}m (50cm)")
            print(f"  Measured: {actual_baseline:.3f}m ({actual_baseline*100:.1f}cm)")
            print(f"  Error:    {(actual_baseline - expected_baseline)*100:+.1f}cm")
            print()
            
            if abs(actual_baseline - expected_baseline) > 0.05:
                scale_correction = expected_baseline / actual_baseline
                print(f"[CORRECTION] X-axis scale factor: {scale_correction:.4f}")
                print(f"  Apply: corrected_x = original_x * {scale_correction:.4f}")
                print()
        
        # Y-axis assessment
        avg_y_error = (left['y_error'] + right['y_error']) / 2
        print(f"Y-axis (depth):")
        print(f"  Average error: {avg_y_error*100:+.2f}cm")
        
        if abs(avg_y_error) < 0.02:
            print(f"  [OK] Y-axis good")
        elif abs(avg_y_error) < 0.05:
            print(f"  [ACCEPTABLE] Y-axis acceptable")
        else:
            print(f"  [CORRECTION] Y offset: {avg_y_error:+.4f}m")
            print(f"  Apply: corrected_y = original_y - {avg_y_error:.4f}")
        
        print()
    
    elif 'LEFT' in results:
        print("[INCOMPLETE] Only LEFT camera data available")
        print("Run calibration again with both cameras for full analysis")
        print()
    
    elif 'RIGHT' in results:
        print("[INCOMPLETE] Only RIGHT camera data available")
        print("Run calibration again with both cameras for full analysis")
        print()
    
    print("="*70)
    print("  RECOMMENDATIONS")
    print("="*70)
    print()
    
    if 'LEFT' in results and 'RIGHT' in results:
        left = results['LEFT']
        right = results['RIGHT']
        
        needs_correction = False
        
        # Check if corrections are needed
        if max(abs(left['x_error']), abs(right['x_error'])) > 0.05:
            needs_correction = True
            print("1. X-axis correction needed (>5cm error)")
        
        if abs((left['y_error'] + right['y_error']) / 2) > 0.05:
            needs_correction = True
            print("2. Y-axis correction needed (>5cm error)")
        
        if not needs_correction:
            print("[EXCELLENT] Current projection math is accurate!")
            print("No corrections needed. System is properly calibrated.")
            print()
            print("You can proceed with 3D reconstruction using current settings.")
        else:
            print()
            print("To apply corrections:")
            print("1. Share this analysis output")
            print("2. I'll create a corrected projection script")
            print("3. Re-run calibration to verify")
            print("4. Iterate until error < 2cm")
    
    print()
    print("="*70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_calibration_data.py <calibration_json_file>")
        print()
        print("Example:")
        print("  python analyze_calibration_data.py camera/vertical_calibration_20251024_225833.json")
        return
    
    json_file = sys.argv[1]
    
    if not Path(json_file).exists():
        print(f"[ERROR] File not found: {json_file}")
        return
    
    analyze_calibration(json_file)


if __name__ == "__main__":
    main()




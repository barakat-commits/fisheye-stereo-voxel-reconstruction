"""
Generate ArUco Calibration Board

Creates a printable PDF with ArUco markers arranged in a grid.
Much better for fisheye distortion than checkerboards!
"""

import cv2
import numpy as np
from pathlib import Path


def generate_aruco_board():
    """
    Generate an ArUco calibration board and save as image.
    """
    print("="*70)
    print("  ARUCO CALIBRATION BOARD GENERATOR")
    print("="*70)
    print()
    
    # ArUco dictionary (4x4 markers, 50 IDs)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    
    # Board configuration
    markers_x = 5      # 5 markers across
    markers_y = 4      # 4 markers down
    marker_length = 200   # Marker size in pixels (for A4: ~40mm)
    marker_separation = 50  # Separation in pixels (~10mm)
    
    # Create board
    board = cv2.aruco.GridBoard(
        (markers_x, markers_y),
        marker_length,
        marker_separation,
        aruco_dict
    )
    
    # Calculate image size
    img_width = markers_x * marker_length + (markers_x - 1) * marker_separation + 200
    img_height = markers_y * marker_length + (markers_y - 1) * marker_separation + 200
    
    # Generate image
    board_img = board.generateImage((img_width, img_height), marginSize=100, borderBits=1)
    
    # Save
    output_dir = Path("camera")
    output_path = output_dir / "aruco_board.png"
    cv2.imwrite(str(output_path), board_img)
    
    print("[OK] ArUco board generated!")
    print()
    print(f"Saved to: {output_path}")
    print()
    print("Board specifications:")
    print(f"  - Grid: {markers_x}x{markers_y} markers")
    print(f"  - Marker size: {marker_length} pixels (~40mm on A4)")
    print(f"  - Separation: {marker_separation} pixels (~10mm)")
    print(f"  - Dictionary: DICT_4X4_50")
    print(f"  - Image size: {img_width}x{img_height} pixels")
    print()
    print("="*70)
    print("  HOW TO USE")
    print("="*70)
    print()
    print("1. PRINT THE BOARD:")
    print("   - Print camera/aruco_board.png on A4 paper")
    print("   - Use highest quality / photo paper if possible")
    print("   - Make sure it prints at actual size (no scaling)")
    print()
    print("2. MOUNT ON FLAT SURFACE:")
    print("   - Attach to cardboard or foam board")
    print("   - Must be completely flat (no curves/bends)")
    print()
    print("3. RUN CALIBRATION:")
    print("   - python camera\\aruco_stereo_capture.py")
    print("   - Hold board above both cameras")
    print("   - Move to different positions and angles")
    print("   - Capture 20+ image pairs")
    print()
    print("="*70)
    print()
    print("Alternative: Display on tablet/monitor")
    print("  - Open aruco_board.png fullscreen")
    print("  - Hold tablet ~30cm above cameras")
    print("  - Make sure screen is bright")
    print()
    print("="*70)
    
    return str(output_path)


if __name__ == "__main__":
    generate_aruco_board()


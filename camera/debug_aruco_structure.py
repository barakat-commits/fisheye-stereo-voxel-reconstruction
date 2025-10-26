"""Quick debug to see ArUco corner structure"""
import cv2
import numpy as np

# Load one test image
img = cv2.imread("camera/aruco_calibration/left_000.png", cv2.IMREAD_GRAYSCALE)

# Detect
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
aruco_params = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

corners, ids, _ = detector.detectMarkers(img)

print(f"Number of markers detected: {len(corners) if corners else 0}")
if corners and len(corners) > 0:
    print(f"\nFirst marker:")
    print(f"  corners type: {type(corners)}")
    print(f"  corners length: {len(corners)}")
    print(f"  corners[0] type: {type(corners[0])}")
    print(f"  corners[0] shape: {corners[0].shape}")
    print(f"  corners[0]:\n{corners[0]}")

# Check board object points
board = cv2.aruco.GridBoard(
    (5, 4),
    0.04,
    0.01,
    aruco_dict
)
board_obj_points = board.getObjPoints()
print(f"\nBoard object points:")
print(f"  type: {type(board_obj_points)}")
if isinstance(board_obj_points, tuple):
    print(f"  tuple length: {len(board_obj_points)}")
    if len(board_obj_points) > 0:
        print(f"  first element type: {type(board_obj_points[0])}")
        if hasattr(board_obj_points[0], 'shape'):
            print(f"  first element shape: {board_obj_points[0].shape}")
else:
    print(f"  shape: {board_obj_points.shape}")
print(f"  First few elements: {board_obj_points[0:8]}")


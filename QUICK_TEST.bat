@echo off
echo ============================================================
echo   QUICK 3D VOXEL TEST
echo ============================================================
echo.
echo Instructions:
echo   1. Turn on room lights
echo   2. Get white paper or bright phone screen ready
echo   3. Press any key to start...
echo.
pause >nul

echo.
echo Starting camera system...
echo When "[RECORDING]" appears, wave your bright object!
echo.

python "F:\Data\Cursor Folder\camera\motion_visual_3d.py"

echo.
echo ============================================================
echo Test complete!
echo.
echo To view 3D results:
echo   python spacevoxelviewer.py data\motion_visual_3d.bin
echo.
echo ============================================================
pause




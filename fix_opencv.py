"""
Post-install script to fix OpenCV installation for headless environments.
This script replaces opencv-python with opencv-python-headless if needed.
"""
import subprocess
import sys
import os

def fix_opencv():
    """Uninstall GUI OpenCV and ensure headless version is installed."""
    try:
        # Check if opencv-python (GUI version) is installed
        import cv2
        cv2_path = cv2.__file__
        
        # If we're using the GUI version, try to switch to headless
        if 'opencv-python' in cv2_path and 'headless' not in cv2_path:
            print("Detected GUI version of OpenCV, attempting to switch to headless...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "uninstall", "-y", 
                "opencv-python", "opencv-contrib-python"
            ])
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "opencv-python-headless>=4.8.0"
            ])
            print("Successfully switched to opencv-python-headless")
    except Exception as e:
        print(f"Warning: Could not fix OpenCV installation: {e}")

if __name__ == "__main__":
    fix_opencv()


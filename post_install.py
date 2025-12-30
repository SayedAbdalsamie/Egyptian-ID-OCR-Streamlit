"""
Post-install script to fix OpenCV installation.
This script should be run after pip install to ensure opencv-python-headless is used.
"""
import subprocess
import sys

def fix_opencv():
    """Uninstall GUI OpenCV packages and install headless version."""
    try:
        # Check if opencv-python (GUI version) is installed
        try:
            import cv2
            cv2_path = cv2.__file__
            print(f"OpenCV found at: {cv2_path}")
            
            # Check if it's the GUI version
            if 'opencv-python' in cv2_path and 'headless' not in cv2_path:
                print("Detected GUI version of OpenCV, switching to headless...")
                # Uninstall GUI versions
                subprocess.check_call([
                    sys.executable, "-m", "pip", "uninstall", "-y", 
                    "opencv-python", "opencv-contrib-python"
                ])
                # Install headless version
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    "opencv-python-headless>=4.8.0"
                ])
                print("Successfully switched to opencv-python-headless")
            else:
                print("OpenCV headless version already installed or using system package")
        except ImportError:
            print("OpenCV not found, installing headless version...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "opencv-python-headless>=4.8.0"
            ])
            print("Successfully installed opencv-python-headless")
    except Exception as e:
        print(f"Warning: Could not fix OpenCV installation: {e}")
        # Don't fail the installation if this doesn't work
        pass

if __name__ == "__main__":
    fix_opencv()


"""
Wrapper for cv2 import that handles headless/GUI version issues.
This module provides a fallback mechanism for OpenCV imports in headless environments.
"""
import os
import sys

# Set environment variables before any cv2 import attempts
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '0'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['OPENCV_DISABLE_OPENCL'] = '1'
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'

# Try to add common library paths
if sys.platform == 'linux':
    common_lib_paths = [
        '/usr/lib/x86_64-linux-gnu',
        '/usr/lib',
        '/lib/x86_64-linux-gnu',
        '/lib'
    ]
    current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
    for path in common_lib_paths:
        if path not in current_ld_path:
            if current_ld_path:
                os.environ['LD_LIBRARY_PATH'] = f"{current_ld_path}:{path}"
            else:
                os.environ['LD_LIBRARY_PATH'] = path

# Try to import cv2 with error handling
try:
    import cv2
    # Verify it's working by checking a simple function
    try:
        cv2.__version__
    except Exception:
        raise ImportError("cv2 imported but not functional")
except ImportError as e:
    # If import fails, try to provide helpful error message
    error_msg = str(e)
    if 'libGL.so.1' in error_msg or 'libGL' in error_msg:
        raise ImportError(
            "OpenCV requires libGL.so.1 but it cannot be found. "
            "This usually happens when opencv-python (GUI version) is installed "
            "instead of opencv-python-headless. "
            "Please ensure opencv-python-headless is installed: "
            "pip uninstall opencv-python opencv-contrib-python && "
            "pip install opencv-python-headless"
        ) from e
    else:
        raise

# Export cv2 for use in other modules
__all__ = ['cv2']


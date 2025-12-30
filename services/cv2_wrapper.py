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
# CRITICAL: Preload libGL.so.1 using ctypes BEFORE importing cv2
# This must happen before OpenCV tries to load it
if sys.platform == 'linux':
    try:
        import ctypes
        import ctypes.util
        import glob
        
        # Try to find and load libGL.so.1 manually - be very aggressive
        # Check multiple possible locations
        libgl_paths = [
            '/usr/lib/x86_64-linux-gnu/libGL.so.1',
            '/usr/lib/x86_64-linux-gnu/libGL.so',
            '/usr/lib/libGL.so.1',
            '/usr/lib/libGL.so',
            '/lib/x86_64-linux-gnu/libGL.so.1',
            '/lib/x86_64-linux-gnu/libGL.so',
            '/lib/libGL.so.1',
            '/lib/libGL.so',
        ]
        
        # Also search for any libGL* files
        for pattern in ['/usr/lib/x86_64-linux-gnu/libGL*', '/usr/lib/libGL*', '/lib/x86_64-linux-gnu/libGL*', '/lib/libGL*']:
            libgl_paths.extend(glob.glob(pattern))
        
        libgl_loaded = False
        for lib_path in libgl_paths:
            if os.path.exists(lib_path) and os.path.isfile(lib_path):
                try:
                    # Use RTLD_GLOBAL to make it available to all modules
                    ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
                    libgl_loaded = True
                    break
                except (OSError, AttributeError):
                    continue
        
        # Also try using ctypes.util.find_library
        if not libgl_loaded:
            for lib_name in ['GL', 'libGL.so.1', 'libGL']:
                lib_path = ctypes.util.find_library(lib_name)
                if lib_path:
                    try:
                        ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
                        libgl_loaded = True
                        break
                    except (OSError, AttributeError):
                        continue
    except Exception as e:
        # If ctypes approach fails, log but continue
        # The import will fail with a better error message
        pass

# Now try to import cv2
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
            "The system packages are installed, but OpenCV still cannot find the library. "
            "This may be a library path issue or the wrong OpenCV package is installed."
        ) from e
    else:
        raise

# Export cv2 for use in other modules
__all__ = ['cv2']


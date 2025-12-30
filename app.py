import os
import sys
import uuid
import json
import subprocess
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# Try to fix OpenCV installation BEFORE importing anything that uses cv2
# This runs once per app instance
if 'OPENCV_FIX_ATTEMPTED' not in os.environ:
    try:
        # Check if we have the GUI version installed
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "opencv-python"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # GUI version is installed, try to fix it
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", "opencv-python", "opencv-contrib-python"],
                    capture_output=True,
                    timeout=30
                )
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--no-deps", "opencv-python-headless>=4.8.0"],
                    capture_output=True,
                    timeout=60
                )
                # Clear cv2 from cache if it was imported
                if 'cv2' in sys.modules:
                    del sys.modules['cv2']
            except Exception:
                pass  # If fix fails, continue and let wrapper handle it
    except Exception:
        pass  # If check fails, continue normally
    os.environ['OPENCV_FIX_ATTEMPTED'] = '1'

# Import cv2 through wrapper - this must happen before any service imports
# The wrapper will handle environment setup and provide better error messages
try:
    from services.cv2_wrapper import cv2
except ImportError as e:
    # If cv2 import fails, show a helpful error message
    error_msg = str(e)
    st.error("""
    ## ⚠️ OpenCV Import Error
    
    The application cannot import OpenCV. This is a known issue with Streamlit Cloud deployments.
    
    **The Problem:**
    - `paddleocr`/`paddlepaddle` installs `opencv-python` (GUI version) which requires `libGL.so.1`
    - Even though system packages are installed, OpenCV cannot find the library
    - The automatic fix attempt may have failed due to permission restrictions
    
    **Error Details:**
    """)
    st.code(error_msg, language='text')
    st.warning("""
    **Workaround Options:**
    1. This may require manual intervention in the Streamlit Cloud environment
    2. Consider using a different deployment platform that allows post-install scripts
    3. Or use a different OCR library that doesn't have this dependency conflict
    """)
    st.stop()

from services.detection_service import DetectionService
from services.crop_service import CropService
from services.ocr_service import OCRService
from services.utils import ensure_directories

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Egyptian ID OCR",
    page_icon="🆔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'detection_service' not in st.session_state:
    st.session_state.detection_service = None
if 'crop_service' not in st.session_state:
    st.session_state.crop_service = None
if 'ocr_service' not in st.session_state:
    st.session_state.ocr_service = None
if 'uploaded_image_path' not in st.session_state:
    st.session_state.uploaded_image_path = None
if 'detections' not in st.session_state:
    st.session_state.detections = None
if 'crop_map' not in st.session_state:
    st.session_state.crop_map = None
if 'ocr_result' not in st.session_state:
    st.session_state.ocr_result = None

# Setup directories
UPLOAD_FOLDER = os.path.join("static", "uploads")
CROPS_FOLDER = os.path.join("static", "crops")
ensure_directories([UPLOAD_FOLDER, CROPS_FOLDER])

# Initialize services (lazy loading)
def get_detection_service():
    if st.session_state.detection_service is None:
        with st.spinner("Loading detection model..."):
            try:
                st.session_state.detection_service = DetectionService()
            except Exception as e:
                st.error(f"Failed to load detection model: {str(e)}")
                return None
    return st.session_state.detection_service

def get_crop_service():
    if st.session_state.crop_service is None:
        st.session_state.crop_service = CropService(crops_dir=CROPS_FOLDER)
    return st.session_state.crop_service

def get_ocr_service():
    if st.session_state.ocr_service is None:
        st.session_state.ocr_service = OCRService()
    return st.session_state.ocr_service

def process_image(image_path: str):
    """Process the uploaded image through detection, cropping, and OCR."""
    try:
        # Step 1: Detection
        with st.spinner("🔍 Detecting regions..."):
            detection_service = get_detection_service()
            if detection_service is None:
                st.error("Detection service not available")
                return
            
            detections = detection_service.detect(image_path)
            st.session_state.detections = detections
            st.success(f"✅ Detected {len(detections)} regions")
        
        # Step 2: Cropping
        with st.spinner("✂️ Cropping regions..."):
            crop_service = get_crop_service()
            crop_map = crop_service.crop_regions(image_path, detections)
            st.session_state.crop_map = crop_map
            st.success(f"✅ Cropped {len(crop_map)} regions")
        
        # Step 3: OCR
        with st.spinner("📝 Extracting text..."):
            ocr_service = get_ocr_service()
            
            # Prepare image list in order
            image_order = ["Add1", "Add2", "Name1", "Name2", "Num1", "Num2"]
            image_list = [crop_map[label] for label in image_order if label in crop_map]
            
            if len(image_list) == 6:
                ocr_result = ocr_service.run_ocr(image_list)
                st.session_state.ocr_result = ocr_result
                st.success("✅ Text extraction completed")
            else:
                st.error(f"Expected 6 crops, got {len(image_list)}")
                return
        
        # Refresh to show results
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error processing image: {str(e)}")
        st.exception(e)

def display_results():
    """Display OCR results in a formatted way."""
    ocr_result = st.session_state.ocr_result
    crop_map = st.session_state.crop_map
    
    if not ocr_result:
        st.warning("No results to display")
        return
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📄 Extracted Data", "🖼️ Cropped Regions", "📊 Raw Data"])
    
    with tab1:
        st.subheader("Extracted Information")
        
        # Field labels mapping
        field_labels = {
            "Add1": "Address Line 1 (Arabic)",
            "Add2": "Address Line 2 (Arabic)",
            "Name1": "Name Line 1 (Arabic)",
            "Name2": "Name Line 2 (Arabic)",
            "Num1": "National ID Number",
            "Num2": "ID Card Number",
            "BD": "Birth Date"
        }
        
        # Display results in columns
        col1, col2 = st.columns(2)
        
        with col1:
            for field in ["Name1", "Name2", "Add1", "Add2"]:
                if field in ocr_result:
                    value = ocr_result[field]
                    if isinstance(value, list):
                        text = " ".join([str(v) for v in value if v])
                    else:
                        text = str(value) if value else ""
                    
                    st.markdown(f"**{field_labels[field]}:**")
                    st.info(text if text else "Not detected")
                    st.markdown("---")
        
        with col2:
            for field in ["Num1", "Num2", "BD"]:
                if field in ocr_result:
                    value = ocr_result[field]
                    if isinstance(value, list):
                        text = " ".join([str(v) for v in value if v])
                    else:
                        text = str(value) if value else ""
                    
                    st.markdown(f"**{field_labels[field]}:**")
                    st.info(text if text else "Not detected")
                    st.markdown("---")
        
        # Download results as JSON
        results_json = json.dumps(ocr_result, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Download Results as JSON",
            data=results_json,
            file_name="ocr_results.json",
            mime="application/json"
        )
    
    with tab2:
        st.subheader("Cropped Regions")
        
        if crop_map:
            # Display crops in a grid
            crops_per_row = 3
            crop_items = list(crop_map.items())
            
            for i in range(0, len(crop_items), crops_per_row):
                cols = st.columns(crops_per_row)
                for j, (label, path) in enumerate(crop_items[i:i+crops_per_row]):
                    with cols[j]:
                        if os.path.exists(path):
                            crop_img = Image.open(path)
                            st.image(crop_img, caption=label, use_container_width=True)
                        else:
                            st.warning(f"Image not found: {label}")
        else:
            st.info("No cropped regions available")
    
    with tab3:
        st.subheader("Raw OCR Data")
        st.json(ocr_result)
        
        if crop_map:
            st.subheader("Crop Map")
            st.json(crop_map)

# Main title
st.title("🆔 Egyptian ID Card OCR")
st.markdown("Upload an Egyptian ID card image to extract information using AI-powered OCR")

# Sidebar
with st.sidebar:
    st.header("Settings")
    st.markdown("---")
    
    # Model settings
    st.subheader("Model Settings")
    detection_threshold = st.slider(
        "Detection Threshold",
        min_value=0.1,
        max_value=1.0,
        value=0.25,
        step=0.05,
        help="Minimum confidence score for detection"
    )
    os.environ["DETECTION_SCORE_THRESHOLD"] = str(detection_threshold)
    
    crop_max_size = st.slider(
        "Max Crop Size",
        min_value=400,
        max_value=1200,
        value=800,
        step=100,
        help="Maximum dimension for cropped images"
    )
    os.environ["CROP_MAX_SIZE"] = str(crop_max_size)
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This application uses:
    - **Faster R-CNN** for region detection
    - **PaddleOCR** for text extraction
    - **Arabic OCR** for most fields
    - **English OCR** for Num2 field
    """)

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📤 Upload Image")
    uploaded_file = st.file_uploader(
        "Choose an Egyptian ID card image",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a clear image of an Egyptian ID card"
    )
    
    if uploaded_file is not None:
        # Save uploaded image
        file_ext = os.path.splitext(uploaded_file.name)[1]
        unique_name = f"{uuid.uuid4().hex}{file_ext}"
        upload_path = os.path.join(UPLOAD_FOLDER, unique_name)
        
        # Save file
        with open(upload_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.session_state.uploaded_image_path = upload_path
        
        # Display uploaded image
        image = Image.open(upload_path)
        st.image(image, caption="Uploaded ID Card", use_container_width=True)
        
        # Process button
        if st.button("🔍 Process ID Card", type="primary", use_container_width=True):
            process_image(upload_path)
    
    elif st.session_state.uploaded_image_path and os.path.exists(st.session_state.uploaded_image_path):
        # Display previously uploaded image
        image = Image.open(st.session_state.uploaded_image_path)
        st.image(image, caption="Uploaded ID Card", use_container_width=True)
        
        if st.button("🔍 Process ID Card", type="primary", use_container_width=True):
            process_image(st.session_state.uploaded_image_path)

with col2:
    st.header("📋 Results")
    
    if st.session_state.ocr_result:
        display_results()
    else:
        st.info("Upload an image and click 'Process ID Card' to see results here")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>Egyptian ID OCR - Powered by Faster R-CNN & PaddleOCR</p>
    </div>
    """,
    unsafe_allow_html=True
)


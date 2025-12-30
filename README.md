# Egyptian ID OCR - Streamlit Version

A Streamlit-based web application for extracting information from Egyptian ID cards using AI-powered OCR.

## Features

- **Easy-to-use Web Interface**: Simple drag-and-drop image upload
- **Automatic Region Detection**: Uses Faster R-CNN to detect ID card regions
- **Smart Cropping**: Automatically crops detected regions
- **Multi-language OCR**: 
  - Arabic OCR for most fields (Add1, Add2, Name1, Name2, Num1)
  - English OCR for Num2 field
- **Birth Date Extraction**: Automatically derives birth date from National ID number
- **Visual Results**: View extracted data, cropped regions, and raw results

## Project Structure

```
Egyptian-ID-OCR-Streamlit/
├── app.py                    # Main Streamlit application
├── models/
│   ├── model_loader.py      # Faster R-CNN model loader
│   └── fasterrcnn_custom_epoch_10.pth  # Model weights (downloaded automatically)
├── services/
│   ├── detection_service.py  # Faster R-CNN detection
│   ├── crop_service.py       # OpenCV cropping with enhancement
│   ├── ocr_service.py        # PaddleOCR with language selection
│   └── utils.py              # Date derivation and numeral conversion
├── static/
│   ├── uploads/              # Uploaded images
│   └── crops/                # Cropped regions
├── requirements.txt
└── README.md
```

## Setup

### Prerequisites

- Python 3.10+
- pip

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd Egyptian-ID-OCR-Streamlit
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional: Create a `.env` file for configuration:**
   ```env
   MODEL_WEIGHTS_PATH=models/fasterrcnn_custom_epoch_10.pth
   DETECTION_SCORE_THRESHOLD=0.25
   CROP_MAX_SIZE=800
   ```

## Running the Application

### Start the Streamlit app:

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Usage

1. **Upload Image**: Click "Browse files" or drag and drop an Egyptian ID card image
2. **Process**: Click the "Process ID Card" button
3. **View Results**: 
   - **Extracted Data**: See all extracted information in a formatted view
   - **Cropped Regions**: View the individual cropped regions
   - **Raw Data**: See the raw JSON output

## Output Format

The application extracts the following fields:

- **Add1**: Address Line 1 (Arabic)
- **Add2**: Address Line 2 (Arabic)
- **Name1**: Name Line 1 (Arabic)
- **Name2**: Name Line 2 (Arabic)
- **Num1**: National ID Number (14 digits)
- **Num2**: ID Card Number
- **BD**: Birth Date (automatically derived from Num1, format: DD/MM/YYYY)

### Example Output:

```json
{
  "Add1": ["القاهرة", "مدينة نصر"],
  "Add2": ["شارع", "التحرير"],
  "Name1": ["محمد", "أحمد"],
  "Name2": ["علي", "حسن"],
  "Num1": ["30123456789012"],
  "Num2": ["123456"],
  "BD": ["01/01/2001"]
}
```

## Model Information

- **Detection Model**: Faster R-CNN (ResNet-50 FPN)
- **Model Source**: Automatically downloaded from Hugging Face Hub
  - Repository: `Sayedabdalsamie/Area_detection_for_ID_OCR`
  - File: `fasterrcnn_custom_epoch_10.pth`
- **OCR Engine**: PaddleOCR
  - Arabic model for most fields
  - English model for Num2 field

## Configuration

You can adjust settings in the sidebar:

- **Detection Threshold**: Minimum confidence score for region detection (0.1 - 1.0)
- **Max Crop Size**: Maximum dimension for cropped images (400 - 1200 pixels)

## Notes

- **BD (Birth Date)** is automatically derived from Num1 using Egyptian National ID format:
  - First digit: century (2 = 1900s, 3 = 2000s)
  - Next 2 digits: year
  - Next 2 digits: month
  - Next 2 digits: day
- **Add2 numerals** are converted to Eastern Arabic format
- **Num2** uses English OCR, all other classes use Arabic OCR
- Cropped images are automatically resized for optimal OCR accuracy

## Troubleshooting

### Model Download Issues

If the model fails to download automatically:
1. Check your internet connection
2. Ensure you have write permissions in the `models/` directory
3. You can manually download the model from Hugging Face and place it in `models/`

### Memory Issues

If you encounter memory errors:
- Reduce the `CROP_MAX_SIZE` setting
- Close other applications using GPU/CPU resources
- Process images one at a time

### OCR Errors

If OCR fails:
- Ensure the uploaded image is clear and well-lit
- Check that the ID card is properly oriented
- Try adjusting the detection threshold

## Differences from Flask Version

This Streamlit version provides:
- **Interactive Web UI**: No need for a separate frontend
- **Real-time Processing**: See progress as the image is processed
- **Visual Results**: View cropped regions alongside extracted text
- **Easy Configuration**: Adjust settings via sidebar sliders
- **Simplified Deployment**: Single command to run the entire application

## Deployment to Streamlit Cloud

This application is configured for deployment on Streamlit Cloud:

1. **Push your code to GitHub** (already done)
2. **Go to [share.streamlit.io](https://share.streamlit.io)**
3. **Sign in with GitHub**
4. **Click "New app"**
5. **Select your repository**: `SayedAbdalsamie/Egyptian-ID-OCR-Streamlit`
6. **Set the main file path**: `app.py`
7. **Click "Deploy"**

The app will automatically:
- Use Python 3.11 (specified in `runtime.txt`)
- Install dependencies from `requirements.txt`
- Install system packages from `packages.txt` (if needed)

**Note**: The first deployment may take several minutes as it downloads the Faster R-CNN model from Hugging Face.

## Security

⚠️ **Important**: This application is for demonstration purposes. Before production use:
- Add authentication
- Implement rate limiting
- Add input validation
- Secure file uploads
- Add error logging

## License

Same as the original Flask version.

## Support

For issues or questions, please refer to the original project documentation or create an issue in the repository.


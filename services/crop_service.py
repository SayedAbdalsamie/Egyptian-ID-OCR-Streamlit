import os
from typing import Dict, Tuple

import cv2


Box = Tuple[int, int, int, int]


class CropService:
    """Crops detected regions and saves them to disk."""

    def __init__(self, crops_dir: str) -> None:
        self.crops_dir = crops_dir
        os.makedirs(self.crops_dir, exist_ok=True)

    def crop_regions(
        self, image_path: str, detections: Dict[str, Box]
    ) -> Dict[str, str]:
        """
        Given an image path and a mapping label->box, writes crops to disk.
        Returns mapping label->crop_file_path.
        Excludes BD class as per requirements.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise RuntimeError("Failed to read image for cropping")

        crop_map: Dict[str, str] = {}
        max_size = int(
            os.environ.get("CROP_MAX_SIZE", "800")
        )  # Max dimension in pixels - increased for better OCR quality

        for label, (x1, y1, x2, y2) in detections.items():
            # Skip BD class
            if label == "BD":
                continue

            x1c, y1c = max(0, x1), max(0, y1)
            x2c, y2c = max(x1c + 1, x2), max(y1c + 1, y2)
            
            # Validate crop dimensions
            if x2c <= x1c or y2c <= y1c:
                print(f"Warning: Invalid crop dimensions for {label}: ({x1c}, {y1c}, {x2c}, {y2c}), skipping")
                continue
            
            crop = img[y1c:y2c, x1c:x2c]
            
            # Validate crop is not empty
            if crop.size == 0 or crop.shape[0] == 0 or crop.shape[1] == 0:
                print(f"Warning: Empty crop for {label}, skipping")
                continue

            # Use original image - no grayscale conversion or enhancement
            # Pass original BGR image directly

            # For Num1, double the size for better OCR accuracy
            h, w = crop.shape[:2]
            if label == "Num1":
                # Double the dimensions
                new_h = h * 2
                new_w = w * 2
                crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

            # Resize crop if too large, maintaining aspect ratio with high-quality interpolation
            h, w = crop.shape[:2]
            if h > max_size or w > max_size:
                if h > w:
                    new_h = max_size
                    new_w = int(w * (max_size / h))
                else:
                    new_w = max_size
                    new_h = int(h * (max_size / w))
                # Use INTER_LANCZOS4 for better quality when downscaling
                crop = cv2.resize(
                    crop, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4
                )
            # Ensure minimum size for readability and OCR (PaddleOCR needs at least 32x32)
            elif h < 32 or w < 32:
                min_size = 64  # Use 64 as minimum to ensure OCR works reliably
                scale = max(min_size / h, min_size / w)
                new_h = int(h * scale)
                new_w = int(w * scale)
                crop = cv2.resize(
                    crop, (new_w, new_h), interpolation=cv2.INTER_CUBIC
                )

            out_path = os.path.join(self.crops_dir, f"{label}.png")
            try:
                # Use moderate compression to balance file size and quality
                cv2.imwrite(out_path, crop, [cv2.IMWRITE_PNG_COMPRESSION, 3])
            except Exception:
                # If write fails, skip this crop but continue others
                continue
            crop_map[label] = out_path

        return crop_map


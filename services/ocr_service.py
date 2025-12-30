from paddleocr import PaddleOCR
import os

# Use the cv2 wrapper that handles headless/GUI version issues
from services.cv2_wrapper import cv2

import numpy as np
from PIL import Image
from services.utils import derive_birthdate_from_national_id, to_english_numerals


class OCRService:

    def __init__(self):
        # Lazy loading - don't initialize OCR models until first use
        # This prevents memory access violations at startup
        self._ocr_ar = None
        self._ocr_en = None
        self._initialization_error = None

    @property
    def ocr_ar(self):
        """Lazy initialization of Arabic OCR model."""
        if self._ocr_ar is None:
            try:
                self._ocr_ar = PaddleOCR(
                    lang="ar",
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                )
            except Exception as e:
                self._initialization_error = (
                    f"Failed to initialize Arabic OCR: {str(e)}"
                )
                raise RuntimeError(self._initialization_error)
        return self._ocr_ar

    @property
    def ocr_en(self):
        """Lazy initialization of English OCR model."""
        if self._ocr_en is None:
            try:
                self._ocr_en = PaddleOCR(
                    lang="en",
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                )
            except Exception as e:
                self._initialization_error = (
                    f"Failed to initialize English OCR: {str(e)}"
                )
                raise RuntimeError(self._initialization_error)
        return self._ocr_en

    def _validate_image(self, image_path: str) -> bool:
        """
        Simple validation - just check if image exists and can be read.
        Returns True if valid, False otherwise.
        """
        if not image_path or not isinstance(image_path, str):
            return False

        if not os.path.exists(image_path):
            return False

        # Check file size
        try:
            file_size = os.path.getsize(image_path)
            if file_size == 0:
                return False
        except Exception:
            return False

        # Try to read with PIL to verify it's a valid image
        try:
            img = Image.open(image_path)
            width, height = img.size
            img.close()
            if width == 0 or height == 0:
                return False
            return True
        except Exception:
            return False

    def run_ocr(self, image_list):
        """
        image_list must be a list of 6 items in this order:
        [Add1, Add2, Name1, Name2, Num1, Num2]
        """
        results = {}

        # Process each image with error handling
        # Use model names instead of model instances for lazy loading
        ocr_tasks = [
            ("Add1", "ar", image_list[0]),
            ("Add2", "ar", image_list[1]),
            ("Name1", "ar", image_list[2]),
            ("Name2", "ar", image_list[3]),
            ("Num1", "ar", image_list[4]),
            ("Num2", "en", image_list[5]),
        ]

        for label, ocr_model_name, image_path in ocr_tasks:
            validated_path = None
            try:
                # Get the appropriate OCR model (lazy loading)
                try:
                    if ocr_model_name == "ar":
                        ocr_model = self.ocr_ar
                    else:
                        ocr_model = self.ocr_en
                except RuntimeError as init_error:
                    print(
                        f"OCR model initialization failed for {label}: {str(init_error)}"
                    )
                    results[label] = []
                    continue

                # Simple validation - just check if file exists and is readable
                if not self._validate_image(image_path):
                    print(f"Image validation failed for {label}: {image_path}")
                    results[label] = []
                    continue

                # Use original image path directly - PaddleOCR handles image formats well
                # Skip preprocessing to avoid tensor memory issues
                try:
                    result = ocr_model.predict(input=image_path)
                    results[label] = result
                except Exception as ocr_error:
                    error_msg = str(ocr_error)
                    # Check if it's a tensor memory error
                    if (
                        "Tensor holds no memory" in error_msg
                        or "mutable_data" in error_msg
                    ):
                        print(
                            f"Tensor memory error for {label} - image may be corrupted or incompatible: {image_path}"
                        )
                    else:
                        print(f"OCR error for {label} ({image_path}): {error_msg}")
                    results[label] = []

            except (ValueError, FileNotFoundError) as validation_error:
                print(
                    f"Image validation error for {label} ({image_path}): {str(validation_error)}"
                )
                results[label] = []
            except Exception as e:
                print(f"Unexpected error for {label} ({image_path}): {str(e)}")
                results[label] = []

        # Extract rec_texts safely
        def get_text(result, reverse_order=False):
            if isinstance(result, list) and len(result) > 0:
                first = result[0]
                # OCRResult is dict-like, access rec_texts as a key
                try:
                    # Use dict-like access (get method or dict access)
                    if hasattr(first, "get"):
                        rec_texts = first.get("rec_texts", [])
                    elif hasattr(first, "__getitem__"):
                        rec_texts = first["rec_texts"]
                    else:
                        rec_texts = []

                    # Ensure it's a list
                    if rec_texts:
                        if not isinstance(rec_texts, list):
                            rec_texts = [rec_texts]
                        
                        # For Arabic text, reverse the order since OCR detects LTR but Arabic reads RTL
                        if reverse_order and len(rec_texts) > 1:
                            rec_texts = list(reversed(rec_texts))
                        
                        return rec_texts
                except (KeyError, AttributeError, TypeError):
                    pass
            return []

        # Extract text from results
        # Reverse order for Arabic fields (Add1, Add2, Name1, Name2, Num1) since OCR detects LTR but Arabic reads RTL
        # Keep original order for Num2 (English)
        ocr_result = {
            "Add1": get_text(results.get("Add1", []), reverse_order=True),
            "Add2": get_text(results.get("Add2", []), reverse_order=True),
            "Name1": get_text(results.get("Name1", []), reverse_order=True),
            "Name2": get_text(results.get("Name2", []), reverse_order=True),
            "Num1": get_text(results.get("Num1", []), reverse_order=True),
            "Num2": get_text(results.get("Num2", []), reverse_order=False),  # English, keep original order
            "BD": []  # Initialize BD, will be populated below
        }
        
        # Derive BD (Birth Date) from Num1 using Egyptian ID format
        # Num1 is a list, get the first element (the extracted number)
        num1_text = ""
        if ocr_result.get("Num1") and len(ocr_result["Num1"]) > 0:
            # Get the first extracted text from Num1 (may contain Eastern Arabic numerals)
            num1_text = str(ocr_result["Num1"][0]).strip()
            # Convert Eastern Arabic numerals to English numerals for BD extraction
            num1_english = to_english_numerals(num1_text)
            # Remove any non-digit characters (in case OCR includes spaces or other chars)
            num1_digits = ''.join(filter(str.isdigit, num1_english))
            # Derive birth date from the first 7 digits (now in English numerals)
            if len(num1_digits) >= 7:
                bd = derive_birthdate_from_national_id(num1_digits)
                ocr_result["BD"] = [bd] if bd else []
            else:
                ocr_result["BD"] = []
        else:
            ocr_result["BD"] = []
        
        return ocr_result

    def _run_single_ocr(self, image_path: str, lang: str = "ar") -> str:
        """Run OCR on a single image and return text as a string."""
        try:
            # Get the appropriate OCR model (lazy loading)
            if lang == "en":
                ocr_model = self.ocr_en
            else:
                ocr_model = self.ocr_ar
            
            # Validate image
            if not self._validate_image(image_path):
                return ""
            
            # Run OCR
            result = ocr_model.predict(input=image_path)
            if not result:
                return ""
            
            texts = []
            # Extract text from result
            for res in result:
                if isinstance(res, dict):
                    rec_texts = res.get("rec_texts", [])
                elif hasattr(res, "rec_texts"):
                    rec_texts = res.rec_texts
                elif hasattr(res, "get"):
                    rec_texts = res.get("rec_texts", [])
                else:
                    continue
                
                if rec_texts:
                    if isinstance(rec_texts, list):
                        texts.extend([str(t) for t in rec_texts if t])
                    else:
                        texts.append(str(rec_texts))
            
            # Return merged text
            return " ".join(texts).strip()
        except Exception as e:
            print(f"OCR Error for {image_path}: {e}")
            return ""

    def process_crops(self, crop_map):
        """
        crop_map = {
            "Add1": "path.jpg",
            "Add2": "path.jpg",
            "Name1": "path.jpg",
            "Name2": "path.jpg",
            "Num1": "path.jpg",
            "Num2": "path.jpg",
        }
        """

        out = {"Add1": "", "Add2": "", "Name1": "", "Name2": "", "Num1": "", "Num2": "", "BD": ""}

        for class_name, image_path in crop_map.items():
            if not os.path.exists(image_path):
                continue

            # Num2 uses English OCR
            if class_name == "Num2":
                out[class_name] = self._run_single_ocr(image_path, lang="en")
            else:
                out[class_name] = self._run_single_ocr(image_path, lang="ar")

        # Derive BD from Num1 using Egyptian ID format
        num1_text = out.get("Num1", "")
        if num1_text:
            # Convert Eastern Arabic numerals to English numerals for BD extraction
            num1_english = to_english_numerals(str(num1_text))
            # Remove non-digit characters
            num1_digits = ''.join(filter(str.isdigit, num1_english))
            if len(num1_digits) >= 7:
                bd = derive_birthdate_from_national_id(num1_digits)
                out["BD"] = bd if bd else ""
            else:
                out["BD"] = ""
        else:
            out["BD"] = ""

        return out


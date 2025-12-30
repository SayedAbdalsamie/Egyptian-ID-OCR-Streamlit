import os
from typing import Dict, Tuple

import torch
import torchvision.transforms as T
from PIL import Image

from models.model_loader import ModelLoader

# Class mapping
CUSTOM_CLASSES: Dict[int, str] = {
    1: "Add1",
    2: "Add2",
    3: "BD",
    4: "Name1",
    5: "Name2",
    6: "Num1",
    7: "Num2",
}

Box = Tuple[int, int, int, int]  # x1, y1, x2, y2


class DetectionService:
    """Handles detection via Faster R-CNN."""

    def __init__(self) -> None:
        # Will raise if model can't be loaded; we want strict behavior
        self.model = ModelLoader(num_classes=len(CUSTOM_CLASSES) + 1).load()

    def detect(self, image_path: str) -> Dict[str, Box]:
        """
        Returns a mapping from label to bounding box.
        """
        self.model.eval()
        img = Image.open(image_path).convert("RGB")
        orig_width, orig_height = img.size
        
        # Resize image to 293x293 before detection (as required by the model)
        img_resized = img.resize((293, 293), Image.Resampling.LANCZOS)
        
        transform = T.Compose([T.ToTensor()])
        tensor = transform(img_resized)

        with torch.no_grad():
            outputs = self.model([tensor])[0]

        boxes = outputs.get("boxes")
        labels = outputs.get("labels")
        scores = outputs.get("scores")

        result: Dict[str, Box] = {}
        score_thresh = float(os.environ.get("DETECTION_SCORE_THRESHOLD", "0.25"))
        scale_x = orig_width / 293.0
        scale_y = orig_height / 293.0

        for b, l, s in zip(boxes, labels, scores):
            if float(s) < score_thresh:
                continue
            class_id = int(l)
            label = CUSTOM_CLASSES.get(class_id)
            if not label:
                continue

            x1, y1, x2, y2 = [int(v) for v in b.tolist()]
            x1 = int(x1 * scale_x)
            y1 = int(y1 * scale_y)
            x2 = int(x2 * scale_x)
            y2 = int(y2 * scale_y)

            # Add padding
            pad_x = max(2, int(0.01 * (x2 - x1)))
            pad_y = max(2, int(0.01 * (y2 - y1)))
            x1 = max(0, x1 - pad_x)
            y1 = max(0, y1 - pad_y)
            x2 = min(orig_width, x2 + pad_x)
            y2 = min(orig_height, y2 + pad_y)

            result[label] = (x1, y1, x2, y2)

        if not result:
            raise ValueError("No detections above threshold")

        return result


import os
from typing import Any

import torch
from huggingface_hub import hf_hub_download


class ModelLoader:
    """
    Loads a Faster R-CNN model for detection.

    Resolution priority for weights:
    1. Explicit local path via MODEL_WEIGHTS_PATH (if file exists)
    2. Local file next to this module: fasterrcnn_custom_epoch_10.pth
    3. Download from Hugging Face Hub (defaults to
       'Sayedabdalsamie/Area_detection_for_ID_OCR', overridable via env).
    """

    def __init__(self, num_classes: int) -> None:
        self.num_classes = num_classes

    def _resolve_weights_path(self) -> str:
        """Return a local path to the weights, downloading from HF if needed."""
        # 1) Explicit path via env
        env_path = os.environ.get("MODEL_WEIGHTS_PATH", "").strip()
        if env_path and os.path.exists(env_path):
            return env_path

        # 2) Default local file next to this module
        models_dir = os.path.dirname(__file__)
        default_local = os.path.join(models_dir, "fasterrcnn_custom_epoch_10.pth")
        if os.path.exists(default_local):
            return default_local

        # 3) Download from Hugging Face Hub
        repo_id = os.environ.get(
            "HF_MODEL_REPO", "Sayedabdalsamie/Area_detection_for_ID_OCR"
        )
        filename = os.environ.get(
            "HF_MODEL_FILENAME", "fasterrcnn_custom_epoch_10.pth"
        )

        try:
            weights_path = hf_hub_download(repo_id=repo_id, filename=filename)
        except Exception as e:
            raise RuntimeError(
                f"Could not download model weights from Hugging Face "
                f"({repo_id}/{filename}): {e}"
            )

        return weights_path

    def load(self) -> Any:  # returns Torch model or raises
        weights_path = self._resolve_weights_path()

        try:
            from torchvision.models.detection import fasterrcnn_resnet50_fpn
        except Exception:
            raise RuntimeError(
                "torchvision is not available; cannot load detector model"
            )

        # Create model without downloading weights; ensure proper classification head shape
        def build_model(num_classes: int) -> Any:
            try:
                return fasterrcnn_resnet50_fpn(
                    weights=None, weights_backbone=None, num_classes=num_classes
                )
            except TypeError:
                return fasterrcnn_resnet50_fpn(weights=None, num_classes=num_classes)

        model = build_model(self.num_classes)

        # Require a valid checkpoint
        if not weights_path or not os.path.exists(weights_path):
            raise RuntimeError(
                "Detector weights file does not exist. Tried: "
                f"{weights_path}"
            )

        try:
            state = torch.load(weights_path, map_location="cpu")
            try:
                model.load_state_dict(state, strict=False)
            except RuntimeError as e:
                # Attempt to infer num_classes from checkpoint head and rebuild model
                cls_key = "roi_heads.box_predictor.cls_score.weight"
                head_weight = state.get(cls_key)
                if head_weight is None:
                    raise RuntimeError(f"Failed to load model weights: {e}")
                inferred_num_classes = int(head_weight.shape[0])
                model = build_model(inferred_num_classes)
                model.load_state_dict(state, strict=False)
        except Exception as e:
            raise RuntimeError(f"Failed to load model weights: {e}")

        model.eval()
        return model


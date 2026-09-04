"""
Loads a trained disease model checkpoint (if present) and serves
predictions on PIL images. Never fabricates a prediction: if no trained
checkpoint exists, `is_available()` returns False and `predict()` raises
ModelNotAvailableError, which the API layer turns into a clear 503.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelNotAvailableError(Exception):
    pass


class DiseaseInferenceService:
    def __init__(self):
        self._model = None
        self._class_to_idx: Optional[Dict[str, int]] = None
        self._idx_to_class: Optional[Dict[int, str]] = None
        self._metadata: Optional[dict] = None
        self._crop_disease_lookup: Optional[Dict[str, Tuple[str, str]]] = None
        self._load_attempted = False
        self._transform = None
        self._device = None

    @property
    def artifact_dir(self) -> Path:
        return settings.model_artifact_root_path / "disease"

    def is_available(self) -> bool:
        self._ensure_loaded()
        return self._model is not None

    def metadata(self) -> Optional[dict]:
        self._ensure_loaded()
        return self._metadata

    def _load_class_disease_lookup(self):
        """Builds final_class -> (canonical_crop, canonical_disease) from
        the authoritative class mapping CSV, so predictions can surface
        crop/disease metadata without inventing anything not present in
        the dataset."""
        import pandas as pd
        mapping_path = settings.disease_dataset_root_path / "disease_class_mapping.csv"
        if not mapping_path.exists():
            self._crop_disease_lookup = {}
            return
        df = pd.read_csv(mapping_path)
        lookup = {}
        for _, row in df.drop_duplicates(subset=["final_class"]).iterrows():
            lookup[row["final_class"]] = (row["canonical_crop"], row["canonical_disease"])
        self._crop_disease_lookup = lookup

    def _ensure_loaded(self):
        if self._load_attempted:
            return
        self._load_attempted = True

        model_path = self.artifact_dir / "best_model.pt"
        class_mapping_path = self.artifact_dir / "class_mapping.json"
        metadata_path = self.artifact_dir / "metadata.json"

        if not (model_path.exists() and class_mapping_path.exists() and metadata_path.exists()):
            logger.warning(
                "Disease model artifacts not found under %s. "
                "The disease prediction endpoint will report the model as unavailable "
                "until training has been completed (see app.ml.disease.train).",
                self.artifact_dir,
            )
            return

        try:
            import torch
            from app.ml.disease.model import build_model, get_device, get_transforms
        except ImportError:
            logger.warning("PyTorch not installed; disease inference cannot be loaded.")
            return

        with open(class_mapping_path) as f:
            mapping = json.load(f)
        self._idx_to_class = {int(k): v for k, v in mapping["idx_to_class"].items()}
        self._class_to_idx = mapping["class_to_idx"]

        with open(metadata_path) as f:
            self._metadata = json.load(f)

        self._device = get_device()
        architecture = self._metadata.get("hyperparameters", {}).get("architecture", "mobilenet_v3_large")
        image_size = self._metadata.get("hyperparameters", {}).get("image_size", settings.DISEASE_IMAGE_SIZE)

        model = build_model(num_classes=len(self._idx_to_class), architecture=architecture, pretrained=False)
        model.load_state_dict(torch.load(model_path, map_location=self._device))
        model.to(self._device)
        model.eval()
        self._model = model
        self._transform = get_transforms(image_size, train=False)

        self._load_class_disease_lookup()
        logger.info("Loaded disease model (%s) with %d classes", architecture, len(self._idx_to_class))

    def predict(self, image_bytes: bytes, top_k: int = 3) -> List[dict]:
        self._ensure_loaded()
        if self._model is None:
            raise ModelNotAvailableError(
                "Disease detection model is not trained yet. See README for training instructions; "
                "training requires the raw image dataset which was not present in this metadata-only package."
            )
        import torch
        from PIL import Image, UnidentifiedImageError

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except UnidentifiedImageError as exc:
            raise ValueError("Uploaded file is not a readable image") from exc

        tensor = self._transform(image).unsqueeze(0).to(self._device)
        with torch.no_grad():
            logits = self._model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0)

        top_k = min(top_k, probs.shape[0])
        top_probs, top_indices = torch.topk(probs, top_k)

        results = []
        for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
            final_class = self._idx_to_class[idx]
            crop, disease = (self._crop_disease_lookup or {}).get(final_class, (None, None))
            results.append({
                "class": final_class,
                "confidence": round(float(prob), 6),
                "canonical_crop": crop,
                "canonical_disease": disease,
            })
        return results


disease_inference_service = DiseaseInferenceService()

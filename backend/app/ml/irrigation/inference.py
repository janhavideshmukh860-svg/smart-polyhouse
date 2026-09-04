"""
Loads trained irrigation model artifacts from disk and exposes simple
predict() functions. This module never trains a model - it only loads
what app.ml.irrigation.train has already produced under
MODEL_ARTIFACT_ROOT/irrigation/.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import joblib
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger
from app.ml.irrigation.forecasting import HORIZONS

logger = get_logger(__name__)


class ModelNotAvailableError(Exception):
    """Raised when a requested model's artifacts have not been trained yet."""


class CalibrationInferenceService:
    def __init__(self):
        self._model = None
        self._scaler = None
        self._feature_list: Optional[list] = None
        self._metadata: Optional[dict] = None
        self._load_attempted = False

    @property
    def artifact_dir(self) -> Path:
        return settings.model_artifact_root_path / "irrigation" / "calibration"

    def is_available(self) -> bool:
        self._ensure_loaded()
        return self._model is not None

    def _ensure_loaded(self):
        if self._load_attempted:
            return
        self._load_attempted = True
        model_path = self.artifact_dir / "model.joblib"
        scaler_path = self.artifact_dir / "scaler.joblib"
        features_path = self.artifact_dir / "feature_list.json"
        metadata_path = self.artifact_dir / "metadata.json"

        if not (model_path.exists() and scaler_path.exists() and features_path.exists()):
            logger.warning("Calibration model artifacts not found under %s", self.artifact_dir)
            return

        self._model = joblib.load(model_path)
        self._scaler = joblib.load(scaler_path)
        with open(features_path) as f:
            self._feature_list = json.load(f)
        if metadata_path.exists():
            with open(metadata_path) as f:
                self._metadata = json.load(f)
        logger.info("Loaded calibration model from %s", self.artifact_dir)

    def metadata(self) -> Optional[dict]:
        self._ensure_loaded()
        return self._metadata

    def predict(self, features: Dict[str, float]) -> float:
        self._ensure_loaded()
        if self._model is None:
            raise ModelNotAvailableError(
                "Calibration model is not trained yet. Run `python -m app.ml.irrigation.train --only calibration`."
            )
        row = pd.DataFrame([{col: features[col] for col in self._feature_list}])
        scaled = self._scaler.transform(row[self._feature_list])
        scaled_df = pd.DataFrame(scaled, columns=self._feature_list)
        pred = self._model.predict(scaled_df)[0]
        return float(pred)


class ForecastingInferenceService:
    def __init__(self):
        self._models: Dict[str, object] = {}
        self._scaler = None
        self._feature_list: Optional[list] = None
        self._metadata: Optional[dict] = None
        self._load_attempted = False

    @property
    def artifact_dir(self) -> Path:
        return settings.model_artifact_root_path / "irrigation" / "forecasting"

    def is_available(self) -> bool:
        self._ensure_loaded()
        return len(self._models) == len(HORIZONS)

    def _ensure_loaded(self):
        if self._load_attempted:
            return
        self._load_attempted = True

        scaler_path = self.artifact_dir / "scaler.joblib"
        features_path = self.artifact_dir / "feature_list.json"
        metadata_path = self.artifact_dir / "metadata.json"

        if not (scaler_path.exists() and features_path.exists()):
            logger.warning("Forecasting scaler/feature list not found under %s", self.artifact_dir)
            return

        self._scaler = joblib.load(scaler_path)
        with open(features_path) as f:
            self._feature_list = json.load(f)
        if metadata_path.exists():
            with open(metadata_path) as f:
                self._metadata = json.load(f)

        for horizon in HORIZONS:
            model_path = self.artifact_dir / horizon / "model.joblib"
            if model_path.exists():
                self._models[horizon] = joblib.load(model_path)
            else:
                logger.warning("Forecasting model for horizon=%s not found at %s", horizon, model_path)

        logger.info("Loaded %d/%d forecasting horizon models", len(self._models), len(HORIZONS))

    def metadata(self) -> Optional[dict]:
        self._ensure_loaded()
        return self._metadata

    def predict(self, features: Dict[str, float]) -> Dict[str, float]:
        self._ensure_loaded()
        if not self._models:
            raise ModelNotAvailableError(
                "Forecasting models are not trained yet. Run `python -m app.ml.irrigation.train --only forecasting`."
            )
        row = pd.DataFrame([{col: features[col] for col in self._feature_list}])
        scaled = self._scaler.transform(row[self._feature_list])
        scaled_df = pd.DataFrame(scaled, columns=self._feature_list)

        results = {}
        for horizon, model in self._models.items():
            results[horizon] = float(model.predict(scaled_df)[0])
        return results


# Module-level singletons (lazy-loaded on first use, centralizes model access)
calibration_service = CalibrationInferenceService()
forecasting_service = ForecastingInferenceService()

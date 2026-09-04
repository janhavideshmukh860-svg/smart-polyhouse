"""
Central model-status resolution, used by both GET /models/status and the
dashboard endpoint, so the two never disagree about whether a model is
ready.
"""
from __future__ import annotations

from app.ml.disease.inference import disease_inference_service
from app.ml.irrigation.forecasting import HORIZONS
from app.ml.irrigation.inference import calibration_service, forecasting_service
from app.schemas.model_status import ModelStatusEntry, ModelsStatusResponse
from app.services.model_service import (
    get_calibration_model_metadata,
    get_disease_model_metadata,
    get_forecasting_model_metadata,
)


def get_models_status() -> ModelsStatusResponse:
    # --- Irrigation calibration ---
    if calibration_service.is_available():
        meta = get_calibration_model_metadata() or {}
        calibration_entry = ModelStatusEntry(
            status="READY",
            model_type=meta.get("model_type"),
            version=meta.get("version"),
            metrics=meta.get("test_metrics"),
        )
    else:
        calibration_entry = ModelStatusEntry(
            status="NOT_YET_TRAINED",
            detail="Run `python -m app.ml.irrigation.train --only calibration`.",
        )

    # --- Irrigation forecasting ---
    if forecasting_service.is_available():
        meta = get_forecasting_model_metadata() or {}
        horizon_metrics = {
            h: meta.get("horizons", {}).get(h, {}).get("test_metrics") for h in HORIZONS
        }
        forecasting_entry = ModelStatusEntry(
            status="READY",
            model_type=meta.get("model_type"),
            version=meta.get("version"),
            metrics=horizon_metrics,
            horizons=list(HORIZONS),
        )
    else:
        forecasting_entry = ModelStatusEntry(
            status="NOT_YET_TRAINED",
            detail="Run `python -m app.ml.irrigation.train --only forecasting`.",
        )

    # --- Disease ---
    if disease_inference_service.is_available():
        meta = get_disease_model_metadata() or {}
        disease_entry = ModelStatusEntry(
            status="READY",
            model_type=meta.get("model_type"),
            version=meta.get("version"),
            metrics=meta.get("test_metrics_summary"),
        )
    else:
        disease_entry = ModelStatusEntry(
            status="NOT_YET_TRAINED",
            detail=(
                "Disease model requires the original image dataset and completed training. "
                "The current dataset package contains manifests/metadata only, not the raw "
                "images. See README section 6.3 / 9.4 for training instructions once images "
                "are available."
            ),
        )

    return ModelsStatusResponse(
        irrigation_calibration=calibration_entry,
        irrigation_forecasting=forecasting_entry,
        disease=disease_entry,
    )

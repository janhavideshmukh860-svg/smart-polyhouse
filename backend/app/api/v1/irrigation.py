from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.logging import get_logger
from app.ml.irrigation.inference import ModelNotAvailableError
from app.schemas.decision import IrrigationDecisionRequest, IrrigationDecisionResponse
from app.schemas.disease import ModelInfo
from app.schemas.irrigation import (
    CalibrationPredictRequest,
    CalibrationPredictResponse,
    ForecastCurrentResponse,
    ForecastPredictRequest,
    ForecastPredictResponse,
)
from app.services.irrigation_service import irrigation_service
from app.services.recommendation_service import generate_irrigation_recommendation

logger = get_logger(__name__)
router = APIRouter(prefix="/irrigation", tags=["Irrigation"])


def _calibration_model_info() -> ModelInfo:
    meta = irrigation_service.calibration_metadata() or {}
    return ModelInfo(
        name=meta.get("model_name", "irrigation_calibration"),
        version=meta.get("version", "unknown"),
        task="irrigation_calibration",
        status=meta.get("status", "trained"),
    )


def _forecast_model_info() -> ModelInfo:
    meta = irrigation_service.forecasting_metadata() or {}
    return ModelInfo(
        name=meta.get("model_name", "irrigation_forecasting"),
        version=meta.get("version", "unknown"),
        task="irrigation_forecasting",
        status=meta.get("status", "trained"),
    )


@router.post("/calibrate", response_model=CalibrationPredictResponse)
def calibrate(payload: CalibrationPredictRequest) -> CalibrationPredictResponse:
    """Converts a raw low-cost sensor reading into a calibrated volumetric
    soil moisture percentage."""
    features = payload.model_dump()
    if features.get("Hour_sin") is None:
        import math
        hour = features["Hour"]
        day_of_year = features["DayOfYear"]
        features["Hour_sin"] = math.sin(2 * math.pi * hour / 24)
        features["Hour_cos"] = math.cos(2 * math.pi * hour / 24)
        features["Day_sin"] = math.sin(2 * math.pi * day_of_year / 365)
        features["Day_cos"] = math.cos(2 * math.pi * day_of_year / 365)

    try:
        prediction = irrigation_service.predict_calibration(features)
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    return CalibrationPredictResponse(
        predicted_volumetric_moisture_pct=round(prediction, 3),
        model=_calibration_model_info(),
    )


@router.post("/predict", response_model=ForecastPredictResponse)
def predict_forecast(payload: ForecastPredictRequest) -> ForecastPredictResponse:
    """Predicts soil moisture at 1h/6h/12h/24h horizons from the current
    sensor + environmental state."""
    features = payload.model_dump()
    try:
        results = irrigation_service.predict_forecast(features)
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    return ForecastPredictResponse(
        reference_time=datetime.now(timezone.utc),
        current_moisture_pct=payload.Volumetric_Moisture_Pct,
        forecast_1h=round(results["1h"], 3),
        forecast_6h=round(results["6h"], 3),
        forecast_12h=round(results["12h"], 3),
        forecast_24h=round(results["24h"], 3),
        models={
            "calibration": _calibration_model_info(),
            "forecasting": _forecast_model_info(),
        },
    )


@router.get("/forecast", response_model=ForecastPredictResponse)
def get_forecast_example() -> ForecastPredictResponse:
    """Convenience GET that documents the forecast shape using a
    representative recent record from the authoritative test split (NOT a
    live sensor feed - Part 1 has no real-time ingestion yet). Prefer
    POST /irrigation/predict with real current sensor data."""
    import pandas as pd
    from app.core.config import settings

    test_path = settings.irrigation_dataset_root_path / "forecasting" / "test.csv"
    if not test_path.exists():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Forecasting dataset not available")

    df = pd.read_csv(test_path)
    row = df.iloc[-1]
    from app.ml.irrigation.preprocessing import forecasting_feature_columns
    feature_cols = forecasting_feature_columns(df)
    features = {c: row[c] for c in feature_cols}

    try:
        results = irrigation_service.predict_forecast(features)
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    return ForecastPredictResponse(
        reference_time=datetime.now(timezone.utc),
        current_moisture_pct=float(row["Volumetric_Moisture_Pct"]),
        forecast_1h=round(results["1h"], 3),
        forecast_6h=round(results["6h"], 3),
        forecast_12h=round(results["12h"], 3),
        forecast_24h=round(results["24h"], 3),
        models={
            "calibration": _calibration_model_info(),
            "forecasting": _forecast_model_info(),
        },
    )


@router.post("/decision", response_model=IrrigationDecisionResponse)
def get_irrigation_decision(
    payload: IrrigationDecisionRequest,
    db: Session = Depends(get_db_session),
) -> IrrigationDecisionResponse:
    """
    The Irrigation Decision Engine (Part 2): runs the forecasting models
    on the given current state, then applies rule-based threshold
    interpretation (app.services.decision_engine) to produce an
    explainable recommendation. Persists a Recommendation row and may
    raise an Alert for MEDIUM+ urgency outcomes (best-effort - failures
    to persist do not block the response).
    """
    features = payload.model_dump(exclude={"polyhouse_id"})
    try:
        result = generate_irrigation_recommendation(
            features=features, db=db, polyhouse_id=payload.polyhouse_id, persist=True
        )
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return IrrigationDecisionResponse(
        recommendation_id=result.persisted_id,
        status=result.decision.status,
        urgency=result.decision.urgency,
        current_moisture=result.current_moisture,
        forecast=result.forecast,
        recommendation=result.decision.recommendation_text,
        reason=result.decision.reason,
        risk_factors=result.decision.risk_factors,
        model_confidence=result.decision.model_confidence,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/current", response_model=ForecastCurrentResponse)
def get_current() -> ForecastCurrentResponse:
    """Part 1 has no live sensor ingestion endpoint yet, so this reports
    that no real-time reading is available rather than fabricating one.
    Part 2 / the sensor ingestion layer will populate sensor_readings,
    after which this endpoint will return the latest real value."""
    return ForecastCurrentResponse(source="unavailable")

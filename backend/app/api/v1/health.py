from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.core.config import settings
from app.database.database import check_database_connection
from app.ml.disease.inference import disease_inference_service
from app.ml.irrigation.inference import calibration_service, forecasting_service
from app.schemas.common import ComponentStatus, HealthResponse, SystemStatusResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Lightweight liveness check - does not touch the database or ML
    models, so it always responds quickly if the process is up."""
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc))


@router.get("/system/status", response_model=SystemStatusResponse)
def system_status() -> SystemStatusResponse:
    db_ok = check_database_connection()
    db_status = ComponentStatus(
        name="database",
        available=db_ok,
        detail=None if db_ok else "Database unreachable or not configured. Set DATABASE_URL in .env.",
    )

    disease_ok = disease_inference_service.is_available()
    disease_status = ComponentStatus(
        name="disease_model",
        available=disease_ok,
        detail=None if disease_ok else "Disease model not trained yet (requires raw image dataset).",
    )

    calib_ok = calibration_service.is_available()
    calib_status = ComponentStatus(
        name="irrigation_calibration_model",
        available=calib_ok,
        detail=None if calib_ok else "Calibration model artifacts not found.",
    )

    fcst_ok = forecasting_service.is_available()
    fcst_status = ComponentStatus(
        name="irrigation_forecasting_models",
        available=fcst_ok,
        detail=None if fcst_ok else "One or more forecasting horizon models not found.",
    )

    return SystemStatusResponse(
        backend_status="ok",
        database=db_status,
        disease_model=disease_status,
        irrigation_calibration_model=calib_status,
        irrigation_forecasting_models=fcst_status,
        app_version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.api.v1.farms import get_owned_polyhouse
from app.database.models import DiseasePrediction, User
from app.database.repositories.alert_repository import AlertRepository
from app.database.repositories.recommendation_repository import RecommendationRepository
from app.database.repositories.sensor_repository import SensorReadingRepository
from app.ml.disease.inference import disease_inference_service
from app.schemas.alert import AlertResponse
from app.schemas.dashboard import (
    DashboardDiseaseState,
    DashboardIrrigationState,
    DashboardResponse,
    DashboardSensorState,
)
from app.services.model_status_service import get_models_status

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/{polyhouse_id}", response_model=DashboardResponse)
def get_dashboard(
    polyhouse_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> DashboardResponse:
    """
    Consolidated dashboard endpoint - one call for everything a frontend
    landing page needs. All fields reflect real, current database/model
    state; nothing here is fabricated. Where data is genuinely
    unavailable (no sensor readings yet, disease model untrained,
    forecasting requires fields not present in ingested sensor readings),
    the response says so explicitly via `available`/`status`/`detail`
    fields rather than inventing a plausible-looking value.
    """
    # Ownership check - 404 for polyhouses the caller does not own.
    get_owned_polyhouse(db, polyhouse_id, current_user)

    now = datetime.now(timezone.utc)

    # ---- Sensor state ----
    sensor_repo = SensorReadingRepository(db)
    latest_reading = sensor_repo.latest_for_polyhouse(polyhouse_id)
    data_freshness_minutes = None
    if latest_reading is not None:
        data_freshness_minutes = round((now - latest_reading.recorded_at).total_seconds() / 60.0, 1)
        sensor_state = DashboardSensorState(
            available=True,
            recorded_at=latest_reading.recorded_at,
            volumetric_moisture_pct=latest_reading.volumetric_moisture_pct,
            soil_temperature_c=latest_reading.soil_temperature_c,
            atm_temperature_c=latest_reading.atm_temperature_c,
        )
    else:
        sensor_state = DashboardSensorState(available=False, detail="No sensor readings ingested yet for this polyhouse.")

    # ---- Irrigation state ----
    # NOTE: full forecasting requires fields (Farm_ID, SM_Level_15cm,
    # SM_Volume_15cm, SM_Aggregate_Pct, SM_Volume_Pct) that are specific
    # to the original dataset schema and are not part of the generic
    # sensor_readings table. Rather than fabricate those fields, the
    # dashboard reports the last CALIBRATED moisture value if one was
    # ingested, and directs the caller to POST /irrigation/decision with
    # the full feature payload for a live forecast + recommendation.
    if latest_reading is not None and latest_reading.volumetric_moisture_pct is not None:
        latest_rec = RecommendationRepository(db).latest_for_polyhouse(polyhouse_id)
        if latest_rec is not None:
            stored_forecast = (latest_rec.inputs_snapshot or {}).get("forecast")
            irrigation_state = DashboardIrrigationState(
                available=True,
                current_moisture=latest_reading.volumetric_moisture_pct,
                forecast=stored_forecast,
                status=latest_rec.status.value,
                urgency=latest_rec.urgency.value,
                recommendation=latest_rec.recommendation_text,
            )
        else:
            irrigation_state = DashboardIrrigationState(
                available=True,
                current_moisture=latest_reading.volumetric_moisture_pct,
                detail="No decision has been generated yet for this polyhouse. POST /api/v1/irrigation/decision to get a live forecast + recommendation.",
            )
    else:
        irrigation_state = DashboardIrrigationState(
            available=False,
            detail="No calibrated moisture reading available yet for this polyhouse.",
        )

    # ---- Disease state ----
    if disease_inference_service.is_available():
        stmt = (
            select(DiseasePrediction)
            .where(DiseasePrediction.polyhouse_id == polyhouse_id)
            .order_by(DiseasePrediction.created_at.desc())
            .limit(1)
        )
        latest_pred = db.execute(stmt).scalars().first()
        disease_state = DashboardDiseaseState(
            status="MODEL_AVAILABLE",
            latest_prediction=(
                {
                    "predicted_class": latest_pred.predicted_class,
                    "confidence": latest_pred.confidence,
                    "created_at": latest_pred.created_at.isoformat(),
                }
                if latest_pred is not None
                else None
            ),
            detail=None if latest_pred is not None else "Model is trained but no prediction has been submitted for this polyhouse yet.",
        )
    else:
        disease_state = DashboardDiseaseState(
            status="MODEL_NOT_TRAINED",
            detail="Disease model requires the original image dataset and completed training.",
        )

    # ---- Alerts & recommendations ----
    alert_repo = AlertRepository(db)
    active_alerts = alert_repo.list_active(polyhouse_id=polyhouse_id, limit=20)

    rec_repo = RecommendationRepository(db)
    recent_recommendations = rec_repo.list_for_polyhouse(polyhouse_id, limit=50)

    return DashboardResponse(
        polyhouse_id=polyhouse_id,
        generated_at=now,
        sensor_state=sensor_state,
        irrigation=irrigation_state,
        disease=disease_state,
        active_alerts=[AlertResponse.model_validate(a) for a in active_alerts],
        recent_recommendations_count=len(recent_recommendations),
        model_status=get_models_status(),
        data_freshness_minutes=data_freshness_minutes,
    )

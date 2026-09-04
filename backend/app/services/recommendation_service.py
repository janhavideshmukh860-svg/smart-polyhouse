"""
Recommendation Service.

Orchestrates: irrigation ML predictions -> decision engine (rule-based
interpretation) -> persisted Recommendation row -> Alert Engine (for
MEDIUM+ urgency). This is the "Irrigation Decision Engine" referenced in
the Part 2 spec, wired into the database and alerting.
"""
from __future__ import annotations

import uuid
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.models import Recommendation
from app.database.repositories.recommendation_repository import RecommendationRepository
from app.ml.irrigation.inference import ModelNotAvailableError
from app.services import alert_engine
from app.services.decision_engine import IrrigationDecision, evaluate_irrigation_decision
from app.services.irrigation_service import irrigation_service

logger = get_logger(__name__)


class IrrigationRecommendationResult:
    def __init__(self, decision: IrrigationDecision, current_moisture: float, forecast: Dict[str, float], persisted_id: Optional[uuid.UUID] = None):
        self.decision = decision
        self.current_moisture = current_moisture
        self.forecast = forecast
        self.persisted_id = persisted_id


def generate_irrigation_recommendation(
    features: Dict[str, float],
    db: Optional[Session] = None,
    polyhouse_id: Optional[uuid.UUID] = None,
    persist: bool = True,
) -> IrrigationRecommendationResult:
    """
    features: the same feature dict accepted by
    IrrigationService.predict_forecast (current sensor/environmental
    state including Volumetric_Moisture_Pct).

    Raises ModelNotAvailableError if the forecasting models are not
    trained - callers map this to a 503 with a clear message, never a
    fabricated recommendation.
    """
    if not irrigation_service.forecasting_available():
        raise ModelNotAvailableError(
            "Irrigation forecasting models are not available - cannot generate a recommendation without them."
        )

    current_moisture = features.get("Volumetric_Moisture_Pct")
    if current_moisture is None:
        raise ValueError("features must include 'Volumetric_Moisture_Pct' (the current calibrated/measured state)")

    forecast = irrigation_service.predict_forecast(features)
    decision = evaluate_irrigation_decision(current_moisture, forecast)

    persisted_id = None
    if persist and db is not None:
        try:
            record = Recommendation(
                polyhouse_id=polyhouse_id,
                domain="irrigation",
                status=decision.status,
                urgency=decision.urgency,
                recommendation_text=decision.recommendation_text,
                reason=decision.reason,
                risk_factors=decision.risk_factors,
                inputs_snapshot={"current_moisture_pct": current_moisture, "forecast": forecast},
                model_confidence=decision.model_confidence,
            )
            repo = RecommendationRepository(db)
            record = repo.create(record)
            db.commit()
            persisted_id = record.id

            # Alert engine: only fires for MEDIUM+ urgency, traceable to this recommendation.
            alert_engine.maybe_create_water_stress_alert(
                db, polyhouse_id, decision.status, decision.urgency, decision.reason, recommendation_id=persisted_id
            )
        except Exception:
            logger.exception("Failed to persist irrigation recommendation (returning result without DB id)")
            db.rollback()

    return IrrigationRecommendationResult(decision=decision, current_moisture=current_moisture, forecast=forecast, persisted_id=persisted_id)

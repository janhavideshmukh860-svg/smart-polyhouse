"""
Irrigation service layer - wraps the calibration and forecasting
inference modules. Part 2's WaterOptimizationEngine will sit on top of
this service rather than duplicating model-loading logic.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.models import ForecastResult, IrrigationPrediction
from app.ml.irrigation.inference import (
    ModelNotAvailableError,
    calibration_service,
    forecasting_service,
)

logger = get_logger(__name__)


class IrrigationService:
    # ---- Calibration ----
    def calibration_available(self) -> bool:
        return calibration_service.is_available()

    def calibration_metadata(self) -> Optional[dict]:
        return calibration_service.metadata()

    def predict_calibration(self, features: Dict[str, float]) -> float:
        return calibration_service.predict(features)

    def predict_calibration_and_log(self, db: Optional[Session], features: Dict[str, float], polyhouse_id=None) -> float:
        prediction = self.predict_calibration(features)
        if db is not None:
            try:
                record = IrrigationPrediction(
                    polyhouse_id=polyhouse_id,
                    predicted_volumetric_moisture_pct=prediction,
                    input_features=features,
                )
                db.add(record)
                db.commit()
            except Exception:
                logger.exception("Failed to persist calibration prediction (continuing without DB log)")
                db.rollback()
        return prediction

    # ---- Forecasting ----
    def forecasting_available(self) -> bool:
        return forecasting_service.is_available()

    def forecasting_metadata(self) -> Optional[dict]:
        return forecasting_service.metadata()

    def predict_forecast(self, features: Dict[str, float]) -> Dict[str, float]:
        return forecasting_service.predict(features)

    def predict_forecast_and_log(self, db: Optional[Session], features: Dict[str, float], polyhouse_id=None) -> Dict[str, float]:
        results = self.predict_forecast(features)
        if db is not None:
            try:
                record = ForecastResult(
                    polyhouse_id=polyhouse_id,
                    reference_time=datetime.now(timezone.utc),
                    current_moisture_pct=features.get("Volumetric_Moisture_Pct"),
                    forecast_1h=results.get("1h"),
                    forecast_6h=results.get("6h"),
                    forecast_12h=results.get("12h"),
                    forecast_24h=results.get("24h"),
                    input_features=features,
                )
                db.add(record)
                db.commit()
            except Exception:
                logger.exception("Failed to persist forecast result (continuing without DB log)")
                db.rollback()
        return results


irrigation_service = IrrigationService()

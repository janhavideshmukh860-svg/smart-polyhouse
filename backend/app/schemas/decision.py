from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.database.models import RecommendationStatus, RecommendationUrgency


class IrrigationDecisionRequest(BaseModel):
    """Same shape as ForecastPredictRequest - the current sensor/
    environmental state used to derive both the forecast and the
    recommendation in one call."""

    Farm_ID: str
    Volumetric_Moisture_Pct: float
    Sensor_Board_Temperature_C: float
    Raw_Capacitive_ADC: float
    Sensor_Voltage_V: float
    Atm_Pressure_inHg: float
    Atm_Temperature_C: float
    Soil_Temperature_C: float
    SM_Level_15cm: float
    SM_Volume_15cm: float
    SM_Aggregate_Pct: float
    SM_Volume_Pct: float
    Hour: int = Field(ge=0, le=23)
    Day: int = Field(ge=1, le=31)
    Month: int = Field(ge=1, le=12)
    DayOfWeek: int = Field(ge=0, le=6)
    DayOfYear: int = Field(ge=1, le=366)
    Hour_sin: float
    Hour_cos: float
    Day_sin: float
    Day_cos: float
    polyhouse_id: Optional[uuid.UUID] = None


class ForecastBlock(BaseModel):
    h1: Optional[float] = Field(default=None, alias="1h")
    h6: Optional[float] = Field(default=None, alias="6h")
    h12: Optional[float] = Field(default=None, alias="12h")
    h24: Optional[float] = Field(default=None, alias="24h")

    model_config = {"populate_by_name": True}


class IrrigationDecisionResponse(BaseModel):
    """Deliberately separates MEASURED STATE, MODEL PREDICTION,
    RULE-BASED INTERPRETATION, and RECOMMENDATION into distinct fields -
    see app.services.decision_engine module docstring."""

    recommendation_id: Optional[uuid.UUID] = None
    status: RecommendationStatus
    urgency: RecommendationUrgency
    current_moisture: float = Field(description="Measured/calibrated state - not a prediction")
    forecast: Dict[str, float] = Field(description="Model predictions for 1h/6h/12h/24h horizons")
    recommendation: str
    reason: str
    risk_factors: List[str] = Field(default_factory=list, description="Rule-based interpretation, not a model output")
    model_confidence: Optional[float] = Field(
        default=None,
        description="Null unless the underlying model produces a genuine calibrated confidence estimate (regression models here do not).",
    )
    generated_at: datetime

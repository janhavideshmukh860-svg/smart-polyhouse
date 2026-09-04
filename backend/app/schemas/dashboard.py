from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.schemas.alert import AlertResponse
from app.schemas.model_status import ModelsStatusResponse


class DashboardSensorState(BaseModel):
    available: bool
    recorded_at: Optional[datetime] = None
    volumetric_moisture_pct: Optional[float] = None
    soil_temperature_c: Optional[float] = None
    atm_temperature_c: Optional[float] = None
    detail: Optional[str] = None


class DashboardIrrigationState(BaseModel):
    available: bool
    current_moisture: Optional[float] = None
    forecast: Optional[Dict[str, float]] = None
    status: Optional[str] = None
    urgency: Optional[str] = None
    recommendation: Optional[str] = None
    detail: Optional[str] = None


class DashboardDiseaseState(BaseModel):
    status: str  # MODEL_AVAILABLE | MODEL_NOT_TRAINED
    latest_prediction: Optional[Dict[str, Any]] = None
    detail: Optional[str] = None


class DashboardResponse(BaseModel):
    polyhouse_id: Optional[uuid.UUID] = None
    generated_at: datetime
    sensor_state: DashboardSensorState
    irrigation: DashboardIrrigationState
    disease: DashboardDiseaseState
    active_alerts: List[AlertResponse]
    recent_recommendations_count: int
    model_status: ModelsStatusResponse
    data_freshness_minutes: Optional[float] = None

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.disease import ModelInfo


class CalibrationPredictRequest(BaseModel):
    """Raw low-cost sensor + environmental reading to be calibrated into a
    volumetric soil moisture percentage. Field names mirror the authoritative
    calibration dataset's feature_columns exactly."""

    Raw_Capacitive_ADC: float
    Sensor_Voltage_V: float
    Sensor_Board_Temperature_C: float
    Atm_Pressure_inHg: float
    Atm_Temperature_C: float
    Soil_Temperature_C: float
    Hour: int = Field(ge=0, le=23)
    Day: int = Field(ge=1, le=31)
    Month: int = Field(ge=1, le=12)
    DayOfWeek: int = Field(ge=0, le=6)
    DayOfYear: int = Field(ge=1, le=366)
    Hour_sin: Optional[float] = None
    Hour_cos: Optional[float] = None
    Day_sin: Optional[float] = None
    Day_cos: Optional[float] = None


class CalibrationPredictResponse(BaseModel):
    predicted_volumetric_moisture_pct: float
    model: ModelInfo


class ForecastPredictRequest(BaseModel):
    """Current-timestep features used to forecast future moisture. Mirrors
    the authoritative forecasting dataset's feature columns (excluding the
    target_* columns, which are what we predict)."""

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


class ForecastPredictResponse(BaseModel):
    reference_time: datetime
    current_moisture_pct: float
    forecast_1h: float
    forecast_6h: float
    forecast_12h: float
    forecast_24h: float
    models: dict[str, ModelInfo]


class ForecastCurrentResponse(BaseModel):
    """Response for GET /irrigation/current - latest known/calibrated
    reading for a polyhouse. Part 1 serves this from the most recent
    stored sensor_reading / irrigation_prediction, when the DB is
    configured, or explains that no data is available."""

    polyhouse_id: Optional[str] = None
    recorded_at: Optional[datetime] = None
    volumetric_moisture_pct: Optional[float] = None
    source: str = Field(description="'calibrated_prediction' | 'raw_sensor_reading' | 'unavailable'")

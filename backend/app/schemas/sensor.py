from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SensorReadingCreate(BaseModel):
    polyhouse_id: uuid.UUID
    recorded_at: Optional[datetime] = Field(
        default=None, description="Defaults to server-received time if omitted"
    )
    raw_capacitive_adc: Optional[float] = None
    sensor_voltage_v: Optional[float] = Field(default=None, ge=0, le=12)
    sensor_board_temperature_c: Optional[float] = Field(default=None, ge=-40, le=85)
    atm_pressure_inhg: Optional[float] = Field(default=None, ge=20, le=35)
    atm_temperature_c: Optional[float] = Field(default=None, ge=-40, le=60)
    soil_temperature_c: Optional[float] = Field(default=None, ge=-20, le=60)
    volumetric_moisture_pct: Optional[float] = Field(default=None, ge=0, le=100)

    @field_validator(
        "raw_capacitive_adc",
        "sensor_voltage_v",
        "sensor_board_temperature_c",
        "atm_pressure_inhg",
        "atm_temperature_c",
        "soil_temperature_c",
        "volumetric_moisture_pct",
    )
    @classmethod
    def _reject_nan_inf(cls, v):
        if v is not None:
            import math
            if math.isnan(v) or math.isinf(v):
                raise ValueError("value must be a finite number")
        return v


class SensorReadingResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    polyhouse_id: uuid.UUID
    recorded_at: datetime
    raw_capacitive_adc: Optional[float] = None
    sensor_voltage_v: Optional[float] = None
    sensor_board_temperature_c: Optional[float] = None
    atm_pressure_inhg: Optional[float] = None
    atm_temperature_c: Optional[float] = None
    soil_temperature_c: Optional[float] = None
    volumetric_moisture_pct: Optional[float] = None
    created_at: datetime


class SensorReadingListResponse(BaseModel):
    total: int
    readings: list[SensorReadingResponse]

"""Shared response envelopes and common schema pieces used across the API,
so that responses stay predictable for the Lovable frontend."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error envelope. FastAPI exception handlers convert all
    unhandled/handled errors into this shape - raw Python exceptions are
    never returned to the client."""
    error: ErrorDetail


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


class ComponentStatus(BaseModel):
    name: str
    available: bool
    detail: Optional[str] = None


class SystemStatusResponse(BaseModel):
    backend_status: str
    database: ComponentStatus
    disease_model: ComponentStatus
    irrigation_calibration_model: ComponentStatus
    irrigation_forecasting_models: ComponentStatus
    app_version: str
    environment: str

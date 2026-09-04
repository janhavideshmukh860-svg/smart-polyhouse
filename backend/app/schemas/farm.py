"""Schemas for farm / polyhouse management.

These complete the ownership-scoped CRUD surface the frontend needs in order
to select the polyhouse that every other endpoint (sensors, dashboard,
irrigation decision, alerts, recommendations) is keyed on.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FarmCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location_label: Optional[str] = Field(default=None, max_length=255)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)


class FarmUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    location_label: Optional[str] = Field(default=None, max_length=255)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)


class PolyhouseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    area_sq_m: Optional[float] = Field(default=None, gt=0, le=1_000_000)
    external_sensor_reference: Optional[str] = Field(default=None, max_length=255)


class PolyhouseUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    area_sq_m: Optional[float] = Field(default=None, gt=0, le=1_000_000)
    external_sensor_reference: Optional[str] = Field(default=None, max_length=255)


class PolyhouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    name: str
    area_sq_m: Optional[float] = None
    external_sensor_reference: Optional[str] = None
    created_at: datetime


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    location_label: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime


class FarmWithPolyhousesResponse(FarmResponse):
    polyhouses: list[PolyhouseResponse] = []


class FarmListResponse(BaseModel):
    total: int
    farms: list[FarmWithPolyhousesResponse]


class PolyhouseListResponse(BaseModel):
    total: int
    polyhouses: list[PolyhouseResponse]

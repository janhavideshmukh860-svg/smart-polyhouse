from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.database.models import RecommendationStatus, RecommendationUrgency


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    polyhouse_id: Optional[uuid.UUID] = None
    domain: str
    status: RecommendationStatus
    urgency: RecommendationUrgency
    recommendation_text: str
    reason: str
    risk_factors: Optional[Any] = None
    inputs_snapshot: Optional[Any] = None
    model_confidence: Optional[float] = None
    created_at: datetime


class RecommendationListResponse(BaseModel):
    total: int
    recommendations: list[RecommendationResponse]

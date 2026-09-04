"""Recommendations API.

Exposes the persisted output of the Irrigation Decision Engine. The
recommendation is a RULE-BASED INTERPRETATION layered on top of model
predictions - `inputs_snapshot` carries the measured state and the model
forecast that produced it, so the frontend can keep those three layers
visually distinct.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.api.v1.farms import get_owned_polyhouse
from app.database.models import Farm, Polyhouse, Recommendation, User
from app.schemas.recommendation import RecommendationListResponse, RecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", response_model=RecommendationListResponse)
def list_recommendations(
    polyhouse_id: Optional[uuid.UUID] = Query(default=None),
    domain: Optional[str] = Query(default=None, max_length=50),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> RecommendationListResponse:
    stmt = select(Recommendation)

    if polyhouse_id is not None:
        # Raises 404 when the polyhouse is not owned by the caller.
        get_owned_polyhouse(db, polyhouse_id, current_user)
        stmt = stmt.where(Recommendation.polyhouse_id == polyhouse_id)
    else:
        # Restrict to polyhouses the caller owns.
        owned = (
            select(Polyhouse.id)
            .join(Farm, Polyhouse.farm_id == Farm.id)
            .where(Farm.owner_id == current_user.id)
        )
        stmt = stmt.where(Recommendation.polyhouse_id.in_(owned))

    if domain:
        stmt = stmt.where(Recommendation.domain == domain)

    stmt = stmt.order_by(Recommendation.created_at.desc()).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return RecommendationListResponse(
        total=len(rows),
        recommendations=[RecommendationResponse.model_validate(r) for r in rows],
    )

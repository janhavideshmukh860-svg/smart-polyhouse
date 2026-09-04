from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select

from app.database.models import Recommendation
from app.database.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    model = Recommendation

    def list_for_polyhouse(self, polyhouse_id: uuid.UUID, limit: int = 20) -> Sequence[Recommendation]:
        stmt = (
            select(Recommendation)
            .where(Recommendation.polyhouse_id == polyhouse_id)
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def latest_for_polyhouse(self, polyhouse_id: uuid.UUID) -> Recommendation | None:
        stmt = (
            select(Recommendation)
            .where(Recommendation.polyhouse_id == polyhouse_id)
            .order_by(Recommendation.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

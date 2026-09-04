from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select

from app.database.models import Alert, AlertStatus
from app.database.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    model = Alert

    def list_active(self, polyhouse_id: uuid.UUID | None = None, limit: int = 50) -> Sequence[Alert]:
        stmt = select(Alert).where(Alert.status == AlertStatus.active)
        if polyhouse_id is not None:
            stmt = stmt.where(Alert.polyhouse_id == polyhouse_id)
        stmt = stmt.order_by(Alert.created_at.desc()).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def list_for_polyhouse(self, polyhouse_id: uuid.UUID, limit: int = 50) -> Sequence[Alert]:
        stmt = (
            select(Alert)
            .where(Alert.polyhouse_id == polyhouse_id)
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

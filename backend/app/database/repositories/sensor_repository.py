from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select

from app.database.models import SensorReading
from app.database.repositories.base import BaseRepository


class SensorReadingRepository(BaseRepository[SensorReading]):
    model = SensorReading

    def latest_for_polyhouse(self, polyhouse_id: uuid.UUID) -> SensorReading | None:
        stmt = (
            select(SensorReading)
            .where(SensorReading.polyhouse_id == polyhouse_id)
            .order_by(SensorReading.recorded_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def history_for_polyhouse(self, polyhouse_id: uuid.UUID, limit: int = 100) -> Sequence[SensorReading]:
        stmt = (
            select(SensorReading)
            .where(SensorReading.polyhouse_id == polyhouse_id)
            .order_by(SensorReading.recorded_at.desc())
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from app.database.models import ModelRegistry, ModelStatus, ModelTask
from app.database.repositories.base import BaseRepository


class ModelRegistryRepository(BaseRepository[ModelRegistry]):
    model = ModelRegistry

    def get_active_for_task(self, task: ModelTask) -> Optional[ModelRegistry]:
        stmt = (
            select(ModelRegistry)
            .where(ModelRegistry.task == task, ModelRegistry.status == ModelStatus.active)
            .order_by(ModelRegistry.training_date.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def list_for_task(self, task: ModelTask) -> Sequence[ModelRegistry]:
        stmt = select(ModelRegistry).where(ModelRegistry.task == task).order_by(ModelRegistry.training_date.desc())
        return self.db.execute(stmt).scalars().all()

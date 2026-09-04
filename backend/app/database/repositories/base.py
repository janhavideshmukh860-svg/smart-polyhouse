from __future__ import annotations

import uuid
from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic CRUD repository. Concrete repositories subclass this with a
    specific ORM model to avoid duplicating boilerplate query code."""

    model: Type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get(self, id_: uuid.UUID) -> Optional[ModelT]:
        return self.db.get(self.model, id_)

    def list(self, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        stmt = select(self.model).limit(limit).offset(offset)
        return self.db.execute(stmt).scalars().all()

    def create(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()

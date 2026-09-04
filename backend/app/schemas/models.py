from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

from app.database.models import ModelStatus, ModelTask


class ModelRegistryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    model_name: str
    model_type: str
    version: str
    task: ModelTask
    training_dataset: str
    training_date: Optional[datetime] = None
    metrics: Optional[Dict[str, Any]] = None
    artifact_path: str
    status: ModelStatus


class ModelRegistryListResponse(BaseModel):
    total: int
    models: list[ModelRegistryEntry]

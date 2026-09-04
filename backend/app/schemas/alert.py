from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel

from app.database.models import AlertSeverity, AlertStatus


class AlertResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    polyhouse_id: Optional[uuid.UUID] = None
    alert_type: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    source_reference: Optional[Dict[str, Any]] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class AlertListResponse(BaseModel):
    total: int
    alerts: list[AlertResponse]

"""
Alert Engine.

Generates Alert rows from real, traceable events - never from fabricated
data. Each alert's `source_reference` records exactly what triggered it
(a recommendation id + status, a sensor reading's age, a model
availability check) so it can be audited.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.database.models import Alert, AlertSeverity, RecommendationStatus, RecommendationUrgency
from app.database.repositories.alert_repository import AlertRepository

logger = get_logger(__name__)

_URGENCY_TO_SEVERITY = {
    RecommendationUrgency.low: None,  # LOW urgency does not generate an alert
    RecommendationUrgency.medium: AlertSeverity.warning,
    RecommendationUrgency.high: AlertSeverity.high,
    RecommendationUrgency.critical: AlertSeverity.critical,
}


def maybe_create_water_stress_alert(
    db: Session,
    polyhouse_id: Optional[uuid.UUID],
    status: RecommendationStatus,
    urgency: RecommendationUrgency,
    reason: str,
    recommendation_id: Optional[uuid.UUID] = None,
) -> Optional[Alert]:
    """Creates an alert only for MEDIUM+ urgency irrigation decisions.
    Returns None (no alert created) for LOW urgency / NORMAL status."""
    severity = _URGENCY_TO_SEVERITY.get(urgency)
    if severity is None or status == RecommendationStatus.normal:
        return None

    alert = Alert(
        polyhouse_id=polyhouse_id,
        alert_type="water_stress",
        severity=severity,
        message=f"{status.value}: {reason}",
        source_reference={
            "recommendation_id": str(recommendation_id) if recommendation_id else None,
            "status": status.value,
            "urgency": urgency.value,
        },
    )
    try:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        logger.info("Created water_stress alert (%s) for polyhouse=%s", severity.value, polyhouse_id)
        return alert
    except Exception:
        logger.exception("Failed to persist water_stress alert")
        db.rollback()
        return None


def maybe_create_model_unavailable_alert(db: Session, model_task: str, detail: str) -> Optional[Alert]:
    """Creates an INFO-level alert noting a model is unavailable (e.g.
    disease model not trained). Deduplicates naively by checking for an
    existing active alert of the same type within this call - callers
    invoke this at low frequency (e.g. once per dashboard refresh), so
    this is a soft measure, not a hard uniqueness constraint."""
    from app.database.repositories.alert_repository import AlertRepository

    repo = AlertRepository(db)
    existing = [a for a in repo.list_active() if a.alert_type == f"model_unavailable_{model_task}"]
    if existing:
        return None

    alert = Alert(
        polyhouse_id=None,
        alert_type=f"model_unavailable_{model_task}",
        severity=AlertSeverity.info,
        message=detail,
        source_reference={"model_task": model_task},
    )
    try:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
    except Exception:
        logger.exception("Failed to persist model_unavailable alert")
        db.rollback()
        return None


def maybe_create_stale_sensor_alert(
    db: Session, polyhouse_id: uuid.UUID, last_recorded_at: datetime
) -> Optional[Alert]:
    age_minutes = (datetime.now(timezone.utc) - last_recorded_at).total_seconds() / 60.0
    if age_minutes < settings.SENSOR_STALE_AFTER_MINUTES:
        return None

    alert = Alert(
        polyhouse_id=polyhouse_id,
        alert_type="sensor_stale",
        severity=AlertSeverity.warning,
        message=(
            f"No new sensor reading for polyhouse in {age_minutes:.0f} minutes "
            f"(threshold: {settings.SENSOR_STALE_AFTER_MINUTES} minutes)."
        ),
        source_reference={"last_recorded_at": last_recorded_at.isoformat(), "age_minutes": round(age_minutes, 1)},
    )
    try:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
    except Exception:
        logger.exception("Failed to persist sensor_stale alert")
        db.rollback()
        return None

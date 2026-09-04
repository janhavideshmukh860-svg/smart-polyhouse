from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.api.v1.farms import get_owned_polyhouse
from app.database.models import Alert, AlertStatus, User
from app.database.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertListResponse, AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
def list_alerts(
    polyhouse_id: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> AlertListResponse:
    pid = None
    if polyhouse_id:
        try:
            pid = uuid.UUID(polyhouse_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="polyhouse_id must be a valid UUID")

    if pid is not None:
        get_owned_polyhouse(db, pid, current_user)

    repo = AlertRepository(db)
    if active_only:
        alerts = repo.list_active(polyhouse_id=pid, limit=limit)
    elif pid is not None:
        alerts = repo.list_for_polyhouse(pid, limit=limit)
    else:
        alerts = repo.list(limit=limit)

    return AlertListResponse(total=len(alerts), alerts=list(alerts))


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Alert:
    try:
        aid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="alert_id must be a valid UUID")

    repo = AlertRepository(db)
    alert = repo.get(aid)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.polyhouse_id is not None:
        get_owned_polyhouse(db, alert.polyhouse_id, current_user)

    alert.status = AlertStatus.acknowledged
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Alert:
    from datetime import datetime, timezone

    try:
        aid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="alert_id must be a valid UUID")

    repo = AlertRepository(db)
    alert = repo.get(aid)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.polyhouse_id is not None:
        get_owned_polyhouse(db, alert.polyhouse_id, current_user)

    alert.status = AlertStatus.resolved
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert

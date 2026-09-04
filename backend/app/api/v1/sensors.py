from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.api.v1.farms import get_owned_polyhouse
from app.core.logging import get_logger
from app.database.models import SensorReading, User
from app.database.repositories.sensor_repository import SensorReadingRepository
from app.schemas.sensor import SensorReadingCreate, SensorReadingListResponse, SensorReadingResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/sensors", tags=["Sensor Ingestion"])


@router.post("/readings", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED)
def ingest_reading(
    payload: SensorReadingCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> SensorReading:
    """Ingests a single real sensor reading. Requires authentication so
    arbitrary anonymous clients cannot write fabricated sensor data into
    the database. Pydantic validation (see schemas.sensor) rejects
    obviously invalid values (out-of-range voltage/temperature/pressure,
    NaN/Inf) before they ever reach the database."""
    # Ownership check: a user may only write readings into their own polyhouse.
    get_owned_polyhouse(db, payload.polyhouse_id, current_user)

    reading = SensorReading(
        polyhouse_id=payload.polyhouse_id,
        recorded_at=payload.recorded_at or datetime.now(timezone.utc),
        raw_capacitive_adc=payload.raw_capacitive_adc,
        sensor_voltage_v=payload.sensor_voltage_v,
        sensor_board_temperature_c=payload.sensor_board_temperature_c,
        atm_pressure_inhg=payload.atm_pressure_inhg,
        atm_temperature_c=payload.atm_temperature_c,
        soil_temperature_c=payload.soil_temperature_c,
        volumetric_moisture_pct=payload.volumetric_moisture_pct,
    )
    try:
        db.add(reading)
        db.commit()
        db.refresh(reading)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to persist sensor reading")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not store sensor reading - database error")
    return reading


@router.get("/readings/{polyhouse_id}", response_model=SensorReadingListResponse)
def get_reading_history(
    polyhouse_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> SensorReadingListResponse:
    import uuid
    try:
        pid = uuid.UUID(polyhouse_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="polyhouse_id must be a valid UUID")

    get_owned_polyhouse(db, pid, current_user)
    repo = SensorReadingRepository(db)
    readings = repo.history_for_polyhouse(pid, limit=limit)
    return SensorReadingListResponse(total=len(readings), readings=list(readings))


@router.get("/readings/{polyhouse_id}/latest", response_model=SensorReadingResponse)
def get_latest_reading(
    polyhouse_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> SensorReading:
    import uuid
    try:
        pid = uuid.UUID(polyhouse_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="polyhouse_id must be a valid UUID")

    get_owned_polyhouse(db, pid, current_user)
    repo = SensorReadingRepository(db)
    reading = repo.latest_for_polyhouse(pid)
    if reading is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No sensor readings found for this polyhouse")
    return reading

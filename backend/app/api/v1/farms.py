"""Farm & polyhouse management API.

Every route is scoped to the authenticated owner: a user can only read or
mutate farms they own, and polyhouses belonging to those farms. The
ownership helpers exported here (`get_owned_farm`, `get_owned_polyhouse`)
are reused by other routers so the check lives in exactly one place.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_active_user, get_db_session
from app.database.models import Farm, Polyhouse, User
from app.schemas.farm import (
    FarmCreateRequest,
    FarmListResponse,
    FarmResponse,
    FarmUpdateRequest,
    FarmWithPolyhousesResponse,
    PolyhouseCreateRequest,
    PolyhouseListResponse,
    PolyhouseResponse,
    PolyhouseUpdateRequest,
)

router = APIRouter(prefix="/farms", tags=["Farms & Polyhouses"])


# ---------------------------------------------------------------------------
# Ownership helpers (importable by other routers)
# ---------------------------------------------------------------------------
def get_owned_farm(db: Session, farm_id: uuid.UUID, user: User) -> Farm:
    farm = db.get(Farm, farm_id)
    if farm is None or farm.owner_id != user.id:
        # 404 rather than 403 so we never disclose existence of others' data.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm


def get_owned_polyhouse(db: Session, polyhouse_id: uuid.UUID, user: User) -> Polyhouse:
    stmt = (
        select(Polyhouse)
        .join(Farm, Polyhouse.farm_id == Farm.id)
        .where(Polyhouse.id == polyhouse_id, Farm.owner_id == user.id)
    )
    polyhouse = db.execute(stmt).scalars().first()
    if polyhouse is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Polyhouse not found")
    return polyhouse


# ---------------------------------------------------------------------------
# Farms
# ---------------------------------------------------------------------------
@router.get("", response_model=FarmListResponse)
def list_farms(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> FarmListResponse:
    stmt = (
        select(Farm)
        .options(selectinload(Farm.polyhouses))
        .where(Farm.owner_id == current_user.id)
        .order_by(Farm.created_at.asc())
    )
    farms = db.execute(stmt).scalars().all()
    return FarmListResponse(
        total=len(farms),
        farms=[FarmWithPolyhousesResponse.model_validate(f) for f in farms],
    )


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(
    payload: FarmCreateRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Farm:
    farm = Farm(owner_id=current_user.id, **payload.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/{farm_id}", response_model=FarmWithPolyhousesResponse)
def get_farm(
    farm_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Farm:
    return get_owned_farm(db, farm_id, current_user)


@router.patch("/{farm_id}", response_model=FarmResponse)
def update_farm(
    farm_id: uuid.UUID,
    payload: FarmUpdateRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Farm:
    farm = get_owned_farm(db, farm_id, current_user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(farm, key, value)
    db.commit()
    db.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_farm(
    farm_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    farm = get_owned_farm(db, farm_id, current_user)
    db.delete(farm)
    db.commit()


# ---------------------------------------------------------------------------
# Polyhouses
# ---------------------------------------------------------------------------
@router.get("/{farm_id}/polyhouses", response_model=PolyhouseListResponse)
def list_polyhouses(
    farm_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> PolyhouseListResponse:
    farm = get_owned_farm(db, farm_id, current_user)
    stmt = select(Polyhouse).where(Polyhouse.farm_id == farm.id).order_by(Polyhouse.created_at.asc())
    rows = db.execute(stmt).scalars().all()
    return PolyhouseListResponse(
        total=len(rows),
        polyhouses=[PolyhouseResponse.model_validate(p) for p in rows],
    )


@router.post("/{farm_id}/polyhouses", response_model=PolyhouseResponse, status_code=status.HTTP_201_CREATED)
def create_polyhouse(
    farm_id: uuid.UUID,
    payload: PolyhouseCreateRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Polyhouse:
    farm = get_owned_farm(db, farm_id, current_user)
    polyhouse = Polyhouse(farm_id=farm.id, **payload.model_dump())
    db.add(polyhouse)
    db.commit()
    db.refresh(polyhouse)
    return polyhouse


@router.patch("/polyhouses/{polyhouse_id}", response_model=PolyhouseResponse)
def update_polyhouse(
    polyhouse_id: uuid.UUID,
    payload: PolyhouseUpdateRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Polyhouse:
    polyhouse = get_owned_polyhouse(db, polyhouse_id, current_user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(polyhouse, key, value)
    db.commit()
    db.refresh(polyhouse)
    return polyhouse


@router.delete("/polyhouses/{polyhouse_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_polyhouse(
    polyhouse_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    polyhouse = get_owned_polyhouse(db, polyhouse_id, current_user)
    db.delete(polyhouse)
    db.commit()

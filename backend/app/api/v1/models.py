from __future__ import annotations

from fastapi import APIRouter

from app.schemas.model_status import ModelsStatusResponse
from app.services.model_service import collect_local_registry
from app.services.model_status_service import get_models_status

router = APIRouter(prefix="/models", tags=["Model Registry"])


@router.get("")
def list_models():
    """Lists all locally known trained model artifacts and their metrics.
    This reads directly from the model artifact metadata files (the
    source of truth for artifact paths) rather than requiring a database
    connection, so it works even when DATABASE_URL is not configured."""
    entries = collect_local_registry()
    return {"total": len(entries), "models": entries}


@router.get("/status", response_model=ModelsStatusResponse)
def models_status() -> ModelsStatusResponse:
    """Frontend-friendly READY / NOT_YET_TRAINED status for each model
    task, with real metrics where available. See
    app.services.model_status_service for the single source of truth
    this and the dashboard endpoint both use."""
    return get_models_status()

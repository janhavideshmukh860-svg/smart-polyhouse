from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ModelStatusEntry(BaseModel):
    status: str  # READY | NOT_YET_TRAINED | UNAVAILABLE
    model_type: Optional[str] = None
    version: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    horizons: Optional[List[str]] = None
    detail: Optional[str] = None


class ModelsStatusResponse(BaseModel):
    irrigation_calibration: ModelStatusEntry
    irrigation_forecasting: ModelStatusEntry
    disease: ModelStatusEntry

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DiseaseClassInfo(BaseModel):
    final_class: str
    canonical_crop: str
    canonical_disease: str


class ModelInfo(BaseModel):
    name: str
    version: str
    task: str
    status: str


class DiseasePredictionResult(BaseModel):
    class_: str = Field(alias="class")
    confidence: float
    canonical_crop: Optional[str] = None
    canonical_disease: Optional[str] = None

    model_config = {"populate_by_name": True}


class DiseasePredictionResponse(BaseModel):
    prediction: DiseasePredictionResult
    top_k: List[DiseasePredictionResult] = Field(default_factory=list)
    model: ModelInfo


class DiseaseClassListResponse(BaseModel):
    total_classes: int
    total_crops: int
    classes: List[DiseaseClassInfo]

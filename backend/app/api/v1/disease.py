from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.api.v1.farms import get_owned_polyhouse
from app.core.logging import get_logger
from app.database.models import DiseasePrediction, User
from app.ml.disease.dataset import load_class_mapping
from app.ml.disease.inference import ModelNotAvailableError, disease_inference_service
from app.schemas.disease import (
    DiseaseClassInfo,
    DiseaseClassListResponse,
    DiseasePredictionResponse,
    DiseasePredictionResult,
    ModelInfo,
)
from app.services.disease_service import disease_service

logger = get_logger(__name__)
router = APIRouter(prefix="/disease", tags=["Disease Detection"])

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}


@router.get("/status")
def disease_status():
    """Clean structured availability state, per Part 2 spec section 9 -
    distinguishes MODEL_AVAILABLE from MODEL_NOT_TRAINED rather than
    letting callers infer it from a failed prediction."""
    if disease_inference_service.is_available():
        meta = disease_inference_service.metadata() or {}
        return {
            "status": "MODEL_AVAILABLE",
            "model_type": meta.get("model_type"),
            "version": meta.get("version"),
        }
    return {
        "status": "MODEL_NOT_TRAINED",
        "message": (
            "Disease model requires the original image dataset and completed training. "
            "The current dataset package contains manifests/metadata only, not the raw images."
        ),
    }


@router.get("/classes", response_model=DiseaseClassListResponse)
def list_classes() -> DiseaseClassListResponse:
    """Returns the 38 canonical disease classes and their crop/disease
    breakdown, straight from the authoritative disease_class_mapping.csv."""
    try:
        df = load_class_mapping()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    unique = df.drop_duplicates(subset=["final_class"])
    classes = [
        DiseaseClassInfo(
            final_class=row["final_class"],
            canonical_crop=row["canonical_crop"],
            canonical_disease=row["canonical_disease"],
        )
        for _, row in unique.iterrows()
    ]
    return DiseaseClassListResponse(
        total_classes=len(classes),
        total_crops=unique["canonical_crop"].nunique(),
        classes=classes,
    )


@router.post("/predict", response_model=DiseasePredictionResponse)
async def predict_disease(
    file: UploadFile = File(...),
    top_k: int = Query(default=3, ge=1, le=10),
    polyhouse_id: Optional[uuid.UUID] = Query(default=None),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> DiseasePredictionResponse:
    # Uploads are authenticated, and a supplied polyhouse must belong to the caller.
    if polyhouse_id is not None:
        get_owned_polyhouse(db, polyhouse_id, current_user)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds maximum size of {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB",
        )

    try:
        results = disease_service.predict_and_log(db, image_bytes, polyhouse_id=polyhouse_id, top_k=top_k)
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    metadata = disease_service.model_metadata() or {}
    model_info = ModelInfo(
        name=metadata.get("model_name", "disease_detection"),
        version=metadata.get("version", "unknown"),
        task="disease_classification",
        status=metadata.get("status", "trained"),
    )

    top_result = results[0]
    return DiseasePredictionResponse(
        prediction=DiseasePredictionResult(**{
            "class": top_result["class"],
            "confidence": top_result["confidence"],
            "canonical_crop": top_result.get("canonical_crop"),
            "canonical_disease": top_result.get("canonical_disease"),
        }),
        top_k=[
            DiseasePredictionResult(**{
                "class": r["class"],
                "confidence": r["confidence"],
                "canonical_crop": r.get("canonical_crop"),
                "canonical_disease": r.get("canonical_disease"),
            })
            for r in results
        ],
        model=model_info,
    )


@router.get("/history/{polyhouse_id}")
def get_disease_history(
    polyhouse_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
):
    """Persisted disease prediction history for a polyhouse. Requires
    auth. Returns an empty list (not an error) if no predictions have
    ever been logged - this is a real, honest empty state, not a
    fabricated one."""
    from sqlalchemy import select

    get_owned_polyhouse(db, polyhouse_id, current_user)

    stmt = (
        select(DiseasePrediction)
        .where(DiseasePrediction.polyhouse_id == polyhouse_id)
        .order_by(DiseasePrediction.created_at.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).scalars().all()
    return {
        "total": len(rows),
        "predictions": [
            {
                "id": str(r.id),
                "predicted_class": r.predicted_class,
                "confidence": r.confidence,
                "canonical_crop": r.canonical_crop,
                "canonical_disease": r.canonical_disease,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }

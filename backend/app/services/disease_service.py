"""
Disease detection service layer - the boundary between the API routes and
the ML inference module. Part 2's RiskFusionEngine / DecisionEngine can
call into this service (or wrap it) rather than talking to the ML layer
directly.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.models import DiseasePrediction
from app.ml.disease.inference import ModelNotAvailableError, disease_inference_service

logger = get_logger(__name__)


class DiseaseService:
    def is_model_available(self) -> bool:
        return disease_inference_service.is_available()

    def model_metadata(self) -> Optional[dict]:
        return disease_inference_service.metadata()

    def predict(self, image_bytes: bytes, top_k: int = 3) -> List[dict]:
        """Raises ModelNotAvailableError or ValueError (bad image) - the
        API layer maps these to proper HTTP status codes."""
        return disease_inference_service.predict(image_bytes, top_k=top_k)

    def predict_and_log(
        self,
        db: Optional[Session],
        image_bytes: bytes,
        user_id=None,
        polyhouse_id=None,
        top_k: int = 3,
    ) -> List[dict]:
        results = self.predict(image_bytes, top_k=top_k)
        if db is not None and results:
            try:
                top = results[0]
                record = DiseasePrediction(
                    user_id=user_id,
                    polyhouse_id=polyhouse_id,
                    predicted_class=top["class"],
                    confidence=top["confidence"],
                    top_k={r["class"]: r["confidence"] for r in results},
                    canonical_crop=top.get("canonical_crop"),
                    canonical_disease=top.get("canonical_disease"),
                )
                db.add(record)
                db.commit()
            except Exception:
                logger.exception("Failed to persist disease prediction (continuing without DB log)")
                db.rollback()
        return results


disease_service = DiseaseService()

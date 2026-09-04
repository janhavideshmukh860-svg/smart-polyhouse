"""
Centralized model registry service.

Provides a single place that knows about all trained model artifacts
(disease, irrigation calibration, irrigation forecasting) and their
metadata, backed by the JSON metadata files each training script writes
under MODEL_ARTIFACT_ROOT. When a database is configured, entries are
also (best-effort) synced into the `model_registry` table so the rest of
the backend/API can query model history through normal DB queries too.

This keeps model paths out of the API/service code - callers ask the
registry "what's the current model for task X" rather than hard-coding
ml_models/... paths anywhere else.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.database.models import ModelRegistry, ModelStatus, ModelTask

logger = get_logger(__name__)


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def get_disease_model_metadata() -> Optional[dict]:
    return _read_json(settings.model_artifact_root_path / "disease" / "metadata.json")


def get_calibration_model_metadata() -> Optional[dict]:
    return _read_json(settings.model_artifact_root_path / "irrigation" / "calibration" / "metadata.json")


def get_forecasting_model_metadata() -> Optional[dict]:
    return _read_json(settings.model_artifact_root_path / "irrigation" / "forecasting" / "metadata.json")


def collect_local_registry() -> list[dict]:
    """Returns a list of all locally-known model metadata dicts, tagged
    with their task, for use by the /system/status and /models endpoints
    even when no database is configured."""
    entries = []
    disease = get_disease_model_metadata()
    if disease:
        entries.append({**disease, "task": "disease_classification"})
    calibration = get_calibration_model_metadata()
    if calibration:
        entries.append({**calibration, "task": "irrigation_calibration"})
    forecasting = get_forecasting_model_metadata()
    if forecasting:
        entries.append({**forecasting, "task": "irrigation_forecasting"})
    return entries


def sync_registry_to_db(db: Session) -> int:
    """Best-effort upsert of local model metadata JSON files into the
    model_registry table. Returns number of rows written. Safe to call
    repeatedly (idempotent on model_name+version)."""
    task_map = {
        "disease_classification": ModelTask.disease_classification,
        "irrigation_calibration": ModelTask.irrigation_calibration,
        "irrigation_forecasting": ModelTask.irrigation_forecasting,
    }
    artifact_dir_map = {
        "disease_classification": settings.model_artifact_root_path / "disease",
        "irrigation_calibration": settings.model_artifact_root_path / "irrigation" / "calibration",
        "irrigation_forecasting": settings.model_artifact_root_path / "irrigation" / "forecasting",
    }

    written = 0
    for entry in collect_local_registry():
        task_key = entry["task"]
        existing = (
            db.query(ModelRegistry)
            .filter(
                ModelRegistry.model_name == entry.get("model_name", task_key),
                ModelRegistry.version == entry.get("version", "1.0.0"),
            )
            .one_or_none()
        )
        training_date = None
        if entry.get("training_date"):
            try:
                training_date = datetime.fromisoformat(entry["training_date"])
            except ValueError:
                training_date = None

        metrics = entry.get("test_metrics") or entry.get("test_metrics_summary") or entry.get("horizons")

        if existing:
            existing.metrics = metrics
            existing.status = ModelStatus.active if entry.get("status") == "trained" else ModelStatus.failed
            existing.training_date = training_date
        else:
            row = ModelRegistry(
                model_name=entry.get("model_name", task_key),
                model_type=entry.get("model_type", "unknown"),
                version=entry.get("version", "1.0.0"),
                task=task_map[task_key],
                training_dataset=entry.get("training_dataset", "unknown"),
                training_date=training_date,
                metrics=metrics,
                artifact_path=str(artifact_dir_map[task_key]),
                status=ModelStatus.active if entry.get("status") == "trained" else ModelStatus.failed,
                extra_metadata=entry,
            )
            db.add(row)
        written += 1
    db.commit()
    logger.info("Synced %d model registry entries to database", written)
    return written

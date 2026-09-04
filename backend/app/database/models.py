"""
SQLAlchemy ORM models for the Smart Polyhouse backend.

Design notes
------------
- UUID primary keys (as PostgreSQL native UUID) for all business entities.
- All tables carry created_at / updated_at timestamps.
- Foreign keys + indexes are defined explicitly.
- This schema intentionally leaves room for Part 2 tables
  (recommendations, alerts, simulation_runs, decision_logs,
  environmental_risk, water_optimization, explainability_results) which
  will reference farms / polyhouses / sensor_readings / predictions
  defined here, without requiring migration of this Part 1 schema.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


def gen_uuid() -> uuid.UUID:
    return uuid.uuid4()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class UserRole(str, enum.Enum):
    admin = "admin"
    farmer = "farmer"
    researcher = "researcher"


class ModelTask(str, enum.Enum):
    disease_classification = "disease_classification"
    irrigation_calibration = "irrigation_calibration"
    irrigation_forecasting = "irrigation_forecasting"


class ModelStatus(str, enum.Enum):
    training = "training"
    trained = "trained"
    evaluated = "evaluated"
    active = "active"
    archived = "archived"
    failed = "failed"


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.farmer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    farms: Mapped[list["Farm"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Farms / Polyhouses / Crops
# ---------------------------------------------------------------------------
class Farm(Base, TimestampMixin):
    __tablename__ = "farms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="farms")
    polyhouses: Mapped[list["Polyhouse"]] = relationship(back_populates="farm", cascade="all, delete-orphan")


class Polyhouse(Base, TimestampMixin):
    __tablename__ = "polyhouses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    farm_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    area_sq_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    external_sensor_reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="e.g. Farm_ID value used in the irrigation dataset (Kolkata_Farm_1)"
    )

    farm: Mapped["Farm"] = relationship(back_populates="polyhouses")
    crops: Mapped[list["Crop"]] = relationship(back_populates="polyhouse", cascade="all, delete-orphan")
    sensor_readings: Mapped[list["SensorReading"]] = relationship(back_populates="polyhouse", cascade="all, delete-orphan")


class Crop(Base, TimestampMixin):
    __tablename__ = "crops"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    polyhouse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("polyhouses.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_name: Mapped[str] = mapped_column(String(120), nullable=False, comment="Canonical crop name, e.g. Tomato")
    variety: Mapped[str | None] = mapped_column(String(120), nullable=True)
    planted_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    polyhouse: Mapped["Polyhouse"] = relationship(back_populates="crops")
    stages: Mapped[list["CropStage"]] = relationship(back_populates="crop", cascade="all, delete-orphan")


class CropStage(Base, TimestampMixin):
    """Growth-stage timeline for a crop instance. Part 2's crop-stage
    adaptive AI will read/extend this table."""

    __tablename__ = "crop_stages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    crop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crops.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_name: Mapped[str] = mapped_column(String(120), nullable=False, comment="e.g. seedling, vegetative, flowering, fruiting")
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    crop: Mapped["Crop"] = relationship(back_populates="stages")


# ---------------------------------------------------------------------------
# Sensor readings (raw IoT input, mirrors irrigation dataset schema)
# ---------------------------------------------------------------------------
class SensorReading(Base, TimestampMixin):
    __tablename__ = "sensor_readings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    polyhouse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("polyhouses.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    raw_capacitive_adc: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensor_voltage_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensor_board_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    atm_pressure_inhg: Mapped[float | None] = mapped_column(Float, nullable=True)
    atm_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    soil_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    volumetric_moisture_pct: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Ground-truth/calibrated moisture if known"
    )

    polyhouse: Mapped["Polyhouse"] = relationship(back_populates="sensor_readings")

    __table_args__ = (
        Index("ix_sensor_readings_polyhouse_time", "polyhouse_id", "recorded_at"),
    )


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
class ModelRegistry(Base, TimestampMixin):
    """Central registry of trained model artifacts. All inference services
    resolve their active model through this table (or, when the DB is not
    configured, through the equivalent local JSON registry file) rather
    than hard-coding file paths."""

    __tablename__ = "model_registry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    model_name: Mapped[str] = mapped_column(String(150), nullable=False)
    model_type: Mapped[str] = mapped_column(String(80), nullable=False, comment="e.g. efficientnet_b0, random_forest, hist_gradient_boosting")
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    task: Mapped[ModelTask] = mapped_column(Enum(ModelTask, name="model_task"), nullable=False)
    training_dataset: Mapped[str] = mapped_column(String(255), nullable=False, comment="Manifest/config reference used for training")
    training_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ModelStatus] = mapped_column(Enum(ModelStatus, name="model_status"), default=ModelStatus.trained, nullable=False)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_name_version"),
        Index("ix_model_registry_task_status", "task", "status"),
    )


# ---------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------
class DiseasePrediction(Base, TimestampMixin):
    __tablename__ = "disease_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    polyhouse_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("polyhouses.id", ondelete="SET NULL"), nullable=True, index=True)
    model_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("model_registry.id", ondelete="SET NULL"), nullable=True)

    predicted_class: Mapped[str] = mapped_column(String(150), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    top_k: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="Top-K class:confidence pairs")
    canonical_crop: Mapped[str | None] = mapped_column(String(120), nullable=True)
    canonical_disease: Mapped[str | None] = mapped_column(String(150), nullable=True)
    image_reference: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="Stored filename/path reference, not the raw binary")


class IrrigationPrediction(Base, TimestampMixin):
    """Calibration-model predictions: raw sensor reading -> calibrated
    volumetric moisture percentage."""

    __tablename__ = "irrigation_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    polyhouse_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("polyhouses.id", ondelete="SET NULL"), nullable=True, index=True)
    sensor_reading_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sensor_readings.id", ondelete="SET NULL"), nullable=True)
    model_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("model_registry.id", ondelete="SET NULL"), nullable=True)

    predicted_volumetric_moisture_pct: Mapped[float] = mapped_column(Float, nullable=False)
    input_features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class ForecastResult(Base, TimestampMixin):
    """Multi-horizon soil moisture forecasting results."""

    __tablename__ = "forecast_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    polyhouse_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("polyhouses.id", ondelete="SET NULL"), nullable=True, index=True)
    model_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("model_registry.id", ondelete="SET NULL"), nullable=True)

    reference_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_moisture_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_1h: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_6h: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_12h: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class PredictionHistory(Base, TimestampMixin):
    """Generic append-only audit log across all prediction types, useful
    for dashboards and for Part 2's decision_logs / explainability layer
    to join against."""

    __tablename__ = "prediction_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    prediction_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="disease | irrigation_calibration | irrigation_forecast")
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, comment="FK to the specific prediction row (polymorphic)")
    summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_prediction_history_type_ref", "prediction_type", "reference_id"),
    )


# ---------------------------------------------------------------------------
# Part 2: Recommendations & Alerts
# ---------------------------------------------------------------------------
class RecommendationStatus(str, enum.Enum):
    normal = "NORMAL"
    monitor = "MONITOR"
    irrigation_recommended = "IRRIGATION_RECOMMENDED"
    high_water_stress_risk = "HIGH_WATER_STRESS_RISK"


class RecommendationUrgency(str, enum.Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
    critical = "CRITICAL"


class Recommendation(Base, TimestampMixin):
    """Persisted output of the Irrigation Decision Engine (and, in future,
    other decision engines). Kept separate from ForecastResult /
    IrrigationPrediction because a recommendation is a RULE-BASED
    INTERPRETATION layered on top of model predictions, not a model
    prediction itself - the distinction the Part 2 spec requires the API
    to preserve (prediction vs. measured state vs. rule-based
    interpretation vs. recommendation)."""

    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    polyhouse_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("polyhouses.id", ondelete="CASCADE"), nullable=True, index=True)
    forecast_result_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("forecast_results.id", ondelete="SET NULL"), nullable=True)

    domain: Mapped[str] = mapped_column(String(50), nullable=False, default="irrigation", comment="irrigation | disease | combined")
    status: Mapped[RecommendationStatus] = mapped_column(Enum(RecommendationStatus, name="recommendation_status"), nullable=False)
    urgency: Mapped[RecommendationUrgency] = mapped_column(Enum(RecommendationUrgency, name="recommendation_urgency"), nullable=False)
    recommendation_text: Mapped[str] = mapped_column(String(500), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    risk_factors: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="List of named risk factors that contributed")
    inputs_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="The current_moisture/forecast/etc. values used to derive this recommendation")
    model_confidence: Mapped[float | None] = mapped_column(Float, nullable=True, comment="Only set when a real model-derived confidence exists; null otherwise")

    __table_args__ = (
        Index("ix_recommendations_polyhouse_created", "polyhouse_id", "created_at"),
    )


class AlertSeverity(str, enum.Enum):
    info = "INFO"
    warning = "WARNING"
    high = "HIGH"
    critical = "CRITICAL"


class AlertStatus(str, enum.Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"


class Alert(Base, TimestampMixin):
    """Backend-generated alerts (water stress risk, stale sensor data,
    model unavailability, abnormal readings, etc.). Never generated from
    fabricated data - always traceable to a real recommendation, sensor
    reading, or model-status check via `source_reference`."""

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    polyhouse_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("polyhouses.id", ondelete="CASCADE"), nullable=True, index=True)
    alert_type: Mapped[str] = mapped_column(String(80), nullable=False, comment="e.g. water_stress, sensor_stale, model_unavailable, abnormal_reading")
    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity, name="alert_severity"), nullable=False)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus, name="alert_status"), default=AlertStatus.active, nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    source_reference: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="Traceability: which recommendation/reading/model-check produced this alert")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_alerts_polyhouse_status", "polyhouse_id", "status"),
        Index("ix_alerts_severity_status", "severity", "status"),
    )

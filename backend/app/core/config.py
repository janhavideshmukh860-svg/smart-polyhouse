"""
Centralized application configuration.

All configuration is loaded from environment variables (via a .env file in
development). Nothing sensitive is hard-coded. See `.env.example` for the
full list of supported variables.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = backend/ (two levels up from this file: app/core/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Application ----
    APP_NAME: str = "Smart Polyhouse Backend"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    APP_VERSION: str = "1.0.0-part1"

    # ---- Server ----
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ---- Database ----
    DATABASE_URL: str = "postgresql+psycopg2://postgres:password@localhost:5432/smart_polyhouse"
    ALLOW_START_WITHOUT_DB: bool = True
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # ---- JWT ----
    JWT_SECRET_KEY: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080

    # ---- CORS ----
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"

    # ---- Dataset / Model Paths ----
    DATASET_ROOT: str = "./dataset/06_final_dataset"
    DISEASE_DATASET_ROOT: str = "./dataset/06_final_dataset/disease"
    IRRIGATION_DATASET_ROOT: str = "./dataset/06_final_dataset/irrigation"
    MODEL_ARTIFACT_ROOT: str = "./ml_models"

    # ---- Logging ----
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    # ---- Disease training defaults ----
    DISEASE_IMAGE_SIZE: int = 224
    DISEASE_BATCH_SIZE: int = 32
    DISEASE_EPOCHS: int = 15
    DISEASE_LEARNING_RATE: float = 3e-4
    DISEASE_NUM_WORKERS: int = 2

    # ---- Irrigation Decision Engine thresholds (Part 2) ----
    # All thresholds are percentages of Volumetric_Moisture_Pct unless
    # noted otherwise. Centralized here (rather than scattered as magic
    # numbers in service code) so they are documented, configurable per
    # deployment/crop, and visible to anyone auditing the recommendation
    # logic. These are conservative, commonly-used agronomic rule-of-thumb
    # bands for general polyhouse vegetable crops - NOT derived from a
    # crop-specific field trial, and should be tuned per crop/soil type in
    # a real deployment.
    IRRIGATION_CRITICAL_MOISTURE_PCT: float = 12.0   # below this now = high stress
    IRRIGATION_LOW_MOISTURE_PCT: float = 18.0        # below this now = recommend irrigation
    IRRIGATION_MONITOR_MOISTURE_PCT: float = 24.0    # below this now = monitor
    IRRIGATION_DECLINE_RATE_WARNING_PCT: float = 4.0 # projected drop (current -> 6h) that triggers MONITOR/warning
    IRRIGATION_DECLINE_RATE_CRITICAL_PCT: float = 8.0  # projected drop (current -> 12h) that triggers HIGH risk

    # ---- Sensor data freshness (Part 2 dashboard/alerts) ----
    SENSOR_STALE_AFTER_MINUTES: int = 120

    @field_validator("APP_ENV")
    @classmethod
    def _validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}")
        return v

    @model_validator(mode="after")
    def _reject_default_secret_in_production(self) -> "Settings":
        if self.APP_ENV == "production" and self.JWT_SECRET_KEY == "CHANGE_ME_TO_A_LONG_RANDOM_SECRET":
            raise ValueError(
                "JWT_SECRET_KEY must be set to a strong random value when APP_ENV=production."
            )
        if self.APP_ENV == "production" and "*" in self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must list explicit origins when APP_ENV=production.")
        return self

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def resolve_path(self, relative: str) -> Path:
        """Resolve a configured path relative to the project root if it is
        not already absolute."""
        p = Path(relative)
        if p.is_absolute():
            return p
        return (PROJECT_ROOT / p).resolve()

    @property
    def dataset_root_path(self) -> Path:
        return self.resolve_path(self.DATASET_ROOT)

    @property
    def disease_dataset_root_path(self) -> Path:
        return self.resolve_path(self.DISEASE_DATASET_ROOT)

    @property
    def irrigation_dataset_root_path(self) -> Path:
        return self.resolve_path(self.IRRIGATION_DATASET_ROOT)

    @property
    def model_artifact_root_path(self) -> Path:
        return self.resolve_path(self.MODEL_ARTIFACT_ROOT)


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor - use as a FastAPI dependency or module-level call."""
    return Settings()


settings = get_settings()

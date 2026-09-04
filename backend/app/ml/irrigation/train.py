"""
Trains and evaluates:
  1. The soil moisture calibration model.
  2. Four independent soil moisture forecasting models (1h/6h/12h/24h).

Usage:
    python -m app.ml.irrigation.train                # trains both
    python -m app.ml.irrigation.train --only calibration
    python -m app.ml.irrigation.train --only forecasting

All splits are used exactly as provided (no reshuffling). Scalers are fit
on the training split only. Metrics are computed on validation (for model
selection reporting) and on the held-out test split (final, reported
once). Nothing here fabricates results - if a split file is missing this
script raises rather than substituting synthetic data.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger
from app.ml.irrigation import calibration as calib_mod
from app.ml.irrigation import forecasting as fcst_mod
from app.ml.irrigation.evaluate import regression_metrics
from app.ml.irrigation.preprocessing import (
    CALIBRATION_FEATURE_COLUMNS,
    CALIBRATION_TARGET_COLUMN,
    FORECASTING_HORIZON_STEPS,
    fit_scaler,
    forecasting_feature_columns,
    load_calibration_split,
    load_forecasting_split,
)

logger = get_logger(__name__)

MODEL_VERSION = "1.0.0"


def _artifact_dir(*parts: str) -> Path:
    p = settings.model_artifact_root_path.joinpath(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p


def train_calibration_model() -> dict:
    logger.info("Loading calibration splits ...")
    train_df = load_calibration_split("train")
    val_df = load_calibration_split("validation")
    test_df = load_calibration_split("test")
    logger.info(
        "Calibration splits loaded: train=%d validation=%d test=%d",
        len(train_df), len(val_df), len(test_df),
    )

    fitted_scaler = fit_scaler(train_df, CALIBRATION_FEATURE_COLUMNS)

    X_train = fitted_scaler.transform(train_df)
    y_train = train_df[CALIBRATION_TARGET_COLUMN]
    X_val = fitted_scaler.transform(val_df)
    y_val = val_df[CALIBRATION_TARGET_COLUMN]
    X_test = fitted_scaler.transform(test_df)
    y_test = test_df[CALIBRATION_TARGET_COLUMN]

    # Baseline
    baseline = calib_mod.build_baseline_model()
    baseline.fit(X_train, y_train)
    baseline_val_metrics = regression_metrics(y_val, baseline.predict(X_val))
    logger.info("Baseline (LinearRegression) validation metrics: %s", baseline_val_metrics)

    # Selected model
    model = calib_mod.build_calibration_model()
    model.fit(X_train, y_train)
    val_metrics = regression_metrics(y_val, model.predict(X_val))
    test_metrics = regression_metrics(y_test, model.predict(X_test))
    logger.info("HistGradientBoostingRegressor validation metrics: %s", val_metrics)
    logger.info("HistGradientBoostingRegressor TEST metrics (final): %s", test_metrics)

    out_dir = _artifact_dir("irrigation", "calibration")
    joblib.dump(model, out_dir / "model.joblib")
    joblib.dump(fitted_scaler.scaler, out_dir / "scaler.joblib")

    metadata = {
        "model_name": "irrigation_calibration",
        "model_type": "hist_gradient_boosting_regressor",
        "version": MODEL_VERSION,
        "task": "irrigation_calibration",
        "target_column": CALIBRATION_TARGET_COLUMN,
        "feature_columns": CALIBRATION_FEATURE_COLUMNS,
        "training_dataset": "06_final_dataset/irrigation/calibration/{train,validation,test}.csv",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "random_seed": calib_mod.RANDOM_SEED,
        "dataset_sizes": {"train": len(train_df), "validation": len(val_df), "test": len(test_df)},
        "baseline_model": "linear_regression",
        "baseline_validation_metrics": baseline_val_metrics,
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
        "status": "trained",
    }
    with open(out_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    with open(out_dir / "feature_list.json", "w") as f:
        json.dump(CALIBRATION_FEATURE_COLUMNS, f, indent=2)

    logger.info("Calibration model artifacts saved to %s", out_dir)
    return metadata


def train_forecasting_models() -> dict:
    logger.info("Loading forecasting splits ...")
    train_df = load_forecasting_split("train")
    val_df = load_forecasting_split("validation")
    test_df = load_forecasting_split("test")
    logger.info(
        "Forecasting splits loaded: train=%d validation=%d test=%d",
        len(train_df), len(val_df), len(test_df),
    )

    feature_cols = forecasting_feature_columns(train_df)
    logger.info("Forecasting feature columns (%d): %s", len(feature_cols), feature_cols)

    fitted_scaler = fit_scaler(train_df, feature_cols)
    X_train = fitted_scaler.transform(train_df)
    X_val = fitted_scaler.transform(val_df)
    X_test = fitted_scaler.transform(test_df)

    out_dir = _artifact_dir("irrigation", "forecasting")
    joblib.dump(fitted_scaler.scaler, out_dir / "scaler.joblib")
    with open(out_dir / "feature_list.json", "w") as f:
        json.dump(feature_cols, f, indent=2)

    horizon_results = {}
    for horizon in fcst_mod.HORIZONS:
        target_col = f"target_moisture_{horizon}"
        logger.info("Training forecasting model for horizon=%s (target=%s) ...", horizon, target_col)

        y_train = train_df[target_col]
        y_val = val_df[target_col]
        y_test = test_df[target_col]

        baseline = fcst_mod.build_baseline_model()
        baseline.fit(X_train, y_train)
        baseline_val_metrics = regression_metrics(y_val, baseline.predict(X_val))

        model = fcst_mod.build_forecast_model(horizon)
        model.fit(X_train, y_train)
        val_metrics = regression_metrics(y_val, model.predict(X_val))
        test_metrics = regression_metrics(y_test, model.predict(X_test))

        logger.info("Horizon %s -> validation: %s | test: %s", horizon, val_metrics, test_metrics)

        horizon_dir = _artifact_dir("irrigation", "forecasting", horizon)
        joblib.dump(model, horizon_dir / "model.joblib")

        horizon_meta = {
            "horizon": horizon,
            "steps_ahead": FORECASTING_HORIZON_STEPS[horizon],
            "target_column": target_col,
            "baseline_model": "linear_regression",
            "baseline_validation_metrics": baseline_val_metrics,
            "validation_metrics": val_metrics,
            "test_metrics": test_metrics,
        }
        with open(horizon_dir / "metadata.json", "w") as f:
            json.dump(horizon_meta, f, indent=2)

        horizon_results[horizon] = horizon_meta

    metadata = {
        "model_name": "irrigation_forecasting",
        "model_type": "hist_gradient_boosting_regressor_per_horizon",
        "version": MODEL_VERSION,
        "task": "irrigation_forecasting",
        "feature_columns": feature_cols,
        "training_dataset": "06_final_dataset/irrigation/forecasting/{train,validation,test}.csv",
        "training_date": datetime.now(timezone.utc).isoformat(),
        "random_seed": fcst_mod.RANDOM_SEED,
        "dataset_sizes": {"train": len(train_df), "validation": len(val_df), "test": len(test_df)},
        "horizons": horizon_results,
        "status": "trained",
    }
    with open(out_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Forecasting model artifacts saved to %s", out_dir)
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Train irrigation ML models")
    parser.add_argument("--only", choices=["calibration", "forecasting"], default=None)
    args = parser.parse_args()

    results = {}
    if args.only in (None, "calibration"):
        results["calibration"] = train_calibration_model()
    if args.only in (None, "forecasting"):
        results["forecasting"] = train_forecasting_models()

    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()

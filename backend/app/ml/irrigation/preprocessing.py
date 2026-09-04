"""
Shared preprocessing utilities for the irrigation calibration and
forecasting pipelines.

Both pipelines read the authoritative, pre-split CSV files exactly as
provided in the dataset package:

    06_final_dataset/irrigation/calibration/{train,validation,test}.csv
    06_final_dataset/irrigation/forecasting/{train,validation,test}.csv

No reshuffling, re-splitting, or synthetic augmentation is performed here.
Scaling is always fit on the training split only, then applied to
validation/test, per the dataset card's leakage rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
from sklearn.preprocessing import StandardScaler

from app.core.config import settings

CALIBRATION_FEATURE_COLUMNS: List[str] = [
    "Raw_Capacitive_ADC",
    "Sensor_Voltage_V",
    "Sensor_Board_Temperature_C",
    "Atm_Pressure_inHg",
    "Atm_Temperature_C",
    "Soil_Temperature_C",
    "Hour",
    "Day",
    "Month",
    "DayOfWeek",
    "DayOfYear",
    "Hour_sin",
    "Hour_cos",
    "Day_sin",
    "Day_cos",
]
CALIBRATION_TARGET_COLUMN = "Volumetric_Moisture_Pct"

# Forecasting: features are every column in the flattened per-timestep
# dataset EXCEPT identifiers/timestamp and the four future target columns.
# This avoids leaking the targets themselves back in as features while
# using everything else the dataset card documents as available at
# prediction time (the "current" observation).
FORECASTING_TARGET_COLUMNS: List[str] = [
    "target_moisture_1h",
    "target_moisture_6h",
    "target_moisture_12h",
    "target_moisture_24h",
]
FORECASTING_NON_FEATURE_COLUMNS: List[str] = ["Timestamp", "Farm_ID"] + FORECASTING_TARGET_COLUMNS
FORECASTING_HORIZON_STEPS = {
    "1h": 4,
    "6h": 24,
    "12h": 48,
    "24h": 96,
}


def load_calibration_split(split: str) -> pd.DataFrame:
    """split in {'train', 'validation', 'test'}"""
    path = settings.irrigation_dataset_root_path / "calibration" / f"{split}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Calibration split not found: {path}")
    return pd.read_csv(path)


def load_forecasting_split(split: str) -> pd.DataFrame:
    path = settings.irrigation_dataset_root_path / "forecasting" / f"{split}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Forecasting split not found: {path}")
    df = pd.read_csv(path, parse_dates=["Timestamp"])
    return df


def forecasting_feature_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if c not in FORECASTING_NON_FEATURE_COLUMNS]


@dataclass
class FittedScaler:
    scaler: StandardScaler
    feature_names: List[str]

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        arr = self.scaler.transform(df[self.feature_names])
        return pd.DataFrame(arr, columns=self.feature_names, index=df.index)


def fit_scaler(train_df: pd.DataFrame, feature_names: List[str]) -> FittedScaler:
    scaler = StandardScaler()
    scaler.fit(train_df[feature_names])
    return FittedScaler(scaler=scaler, feature_names=feature_names)

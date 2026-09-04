"""
Soil moisture calibration model.

Task: regression, Raw sensor + environmental readings -> calibrated
Volumetric_Moisture_Pct.

Model choice: scikit-learn HistGradientBoostingRegressor.
Rationale: tabular data with ~15 numeric/cyclical features and ~15k
training rows. Gradient-boosted trees handle this regime well without GPU
requirements, train in seconds on a laptop, and are a common, defensible
choice for this data size/shape. A plain LinearRegression baseline is
also trained for comparison so the improvement from the chosen model is
demonstrated rather than assumed.
"""
from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression

RANDOM_SEED = 42


def build_baseline_model() -> LinearRegression:
    return LinearRegression()


def build_calibration_model() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        max_iter=300,
        max_depth=8,
        learning_rate=0.05,
        l2_regularization=0.1,
        random_state=RANDOM_SEED,
    )

"""
Multi-horizon soil moisture forecasting models.

Dataset shape: the authoritative forecasting dataset is already provided
as one row per 15-minute timestep, where each row carries the CURRENT
sensor/environmental/soil state plus four future target columns
(target_moisture_1h/6h/12h/24h) that were pre-computed upstream from the
raw chronological series (per the dataset card: 1h = 4 steps ahead, 6h =
24 steps, 12h = 48 steps, 24h = 96 steps, computed independently per
farm).

Because the target engineering (the "look-ahead" step) has already been
performed in the supplied dataset and the provided train/validation/test
files are contiguous, non-shuffled, per-farm-safe slices of that series,
a tabular gradient-boosting model trained directly on this flattened
representation is a faithful, leakage-safe way to model this data - each
row's target was computed strictly from later timestamps than its
features, and rows are never mixed across the train/validation/test
boundary.

An LSTM/sequence model that re-derives rolling windows from the raw
series is a reasonable Part 2 extension (noted in the README), but is not
required to make correct use of the dataset as delivered, and was not
implemented in Part 1 to avoid introducing a second, undocumented
windowing procedure alongside the one already baked into this dataset.

One independent model is trained per horizon so each can be loaded,
retrained, or replaced without affecting the others.
"""
from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression

RANDOM_SEED = 42

HORIZONS = ["1h", "6h", "12h", "24h"]


def build_baseline_model() -> LinearRegression:
    return LinearRegression()


def build_forecast_model(horizon: str) -> HistGradientBoostingRegressor:
    # Slightly shallower / fewer iterations for longer horizons where the
    # signal-to-noise ratio is lower, to reduce overfitting risk.
    depth_by_horizon = {"1h": 8, "6h": 7, "12h": 6, "24h": 6}
    iters_by_horizon = {"1h": 300, "6h": 300, "12h": 250, "24h": 250}
    return HistGradientBoostingRegressor(
        max_iter=iters_by_horizon.get(horizon, 250),
        max_depth=depth_by_horizon.get(horizon, 6),
        learning_rate=0.05,
        l2_regularization=0.1,
        random_state=RANDOM_SEED,
    )

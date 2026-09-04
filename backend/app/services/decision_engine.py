"""
Irrigation Decision Engine.

This module turns ML MODEL OUTPUTS (current calibrated moisture + 1h/6h/
12h/24h forecasts) into a RULE-BASED INTERPRETATION and, from that, an
actionable recommendation. These are deliberately kept as distinct
concepts throughout this module and its output schema, per the Part 2
requirement to not blur "model prediction" with "rule-based
interpretation" with "recommendation":

    MEASURED/CALIBRATED STATE  -> current_moisture_pct (from the
                                   calibration model, itself derived from
                                   a real sensor reading)
    MODEL PREDICTION           -> forecast_1h/6h/12h/24h (from the
                                   forecasting models)
    RULE-BASED INTERPRETATION  -> risk_factors + status (threshold logic
                                   below, NOT a model prediction)
    RECOMMENDATION              -> recommendation_text + urgency + reason

No irrigation QUANTITY (liters, duration) is produced, per the explicit
"do not fabricate liters" requirement - there is no flow-rate/actuator
data in this project to ground such a number in.

model_confidence is always None here: HistGradientBoostingRegressor
regression models do not produce a calibrated probability/confidence
estimate, so fabricating one would violate the no-fabrication rule. If a
future model (e.g. a quantile/probabilistic regressor) can genuinely
produce one, wire it in here explicitly rather than defaulting to a
placeholder number.

Thresholds are centralized in app.core.config.Settings
(IRRIGATION_CRITICAL_MOISTURE_PCT etc.) rather than hard-coded here, so
they're documented and adjustable per deployment/crop without touching
this logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.config import settings
from app.database.models import RecommendationStatus, RecommendationUrgency


@dataclass
class IrrigationDecision:
    status: RecommendationStatus
    urgency: RecommendationUrgency
    recommendation_text: str
    reason: str
    risk_factors: List[str] = field(default_factory=list)
    model_confidence: Optional[float] = None


def evaluate_irrigation_decision(
    current_moisture_pct: float,
    forecast: Dict[str, float],
) -> IrrigationDecision:
    """
    forecast: dict with keys '1h', '6h', '12h', '24h' (values may be
    missing if a given horizon model wasn't available - handled
    defensively below rather than assuming all four are present).
    """
    critical = settings.IRRIGATION_CRITICAL_MOISTURE_PCT
    low = settings.IRRIGATION_LOW_MOISTURE_PCT
    monitor = settings.IRRIGATION_MONITOR_MOISTURE_PCT
    decline_warn = settings.IRRIGATION_DECLINE_RATE_WARNING_PCT
    decline_critical = settings.IRRIGATION_DECLINE_RATE_CRITICAL_PCT

    f6 = forecast.get("6h")
    f12 = forecast.get("12h")

    risk_factors: List[str] = []

    # --- 1. Current measured/calibrated state is already critical ---
    if current_moisture_pct < critical:
        risk_factors.append(
            f"Current calibrated moisture ({current_moisture_pct:.2f}%) is below the "
            f"configured critical threshold ({critical:.2f}%)."
        )
        return IrrigationDecision(
            status=RecommendationStatus.high_water_stress_risk,
            urgency=RecommendationUrgency.critical,
            recommendation_text="Irrigate immediately - high water stress risk.",
            reason=(
                f"Current soil moisture ({current_moisture_pct:.2f}%) is already below the "
                f"critical operational threshold of {critical:.2f}%. Plants are at immediate "
                "risk of water stress based on the calibrated sensor reading alone, independent "
                "of any forecast."
            ),
            risk_factors=risk_factors,
        )

    # --- 2. Current state is low (below the "recommend irrigation" band) ---
    if current_moisture_pct < low:
        risk_factors.append(
            f"Current calibrated moisture ({current_moisture_pct:.2f}%) is below the "
            f"low-moisture threshold ({low:.2f}%)."
        )
        return IrrigationDecision(
            status=RecommendationStatus.irrigation_recommended,
            urgency=RecommendationUrgency.high,
            recommendation_text="Irrigation recommended soon.",
            reason=(
                f"Current soil moisture ({current_moisture_pct:.2f}%) has fallen below the "
                f"configured low-moisture threshold ({low:.2f}%), which typically precedes "
                "water stress if left unaddressed."
            ),
            risk_factors=risk_factors,
        )

    # --- 3. Forecast-driven checks (current state is OK for now) ---
    if f12 is not None and f12 < critical:
        risk_factors.append(
            f"12h forecast ({f12:.2f}%) is projected to fall below the critical threshold ({critical:.2f}%)."
        )
        return IrrigationDecision(
            status=RecommendationStatus.high_water_stress_risk,
            urgency=RecommendationUrgency.high,
            recommendation_text="Plan irrigation proactively - moisture projected to reach critical levels within 12 hours.",
            reason=(
                f"Current moisture ({current_moisture_pct:.2f}%) is currently acceptable, but the "
                f"12-hour forecast model projects a decline to {f12:.2f}%, which is below the "
                f"critical threshold ({critical:.2f}%). Proactive irrigation is recommended to "
                "avoid reaching a high-stress state."
            ),
            risk_factors=risk_factors,
        )

    if f6 is not None and f6 < low:
        risk_factors.append(
            f"6h forecast ({f6:.2f}%) is projected to fall below the low-moisture threshold ({low:.2f}%)."
        )
        return IrrigationDecision(
            status=RecommendationStatus.irrigation_recommended,
            urgency=RecommendationUrgency.medium,
            recommendation_text="Irrigation recommended within the next few hours.",
            reason=(
                f"Current moisture ({current_moisture_pct:.2f}%) is acceptable, but the 6-hour "
                f"forecast model projects a decline to {f6:.2f}%, below the low-moisture threshold "
                f"({low:.2f}%)."
            ),
            risk_factors=risk_factors,
        )

    decline_12h = (current_moisture_pct - f12) if f12 is not None else None
    if decline_12h is not None and decline_12h >= decline_critical:
        risk_factors.append(
            f"Projected 12h decline of {decline_12h:.2f} percentage points exceeds the "
            f"configured rapid-decline threshold ({decline_critical:.2f})."
        )
        return IrrigationDecision(
            status=RecommendationStatus.monitor,
            urgency=RecommendationUrgency.medium,
            recommendation_text="Monitor closely - rapid moisture decline projected.",
            reason=(
                f"The forecast model projects a rapid decline of {decline_12h:.2f} percentage "
                f"points over the next 12 hours (from {current_moisture_pct:.2f}% to {f12:.2f}%), "
                "which exceeds the configured rapid-decline warning rate even though absolute "
                "levels remain above the low-moisture threshold for now."
            ),
            risk_factors=risk_factors,
        )

    decline_6h = (current_moisture_pct - f6) if f6 is not None else None
    if current_moisture_pct < monitor or (decline_6h is not None and decline_6h >= decline_warn):
        if current_moisture_pct < monitor:
            risk_factors.append(
                f"Current moisture ({current_moisture_pct:.2f}%) is below the monitor threshold ({monitor:.2f}%)."
            )
        if decline_6h is not None and decline_6h >= decline_warn:
            risk_factors.append(
                f"Projected 6h decline of {decline_6h:.2f} percentage points exceeds the warning rate ({decline_warn:.2f})."
            )
        return IrrigationDecision(
            status=RecommendationStatus.monitor,
            urgency=RecommendationUrgency.low,
            recommendation_text="Continue monitoring - conditions are within range but approaching a lower threshold.",
            reason=(
                f"Current moisture ({current_moisture_pct:.2f}%) and/or its short-term forecast "
                "trend are approaching the configured lower thresholds. No immediate action is "
                "required, but conditions should be monitored."
            ),
            risk_factors=risk_factors,
        )

    # --- 4. Everything within normal range ---
    return IrrigationDecision(
        status=RecommendationStatus.normal,
        urgency=RecommendationUrgency.low,
        recommendation_text="No action needed - moisture levels are within the normal operating range.",
        reason=(
            f"Current moisture ({current_moisture_pct:.2f}%) and the forecast horizons available "
            f"(6h={f6 if f6 is not None else 'N/A'}, 12h={f12 if f12 is not None else 'N/A'}) all "
            "remain above the configured monitor threshold."
        ),
        risk_factors=[],
    )

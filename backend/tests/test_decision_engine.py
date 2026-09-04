"""
Unit tests for the pure rule-based decision engine logic - no DB, no
network, exercises real threshold branching against the configured
values in app.core.config.settings.
"""
from app.core.config import settings
from app.database.models import RecommendationStatus, RecommendationUrgency
from app.services.decision_engine import evaluate_irrigation_decision


def test_current_moisture_below_critical_triggers_high_stress():
    critical = settings.IRRIGATION_CRITICAL_MOISTURE_PCT
    decision = evaluate_irrigation_decision(critical - 1, {"1h": critical - 1, "6h": critical - 2, "12h": critical - 3, "24h": critical - 4})
    assert decision.status == RecommendationStatus.high_water_stress_risk
    assert decision.urgency == RecommendationUrgency.critical
    assert len(decision.risk_factors) >= 1
    assert decision.model_confidence is None  # never fabricated


def test_current_moisture_below_low_triggers_irrigation_recommended():
    low = settings.IRRIGATION_LOW_MOISTURE_PCT
    critical = settings.IRRIGATION_CRITICAL_MOISTURE_PCT
    moisture = (low + critical) / 2  # between critical and low
    decision = evaluate_irrigation_decision(moisture, {"1h": moisture, "6h": moisture + 1, "12h": moisture + 2, "24h": moisture + 3})
    assert decision.status == RecommendationStatus.irrigation_recommended
    assert decision.urgency == RecommendationUrgency.high


def test_healthy_current_and_forecast_returns_normal():
    monitor = settings.IRRIGATION_MONITOR_MOISTURE_PCT
    healthy = monitor + 20
    decision = evaluate_irrigation_decision(healthy, {"1h": healthy, "6h": healthy - 0.5, "12h": healthy - 1, "24h": healthy - 1.5})
    assert decision.status == RecommendationStatus.normal
    assert decision.urgency == RecommendationUrgency.low
    assert decision.risk_factors == []


def test_forecast_driven_critical_risk_even_if_current_is_fine():
    monitor = settings.IRRIGATION_MONITOR_MOISTURE_PCT
    critical = settings.IRRIGATION_CRITICAL_MOISTURE_PCT
    current = monitor + 10
    decision = evaluate_irrigation_decision(current, {"1h": current - 2, "6h": current - 8, "12h": critical - 1, "24h": critical - 5})
    assert decision.status == RecommendationStatus.high_water_stress_risk
    assert decision.urgency == RecommendationUrgency.high
    assert "12h" in decision.reason or "12-hour" in decision.reason


def test_missing_forecast_horizons_handled_gracefully():
    """The engine must not crash if some horizon keys are absent (e.g. a
    horizon model failed to load) - it should just skip forecast-based
    checks rather than raising."""
    monitor = settings.IRRIGATION_MONITOR_MOISTURE_PCT
    healthy = monitor + 20
    decision = evaluate_irrigation_decision(healthy, {})
    assert decision.status == RecommendationStatus.normal


def test_model_confidence_is_always_none_never_fabricated():
    for moisture in [5, 15, 20, 30, 50]:
        decision = evaluate_irrigation_decision(moisture, {"1h": moisture, "6h": moisture, "12h": moisture, "24h": moisture})
        assert decision.model_confidence is None

"""
These tests exercise the REAL trained irrigation model artifacts produced
by `python -m app.ml.irrigation.train` (checked into ml_models/irrigation/
for this checkpoint). They are skipped automatically if artifacts are
absent (e.g. a fresh clone before running training), rather than faking
a pass.
"""
import pytest

from app.ml.irrigation.inference import calibration_service, forecasting_service

VALID_CALIBRATION_PAYLOAD = {
    "Raw_Capacitive_ADC": 704,
    "Sensor_Voltage_V": 2.271,
    "Sensor_Board_Temperature_C": 17.02,
    "Atm_Pressure_inHg": 30.02,
    "Atm_Temperature_C": 16.38,
    "Soil_Temperature_C": 19.21,
    "Hour": 0,
    "Day": 5,
    "Month": 1,
    "DayOfWeek": 6,
    "DayOfYear": 5,
}

VALID_FORECAST_PAYLOAD = {
    "Farm_ID": "Kolkata_Farm_1",
    "Volumetric_Moisture_Pct": 16.44,
    "Sensor_Board_Temperature_C": 17.0,
    "Raw_Capacitive_ADC": 700.0,
    "Sensor_Voltage_V": 2.27,
    "Atm_Pressure_inHg": 30.0,
    "Atm_Temperature_C": 16.0,
    "Soil_Temperature_C": 19.0,
    "SM_Level_15cm": 1.0,
    "SM_Volume_15cm": 1.0,
    "SM_Aggregate_Pct": 16.0,
    "SM_Volume_Pct": 16.0,
    "Hour": 0,
    "Day": 5,
    "Month": 1,
    "DayOfWeek": 6,
    "DayOfYear": 5,
    "Hour_sin": 0.0,
    "Hour_cos": 1.0,
    "Day_sin": 0.09,
    "Day_cos": 0.99,
}

requires_calibration_model = pytest.mark.skipif(
    not calibration_service.is_available(), reason="Calibration model artifacts not trained in this environment"
)
requires_forecasting_models = pytest.mark.skipif(
    not forecasting_service.is_available(), reason="Forecasting model artifacts not trained in this environment"
)


@requires_calibration_model
def test_calibrate_endpoint_returns_numeric_prediction(client):
    resp = client.post("/api/v1/irrigation/calibrate", json=VALID_CALIBRATION_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["predicted_volumetric_moisture_pct"], float)
    # Sanity bound: moisture percentage should be within a plausible range.
    assert -50 < body["predicted_volumetric_moisture_pct"] < 150
    assert body["model"]["task"] == "irrigation_calibration"


def test_calibrate_endpoint_rejects_missing_fields(client):
    resp = client.post("/api/v1/irrigation/calibrate", json={"Raw_Capacitive_ADC": 704})
    assert resp.status_code == 422


@requires_forecasting_models
def test_forecast_predict_endpoint_returns_all_horizons(client):
    resp = client.post("/api/v1/irrigation/predict", json=VALID_FORECAST_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    for key in ("forecast_1h", "forecast_6h", "forecast_12h", "forecast_24h"):
        assert isinstance(body[key], float)


@requires_forecasting_models
def test_forecast_get_example_endpoint_works(client):
    resp = client.get("/api/v1/irrigation/forecast")
    assert resp.status_code == 200
    body = resp.json()
    assert "forecast_1h" in body and "forecast_24h" in body


def test_predict_endpoint_rejects_invalid_request(client):
    resp = client.post("/api/v1/irrigation/predict", json={"Farm_ID": "X"})
    assert resp.status_code == 422

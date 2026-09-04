def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "timestamp" in body


def test_system_status_endpoint(client):
    resp = client.get("/api/v1/system/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["backend_status"] == "ok"
    assert "database" in body
    assert "disease_model" in body
    assert "irrigation_calibration_model" in body
    assert "irrigation_forecasting_models" in body
    # These booleans reflect real on-disk artifact/DB state, not a mock.
    assert isinstance(body["database"]["available"], bool)
    assert isinstance(body["irrigation_calibration_model"]["available"], bool)


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "service" in resp.json()

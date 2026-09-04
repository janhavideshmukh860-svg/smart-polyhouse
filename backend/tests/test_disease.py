"""
Tests for the disease detection endpoints. Since this environment's
dataset package is metadata-only (no raw images), the model is expected
to be unavailable here - these tests verify the API reports that
correctly (503) rather than crashing or fabricating a prediction, plus
exercise the class-list endpoint which only needs the manifest CSVs.
"""
import io
import uuid

import pytest

from app.api.deps import get_current_active_user
from app.database.models import User, UserRole
from app.main import app
from app.ml.disease.inference import disease_inference_service


@pytest.fixture()
def auth_client(client):
    """Disease prediction now requires authentication (uploads are no
    longer an anonymous endpoint). These tests exercise upload validation
    and the honest model-unavailable path, so the authenticated user is
    supplied via a dependency override rather than a live database."""

    def _fake_user() -> User:
        return User(
            id=uuid.uuid4(),
            email="tester@example.com",
            full_name="Test User",
            hashed_password="x",
            role=UserRole.farmer,
            is_active=True,
        )

    app.dependency_overrides[get_current_active_user] = _fake_user
    yield client
    app.dependency_overrides.pop(get_current_active_user, None)


def test_list_classes_returns_38_canonical_classes(client):
    resp = client.get("/api/v1/disease/classes")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_classes"] == 38
    assert len(body["classes"]) == 38
    assert all("final_class" in c and "canonical_crop" in c for c in body["classes"])


def test_predict_rejects_non_image_content_type(auth_client):
    resp = auth_client.post(
        "/api/v1/disease/predict",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
    )
    assert resp.status_code == 415


def test_predict_rejects_empty_file(auth_client):
    resp = auth_client.post(
        "/api/v1/disease/predict",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
    )
    assert resp.status_code == 400


def test_predict_reports_model_unavailable_when_untrained(auth_client):
    """This test documents Part 1's honest current state: no raw image
    dataset was supplied, so no disease model has been trained, and the
    API must say so (503) rather than returning a fabricated result."""
    if disease_inference_service.is_available():
        pytest.skip("A trained disease model IS available in this environment; skipping the unavailable-path test.")

    fake_jpeg_bytes = b"\xff\xd8\xff\xe0" + b"0" * 100  # minimal JPEG-like header, not a real decodable image
    resp = auth_client.post(
        "/api/v1/disease/predict",
        files={"file": ("leaf.jpg", io.BytesIO(fake_jpeg_bytes), "image/jpeg")},
    )
    assert resp.status_code == 503
    body = resp.json()
    assert "not trained" in body["error"]["message"].lower()

import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_sse_stream_endpoint(client):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        file_bytes = f.read()

    res = client.post(
        "/api/analyze/stream",
        files={"file": ("clean_dataset.csv", file_bytes, "text/csv")}
    )

    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    body = res.text
    assert "event: pipeline_start" in body
    assert "event: step_complete" in body
    assert "event: complete" in body

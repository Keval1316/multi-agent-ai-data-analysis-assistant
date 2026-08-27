import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


import json
import math
import numpy as np
from backend.app.orchestration.events import format_sse_event, clean_nan_and_inf


@pytest.fixture
def client():
    return TestClient(app)


def test_sse_nan_sanitization():
    messy_payload = {
        "category": float("nan"),
        "total": float("inf"),
        "negative_inf": float("-inf"),
        "nested": {
            "arr": [1.0, float("nan"), 3.5],
            "val": np.nan
        }
    }
    raw_sse = format_sse_event("step_complete", messy_payload)
    assert "NaN" not in raw_sse
    assert "Infinity" not in raw_sse

    # Extract JSON line
    for line in raw_sse.split("\n"):
        if line.startswith("data: "):
            json_str = line[6:]
            parsed = json.loads(json_str)
            assert parsed["category"] is None
            assert parsed["total"] is None
            assert parsed["nested"]["arr"] == [1.0, None, 3.5]


def test_sse_stream_clean_dataset(client):
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


def test_sse_stream_messy_dataset(client):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "messy_dataset.csv")
    with open(path, "rb") as f:
        file_bytes = f.read()

    res = client.post(
        "/api/analyze/stream",
        files={"file": ("messy_dataset.csv", file_bytes, "text/csv")}
    )

    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]

    body = res.text
    # Verify every data: line in the entire SSE response is strictly valid JSON
    for line in body.split("\n"):
        if line.startswith("data: "):
            json_str = line[6:]
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
            if "report" in parsed and parsed["report"]:
                assert isinstance(parsed["report"], dict)

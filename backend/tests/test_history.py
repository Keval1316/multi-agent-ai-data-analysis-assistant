import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager
from backend.app.services.reporting.report_builder import ReportBuilder

client = TestClient(app)


@pytest.fixture
def clean_dataset_registered():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    dataset_id, table_name = duckdb_manager.register_dataframe(df, "history_test_ds")
    return df, dataset_id, table_name


def test_history_endpoint_empty():
    ReportBuilder.clear_all_caches()
    response = client.get("/api/dataset/history")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert len(data["history"]) == 0


def test_history_and_delete_endpoint(clean_dataset_registered):
    df, dataset_id, table_name = clean_dataset_registered
    ReportBuilder.clear_all_caches()
    
    # 1. Build and cache report
    report = ReportBuilder.build_report_from_dataset(df, dataset_id, table_name, "clean_dataset.csv")

    # 2. Test GET /api/dataset/history
    resp = client.get("/api/dataset/history")
    assert resp.status_code == 200
    history = resp.json()["history"]
    assert len(history) == 1
    assert history[0]["dataset_id"] == dataset_id
    assert history[0]["filename"] == "clean_dataset.csv"
    assert history[0]["total_rows"] == 20
    assert history[0]["quality_score"] > 0

    # 3. Test GET /api/dataset/{id}/report
    report_resp = client.get(f"/api/dataset/{dataset_id}/report")
    assert report_resp.status_code == 200
    assert report_resp.json()["dataset_id"] == dataset_id

    # 4. Test DELETE /api/dataset/{id}
    del_resp = client.delete(f"/api/dataset/{dataset_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # 4b. Test idempotent DELETE (calling again on deleted id should still return 200 OK)
    del_resp_again = client.delete(f"/api/dataset/{dataset_id}")
    assert del_resp_again.status_code == 200
    assert del_resp_again.json()["success"] is True

    # 5. Verify history is empty again
    resp2 = client.get("/api/dataset/history")
    assert len(resp2.json()["history"]) == 0


def test_clear_all_history_endpoint(clean_dataset_registered):
    df, dataset_id, table_name = clean_dataset_registered
    ReportBuilder.build_report_from_dataset(df, dataset_id, table_name, "clean_dataset.csv")

    # Clear all
    clear_resp = client.delete("/api/dataset/history/all")
    assert clear_resp.status_code == 200
    assert clear_resp.json()["success"] is True

    # Verify history is empty
    resp = client.get("/api/dataset/history")
    assert len(resp.json()["history"]) == 0

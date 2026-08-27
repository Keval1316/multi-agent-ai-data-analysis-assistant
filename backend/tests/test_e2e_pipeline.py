import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.orchestration.graph import analysis_workflow_graph
from backend.app.services.reporting.report_builder import ReportBuilder


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_paths():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples")
    return {
        "clean_csv": os.path.join(base_dir, "clean_dataset.csv"),
        "clean_xlsx": os.path.join(base_dir, "clean_dataset.xlsx"),
        "messy_csv": os.path.join(base_dir, "messy_dataset.csv"),
    }


def test_e2e_clean_csv_pipeline(sample_paths):
    with open(sample_paths["clean_csv"], "rb") as f:
        file_bytes = f.read()

    initial_state = {
        "dataset_id": "e2e_clean_csv_ds",
        "filename": "clean_dataset.csv",
        "file_bytes": file_bytes,
        "logs": [],
        "revision_count": 0,
        "critic_approved": False
    }

    final_state = analysis_workflow_graph.invoke(initial_state)

    assert final_state["dataset_id"] == "e2e_clean_csv_ds"
    assert final_state["profile"].total_rows == 20
    assert final_state["quality"].grade in ["A", "B"]
    assert final_state["understanding"].domain != ""
    assert len(final_state["statistics"].univariate_metrics) >= 2
    assert final_state["sql_results"].successful_queries > 0
    assert len(final_state["charts"].charts) >= 2
    assert len(final_state["insights"].insights) >= 2
    assert final_state["critic_review"].approved is True
    assert final_state["report"] is not None
    assert final_state["pdf_bytes"].startswith(b"%PDF-")


def test_e2e_clean_excel_pipeline(sample_paths):
    with open(sample_paths["clean_xlsx"], "rb") as f:
        file_bytes = f.read()

    initial_state = {
        "dataset_id": "e2e_clean_xlsx_ds",
        "filename": "clean_dataset.xlsx",
        "file_bytes": file_bytes,
        "logs": [],
        "revision_count": 0,
        "critic_approved": False
    }

    final_state = analysis_workflow_graph.invoke(initial_state)

    assert final_state["dataset_id"] == "e2e_clean_xlsx_ds"
    assert final_state["profile"].total_rows == 20
    assert final_state["report"] is not None
    assert final_state["pdf_bytes"].startswith(b"%PDF-")


def test_e2e_messy_csv_pipeline(sample_paths):
    with open(sample_paths["messy_csv"], "rb") as f:
        file_bytes = f.read()

    initial_state = {
        "dataset_id": "e2e_messy_csv_ds",
        "filename": "messy_dataset.csv",
        "file_bytes": file_bytes,
        "logs": [],
        "revision_count": 0,
        "critic_approved": False
    }

    final_state = analysis_workflow_graph.invoke(initial_state)

    assert final_state["dataset_id"] == "e2e_messy_csv_ds"
    # Messy dataset should trigger quality issues and anomalies
    assert len(final_state["quality"].issues) >= 1
    assert len(final_state["patterns"].anomalies) >= 1
    assert final_state["report"] is not None
    assert final_state["pdf_bytes"].startswith(b"%PDF-")


def test_e2e_http_and_sse_api_workflow(client, sample_paths):
    with open(sample_paths["clean_csv"], "rb") as f:
        file_bytes = f.read()

    # 1. Health check
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    # 2. Upload API
    upload_res = client.post(
        "/api/upload",
        files={"file": ("clean_dataset.csv", file_bytes, "text/csv")}
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    dataset_id = upload_data["dataset"]["dataset_id"]
    assert dataset_id != ""

    # 3. Profile & Quality API
    prof_res = client.get(f"/api/dataset/{dataset_id}/profile")
    assert prof_res.status_code == 200
    assert prof_res.json()["total_rows"] == 20

    qual_res = client.get(f"/api/dataset/{dataset_id}/quality")
    assert qual_res.status_code == 200
    assert "quality_score" in qual_res.json()

    # 4. SSE Stream Execution
    stream_res = client.post(
        "/api/analyze/stream",
        files={"file": ("clean_dataset.csv", file_bytes, "text/csv")}
    )
    assert stream_res.status_code == 200
    assert "text/event-stream" in stream_res.headers["content-type"]
    assert "event: complete" in stream_res.text

    # 5. Report API
    report_res = client.get(f"/api/dataset/{dataset_id}/report")
    assert report_res.status_code == 200
    assert "executive_summary" in report_res.json()

    # 6. PDF Export API
    pdf_res = client.get(f"/api/dataset/{dataset_id}/report/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF-")


def test_e2e_security_and_boundary_resilience(client):
    # 1. Reject invalid file extension
    bad_res = client.post(
        "/api/upload",
        files={"file": ("malicious.exe", b"binary content", "application/octet-stream")}
    )
    assert bad_res.status_code == 400

    # 2. Reject empty file
    empty_res = client.post(
        "/api/upload",
        files={"file": ("empty.csv", b"", "text/csv")}
    )
    assert empty_res.status_code == 400

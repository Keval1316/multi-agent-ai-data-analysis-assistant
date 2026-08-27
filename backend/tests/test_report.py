import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager
from backend.app.services.reporting.report_builder import ReportBuilder
from backend.app.models.report import AnalysisReport


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def clean_dataset_registered():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    dataset_id, table_name = duckdb_manager.register_dataframe(df, "report_test_ds")
    return df, dataset_id, table_name


def test_build_report_from_dataset(clean_dataset_registered):
    df, dataset_id, table_name = clean_dataset_registered
    report = ReportBuilder.build_report_from_dataset(df, dataset_id, table_name, "clean_dataset.csv")

    assert isinstance(report, AnalysisReport)
    assert report.dataset_id == dataset_id
    assert report.title != ""
    assert report.executive_summary != ""
    assert len(report.sections) >= 3
    assert len(report.insights.insights) >= 1
    assert len(report.charts.charts) >= 1


def test_api_get_report_endpoint(client, clean_dataset_registered):
    _, dataset_id, _ = clean_dataset_registered
    res = client.get(f"/api/dataset/{dataset_id}/report")

    assert res.status_code == 200
    data = res.json()
    assert data["dataset_id"] == dataset_id
    assert "executive_summary" in data
    assert "sections" in data
    assert len(data["sections"]) >= 3

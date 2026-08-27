import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager
from backend.app.services.reporting.report_builder import ReportBuilder
from backend.app.services.reporting.pdf_exporter import PDFExporter


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def clean_report():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    dataset_id, table_name = duckdb_manager.register_dataframe(df, "pdf_test_ds")
    report = ReportBuilder.build_report_from_dataset(df, dataset_id, table_name, "clean_dataset.csv")
    return dataset_id, report


def test_pdf_exporter_binary_output(clean_report):
    _, report = clean_report
    pdf_bytes = PDFExporter.generate_pdf(report)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # Check PDF magic bytes header
    assert pdf_bytes.startswith(b"%PDF-")


def test_api_download_pdf_endpoint(client, clean_report):
    dataset_id, _ = clean_report
    res = client.get(f"/api/dataset/{dataset_id}/report/pdf")

    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in res.headers["content-disposition"]
    assert res.content.startswith(b"%PDF-")

import os
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.cleaning.cleaner import DataCleaner
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager
from backend.app.services.reporting.report_builder import ReportBuilder

client = TestClient(app)


def test_data_cleaner_transformations():
    # Test messy dataframe with nulls, duplicate rows, and inconsistent casing
    raw_data = {
        "order_id": ["ORD-1", "ORD-2", "ORD-1", "ORD-3", "ORD-4"],
        "category": ["electronics", "Electronics", "electronics", "FURNITURE", None],
        "unit_price": ["$100.50", "250", "$100.50", "N/A", "75.25"],
        "order_date": ["2025-01-01", "2025/01/02", "2025-01-01", "invalid_date", "2025-01-05"]
    }
    df = pd.DataFrame(raw_data)
    cleaned_df, summary = DataCleaner.clean_dataset(df, "test_clean_ds", "messy_sample.csv")

    # 1. Duplicates removed (5 initial rows -> 4 unique)
    assert len(cleaned_df) == 4
    assert summary.duplicates_removed == 1

    # 2. Nulls imputed
    assert cleaned_df["category"].isna().sum() == 0
    assert cleaned_df["unit_price"].isna().sum() == 0

    # 3. Categorical standardized
    assert "Electronics" in cleaned_df["category"].values

    # 4. Numerics cleaned
    assert pd.api.types.is_numeric_dtype(cleaned_df["unit_price"])

    # 5. Export tests
    csv_bytes = DataCleaner.export_csv_bytes(cleaned_df)
    assert len(csv_bytes) > 0
    assert b"order_id,category,unit_price,order_date" in csv_bytes

    excel_bytes = DataCleaner.export_excel_bytes(cleaned_df)
    assert len(excel_bytes) > 0


def test_download_cleaned_endpoints():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "messy_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    dataset_id, table_name = duckdb_manager.register_dataframe(df, "clean_endpoint_test_ds")
    report = ReportBuilder.build_report_from_dataset(df, dataset_id, table_name, "messy_dataset.csv")

    # 1. Test GET /download/cleaned-csv
    csv_res = client.get(f"/api/dataset/{dataset_id}/download/cleaned-csv")
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=\"cleaned_messy_dataset.csv\"" in csv_res.headers["content-disposition"]

    # 2. Test GET /download/cleaned-excel
    xlsx_res = client.get(f"/api/dataset/{dataset_id}/download/cleaned-excel")
    assert xlsx_res.status_code == 200
    assert "spreadsheetml" in xlsx_res.headers["content-type"]

    # 3. Test GET /cleaned-preview
    preview_res = client.get(f"/api/dataset/{dataset_id}/cleaned-preview")
    assert preview_res.status_code == 200
    pdata = preview_res.json()
    assert "rows" in pdata
    assert "columns" in pdata
    assert "cleaning_summary" in pdata

import io
import os
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.exceptions import FileValidationError, IngestionError
from backend.app.services.ingestion.validator import FileValidator
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager

client = TestClient(app)


def test_file_validator_valid():
    name, ext = FileValidator.validate_file_metadata("sales_data.csv", 1024, "text/csv")
    assert name == "sales_data.csv"
    assert ext == ".csv"

    name, ext = FileValidator.validate_file_metadata("reports/Q1-Report.xlsx", 5000)
    assert name == "Q1-Report.xlsx"
    assert ext == ".xlsx"


def test_file_validator_invalid_extension():
    with pytest.raises(FileValidationError, match="Unsupported file format"):
        FileValidator.validate_file_metadata("malicious.exe", 100)

    with pytest.raises(FileValidationError, match="Unsupported file format"):
        FileValidator.validate_file_metadata("data.pdf", 100)


def test_file_validator_empty_file():
    with pytest.raises(FileValidationError, match="The uploaded file is empty"):
        FileValidator.validate_file_metadata("empty.csv", 0)


def test_file_validator_oversized():
    # 15 MB > 10 MB limit
    oversized_bytes = 15 * 1024 * 1024
    with pytest.raises(FileValidationError, match="exceeds maximum allowed limit"):
        FileValidator.validate_file_metadata("huge.csv", oversized_bytes)


def test_dataset_loader_column_sanitization():
    names = set()
    col1 = DatasetLoader.sanitize_column_name(" Total Revenue ($) ", names, 0)
    assert col1 == "Total_Revenue"

    col2 = DatasetLoader.sanitize_column_name("1st Place", names, 1)
    assert col2 == "col_1st_Place"

    col3 = DatasetLoader.sanitize_column_name("Total Revenue ($)", names, 2)
    assert col3 == "Total_Revenue_1"  # Uniqueness handled


def test_dataset_loader_csv_encodings():
    # Latin-1 encoded CSV with accented characters
    latin1_csv = "id,name,city\n1,Renée,Montréal\n2,José,São Paulo".encode("latin-1")
    df, schemas = DatasetLoader.load_and_sanitize(latin1_csv, ".csv")
    assert df.shape == (2, 3)
    assert len(schemas) == 3
    assert schemas[1].name == "name"


def test_dataset_loader_custom_delimiter():
    semicolon_csv = "id;product;price\n101;Chair;45.5\n102;Desk;120.0".encode("utf-8")
    df, schemas = DatasetLoader.load_and_sanitize(semicolon_csv, ".csv")
    assert df.shape == (2, 3)
    assert "product" in df.columns


def test_dataset_loader_excel_file():
    # Read sample excel file
    excel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.xlsx")
    with open(excel_path, "rb") as f:
        content = f.read()

    df, schemas = DatasetLoader.load_and_sanitize(content, ".xlsx")
    assert df.shape[0] == 20
    assert df.shape[1] == 11
    assert any(s.name == "order_id" for s in schemas)


def test_duckdb_registration():
    df = pd.DataFrame({
        "item_id": [1, 2, 3],
        "value": [10.5, 20.0, 30.2]
    })
    dataset_id, table_name = duckdb_manager.register_dataframe(df)
    assert duckdb_manager.table_exists(table_name)

    # Query table directly
    query_df = duckdb_manager.execute_query(f"SELECT SUM(value) as total FROM {table_name}")
    assert float(query_df["total"].iloc[0]) == pytest.approx(60.7)

    # Preview rows
    previews = duckdb_manager.get_preview_rows(table_name, limit=2)
    assert len(previews) == 2
    assert previews[0]["item_id"] == 1


def test_upload_api_valid_csv():
    csv_content = "id,metric,score\n1,alpha,95.5\n2,beta,88.0\n3,gamma,72.3".encode("utf-8")
    response = client.post(
        "/api/upload",
        files={"file": ("test_data.csv", io.BytesIO(csv_content), "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["dataset"]["row_count"] == 3
    assert data["dataset"]["column_count"] == 3
    assert len(data["dataset"]["columns"]) == 3
    assert len(data["dataset"]["preview_rows"]) == 3


def test_upload_api_invalid_extension():
    response = client.post(
        "/api/upload",
        files={"file": ("script.sh", io.BytesIO(b"echo 1"), "text/x-sh")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_api_empty_file():
    response = client.post(
        "/api/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

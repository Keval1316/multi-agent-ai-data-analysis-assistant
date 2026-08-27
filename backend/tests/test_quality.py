import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.services.quality.checker import QualityChecker
from backend.app.models.quality import QualitySeverity

client = TestClient(app)


@pytest.fixture
def clean_df():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    return df


@pytest.fixture
def messy_df():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "messy_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    return df


def test_clean_dataset_quality(clean_df):
    profile = DatasetProfiler.profile_dataset(clean_df, "clean_ds", "dataset_clean_ds")
    report = QualityChecker.audit_dataset(clean_df, profile)

    # Clean dataset should have high score (>= 90) and Grade A
    assert report.quality_score >= 90.0
    assert report.grade in ["A", "B"]
    assert report.is_analysis_ready is True
    # Should have 0 confirmed issues
    assert report.issues_count[QualitySeverity.CONFIRMED_ISSUE.value] == 0


def test_messy_dataset_quality(messy_df):
    profile = DatasetProfiler.profile_dataset(messy_df, "messy_ds", "dataset_messy_ds")
    report = QualityChecker.audit_dataset(messy_df, profile)

    # Messy dataset should trigger confirmed and suspicious issues
    assert report.total_issues > 0
    assert report.issues_count[QualitySeverity.CONFIRMED_ISSUE.value] >= 1  # Duplicate row & negative quantity/price
    assert report.issues_count[QualitySeverity.SUSPICIOUS_ISSUE.value] >= 1  # Extreme outlier 99999 / inconsistent casing

    # Verify duplicate row issue exists
    dup_issue = next((i for i in report.issues if i.category == "duplicate_rows"), None)
    assert dup_issue is not None
    assert dup_issue.severity == QualitySeverity.CONFIRMED_ISSUE

    # Verify outlier or invalid values
    neg_issue = next((i for i in report.issues if i.category == "invalid_values"), None)
    assert neg_issue is not None

    # Quality score should be reduced
    assert report.quality_score < 80.0


def test_api_profile_and_quality_endpoints(clean_df):
    dataset_id, table_name = duckdb_manager.register_dataframe(clean_df, "api_test_ds")

    # Test profile API
    res_prof = client.get(f"/api/dataset/{dataset_id}/profile")
    assert res_prof.status_code == 200
    prof_data = res_prof.json()
    assert prof_data["total_rows"] == 20
    assert len(prof_data["column_profiles"]) == 11

    # Test quality API
    res_qual = client.get(f"/api/dataset/{dataset_id}/quality")
    assert res_qual.status_code == 200
    qual_data = res_qual.json()
    assert qual_data["quality_score"] >= 90.0
    assert "grade" in qual_data

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


def test_student_scores_full_cleaning_bug_fix():
    """
    Directly tests the 6 acceptance criteria for the student_scores.csv incomplete cleaning bug:
    1. Out-of-range scores (-5.0 and 105.0) are corrected and bounded to [0.0, 100.0].
    2. Categorical grades (12 raw variants: 'd', 'D', ' D', 'B', ' B', 'b', 'a', 'c') collapse strictly to canonical uppercase {A, B, C, D}.
    3. Missing grade for Charlie Brown (score 85.0) is derived as 'B' instead of being assigned 'Unknown'.
    4. Contradictory grade for George Clark (score 95.0, grade 'D') is reconciled to 'A'.
    5. A comprehensive change log audit trail and before/after summary report are generated.
    6. Post-cleaning validation passes 100%.
    """
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "student_scores.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")

    cleaned_df, summary = DataCleaner.clean_dataset(df, "student_scores_test", "student_scores.csv")

    # 1. Range Validation: No numeric score is outside [0.0, 100.0]
    assert (cleaned_df["score"] >= 0.0).all(), "Scores must be non-negative"
    assert (cleaned_df["score"] <= 100.0).all(), "Scores must be <= 100"
    
    # Check specific clamped values
    bob_score = cleaned_df.loc[cleaned_df["student_id"] == "STU-102", "score"].values[0]
    diana_score = cleaned_df.loc[cleaned_df["student_id"] == "STU-104", "score"].values[0]
    assert bob_score == 0.0, f"Expected -5.0 to be clamped to 0.0, got {bob_score}"
    assert diana_score == 100.0, f"Expected 105.0 to be clamped to 100.0, got {diana_score}"
    assert summary.out_of_range_corrected >= 2

    # 2. Categorical Normalization: Grades strictly match canonical uppercase {A, B, C, D}
    unique_grades = set(cleaned_df["grade"].dropna().unique())
    assert unique_grades.issubset({"A", "B", "C", "D", "F"}), f"Invalid grade variants found: {unique_grades}"
    assert "d" not in unique_grades
    assert " D" not in unique_grades
    assert "b" not in unique_grades
    assert "a" not in unique_grades
    assert "c" not in unique_grades

    # 3. Derive before defaulting: Missing grade for STU-103 (Charlie Brown, score 85.0) derived as 'B'
    charlie_grade = cleaned_df.loc[cleaned_df["student_id"] == "STU-103", "grade"].values[0]
    assert charlie_grade == "B", f"Expected derived grade 'B' for score 85.0, got '{charlie_grade}'"
    assert charlie_grade != "Unknown", "Missing grade must not default to 'Unknown' string"
    assert summary.nulls_derived >= 1

    # 4. Cross-field consistency: Reconcile contradictory grade for STU-107 (George Clark, score 95.0, grade 'D' -> 'A')
    george_grade = cleaned_df.loc[cleaned_df["student_id"] == "STU-107", "grade"].values[0]
    assert george_grade == "A", f"Expected reconciled grade 'A' for score 95.0, got '{george_grade}'"
    assert summary.cross_field_reconciled >= 1

    # 5. Change Log & Structured Contract
    assert len(summary.change_log) > 0, "Change log must contain recorded transformations"
    rules_applied = {entry.rule for entry in summary.change_log}
    assert "numeric_range_validation" in rules_applied
    assert "categorical_normalization" in rules_applied
    assert "cross_field_derivation" in rules_applied
    assert "cross_field_reconciliation" in rules_applied

    # Check Before/After summary
    assert summary.before_after is not None
    assert summary.before_after.out_of_range_counts_before["score"] == 2
    assert summary.before_after.out_of_range_counts_after["score"] == 0
    assert summary.before_after.missing_rate_per_column_after["grade"] == 0.0

    # 6. Post-cleaning validation
    assert summary.validation_passed is True


def test_messy_dataset_cleaning():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "messy_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")

    cleaned_df, summary = DataCleaner.clean_dataset(df, "messy_dataset_test", "messy_dataset.csv")

    # 1. Duplicates purged
    assert summary.duplicates_removed >= 1

    # 2. Negative quantity in ORD-9008 corrected
    ord_id_col = [c for c in cleaned_df.columns if "order" in c.lower() and "id" in c.lower()][0]
    qty_col = [c for c in cleaned_df.columns if "quantity" in c.lower()][0]
    price_col = [c for c in cleaned_df.columns if "unit" in c.lower() and "price" in c.lower()][0]
    date_col = [c for c in cleaned_df.columns if "order" in c.lower() and "date" in c.lower()][0]

    ord_9008_qty = cleaned_df.loc[cleaned_df[ord_id_col] == "ORD-9008", qty_col].values[0]
    assert ord_9008_qty >= 0, f"Expected non-negative quantity, got {ord_9008_qty}"

    # 3. Missing unit price derived for ORD-9010 (Quantity 2, Total 44 -> Unit Price 22.0)
    ord_9010_price = cleaned_df.loc[cleaned_df[ord_id_col] == "ORD-9010", price_col].values[0]
    assert ord_9010_price == 22.0, f"Expected derived unit price 22.0, got {ord_9010_price}"

    # 4. Region standardized (West, North, East, South)
    assert set(cleaned_df["Region"].unique()).issubset({"North", "South", "East", "West"})

    # 5. Dates normalized to ISO-8601
    assert "invalid-date" not in cleaned_df[date_col].values

    # 6. Validation passed
    assert summary.validation_passed is True


def test_generic_adaptive_rules_across_domains():
    """Verifies that cleaning rules apply generally to HR, Healthcare, and Finance schemas."""
    # HR Dataset
    hr_data = {
        "employee_id": ["EMP-1", "EMP-2", "EMP-3"],
        "age": [28, -5, 140],  # out of range
        "salary": ["$75,000", "$90,000", "N/A"],
        "gender": ["m", "Female", "F"],  # messy categories
        "performance_rating": [4.5, 6.2, 3.0]  # out of 5 scale
    }
    hr_df = pd.DataFrame(hr_data)
    cleaned_hr, hr_summary = DataCleaner.clean_dataset(hr_df, "hr_test", "hr_data.csv")

    assert (cleaned_hr["age"] >= 0).all() and (cleaned_hr["age"] <= 120).all()
    assert (cleaned_hr["performance_rating"] <= 5.0).all()
    assert set(cleaned_hr["gender"].unique()).issubset({"Male", "Female"})
    assert pd.api.types.is_numeric_dtype(cleaned_hr["salary"])
    assert hr_summary.validation_passed is True


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
    assert "change_log" in pdata["cleaning_summary"]
    assert "before_after" in pdata["cleaning_summary"]

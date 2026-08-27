import os
import pandas as pd
import pytest
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager


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


def test_clean_dataset_profiling(clean_df):
    profile = DatasetProfiler.profile_dataset(clean_df, "test_clean", "dataset_test_clean")

    assert profile.total_rows == 20
    assert profile.total_columns == 11
    assert profile.duplicate_rows_count == 0
    assert profile.duplicate_rows_percentage == 0.0

    # Numeric columns should include quantity, unit_price, discount_rate, total_revenue
    assert "quantity" in profile.numeric_column_names
    assert "unit_price" in profile.numeric_column_names
    assert "total_revenue" in profile.numeric_column_names

    # Check stats for total_revenue
    rev_prof = next(c for c in profile.column_profiles if c.name == "total_revenue")
    assert rev_prof.numeric_stats is not None
    assert rev_prof.numeric_stats.min > 0
    assert rev_prof.numeric_stats.max > 500
    assert rev_prof.null_count == 0

    # Identifier candidate
    order_prof = next(c for c in profile.column_profiles if c.name == "order_id")
    assert order_prof.is_identifier_candidate is True


def test_messy_dataset_profiling(messy_df):
    profile = DatasetProfiler.profile_dataset(messy_df, "test_messy", "dataset_test_messy")

    assert profile.total_rows == 21
    # Check duplicate rows detection (seeded duplicate ORD-9002 in messy dataset)
    assert profile.duplicate_rows_count >= 1

    # Check null percentages detected
    cust_prof = next(c for c in profile.column_profiles if "customer_name" in c.name.lower())
    assert cust_prof.null_count >= 1

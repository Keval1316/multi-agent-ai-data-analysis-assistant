import os
import pytest
import pandas as pd
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.models.plan import AnalysisPlan, SQLQueryGoal
from backend.app.services.visualization.chart_generator import ChartGenerator
from backend.app.services.visualization.role_classifier import SemanticRoleClassifier


@pytest.fixture
def clean_dataset():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    profile = DatasetProfiler.profile_dataset(df, "clean_ds", "dataset_clean_ds")
    plan = AnalysisPlan(
        primary_goal="Sales performance",
        descriptive_numeric_columns=["total_revenue", "quantity"],
        sql_query_goals=[
            SQLQueryGoal(
                name="sales_summary",
                purpose="Aggregate metrics",
                columns_needed=["total_revenue"]
            )
        ]
    )
    return df, profile, plan


def test_semantic_role_classification(clean_dataset):
    df, profile, _ = clean_dataset
    roles = SemanticRoleClassifier.profile_all_columns(df, profile)

    # Identifiers must be detected
    assert "order_id" in roles
    assert roles["order_id"].is_identifier is True
    assert roles["order_id"].is_measure is False

    # Datetime must be detected
    assert "order_date" in roles
    assert roles["order_date"].is_datetime is True

    # Measures must be detected
    assert "total_revenue" in roles
    assert roles["total_revenue"].is_measure is True
    assert roles["total_revenue"].is_identifier is False

    # Categories must be detected
    assert "category" in roles
    assert roles["category"].is_category is True
    assert roles["category"].is_identifier is False


def test_dynamic_chart_selection_not_hardcoded_to_four(clean_dataset):
    df, profile, plan = clean_dataset
    collection = ChartGenerator.generate_all(df, profile, plan)

    assert collection.dataset_id == "clean_ds"
    assert len(collection.charts) >= 1

    # Verify no identifier columns are used as primary measures
    for chart in collection.charts:
        assert chart.x_column != "order_id"
        assert chart.y_column != "order_id"
        assert chart.title != ""
        assert chart.insights_summary is not None
        assert len(chart.data) > 0
        assert "font" in chart.layout
        assert chart.layout["font"]["color"] == "#3E2723"


def test_user_question_prioritization(clean_dataset):
    df, profile, plan = clean_dataset

    # Ask specifically about relationship/correlation
    collection_corr = ChartGenerator.generate_all(df, profile, plan, user_query="What is the correlation between quantity and revenue?")
    assert len(collection_corr.charts) > 0
    top_chart = collection_corr.charts[0]
    # The top chart should align with the user question
    assert top_chart.chart_type == "scatter" or "revenue" in (top_chart.y_column or top_chart.x_column or "")

    # Ask specifically about trends
    collection_trend = ChartGenerator.generate_all(df, profile, plan, user_query="Show me sales trend over time")
    assert len(collection_trend.charts) > 0
    assert any(c.chart_type == "line" for c in collection_trend.charts)


def test_categorical_only_dataset():
    # Dataset with only categorical columns
    df_cat = pd.DataFrame({
        "department": ["Engineering", "Sales", "Engineering", "Marketing", "Sales", "Sales"],
        "location": ["US", "US", "EU", "EU", "APAC", "US"]
    })
    profile_cat = DatasetProfiler.profile_dataset(df_cat, "cat_ds", "table_cat")
    plan = AnalysisPlan(
        primary_goal="Department headcounts",
        descriptive_numeric_columns=[],
        sql_query_goals=[SQLQueryGoal(name="dept_counts", purpose="Headcount by dept", columns_needed=["department"])]
    )

    collection = ChartGenerator.generate_all(df_cat, profile_cat, plan)
    assert len(collection.charts) >= 1
    # Frequency bar / count chart should be selected
    assert any(c.chart_type in ["bar", "horizontal_bar", "donut"] for c in collection.charts)


def test_numerical_only_dataset():
    # Dataset with only numerical columns
    df_num = pd.DataFrame({
        "age": [25, 30, 35, 40, 45, 50, 55, 60],
        "income": [50000, 60000, 75000, 90000, 110000, 130000, 140000, 180000]
    })
    profile_num = DatasetProfiler.profile_dataset(df_num, "num_ds", "table_num")
    plan = AnalysisPlan(
        primary_goal="Income and age distribution",
        descriptive_numeric_columns=["income", "age"],
        sql_query_goals=[SQLQueryGoal(name="income_summary", purpose="Summary of income", columns_needed=["income"])]
    )

    collection = ChartGenerator.generate_all(df_num, profile_num, plan)
    assert len(collection.charts) >= 1
    types = {c.chart_type for c in collection.charts}
    assert "scatter" in types or "histogram" in types or "box" in types


def test_identifier_only_dataset_graceful_empty():
    # Dataset containing only unique ID strings
    df_ids = pd.DataFrame({
        "user_uuid": [f"user_{i}" for i in range(100)],
        "session_id": [f"sess_{i}" for i in range(100)]
    })
    profile_ids = DatasetProfiler.profile_dataset(df_ids, "id_ds", "table_ids")
    plan = AnalysisPlan(
        primary_goal="Explore IDs",
        descriptive_numeric_columns=[],
        sql_query_goals=[SQLQueryGoal(name="id_counts", purpose="Count ids", columns_needed=["user_uuid"])]
    )

    collection = ChartGenerator.generate_all(df_ids, profile_ids, plan)
    assert len(collection.charts) == 0
    assert collection.empty_reason is not None
    assert "No meaningful visualizations" in collection.empty_reason

import os
import pytest
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.models.plan import AnalysisPlan, SQLQueryGoal
from backend.app.services.visualization.chart_generator import ChartGenerator


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


def test_chart_generation_all(clean_dataset):
    df, profile, plan = clean_dataset
    collection = ChartGenerator.generate_all(df, profile, plan)

    assert collection.dataset_id == "clean_ds"
    assert len(collection.charts) >= 3

    # Check chart types present
    chart_types = {c.chart_type for c in collection.charts}
    assert "bar" in chart_types
    assert "line" in chart_types or "donut" in chart_types or "scatter" in chart_types

    # Check layout adherence to palette tokens
    for chart in collection.charts:
        assert len(chart.data) > 0
        assert "font" in chart.layout
        assert chart.layout["font"]["color"] == "#40513B"
        assert chart.insights_summary is not None
        assert chart.id.startswith("chart_")


def test_individual_chart_generators(clean_dataset):
    df, _, _ = clean_dataset

    # 1. Bar Chart
    bar = ChartGenerator.generate_bar_chart(df, "category", "total_revenue")
    assert bar is not None
    assert bar.chart_type == "bar"
    assert bar.data[0]["type"] == "bar"
    assert len(bar.data[0]["x"]) > 0

    # 2. Line Chart
    line = ChartGenerator.generate_line_chart(df, "order_date", "total_revenue")
    assert line is not None
    assert line.chart_type == "line"
    assert line.data[0]["type"] == "scatter"
    assert line.data[0]["mode"] == "lines+markers"

    # 3. Scatter Chart
    scatter = ChartGenerator.generate_scatter_chart(df, "quantity", "total_revenue", "category")
    assert scatter is not None
    assert scatter.chart_type == "scatter"
    assert len(scatter.data) > 0

    # 4. Donut Chart
    donut = ChartGenerator.generate_donut_chart(df, "region", "total_revenue")
    assert donut is not None
    assert donut.chart_type == "donut"
    assert donut.data[0]["type"] == "pie"
    assert donut.data[0]["hole"] == 0.55

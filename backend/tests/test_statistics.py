import os
import pytest
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.models.plan import AnalysisPlan, GroupByAnalysisPlan, SQLQueryGoal
from backend.app.services.statistics.engine import StatisticalEngine


@pytest.fixture
def clean_data():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    profile = DatasetProfiler.profile_dataset(df, "clean_ds", "dataset_clean_ds")
    return df, profile


def test_univariate_metrics_computation(clean_data):
    df, _ = clean_data
    metrics = StatisticalEngine.compute_univariate_metrics(df, ["quantity", "total_revenue", "unit_price"])

    assert len(metrics) == 3
    rev_metric = next(m for m in metrics if m.column_name == "total_revenue")
    assert rev_metric.count == 20
    assert rev_metric.min > 0
    assert rev_metric.max > 500
    assert rev_metric.p50 == rev_metric.median
    assert rev_metric.iqr > 0
    assert rev_metric.std > 0


def test_correlations_computation(clean_data):
    df, _ = clean_data
    pairs = [["quantity", "total_revenue"], ["unit_price", "total_revenue"]]
    corrs = StatisticalEngine.compute_correlations(df, pairs)

    assert len(corrs) == 2
    for c in corrs:
        assert -1.0 <= c.pearson_coef <= 1.0
        assert -1.0 <= c.spearman_coef <= 1.0
        assert c.strength in ["Strong Positive", "Moderate Positive", "Weak", "Moderate Negative", "Strong Negative"]


def test_groupby_and_anova_computation(clean_data):
    df, profile = clean_data
    plan = AnalysisPlan(
        primary_goal="Sales performance",
        descriptive_numeric_columns=["total_revenue"],
        correlation_pairs=[["quantity", "total_revenue"]],
        group_by_analyses=[
            GroupByAnalysisPlan(
                group_column="category",
                metric_column="total_revenue",
                aggregation="SUM",
                purpose="Category Revenue breakdown"
            )
        ],
        sql_query_goals=[
            SQLQueryGoal(name="top_cats", purpose="Top categories", columns_needed=["category", "total_revenue"])
        ]
    )

    stat_res = StatisticalEngine.run_analysis(df, profile, plan)

    assert len(stat_res.groupby_results) == 1
    g_res = stat_res.groupby_results[0]
    assert g_res.group_column == "category"
    assert g_res.metric_column == "total_revenue"
    assert len(g_res.items) >= 2

    # Verify shares sum close to 100%
    total_share = sum(item.share_percentage for item in g_res.items if item.share_percentage is not None)
    assert total_share == pytest.approx(100.0, rel=1e-1)

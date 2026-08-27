import os
import pytest
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.services.quality.checker import QualityChecker
from backend.app.agents.understand_dataset import DatasetUnderstandingAgent
from backend.app.agents.plan_analysis import AnalysisPlanningAgent
from backend.app.models.plan import AnalysisPlan, GroupByAnalysisPlan, SQLQueryGoal


@pytest.fixture
def clean_profile_and_quality():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    profile = DatasetProfiler.profile_dataset(df, "clean_ds", "dataset_clean_ds")
    quality = QualityChecker.audit_dataset(df, profile)
    return profile, quality


@pytest.fixture
def messy_profile_and_quality():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "messy_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    profile = DatasetProfiler.profile_dataset(df, "messy_ds", "dataset_messy_ds")
    quality = QualityChecker.audit_dataset(df, profile)
    return profile, quality


def test_understand_dataset_agent(clean_profile_and_quality):
    profile, quality = clean_profile_and_quality
    understanding = DatasetUnderstandingAgent.analyze(profile, quality, "clean_dataset.csv")

    assert understanding.domain != ""
    assert understanding.target_entity != ""
    assert len(understanding.key_kpis) >= 1
    assert len(understanding.important_dimensions) >= 1
    assert len(understanding.core_questions) >= 2


def test_plan_analysis_agent(clean_profile_and_quality):
    profile, quality = clean_profile_and_quality
    understanding = DatasetUnderstandingAgent.analyze(profile, quality, "clean_dataset.csv")
    plan = AnalysisPlanningAgent.plan(profile, understanding)

    assert isinstance(plan, AnalysisPlan)
    assert plan.primary_goal != ""
    assert len(plan.sql_query_goals) >= 1

    # Verify that all referenced columns exist in the actual dataset
    valid_cols = {c.name for c in profile.column_profiles}
    for gp in plan.group_by_analyses:
        assert gp.group_column in valid_cols
        assert gp.metric_column in valid_cols

    for sq in plan.sql_query_goals:
        for col in sq.columns_needed:
            assert col in valid_cols


def test_plan_column_validation_rejects_hallucinations():
    valid_cols = {"quantity", "unit_price", "category", "region"}
    num_cols = {"quantity", "unit_price"}

    # Fabricate a plan with hallucinated columns
    hallucinated_plan = AnalysisPlan(
        primary_goal="Test Goal",
        descriptive_numeric_columns=["quantity", "fake_profit_margin"],
        correlation_pairs=[["quantity", "unit_price"], ["fake_roi", "quantity"]],
        group_by_analyses=[
            GroupByAnalysisPlan(
                group_column="category",
                metric_column="quantity",
                aggregation="SUM",
                purpose="Real group"
            ),
            GroupByAnalysisPlan(
                group_column="fake_department",
                metric_column="fake_budget",
                aggregation="SUM",
                purpose="Fake group"
            ),
        ],
        sql_query_goals=[
            SQLQueryGoal(
                name="valid_query",
                purpose="Test",
                columns_needed=["category", "quantity", "fake_column"]
            )
        ],
        pattern_detection_targets=[],
        recommended_charts=[]
    )

    cleaned_plan = AnalysisPlanningAgent.validate_and_clean_plan(hallucinated_plan, valid_cols, num_cols)

    # Fake numeric column removed
    assert "fake_profit_margin" not in cleaned_plan.descriptive_numeric_columns
    assert "quantity" in cleaned_plan.descriptive_numeric_columns

    # Fake correlation pair removed
    assert len(cleaned_plan.correlation_pairs) == 1
    assert cleaned_plan.correlation_pairs[0] == ["quantity", "unit_price"]

    # Fake group by plan dropped
    assert len(cleaned_plan.group_by_analyses) == 1
    assert cleaned_plan.group_by_analyses[0].group_column == "category"

    # Fake column in SQL goal dropped
    assert "fake_column" not in cleaned_plan.sql_query_goals[0].columns_needed
    assert "category" in cleaned_plan.sql_query_goals[0].columns_needed

import os
import pytest
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.services.quality.checker import QualityChecker
from backend.app.agents.understand_dataset import DatasetUnderstandingAgent
from backend.app.agents.plan_analysis import AnalysisPlanningAgent
from backend.app.services.statistics.engine import StatisticalEngine
from backend.app.services.sql.executor import SQLExecutor
from backend.app.agents.generate_sql import SQLGenerationAgent
from backend.app.services.patterns.detector import PatternDetector
from backend.app.agents.generate_insights import InsightGenerationAgent
from backend.app.services.ingestion.duckdb_manager import duckdb_manager


@pytest.fixture
def analysis_pipeline_context():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    dataset_id, table_name = duckdb_manager.register_dataframe(df, "insights_test_ds")
    profile = DatasetProfiler.profile_dataset(df, dataset_id, table_name)
    quality = QualityChecker.audit_dataset(df, profile)
    understanding = DatasetUnderstandingAgent.analyze(profile, quality, "clean_dataset.csv")
    plan = AnalysisPlanningAgent.plan(profile, understanding)
    statistics = StatisticalEngine.run_analysis(df, profile, plan)
    queries = SQLGenerationAgent.generate(profile, plan, table_name)
    sql_results = SQLExecutor.execute_queries(queries, dataset_id, table_name)
    patterns = PatternDetector.detect_all(df, profile)
    return understanding, statistics, sql_results, patterns, quality


def test_insight_generation(analysis_pipeline_context):
    understanding, statistics, sql_results, patterns, quality = analysis_pipeline_context
    insights = InsightGenerationAgent.generate(
        understanding=understanding,
        statistics=statistics,
        sql_results=sql_results,
        patterns=patterns,
        quality=quality
    )

    assert insights.dataset_id == statistics.dataset_id
    assert len(insights.insights) >= 2
    for ins in insights.insights:
        assert ins.title != ""
        assert ins.finding != ""
        assert ins.supporting_evidence != ""
        assert ins.importance in ["High", "Medium", "Low"]

import os
import pytest
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.services.quality.checker import QualityChecker
from backend.app.agents.understand_dataset import DatasetUnderstandingAgent
from backend.app.agents.plan_analysis import AnalysisPlanningAgent
from backend.app.services.statistics.engine import StatisticalEngine
from backend.app.services.sql.executor import SQLExecutor
from backend.app.agents.generate_sql import SQLGenerationAgent
from backend.app.services.patterns.detector import PatternDetector
from backend.app.agents.generate_insights import InsightGenerationAgent
from backend.app.agents.critic_review import CriticReviewAgent
from backend.app.models.insights import InsightCollection, InsightItem


@pytest.fixture
def pipeline_context():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    dataset_id, table_name = duckdb_manager.register_dataframe(df, "critic_test_ds")
    profile = DatasetProfiler.profile_dataset(df, dataset_id, table_name)
    quality = QualityChecker.audit_dataset(df, profile)
    understanding = DatasetUnderstandingAgent.analyze(profile, quality, "clean_dataset.csv")
    plan = AnalysisPlanningAgent.plan(profile, understanding)
    statistics = StatisticalEngine.run_analysis(df, profile, plan)
    queries = SQLGenerationAgent.generate(profile, plan, table_name)
    sql_results = SQLExecutor.execute_queries(queries, dataset_id, table_name)
    patterns = PatternDetector.detect_all(df, profile)
    return understanding, statistics, sql_results, patterns, quality


def test_critic_approves_valid_insights(pipeline_context):
    understanding, statistics, sql_results, patterns, quality = pipeline_context
    insights = InsightGenerationAgent.generate(
        understanding=understanding,
        statistics=statistics,
        sql_results=sql_results,
        patterns=patterns,
        quality=quality
    )

    review = CriticReviewAgent.review(
        insights=insights,
        statistics=statistics,
        sql_results=sql_results,
        patterns=patterns
    )

    assert review.approved is True
    assert len(review.unsupported_claims) == 0


def test_critic_rejects_hallucinated_insights(pipeline_context):
    _, statistics, sql_results, patterns, _ = pipeline_context

    # Fabricate an insight collection with hallucinated 9999% profit and non-existent stats
    hallucinated_insights = InsightCollection(
        dataset_id=statistics.dataset_id,
        insights=[
            InsightItem(
                id="ins_fake",
                title="Massive Fabricated Growth",
                finding="Revenue grew by 9999% without baseline data, hallucinated profit of $50,000,000.",
                supporting_evidence="Fabricated number that does not exist in dataset statistics.",
                importance="High",
                confidence="High",
                recommendation="Invest immediately.",
                category="Revenue Driver"
            )
        ],
        executive_summary_points=["Hallucinated growth claim"],
        overall_confidence_rating="High"
    )

    review = CriticReviewAgent.review(
        insights=hallucinated_insights,
        statistics=statistics,
        sql_results=sql_results,
        patterns=patterns
    )

    assert review.approved is False
    assert len(review.unsupported_claims) >= 1
    assert len(review.required_corrections) >= 1

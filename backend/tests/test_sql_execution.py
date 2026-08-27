import os
import pytest
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.models.plan import AnalysisPlan, SQLQueryGoal
from backend.app.models.sql import GeneratedSQLQuery
from backend.app.agents.generate_sql import SQLGenerationAgent
from backend.app.services.sql.executor import SQLExecutor


@pytest.fixture
def registered_clean_dataset():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "samples", "clean_dataset.csv")
    with open(path, "rb") as f:
        content = f.read()
    df, _ = DatasetLoader.load_and_sanitize(content, ".csv")
    dataset_id, table_name = duckdb_manager.register_dataframe(df, "sql_exec_test_ds")
    profile = DatasetProfiler.profile_dataset(df, dataset_id, table_name)
    return dataset_id, table_name, profile


def test_sql_execution_single_query(registered_clean_dataset):
    dataset_id, table_name, _ = registered_clean_dataset

    query = GeneratedSQLQuery(
        name="sales_by_category",
        purpose="Compare total revenue across product categories",
        sql=f"SELECT category, SUM(total_revenue) AS total_rev, COUNT(*) as cnt FROM {table_name} GROUP BY category ORDER BY total_rev DESC",
        expected_columns=["category", "total_rev", "cnt"]
    )

    exec_res = SQLExecutor.execute_single_query(query, table_name)

    assert exec_res.is_safe is True
    assert exec_res.execution_status == "success"
    assert exec_res.row_count > 0
    assert "category" in exec_res.columns
    assert "total_rev" in exec_res.columns
    assert len(exec_res.rows) == exec_res.row_count
    assert exec_res.execution_duration_ms >= 0


def test_sql_generation_and_execution_pipeline(registered_clean_dataset):
    dataset_id, table_name, profile = registered_clean_dataset

    plan = AnalysisPlan(
        primary_goal="Revenue and quantity drivers",
        descriptive_numeric_columns=["total_revenue", "quantity"],
        correlation_pairs=[["quantity", "total_revenue"]],
        group_by_analyses=[],
        sql_query_goals=[
            SQLQueryGoal(
                name="revenue_by_region",
                purpose="Evaluate regional revenue contribution",
                columns_needed=["region", "total_revenue"]
            ),
            SQLQueryGoal(
                name="high_value_orders",
                purpose="Identify transactions with revenue over 200",
                columns_needed=["order_id", "total_revenue"]
            )
        ]
    )

    # 1. Generate SQL
    queries = SQLGenerationAgent.generate(profile, plan, table_name)
    assert len(queries) >= 1

    # 2. Execute SQL
    analysis_res = SQLExecutor.execute_queries(queries, dataset_id, table_name)
    assert analysis_res.total_queries == len(queries)
    assert analysis_res.successful_queries > 0
    assert len(analysis_res.results) == len(queries)
    for r in analysis_res.results:
        assert r.is_safe is True
        assert r.execution_status == "success"
        assert len(r.rows) > 0

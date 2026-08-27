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


def test_sql_execution_with_problematic_table_name_as_column():
    """Verifies that SQLExecutor auto-repairs queries where the table name was erroneously selected as a column."""
    import pandas as pd
    df = pd.DataFrame({"page": ["Home", "Product", "Cart", "Checkout"], "visits": [100, 80, 40, 20]})
    dataset_id, table_name = duckdb_manager.register_dataframe(df, "tbl_col_test_ds")

    # This is the exact query pattern that failed previously
    problematic_query = GeneratedSQLQuery(
        name=f"top_{table_name}_by_page",
        purpose=f"Aggregate total page grouped by {table_name}",
        sql=f"SELECT {table_name}, SUM(visits) AS total_visits, COUNT(*) AS record_count FROM {table_name} GROUP BY {table_name} ORDER BY total_visits DESC LIMIT 10",
        expected_columns=[table_name, "total_visits", "record_count"]
    )

    exec_res = SQLExecutor.execute_single_query(problematic_query, table_name)
    assert exec_res.execution_status == "success", f"Auto-repair failed: {exec_res.error_message}"
    assert exec_res.row_count > 0
    assert len(exec_res.rows) > 0


def test_sql_execution_with_string_aggregation_recovery():
    """Verifies that SQLExecutor recovers when SUM/AVG is mistakenly attempted on a string column."""
    import pandas as pd
    df = pd.DataFrame({"page": ["/home", "/pricing", "/about", "/contact"]})
    dataset_id, table_name = duckdb_manager.register_dataframe(df, "str_agg_test_ds")

    bad_query = GeneratedSQLQuery(
        name="overall_dataset_summary",
        purpose="Compute overall average, min, and max for page",
        sql=f"SELECT COUNT(*) AS total_records, AVG(page) AS avg_page, MIN(page) AS min_page, MAX(page) AS max_page FROM {table_name}",
        expected_columns=["total_records", "avg_page"]
    )

    exec_res = SQLExecutor.execute_single_query(bad_query, table_name)
    assert exec_res.execution_status == "success", f"String aggregation recovery failed: {exec_res.error_message}"
    assert exec_res.row_count == 1
    assert exec_res.rows[0]["total_records"] == 4


def test_page_dataset_end_to_end_pipeline():
    """Simulates uploading a dataset with a 'page' column and verifying 100% successful DuckDB query execution."""
    import pandas as pd
    df = pd.DataFrame({"page": ["Home", "Product", "Blog", "Home", "Cart", "Checkout", "Cart"]})
    dataset_id, table_name = duckdb_manager.register_dataframe(df, "page_dataset_pipeline_test")
    profile = DatasetProfiler.profile_dataset(df, dataset_id, table_name)

    plan = AnalysisPlan(
        primary_goal="Analyze page engagement and traffic",
        descriptive_numeric_columns=[],
        correlation_pairs=[],
        group_by_analyses=[],
        sql_query_goals=[
            SQLQueryGoal(
                name="top_page_distribution",
                purpose="Distribution of page visits",
                columns_needed=["page"]
            ),
            SQLQueryGoal(
                name="overall_page_summary",
                purpose="Total records and distinct pages",
                columns_needed=["page"]
            )
        ]
    )

    queries = SQLGenerationAgent.generate(profile, plan, table_name)
    assert len(queries) >= 1

    # Verify table name is NEVER in the SELECT/GROUP BY
    for q in queries:
        assert table_name not in q.sql.split("FROM")[0], f"Table name '{table_name}' found in SELECT projection: {q.sql}"

    analysis_res = SQLExecutor.execute_queries(queries, dataset_id, table_name)
    assert analysis_res.successful_queries == analysis_res.total_queries, f"Failed queries: {analysis_res.failed_queries}"
    assert analysis_res.failed_queries == 0

import pytest
from backend.app.services.sql.validator import SQLValidator


def test_valid_safe_sql_queries():
    # 1. Simple select
    is_safe, reason, sql = SQLValidator.validate_sql("SELECT order_id, total_revenue FROM dataset_tbl", expected_table="dataset_tbl")
    assert is_safe is True
    assert reason is None
    assert "SELECT" in sql

    # 2. Aggregations with GROUP BY and ORDER BY
    is_safe, reason, sql = SQLValidator.validate_sql(
        "SELECT category, SUM(total_revenue) AS rev FROM dataset_tbl GROUP BY category ORDER BY rev DESC LIMIT 5",
        expected_table="dataset_tbl"
    )
    assert is_safe is True

    # 3. CTE (Common Table Expression)
    cte_sql = """
    WITH regional_rev AS (
        SELECT region, SUM(total_revenue) AS total_rev
        FROM dataset_tbl
        GROUP BY region
    )
    SELECT region, total_rev, ROUND(total_rev * 100.0 / SUM(total_rev) OVER(), 2) as pct_share
    FROM regional_rev
    ORDER BY total_rev DESC
    """
    is_safe, reason, sql = SQLValidator.validate_sql(cte_sql, expected_table="dataset_tbl")
    assert is_safe is True


def test_reject_forbidden_keywords():
    dangerous_queries = [
        "DROP TABLE dataset_tbl",
        "DELETE FROM dataset_tbl WHERE id = 1",
        "INSERT INTO dataset_tbl VALUES (1, 'hack')",
        "UPDATE dataset_tbl SET total_revenue = 0",
        "ALTER TABLE dataset_tbl DROP COLUMN region",
        "CREATE TABLE test AS SELECT * FROM dataset_tbl",
        "ATTACH 'database.duckdb'",
        "PRAGMA version",
        "INSTALL httpfs",
        "LOAD httpfs",
        "COPY dataset_tbl TO 'output.parquet'",
        "IMPORT DATABASE 'dump'"
    ]

    for q in dangerous_queries:
        is_safe, reason, _ = SQLValidator.validate_sql(q, expected_table="dataset_tbl")
        assert is_safe is False, f"Failed to reject forbidden query: {q}"
        assert reason is not None


def test_reject_multi_statement_injection():
    injection_queries = [
        "SELECT * FROM dataset_tbl; DROP TABLE dataset_tbl",
        "SELECT 1; DELETE FROM dataset_tbl",
        "SELECT category FROM dataset_tbl; CREATE TABLE fake (a int);"
    ]

    for q in injection_queries:
        is_safe, reason, _ = SQLValidator.validate_sql(q, expected_table="dataset_tbl")
        assert is_safe is False, f"Failed to reject multi-statement injection: {q}"
        assert "Multiple SQL statements" in reason or "Forbidden" in reason


def test_reject_file_and_network_access():
    file_queries = [
        "SELECT * FROM read_csv('secret_passwords.csv')",
        "SELECT * FROM read_parquet('data.parquet')",
        "SELECT * FROM 'http://malicious.com/data.json'",
        "SELECT * FROM 's3://bucket/data.csv'"
    ]

    for q in file_queries:
        is_safe, reason, _ = SQLValidator.validate_sql(q, expected_table="dataset_tbl")
        assert is_safe is False, f"Failed to reject file/network query: {q}"

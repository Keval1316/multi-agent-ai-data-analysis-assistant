import time
from typing import List, Dict, Any, Optional
import pandas as pd
from backend.app.core.logging import logger
from backend.app.models.sql import GeneratedSQLQuery, SQLExecutionResult, SQLAnalysisResult
from backend.app.services.ingestion.duckdb_manager import duckdb_manager
from backend.app.services.sql.validator import SQLValidator


class SQLExecutor:
    """Executes validated analytical SQL queries safely against DuckDB in-memory tables."""

    @classmethod
    def execute_single_query(
        cls,
        query: GeneratedSQLQuery,
        table_name: str
    ) -> SQLExecutionResult:
        # 1. Validate SQL safety
        is_safe, reason, sanitized_sql = SQLValidator.validate_sql(query.sql, expected_table=table_name)
        if not is_safe:
            logger.warning(f"SQL validation rejected query '{query.name}': {reason}")
            return SQLExecutionResult(
                query_name=query.name,
                purpose=query.purpose,
                sql=query.sql,
                is_safe=False,
                validation_error=reason,
                execution_status="rejected",
                row_count=0,
                columns=[],
                rows=[],
                execution_duration_ms=0.0,
                error_message=reason
            )

        # 2. Execute query in DuckDB
        start_time = time.perf_counter()
        try:
            result_df = duckdb_manager.conn.execute(sanitized_sql).df()
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            columns = list(result_df.columns)
            row_count = int(len(result_df))

            # Sanitize NaNs and dates for clean JSON serialization
            clean_df = result_df.where(pd.notnull(result_df), None)
            # Convert datetime columns to strings
            for col in clean_df.select_dtypes(include=["datetime", "datetimetz"]).columns:
                clean_df[col] = clean_df[col].astype(str)

            # Limit output rows to top 100 to prevent payload explosion
            rows = clean_df.head(100).to_dict(orient="records")

            logger.info(f"Executed SQL '{query.name}' in {duration_ms}ms ({row_count} rows)")

            return SQLExecutionResult(
                query_name=query.name,
                purpose=query.purpose,
                sql=sanitized_sql,
                is_safe=True,
                validation_error=None,
                execution_status="success",
                row_count=row_count,
                columns=columns,
                rows=rows,
                execution_duration_ms=duration_ms,
                error_message=None
            )

        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"SQL execution error in '{query.name}': {str(e)}")
            return SQLExecutionResult(
                query_name=query.name,
                purpose=query.purpose,
                sql=sanitized_sql,
                is_safe=True,
                validation_error=None,
                execution_status="failed",
                row_count=0,
                columns=[],
                rows=[],
                execution_duration_ms=duration_ms,
                error_message=str(e)
            )

    @classmethod
    def execute_queries(
        cls,
        queries: List[GeneratedSQLQuery],
        dataset_id: str,
        table_name: str
    ) -> SQLAnalysisResult:
        logger.info(f"Executing {len(queries)} analytical queries on table '{table_name}'")

        results: List[SQLExecutionResult] = []
        success_cnt = 0
        failed_cnt = 0

        for q in queries:
            res = cls.execute_single_query(q, table_name)
            results.append(res)
            if res.execution_status == "success":
                success_cnt += 1
            else:
                failed_cnt += 1

        return SQLAnalysisResult(
            dataset_id=dataset_id,
            table_name=table_name,
            total_queries=len(queries),
            successful_queries=success_cnt,
            failed_queries=failed_cnt,
            results=results
        )

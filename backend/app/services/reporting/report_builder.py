from typing import Dict, Optional
import pandas as pd
from backend.app.core.logging import logger
from backend.app.models.report import AnalysisReport
from backend.app.models.profile import DatasetProfile
from backend.app.models.quality import QualityReport
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.services.quality.checker import QualityChecker
from backend.app.agents.understand_dataset import DatasetUnderstandingAgent
from backend.app.agents.plan_analysis import AnalysisPlanningAgent
from backend.app.services.statistics.engine import StatisticalEngine
from backend.app.agents.generate_sql import SQLGenerationAgent
from backend.app.services.sql.executor import SQLExecutor
from backend.app.services.patterns.detector import PatternDetector
from backend.app.services.visualization.chart_generator import ChartGenerator
from backend.app.agents.revise_insights import InsightRevisionOrchestrator
from backend.app.agents.generate_report import ReportGenerationAgent
from backend.app.services.ingestion.duckdb_manager import duckdb_manager


from backend.app.services.cleaning.cleaner import DataCleaner, CleaningSummary


class ReportBuilder:
    """Manages full end-to-end report generation pipeline and in-memory caching."""

    _cached_reports: Dict[str, AnalysisReport] = {}
    _cached_cleaned_dfs: Dict[str, pd.DataFrame] = {}

    @classmethod
    def get_report(cls, dataset_id: str) -> Optional[AnalysisReport]:
        return cls._cached_reports.get(dataset_id)

    @classmethod
    def cache_report(cls, report: AnalysisReport):
        cls._cached_reports[report.dataset_id] = report

    @classmethod
    def get_cleaned_df(cls, dataset_id: str) -> Optional[pd.DataFrame]:
        return cls._cached_cleaned_dfs.get(dataset_id)

    @classmethod
    def cache_cleaned_df(cls, dataset_id: str, df: pd.DataFrame):
        cls._cached_cleaned_dfs[dataset_id] = df

    @classmethod
    def list_history(cls):
        """Returns summarized metadata of all cached analysis reports ordered most recent first."""
        history = []
        for r in reversed(list(cls._cached_reports.values())):
            history.append({
                "dataset_id": r.dataset_id,
                "filename": r.filename,
                "title": r.title,
                "subtitle": r.subtitle,
                "generated_at": r.generated_at,
                "quality_score": r.quality.quality_score if r.quality else 100,
                "grade": r.quality.grade if r.quality else "A",
                "total_rows": r.profile.total_rows if r.profile else 0,
                "total_columns": r.profile.total_columns if r.profile else 0,
                "domain": r.understanding.domain if r.understanding else "General Data",
                "charts_count": len(r.charts.charts) if r.charts and r.charts.charts else 0,
                "insights_count": len(r.insights.insights) if r.insights and r.insights.insights else 0,
                "cleaning_summary": r.cleaning_summary
            })
        return history

    @classmethod
    def delete_report(cls, dataset_id: str) -> bool:
        """Deletes a cached report and cleans up any related DuckDB table."""
        if dataset_id in cls._cached_reports:
            del cls._cached_reports[dataset_id]
            if dataset_id in cls._cached_cleaned_dfs:
                del cls._cached_cleaned_dfs[dataset_id]
            try:
                tbl = duckdb_manager.generate_table_name(dataset_id)
                duckdb_manager.drop_table(tbl)
            except Exception as e:
                logger.warning(f"Failed to drop DuckDB table for '{dataset_id}': {e}")
            return True
        return False

    @classmethod
    def build_report_from_dataset(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        table_name: str,
        filename: str = "dataset.csv"
    ) -> AnalysisReport:
        logger.info(f"Building complete analysis report for dataset '{dataset_id}' ({filename})")

        # 1. Profile & Quality
        profile = DatasetProfiler.profile_dataset(df, dataset_id, table_name)
        quality = QualityChecker.audit_dataset(df, profile)

        # 2. Understanding & Planning
        understanding = DatasetUnderstandingAgent.analyze(profile, quality, filename)
        plan = AnalysisPlanningAgent.plan(profile, understanding)

        # 3. Statistical Analysis
        statistics = StatisticalEngine.run_analysis(df, profile, plan)

        # 4. SQL Generation & Execution
        queries = SQLGenerationAgent.generate(profile, plan, table_name)
        sql_results = SQLExecutor.execute_queries(queries, dataset_id, table_name)

        # 5. Pattern Detection & Charts
        patterns = PatternDetector.detect_all(df, profile)
        charts = ChartGenerator.generate_all(df, profile, plan)

        # 6. Insight Generation & Critic Loop
        insights, critic_review, rev_cnt = InsightRevisionOrchestrator.run_generation_and_critic_loop(
            understanding=understanding,
            statistics=statistics,
            sql_results=sql_results,
            patterns=patterns,
            quality=quality
        )

        # 7. Compile Full Report
        report = ReportGenerationAgent.generate(
            understanding=understanding,
            profile=profile,
            quality=quality,
            statistics=statistics,
            sql_results=sql_results,
            patterns=patterns,
            charts=charts,
            insights=insights,
            filename=filename
        )

        # 8. Deterministic Data Cleaning & Sanitization
        cleaned_df, cleaning_summary = DataCleaner.clean_dataset(df, dataset_id, filename)
        cls.cache_cleaned_df(dataset_id, cleaned_df)
        report.cleaning_summary = cleaning_summary.model_dump()

        # Cache report
        cls.cache_report(report)
        return report

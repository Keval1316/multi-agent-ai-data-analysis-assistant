import json
from pathlib import Path
from typing import Dict, Optional, List
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

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".cache"
REPORTS_CACHE_DIR = CACHE_DIR / "reports"
CLEANED_CACHE_DIR = CACHE_DIR / "cleaned"

REPORTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ReportBuilder:
    """Manages full end-to-end report generation pipeline and in-memory + disk caching."""

    _cached_reports: Dict[str, AnalysisReport] = {}
    _cached_cleaned_dfs: Dict[str, pd.DataFrame] = {}

    @classmethod
    def get_report(cls, dataset_id: str) -> Optional[AnalysisReport]:
        if dataset_id in cls._cached_reports:
            return cls._cached_reports[dataset_id]
        
        # Check disk cache
        try:
            report_file = REPORTS_CACHE_DIR / f"{dataset_id}.json"
            if report_file.exists():
                with open(report_file, "r", encoding="utf-8") as f:
                    report = AnalysisReport.model_validate_json(f.read())
                    cls._cached_reports[dataset_id] = report
                    return report
        except Exception as e:
            logger.warning(f"Failed to read report '{dataset_id}' from disk cache: {e}")

        return None

    @classmethod
    def cache_report(cls, report: AnalysisReport):
        cls._cached_reports[report.dataset_id] = report
        try:
            REPORTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            report_file = REPORTS_CACHE_DIR / f"{report.dataset_id}.json"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))
        except Exception as e:
            logger.warning(f"Failed to persist report '{report.dataset_id}' to disk cache: {e}")

    @classmethod
    def get_cleaned_df(cls, dataset_id: str) -> Optional[pd.DataFrame]:
        if dataset_id in cls._cached_cleaned_dfs:
            return cls._cached_cleaned_dfs[dataset_id]

        # Check disk cache
        try:
            csv_file = CLEANED_CACHE_DIR / f"{dataset_id}.csv"
            if csv_file.exists():
                df = pd.read_csv(csv_file)
                cls._cached_cleaned_dfs[dataset_id] = df
                # Re-register into DuckDB if needed
                tbl = duckdb_manager.generate_table_name(dataset_id)
                if not duckdb_manager.table_exists(tbl):
                    duckdb_manager.register_dataframe(df, dataset_id, tbl)
                return df
        except Exception as e:
            logger.warning(f"Failed to read cleaned df '{dataset_id}' from disk cache: {e}")

        return None

    @classmethod
    def cache_cleaned_df(cls, dataset_id: str, df: pd.DataFrame):
        cls._cached_cleaned_dfs[dataset_id] = df
        try:
            CLEANED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            csv_file = CLEANED_CACHE_DIR / f"{dataset_id}.csv"
            df.to_csv(csv_file, index=False)
        except Exception as e:
            logger.warning(f"Failed to persist cleaned df for '{dataset_id}' to disk cache: {e}")

    @classmethod
    def list_history(cls):
        """Returns summarized metadata of all cached analysis reports ordered most recent first."""
        # Sync disk cache into memory
        try:
            if REPORTS_CACHE_DIR.exists():
                for f in REPORTS_CACHE_DIR.glob("*.json"):
                    did = f.stem
                    if did not in cls._cached_reports:
                        with open(f, "r", encoding="utf-8") as rf:
                            cls._cached_reports[did] = AnalysisReport.model_validate_json(rf.read())
        except Exception as e:
            logger.warning(f"Error syncing history from disk cache: {e}")

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
        """Deletes a cached report and cleans up any related DuckDB table and disk cache."""
        deleted = False
        if dataset_id in cls._cached_reports:
            del cls._cached_reports[dataset_id]
            deleted = True
        if dataset_id in cls._cached_cleaned_dfs:
            del cls._cached_cleaned_dfs[dataset_id]
            deleted = True

        # Delete from disk cache
        try:
            report_file = REPORTS_CACHE_DIR / f"{dataset_id}.json"
            if report_file.exists():
                report_file.unlink()
                deleted = True
            csv_file = CLEANED_CACHE_DIR / f"{dataset_id}.csv"
            if csv_file.exists():
                csv_file.unlink()
                deleted = True
        except Exception as e:
            logger.warning(f"Failed to delete disk files for '{dataset_id}': {e}")

        try:
            tbl = duckdb_manager.generate_table_name(dataset_id)
            duckdb_manager.drop_table(tbl)
        except Exception as e:
            logger.warning(f"Failed to drop DuckDB table for '{dataset_id}': {e}")

        return deleted

    @classmethod
    def build_report_from_dataset(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        table_name: str,
        filename: str = "dataset.csv"
    ) -> AnalysisReport:
        logger.info(f"Building complete analysis report for dataset '{dataset_id}' ({filename})")

        # 1. Profile & Quality on raw input
        raw_profile = DatasetProfiler.profile_dataset(df, dataset_id, table_name)
        quality = QualityChecker.audit_dataset(df, raw_profile)

        # 2. Early Data Cleaning & Sanitization
        cleaned_df, cleaning_summary = DataCleaner.clean_dataset(df, dataset_id, filename)
        cls.cache_cleaned_df(dataset_id, cleaned_df)

        # Re-register cleaned table in DuckDB and re-profile
        duckdb_manager.register_dataframe(cleaned_df, dataset_id, table_name)
        profile = DatasetProfiler.profile_dataset(cleaned_df, dataset_id, table_name)

        # 3. Understanding & Planning
        understanding = DatasetUnderstandingAgent.analyze(profile, quality, filename)
        plan = AnalysisPlanningAgent.plan(profile, understanding)

        # 4. Statistical Analysis on Cleaned Data
        statistics = StatisticalEngine.run_analysis(cleaned_df, profile, plan)

        # 5. SQL Generation & Execution against Cleaned Table
        queries = SQLGenerationAgent.generate(profile, plan, table_name)
        sql_results = SQLExecutor.execute_queries(queries, dataset_id, table_name)

        # 6. Pattern Detection & Visualizations
        patterns = PatternDetector.detect_all(cleaned_df, profile)
        charts = ChartGenerator.generate_all(cleaned_df, profile, plan)

        # 7. Insight Generation & Adversarial Critic Loop
        insights, critic_review, rev_cnt = InsightRevisionOrchestrator.run_generation_and_critic_loop(
            understanding=understanding,
            statistics=statistics,
            sql_results=sql_results,
            patterns=patterns,
            quality=quality
        )

        # 8. Compile Comprehensive Report
        report = ReportGenerationAgent.generate(
            understanding=understanding,
            profile=profile,
            quality=quality,
            statistics=statistics,
            sql_results=sql_results,
            patterns=patterns,
            charts=charts,
            insights=insights,
            cleaning_summary=cleaning_summary.model_dump(),
            filename=filename
        )

        # Cache report
        cls.cache_report(report)
        return report

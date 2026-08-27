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


class ReportBuilder:
    """Manages full end-to-end report generation pipeline and in-memory caching."""

    _cached_reports: Dict[str, AnalysisReport] = {}

    @classmethod
    def get_report(cls, dataset_id: str) -> Optional[AnalysisReport]:
        return cls._cached_reports.get(dataset_id)

    @classmethod
    def cache_report(cls, report: AnalysisReport):
        cls._cached_reports[report.dataset_id] = report

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

        # Cache report
        cls.cache_report(report)
        return report

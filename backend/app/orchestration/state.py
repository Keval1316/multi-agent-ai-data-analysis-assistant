from typing import TypedDict, Optional, List, Dict, Any
import pandas as pd
from backend.app.models.profile import DatasetProfile
from backend.app.models.quality import QualityReport
from backend.app.models.understanding import DatasetUnderstanding
from backend.app.models.plan import AnalysisPlan
from backend.app.models.statistics import StatisticalAnalysisResult
from backend.app.models.sql import GeneratedSQLQuery, SQLAnalysisResult
from backend.app.models.patterns import PatternDetectionResult
from backend.app.models.visualization import ChartCollection
from backend.app.models.insights import InsightCollection
from backend.app.models.critic import CriticReviewResult
from backend.app.models.report import AnalysisReport


class AnalysisWorkflowState(TypedDict, total=False):
    dataset_id: str
    filename: str
    file_bytes: Optional[bytes]
    file_extension: str
    table_name: str
    df: Optional[pd.DataFrame]

    # Pipeline Artifacts
    profile: Optional[DatasetProfile]
    quality: Optional[QualityReport]
    understanding: Optional[DatasetUnderstanding]
    plan: Optional[AnalysisPlan]
    statistics: Optional[StatisticalAnalysisResult]
    sql_queries: List[GeneratedSQLQuery]
    validated_sql_queries: List[GeneratedSQLQuery]
    sql_results: Optional[SQLAnalysisResult]
    patterns: Optional[PatternDetectionResult]
    charts: Optional[ChartCollection]
    insights: Optional[InsightCollection]
    critic_review: Optional[CriticReviewResult]
    critic_approved: bool
    revision_count: int
    revision_critique: Optional[str]
    report: Optional[AnalysisReport]
    pdf_bytes: Optional[bytes]

    # Execution State
    current_step: str
    step_index: int
    total_steps: int
    status_label: str
    logs: List[str]
    error: Optional[str]

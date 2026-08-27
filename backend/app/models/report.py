from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.models.profile import DatasetProfile
from backend.app.models.quality import QualityReport
from backend.app.models.understanding import DatasetUnderstanding
from backend.app.models.statistics import StatisticalAnalysisResult
from backend.app.models.sql import SQLAnalysisResult
from backend.app.models.patterns import PatternDetectionResult
from backend.app.models.visualization import ChartCollection
from backend.app.models.insights import InsightCollection


class ReportSection(BaseModel):
    id: str
    title: str
    summary: str
    markdown_content: str


class GeneratedReportMarkdown(BaseModel):
    title: str = Field(..., description="Report title")
    subtitle: str = Field(..., description="Report subtitle / scope")
    executive_summary: str = Field(..., description="Comprehensive executive summary in markdown")
    key_findings_markdown: str = Field(..., description="Detailed narrative of key findings")
    strategic_recommendations_markdown: str = Field(..., description="Actionable business recommendations")
    methodology_and_caveats_markdown: str = Field(..., description="Data limitations, methodology, and caveats")


class AnalysisReport(BaseModel):
    dataset_id: str
    filename: str
    generated_at: str
    title: str
    subtitle: str
    executive_summary: str
    markdown_report: str
    sections: List[ReportSection] = Field(default_factory=list)
    understanding: DatasetUnderstanding
    profile: DatasetProfile
    quality: QualityReport
    statistics: StatisticalAnalysisResult
    sql_results: SQLAnalysisResult
    patterns: PatternDetectionResult
    charts: ChartCollection
    insights: InsightCollection
    cleaning_summary: Optional[Dict[str, Any]] = None

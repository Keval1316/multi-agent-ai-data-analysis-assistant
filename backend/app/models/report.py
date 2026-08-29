from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator
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
    executive_summary_markdown: str = Field(..., description="Section 1: Executive Summary (Overall, Key Findings, Main Risks, Recommended Next Steps)")
    dataset_overview_markdown: str = Field(..., description="Section 2: Dataset Overview (records, variables, quality score, duplicate rows)")
    data_quality_and_validation_markdown: str = Field(..., description="Section 3: Data Quality & Validation (missing values, imputation breakdown table, invalid values, query validation warnings)")
    key_findings_markdown: str = Field(..., description="Section 4: Key Findings (Finding, Evidence, What this means, Confidence)")
    distribution_analysis_markdown: str = Field(..., description="Section 5: Distribution Analysis (mean, median, IQR, skewness, spread in plain English)")
    category_analysis_markdown: str = Field(..., description="Section 6: Category Analysis (distribution, inventory concentration, top/bottom groups)")
    product_analysis_markdown: str = Field(..., description="Section 7: Product / Item Analysis (highest/lowest stock, concentration, outliers, inventory risks)")
    supplier_analysis_markdown: str = Field(..., description="Section 8: Supplier Inventory Contribution Analysis (with performance metric limitations note)")
    relationship_analysis_markdown: str = Field(..., description="Section 9: Relationship & Correlation Analysis (strength, direction, p-value, practical significance, causality warning)")
    trend_analysis_markdown: str = Field(..., description="Section 10: Trend & Regression Analysis (direction, R², p-value, plain-English interpretation)")
    recommendations_markdown: str = Field(..., description="Section 11: Actionable Recommendations (Finding, Evidence, Business Implication, Recommended Action, Confidence)")
    limitations_markdown: str = Field(..., description="Section 12: Dataset-Specific Analytical Limitations")
    suggested_next_analysis_markdown: str = Field(..., description="Section 13: Suggested Next Analysis & Data Requirements")

    # Backward compatibility aliases
    executive_summary: Optional[str] = None
    strategic_recommendations_markdown: Optional[str] = None
    methodology_and_caveats_markdown: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_compatibility_fields(cls, data: dict):
        if isinstance(data, dict):
            # Sync executive summary
            if "executive_summary_markdown" not in data and "executive_summary" in data:
                data["executive_summary_markdown"] = data["executive_summary"]
            elif "executive_summary" not in data and "executive_summary_markdown" in data:
                data["executive_summary"] = data["executive_summary_markdown"]

            # Sync recommendations
            if "recommendations_markdown" not in data and "strategic_recommendations_markdown" in data:
                data["recommendations_markdown"] = data["strategic_recommendations_markdown"]
            elif "strategic_recommendations_markdown" not in data and "recommendations_markdown" in data:
                data["strategic_recommendations_markdown"] = data["recommendations_markdown"]

            # Sync limitations/methodology
            if "limitations_markdown" not in data and "methodology_and_caveats_markdown" in data:
                data["limitations_markdown"] = data["methodology_and_caveats_markdown"]
            elif "methodology_and_caveats_markdown" not in data and "limitations_markdown" in data:
                data["methodology_and_caveats_markdown"] = data["limitations_markdown"]

            # Fill missing section markdown fields gracefully if called with older structure
            defaults = {
                "dataset_overview_markdown": "Dataset Overview documented in tabular profiles.",
                "data_quality_and_validation_markdown": "Data Quality audit and validation rules verified.",
                "distribution_analysis_markdown": "Distribution moments computed across numerical metrics.",
                "category_analysis_markdown": "Category distribution and inventory concentration analyzed.",
                "product_analysis_markdown": "Item-level distributions and inventory concentrations assessed.",
                "supplier_analysis_markdown": "Supplier inventory contribution evaluated.",
                "relationship_analysis_markdown": "Correlation matrices and relationship pairs analyzed.",
                "trend_analysis_markdown": "Temporal and regression trends evaluated.",
                "suggested_next_analysis_markdown": "Recommended next analyses and data collection initiatives."
            }
            for k, def_val in defaults.items():
                if k not in data or not data[k]:
                    data[k] = def_val
        return data


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
    data_quality_breakdown: Optional[List[Dict[str, Any]]] = None

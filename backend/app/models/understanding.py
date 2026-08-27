from typing import List, Optional
from pydantic import BaseModel, Field


class KPICandidate(BaseModel):
    name: str = Field(..., description="Human-readable KPI name (e.g., 'Total Net Revenue')")
    column_name: Optional[str] = Field(None, description="Primary column name if directly mapped")
    aggregation: str = Field(..., description="e.g. 'SUM', 'AVG', 'COUNT', 'RATIO'")
    description: str = Field(..., description="Business significance of this metric")
    importance: str = Field("High", description="'High', 'Medium', or 'Low'")


class DimensionCandidate(BaseModel):
    column_name: str = Field(..., description="Name of the categorical or datetime column")
    dimension_name: str = Field(..., description="Descriptive label (e.g., 'Geographic Region')")
    role: str = Field(..., description="'segmentation', 'time_series', 'filtering', 'entity_id'")


class DatasetUnderstanding(BaseModel):
    domain: str = Field(..., description="Business or operational domain (e.g. 'Healthcare', 'Finance', 'Workforce', 'Sales')")
    dataset_summary: str = Field(..., description="Concise narrative summary of the dataset content")
    target_entity: str = Field(..., description="Primary entity recorded (e.g. 'Patient Record', 'Employee Profile', 'Transaction')")
    key_kpis: List[KPICandidate] = Field(..., min_length=1, description="Candidate KPIs and analytical metrics")
    important_dimensions: List[DimensionCandidate] = Field(..., min_length=1, description="Dimensions for grouping/segmentation")
    core_questions: Optional[List[str]] = Field(default_factory=list, description="Initial scoping vectors prior to empirical data modeling")
    data_limitations_note: Optional[str] = Field(None, description="Caveats regarding missingness or data quality")


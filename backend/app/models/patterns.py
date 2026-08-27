from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TrendPattern(BaseModel):
    metric_column: str
    dimension_column: Optional[str] = None
    direction: str = Field(..., description="'increasing', 'decreasing', 'stable', 'volatile'")
    slope: float
    r_squared: float
    growth_rate_pct: float
    description: str
    is_statistically_significant: bool = False


class ParetoConcentrationPattern(BaseModel):
    dimension_column: str
    metric_column: str
    top_categories_count: int
    top_categories_share_pct: float
    total_categories_count: int
    top_category_names: List[str]
    is_pareto_dominated: bool = Field(..., description="True if top ~20% account for >= 60-80% of total")
    description: str


class AnomalyPattern(BaseModel):
    id: str
    metric_column: str
    row_identifier: Optional[str] = None
    value: float
    z_score: float
    deviation_factor: float
    description: str
    severity: str = Field("medium", description="'high', 'medium', 'low'")


class SeasonalityPattern(BaseModel):
    datetime_column: str
    metric_column: str
    period_type: str = Field(..., description="'day_of_week', 'monthly', 'quarterly'")
    peak_period: str
    trough_period: str
    peak_to_trough_ratio: float
    description: str


class PatternDetectionResult(BaseModel):
    dataset_id: str
    trends: List[TrendPattern] = Field(default_factory=list)
    concentrations: List[ParetoConcentrationPattern] = Field(default_factory=list)
    anomalies: List[AnomalyPattern] = Field(default_factory=list)
    seasonality: List[SeasonalityPattern] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)

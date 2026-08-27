from typing import List, Optional
from pydantic import BaseModel, Field


class GroupByAnalysisPlan(BaseModel):
    group_column: str = Field(..., description="Categorical or date column to group by")
    metric_column: str = Field(..., description="Numeric column to aggregate")
    aggregation: str = Field("SUM", description="'SUM', 'AVG', 'COUNT', 'MEDIAN'")
    purpose: str = Field(..., description="Business question addressed by this grouping")


class SQLQueryGoal(BaseModel):
    name: str = Field(..., description="Snake_case query identifier (e.g. 'revenue_by_region')")
    purpose: str = Field(..., description="Analytical goal of the query")
    columns_needed: List[str] = Field(..., description="Columns required for this SQL query")


class RecommendedChart(BaseModel):
    chart_type: str = Field(..., description="'bar', 'line', 'scatter', 'box', 'histogram'")
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    title: str
    purpose: str


class AnalysisPlan(BaseModel):
    primary_goal: str = Field(..., description="Core analytical objective")
    descriptive_numeric_columns: List[str] = Field(default_factory=list, description="Columns for summary statistics")
    correlation_pairs: List[List[str]] = Field(default_factory=list, description="Pairs of numeric columns to check correlation")
    group_by_analyses: List[GroupByAnalysisPlan] = Field(default_factory=list, description="Categorical aggregation breakdowns")
    sql_query_goals: List[SQLQueryGoal] = Field(..., min_length=1, description="Target analytical SQL queries")
    pattern_detection_targets: List[str] = Field(default_factory=list, description="Targets for trend, anomaly, or segment detection")
    recommended_charts: List[RecommendedChart] = Field(default_factory=list, description="Key charts to generate")

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PlotlyChartSpec(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    chart_type: str = Field(..., description="'bar', 'horizontal_bar', 'line', 'scatter', 'box', 'donut', 'histogram', 'grouped_bar'")
    data: List[Dict[str, Any]] = Field(..., description="Plotly traces array")
    layout: Dict[str, Any] = Field(..., description="Plotly layout configuration")
    config: Dict[str, Any] = Field(default_factory=lambda: {"responsive": True, "displayModeBar": True, "displaylogo": False})
    insights_summary: Optional[str] = Field(None, description="Analytical takeaway for this visual computed from data")
    x_column: Optional[str] = Field(None, description="Primary X-axis column")
    y_column: Optional[str] = Field(None, description="Primary Y-axis column")
    grouping_column: Optional[str] = Field(None, description="Segmentation or color grouping column")
    aggregation: Optional[str] = Field(None, description="'sum', 'avg', 'median', 'count', 'rate'")
    priority_score: Optional[float] = Field(None, description="Composite ranking score for chart selection")
    reasoning: Optional[str] = Field(None, description="Analytical rationale for selecting this chart")


class ChartCollection(BaseModel):
    dataset_id: str
    charts: List[PlotlyChartSpec] = Field(default_factory=list)
    empty_reason: Optional[str] = Field(None, description="Explanation if no meaningful visualizations could be generated")

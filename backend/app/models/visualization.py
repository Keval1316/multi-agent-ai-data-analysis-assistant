from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PlotlyChartSpec(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    chart_type: str = Field(..., description="'bar', 'line', 'scatter', 'box', 'donut', 'histogram'")
    data: List[Dict[str, Any]] = Field(..., description="Plotly traces array")
    layout: Dict[str, Any] = Field(..., description="Plotly layout configuration")
    config: Dict[str, Any] = Field(default_factory=lambda: {"responsive": True, "displayModeBar": True, "displaylogo": False})
    insights_summary: Optional[str] = Field(None, description="Analytical takeaway for this visual")


class ChartCollection(BaseModel):
    dataset_id: str
    charts: List[PlotlyChartSpec] = Field(default_factory=list)

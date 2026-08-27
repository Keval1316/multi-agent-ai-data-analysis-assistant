from typing import List, Optional
from pydantic import BaseModel, Field


class InsightItem(BaseModel):
    id: str = Field(..., description="Unique insight identifier (e.g. 'ins_1')")
    title: str = Field(..., description="Clear, concise headline summarizing the finding")
    finding: str = Field(..., description="Detailed analytical finding grounded strictly in evidence")
    supporting_evidence: str = Field(..., description="Exact numbers, percentages, correlations, or SQL results supporting this claim")
    importance: str = Field("High", description="'High', 'Medium', or 'Low'")
    confidence: str = Field("High", description="'High', 'Medium', or 'Caveat'")
    recommendation: Optional[str] = Field(None, description="Actionable business or strategic recommendation")
    category: str = Field("Performance", description="e.g. 'Revenue Driver', 'Operational Risk', 'Anomaly', 'Efficiency'")


class InsightCollection(BaseModel):
    dataset_id: str
    insights: List[InsightItem] = Field(..., min_length=1, description="List of evidence-grounded insights")
    executive_summary_points: List[str] = Field(default_factory=list, description="Top 3-4 bullet takeaways")
    overall_confidence_rating: str = Field("High", description="'High', 'Medium', 'Low'")

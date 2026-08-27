from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class InsightItem(BaseModel):
    id: str = Field(..., description="Unique insight identifier (e.g. 'ins_1')")
    title: str = Field(..., description="Clear, concise headline summarizing the finding")
    finding: str = Field(..., description="Direct analytical finding grounded strictly in evidence")
    evidence: str = Field(..., description="Exact numbers, percentages, baseline figures, correlations, or SQL outputs")
    interpretation: str = Field(..., description="Business, operational, clinical, or domain significance of the numbers")
    implication: str = Field(..., description="Strategic recommendation or actionable next step for decision-makers")
    question_answered: Optional[str] = Field(None, description="The specific core business/analytical question this insight answers based on actual data patterns")
    empirical_answer: Optional[str] = Field(None, description="Direct quantitative answer backed by empirical data and statistical patterns")
    supporting_evidence: Optional[str] = Field(None, description="Compatibility alias for evidence")
    recommendation: Optional[str] = Field(None, description="Compatibility alias for implication")
    importance: str = Field("High", description="'High', 'Medium', or 'Low'")
    confidence: str = Field("High", description="'High', 'Medium', or 'Caveat'")
    category: str = Field("Performance", description="e.g. 'Performance', 'Growth Driver', 'Operational Risk', 'Anomaly', 'Efficiency'")

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: dict):
        if isinstance(data, dict):
            # Sync evidence and supporting_evidence
            if "evidence" not in data and "supporting_evidence" in data:
                data["evidence"] = data["supporting_evidence"]
            elif "supporting_evidence" not in data and "evidence" in data:
                data["supporting_evidence"] = data["evidence"]

            # Sync implication and recommendation
            if "implication" not in data and "recommendation" in data:
                data["implication"] = data["recommendation"]
            elif "recommendation" not in data and "implication" in data:
                data["recommendation"] = data["implication"]

            # Sync empirical_answer and finding
            if "empirical_answer" not in data and "finding" in data:
                data["empirical_answer"] = data["finding"]
            elif "finding" not in data and "empirical_answer" in data:
                data["finding"] = data["empirical_answer"]

            # Default question_answered if missing
            if not data.get("question_answered"):
                cat = data.get("category", "performance")
                title = data.get("title", "this metric")
                data["question_answered"] = f"What key empirical pattern is revealed regarding {cat} in {title}?"

            # Default interpretation if missing
            if "interpretation" not in data:
                data["interpretation"] = data.get("finding", "")
        return data


class InsightCollection(BaseModel):
    dataset_id: str
    insights: List[InsightItem] = Field(..., min_length=1, description="List of evidence-grounded insights")
    executive_summary_points: List[str] = Field(default_factory=list, description="Top 3-4 bullet takeaways")
    overall_confidence_rating: str = Field("High", description="'High', 'Medium', 'Low'")
    answered_questions: Optional[List[dict]] = Field(default_factory=list, description="List of data-driven questions with empirical answers")



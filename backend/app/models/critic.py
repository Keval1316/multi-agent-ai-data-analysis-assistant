from typing import List, Optional
from pydantic import BaseModel, Field


class UnsupportedClaim(BaseModel):
    insight_id: str
    claim_text: str
    reason: str = Field(..., description="e.g. 'Fabricated number', 'Overstated causation', 'Contradicts computed statistic'")
    ground_truth_fact: Optional[str] = None


class CriticReviewResult(BaseModel):
    approved: bool = Field(..., description="True if all claims are factually supported by analysis evidence")
    feedback: str = Field(..., description="Detailed review commentary")
    unsupported_claims: List[UnsupportedClaim] = Field(default_factory=list, description="Specific unsupported or hallucinated statements")
    required_corrections: List[str] = Field(default_factory=list, description="List of concrete corrections needed")
    severity_of_discrepancy: str = Field("None", description="'None', 'Minor', 'Moderate', 'Critical'")

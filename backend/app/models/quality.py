from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class QualitySeverity(str, Enum):
    CONFIRMED_ISSUE = "confirmed_issue"
    SUSPICIOUS_ISSUE = "suspicious_issue"
    INFORMATIONAL = "informational"


class QualityIssue(BaseModel):
    id: str
    column_name: Optional[str] = None
    category: str = Field(..., description="e.g. 'missing_values', 'duplicate_rows', 'outliers', 'inconsistent_labels', 'mixed_types', 'invalid_values'")
    severity: QualitySeverity
    title: str
    description: str
    affected_count: int = 0
    affected_percentage: float = 0.0
    sample_affected_values: List[Any] = Field(default_factory=list)
    suggested_action: str


class QualityReport(BaseModel):
    dataset_id: str
    table_name: str
    quality_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score from 0 to 100")
    grade: str = Field(..., description="Quality grade: A, B, C, D, or F")
    issues_count: Dict[str, int] = Field(..., description="Summary counts by severity")
    total_issues: int
    issues: List[QualityIssue]
    summary: str
    is_analysis_ready: bool

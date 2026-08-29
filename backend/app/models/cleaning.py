from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChangeLogEntry(BaseModel):
    """Represents a granular, row-level change applied by the data cleaner."""
    row_id: Any = Field(..., description="Row index or primary key identifier")
    column: str = Field(..., description="Column name where transformation was applied")
    original_value: Any = Field(..., description="Raw original value before cleaning")
    new_value: Any = Field(..., description="Sanitized / corrected / derived value")
    rule: str = Field(
        ...,
        description="Cleaning rule applied (e.g. 'numeric_range_validation', 'categorical_normalization', 'cross_field_derivation', 'cross_field_reconciliation', 'null_imputation', 'exact_duplicate_removal', 'near_duplicate_merge', 'placeholder_removal', 'date_normalization', 'encoding_cleanup', 'unit_normalization')"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence level of the transformation (0.0 to 1.0)")
    confidence_level: str = Field(default="HIGH", description="Confidence tier: HIGH (>=0.9), MEDIUM (0.7-0.89), LOW (<0.7)")
    description: Optional[str] = Field(None, description="Detailed human-readable explanation of why this change was made")
    is_assumption: bool = Field(default=False, description="True if change was made based on heuristic assumption")


class UnresolvedIssue(BaseModel):
    """Represents an ambiguous or severe data quality issue flagged for human review."""
    row_id: Optional[Any] = None
    column: Optional[str] = None
    issue_type: str = Field(..., description="Type of issue: conflict, out_of_range, ambiguous_date, high_cardinality, unresolvable")
    raw_value: Any = None
    reason: str = Field(..., description="Why the automated cleaner stopped short of an automatic fix")
    suggested_action: str = Field(..., description="Recommended human action")
    severity: str = Field(default="warning", description="Severity: info, warning, conflict, error")


class ConfidenceAnnotation(BaseModel):
    """Surfaces assumptions and lower-confidence transformations prominently."""
    column: str
    row_id: Optional[Any] = None
    rule: str
    original_value: Any
    new_value: Any
    confidence: float
    reason: str


class BeforeAfterSummary(BaseModel):
    """Comparative before-and-after audit metrics across the dataset."""
    original_rows: int
    cleaned_rows: int
    original_columns: int
    cleaned_columns: int
    missing_rate_per_column_before: Dict[str, float] = Field(default_factory=dict)
    missing_rate_per_column_after: Dict[str, float] = Field(default_factory=dict)
    out_of_range_counts_before: Dict[str, int] = Field(default_factory=dict)
    out_of_range_counts_after: Dict[str, int] = Field(default_factory=dict)
    distinct_categories_before: Dict[str, int] = Field(default_factory=dict)
    distinct_categories_after: Dict[str, int] = Field(default_factory=dict)
    categorical_mappings: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    date_formats_detected: Dict[str, List[str]] = Field(default_factory=dict)
    date_formats_applied: Dict[str, str] = Field(default_factory=dict)
    outliers_flagged: List[Dict[str, Any]] = Field(default_factory=list)
    near_duplicates_merged: int = 0
    encoding_artifacts_fixed: int = 0
    unresolved_count: int = 0


class CleaningSummary(BaseModel):
    """Complete structured output contract returned by DataCleaner."""
    original_rows: int
    cleaned_rows: int
    original_columns: int
    cleaned_columns: int
    duplicates_removed: int = 0
    near_duplicates_merged: int = 0
    encoding_artifacts_fixed: int = 0
    nulls_imputed: int = 0
    nulls_derived: int = 0
    categories_standardized: int = 0
    dates_normalized: int = 0
    numeric_cleaned: int = 0
    out_of_range_corrected: int = 0
    cross_field_reconciled: int = 0
    validation_passed: bool = True
    transformations: List[str] = Field(default_factory=list)
    change_log: List[ChangeLogEntry] = Field(default_factory=list)
    before_after: Optional[BeforeAfterSummary] = None
    unresolved_issues: List[UnresolvedIssue] = Field(default_factory=list)
    confidence_annotations: List[ConfidenceAnnotation] = Field(default_factory=list)

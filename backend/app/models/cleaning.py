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
        description="Cleaning rule applied (e.g. 'numeric_range_validation', 'categorical_normalization', 'cross_field_derivation', 'cross_field_reconciliation', 'null_imputation', 'exact_duplicate_removal', 'placeholder_removal', 'date_normalization')"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence level of the transformation (0.0 to 1.0)")
    description: Optional[str] = Field(None, description="Detailed human-readable explanation of why this change was made")


class UnresolvedIssue(BaseModel):
    """Represents an ambiguous or severe data quality issue flagged for human review."""
    row_id: Optional[Any] = None
    column: Optional[str] = None
    issue_type: str
    raw_value: Any
    reason: str
    suggested_action: str


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
    categorical_mappings: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    unresolved_count: int = 0


class CleaningSummary(BaseModel):
    """Complete structured output contract returned by DataCleaner."""
    original_rows: int
    cleaned_rows: int
    original_columns: int
    cleaned_columns: int
    duplicates_removed: int = 0
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

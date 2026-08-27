from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class NumericStats(BaseModel):
    min: float
    max: float
    mean: float
    median: float
    std: float
    q25: float
    q75: float
    iqr: float
    skewness: Optional[float] = None


class CategoricalValueFreq(BaseModel):
    value: str
    count: int
    percentage: float


class CategoricalStats(BaseModel):
    cardinality: int
    unique_count: int
    top_values: List[CategoricalValueFreq]
    is_high_cardinality: bool


class DatetimeStats(BaseModel):
    min_date: str
    max_date: str
    days_range: Optional[float] = None


class ColumnProfile(BaseModel):
    name: str
    original_name: str
    semantic_type: str = Field(..., description="'numeric', 'categorical', 'datetime', 'boolean', 'identifier'")
    dtype: str
    total_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    is_identifier_candidate: bool = False
    numeric_stats: Optional[NumericStats] = None
    categorical_stats: Optional[CategoricalStats] = None
    datetime_stats: Optional[DatetimeStats] = None
    sample_values: List[Any] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    dataset_id: str
    table_name: str
    total_rows: int
    total_columns: int
    duplicate_rows_count: int
    duplicate_rows_percentage: float
    column_profiles: List[ColumnProfile]
    numeric_column_names: List[str]
    categorical_column_names: List[str]
    datetime_column_names: List[str]
    boolean_column_names: List[str]
    identifier_column_names: List[str]

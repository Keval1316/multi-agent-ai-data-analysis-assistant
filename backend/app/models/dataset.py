from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    name: str = Field(..., description="Sanitized column name used in DuckDB")
    original_name: str = Field(..., description="Original column header in uploaded file")
    dtype: str = Field(..., description="Inferred pandas/DuckDB data type")
    null_count: int = Field(..., description="Number of null/missing values in column")
    sample_values: List[Any] = Field(default_factory=list, description="Non-sensitive sample values")


class DatasetMetadata(BaseModel):
    dataset_id: str = Field(..., description="Unique UUID identifier for this dataset")
    table_name: str = Field(..., description="Sanitized DuckDB table name")
    filename: str = Field(..., description="Original filename uploaded")
    file_size_bytes: int = Field(..., description="File size in bytes")
    row_count: int = Field(..., description="Total number of rows in dataset")
    column_count: int = Field(..., description="Total number of columns")
    columns: List[ColumnSchema] = Field(..., description="List of column schemas")
    preview_rows: List[Dict[str, Any]] = Field(default_factory=list, description="Top preview rows (e.g. 5-10 rows)")
    upload_timestamp: str = Field(..., description="ISO formatted upload timestamp")


class UploadResponse(BaseModel):
    success: bool
    message: str
    dataset: DatasetMetadata

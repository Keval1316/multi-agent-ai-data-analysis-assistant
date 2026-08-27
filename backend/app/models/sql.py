from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GeneratedSQLQuery(BaseModel):
    name: str = Field(..., description="Query identifier (snake_case)")
    purpose: str = Field(..., description="Specific business or analytical question this SQL answers")
    sql: str = Field(..., description="DuckDB SQL statement (SELECT / WITH CTE only)")
    expected_columns: List[str] = Field(default_factory=list, description="Expected column aliases in output")


class SQLGenerationResponse(BaseModel):
    queries: List[GeneratedSQLQuery] = Field(..., min_length=1, description="List of generated safe analytical SQL queries")


class SQLExecutionResult(BaseModel):
    query_name: str
    purpose: str
    sql: str
    is_safe: bool
    validation_error: Optional[str] = None
    execution_status: str = Field("pending", description="'success', 'failed', 'rejected'")
    row_count: int = 0
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    execution_duration_ms: float = 0.0
    error_message: Optional[str] = None


class SQLAnalysisResult(BaseModel):
    dataset_id: str
    table_name: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    results: List[SQLExecutionResult]

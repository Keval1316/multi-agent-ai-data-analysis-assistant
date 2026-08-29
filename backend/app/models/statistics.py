from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class UnivariateMetric(BaseModel):
    column_name: str
    count: int
    mean: float
    median: float
    std: float
    variance: float
    min: float
    max: float
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    iqr: float
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    distribution_symmetry: Optional[str] = Field(None, description="Plain-English description of distribution symmetry/skewness")
    plain_english_summary: Optional[str] = Field(None, description="Plain-English explanation of mean vs median and spread")


class CorrelationPairResult(BaseModel):
    col1: str
    col2: str
    pearson_coef: float
    pearson_pvalue: Optional[float] = None
    spearman_coef: float
    spearman_pvalue: Optional[float] = None
    direction: str = Field("Positive", description="'Positive', 'Negative', or 'None'")
    strength: str = Field(..., description="'Negligible', 'Weak', 'Moderate', 'Strong', 'Very Strong'")
    practical_significance: str = Field(..., description="Assessment of practical effect size (e.g. 'Negligible practical effect', 'Weak practical effect')")
    is_statistically_significant: bool = False
    plain_english_interpretation: Optional[str] = Field(None, description="Plain-English interpretation evaluating statistical vs practical significance and causality warning")


class GroupBySummaryItem(BaseModel):
    group_value: str
    count: int
    sum: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    share_percentage: Optional[float] = None


class GroupByResult(BaseModel):
    group_column: str
    metric_column: str
    aggregation: str
    items: List[GroupBySummaryItem]
    f_statistic: Optional[float] = None
    anova_pvalue: Optional[float] = None
    is_group_difference_significant: Optional[bool] = None


class StatisticalAnalysisResult(BaseModel):
    dataset_id: str
    univariate_metrics: List[UnivariateMetric]
    correlation_results: List[CorrelationPairResult]
    groupby_results: List[GroupByResult]
    methodology_notes: List[str]

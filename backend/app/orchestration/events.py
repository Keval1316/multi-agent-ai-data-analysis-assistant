import json
import math
from datetime import datetime, timezone
from typing import Any, Dict


def clean_nan_and_inf(obj: Any) -> Any:
    """Recursively replaces NaN, Infinity, and -Infinity values with None for standard JSON compatibility."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_nan_and_inf(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_and_inf(v) for v in obj]
    elif isinstance(obj, tuple):
        return [clean_nan_and_inf(v) for v in obj]
    return obj


STEP_METADATA: Dict[str, Dict[str, Any]] = {
    "validate_file": {"index": 1, "label": "Validating File Structure & Encoding", "agent": "FileValidator"},
    "load_dataset": {"index": 2, "label": "Ingesting Raw Data & Registering Tables", "agent": "DatasetLoader"},
    "profile_and_audit": {"index": 3, "label": "Profiling Schema & Auditing Quality", "agent": "QualityChecker"},
    "clean_and_standardize": {"index": 4, "label": "Sanitizing, Imputing & Standardizing Dataset", "agent": "DataCleaner"},
    "understand_dataset": {"index": 5, "label": "Synthesizing Domain, Entity & Analytical Intent", "agent": "DatasetUnderstandingAgent"},
    "plan_analysis": {"index": 6, "label": "Formulating Adaptive Execution Plan", "agent": "AnalysisPlanningAgent"},
    "run_statistical_analysis": {"index": 7, "label": "Computing Distributions, Moments & Correlations", "agent": "StatisticalEngine"},
    "generate_sql": {"index": 8, "label": "Synthesizing Analytical DuckDB SQL Queries", "agent": "SQLGenerationAgent"},
    "validate_sql": {"index": 9, "label": "Verifying SQL AST Security & Syntax", "agent": "SQLValidator"},
    "execute_sql": {"index": 10, "label": "Executing In-Memory DuckDB Aggregations", "agent": "SQLExecutor"},
    "detect_patterns": {"index": 11, "label": "Discovering Trends, Pareto Shares & Outliers", "agent": "PatternDetector"},
    "render_charts": {"index": 12, "label": "Compiling Domain-Adaptive Plotly Visuals", "agent": "ChartGenerator"},
    "generate_insights": {"index": 13, "label": "Extracting Strict 4-Part Evidence Insights", "agent": "InsightGenerationAgent"},
    "critic_review": {"index": 14, "label": "Adversarial Fact-Checking & Ground-Truth Audit", "agent": "CriticReviewAgent"},
    "revise_insights": {"index": 15, "label": "Refining Findings & Correcting Weak Claims", "agent": "InsightRevisionOrchestrator"},
    "generate_report": {"index": 16, "label": "Compiling Comprehensive Executive Report", "agent": "ReportGenerationAgent"},
    "render_pdf": {"index": 17, "label": "Rendering Executive PDF Document & Caching", "agent": "PDFExporter"},
}

TOTAL_PIPELINE_STEPS = 17


def format_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """Formats payload as a standard Server-Sent Event (SSE) string with strict standard JSON."""
    sanitized_data = clean_nan_and_inf(data)
    payload = {
        **sanitized_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return f"event: {event_type}\ndata: {json.dumps(payload, default=str)}\n\n"

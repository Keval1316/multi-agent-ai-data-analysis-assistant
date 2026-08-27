import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional


STEP_METADATA: Dict[str, Dict[str, Any]] = {
    "validate_file": {"index": 1, "label": "Validating File Structure", "agent": "FileValidator"},
    "load_dataset": {"index": 2, "label": "Ingesting & Sanitizing Table", "agent": "DatasetLoader"},
    "profile_and_audit": {"index": 3, "label": "Profiling Schema & Auditing Quality", "agent": "QualityChecker"},
    "understand_dataset": {"index": 4, "label": "Synthesizing Domain & Key KPIs", "agent": "DatasetUnderstandingAgent"},
    "plan_analysis": {"index": 5, "label": "Formulating Execution Analysis Plan", "agent": "AnalysisPlanningAgent"},
    "run_statistical_analysis": {"index": 6, "label": "Computing Distributions & Correlations", "agent": "StatisticalEngine"},
    "generate_sql": {"index": 7, "label": "Synthesizing Analytical DuckDB SQL", "agent": "SQLGenerationAgent"},
    "validate_sql": {"index": 8, "label": "Verifying SQL Syntax & Security Guards", "agent": "SQLValidator"},
    "execute_sql": {"index": 9, "label": "Executing Queries in In-Memory DuckDB", "agent": "SQLExecutor"},
    "detect_patterns": {"index": 10, "label": "Discovering Trends, Pareto & Anomalies", "agent": "PatternDetector"},
    "select_visualizations": {"index": 11, "label": "Selecting Optimal Chart Heuristics", "agent": "ChartGenerator"},
    "render_charts": {"index": 12, "label": "Compiling Interactive Plotly Visuals", "agent": "ChartGenerator"},
    "generate_insights": {"index": 13, "label": "Deriving Evidence-Grounded Insights", "agent": "InsightGenerationAgent"},
    "critic_review": {"index": 14, "label": "Adversarial Fact-Checking & Auditing", "agent": "CriticReviewAgent"},
    "revise_insights": {"index": 15, "label": "Refining & Correcting Findings", "agent": "InsightRevisionOrchestrator"},
    "generate_report": {"index": 16, "label": "Compiling Executive Markdown Report", "agent": "ReportGenerationAgent"},
    "render_pdf": {"index": 17, "label": "Rendering Downloadable PDF Document", "agent": "PDFExporter"},
}

TOTAL_PIPELINE_STEPS = 17


def format_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """Formats payload as a standard Server-Sent Event (SSE) string."""
    payload = {
        **data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"

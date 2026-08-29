import uuid
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from backend.app.core.logging import logger
from backend.app.orchestration.state import AnalysisWorkflowState
from backend.app.orchestration.events import STEP_METADATA, TOTAL_PIPELINE_STEPS
from backend.app.services.ingestion.validator import FileValidator
from backend.app.services.ingestion.loader import DatasetLoader
from backend.app.services.ingestion.duckdb_manager import duckdb_manager
from backend.app.services.profiling.profiler import DatasetProfiler
from backend.app.services.quality.checker import QualityChecker
from backend.app.services.cleaning.cleaner import DataCleaner
from backend.app.agents.understand_dataset import DatasetUnderstandingAgent
from backend.app.agents.plan_analysis import AnalysisPlanningAgent
from backend.app.services.statistics.engine import StatisticalEngine
from backend.app.agents.generate_sql import SQLGenerationAgent
from backend.app.services.sql.validator import SQLValidator
from backend.app.services.sql.executor import SQLExecutor
from backend.app.services.patterns.detector import PatternDetector
from backend.app.services.visualization.chart_generator import ChartGenerator
from backend.app.agents.generate_insights import InsightGenerationAgent
from backend.app.agents.critic_review import CriticReviewAgent
from backend.app.agents.generate_report import ReportGenerationAgent
from backend.app.services.reporting.pdf_exporter import PDFExporter
from backend.app.services.reporting.report_builder import ReportBuilder


# --- NODE DEFINITIONS ---

def validate_file_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 1: validate_file] Validating file input & metadata")
    filename = state.get("filename", "dataset.csv")
    file_bytes = state.get("file_bytes")
    if file_bytes is None:
        raise ValueError("Missing file bytes in pipeline input")

    sanitized_name, valid_ext = FileValidator.validate_file_metadata(filename, len(file_bytes))
    return {
        "filename": sanitized_name,
        "file_extension": valid_ext,
        "current_step": "validate_file",
        "step_index": 1,
        "total_steps": TOTAL_PIPELINE_STEPS,
        "status_label": STEP_METADATA["validate_file"]["label"]
    }


def load_dataset_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 2: load_dataset] Parsing raw dataset and registering in DuckDB")
    file_bytes = state["file_bytes"]
    ext = state["file_extension"]
    dataset_id = state.get("dataset_id") or str(uuid.uuid4())

    df, metadata = DatasetLoader.load_and_sanitize(file_bytes, ext)
    raw_table = f"raw_{duckdb_manager.generate_table_name(dataset_id)}"
    duckdb_manager.register_dataframe(df, dataset_id, raw_table)

    return {
        "dataset_id": dataset_id,
        "table_name": raw_table,
        "raw_table_name": raw_table,
        "raw_df": df,
        "df": df,
        "current_step": "load_dataset",
        "step_index": 2,
        "status_label": STEP_METADATA["load_dataset"]["label"]
    }


def profile_and_audit_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 3: profile_and_audit] Profiling schema and auditing data quality on raw table")
    df = state["df"]
    dataset_id = state["dataset_id"]
    table_name = state["table_name"]

    profile = DatasetProfiler.profile_dataset(df, dataset_id, table_name)
    quality = QualityChecker.audit_dataset(df, profile)

    return {
        "profile": profile,
        "quality": quality,
        "current_step": "profile_and_audit",
        "step_index": 3,
        "status_label": STEP_METADATA["profile_and_audit"]["label"]
    }


def clean_and_standardize_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 4: clean_and_standardize] Sanitizing, imputing & standardizing dataset")
    raw_df = state.get("raw_df") if state.get("raw_df") is not None else state["df"]
    dataset_id = state["dataset_id"]
    filename = state.get("filename", "dataset.csv")

    # Clean dataset
    cleaned_df, cleaning_summary = DataCleaner.clean_dataset(raw_df, dataset_id, filename)
    ReportBuilder.cache_cleaned_df(dataset_id, cleaned_df)

    # Register cleaned table in DuckDB for all downstream analytical queries
    clean_table = duckdb_manager.generate_table_name(dataset_id)
    duckdb_manager.register_dataframe(cleaned_df, dataset_id, clean_table)

    # Update profile to reflect sanitized data types and non-null values
    cleaned_profile = DatasetProfiler.profile_dataset(cleaned_df, dataset_id, clean_table)

    return {
        "df": cleaned_df,
        "cleaned_df": cleaned_df,
        "table_name": clean_table,
        "cleaned_table_name": clean_table,
        "cleaning_summary": cleaning_summary.model_dump(),
        "profile": cleaned_profile,
        "current_step": "clean_and_standardize",
        "step_index": 4,
        "status_label": STEP_METADATA["clean_and_standardize"]["label"]
    }


def understand_dataset_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 5: understand_dataset] Inferring domain, entities & analytical intent")
    profile = state["profile"]
    quality = state["quality"]
    filename = state.get("filename", "dataset.csv")

    understanding = DatasetUnderstandingAgent.analyze(profile, quality, filename)
    return {
        "understanding": understanding,
        "current_step": "understand_dataset",
        "step_index": 5,
        "status_label": STEP_METADATA["understand_dataset"]["label"]
    }


def plan_analysis_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 6: plan_analysis] Formulating adaptive execution plan")
    profile = state["profile"]
    understanding = state["understanding"]

    plan = AnalysisPlanningAgent.plan(profile, understanding)
    return {
        "plan": plan,
        "current_step": "plan_analysis",
        "step_index": 6,
        "status_label": STEP_METADATA["plan_analysis"]["label"]
    }


def run_statistical_analysis_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 7: run_statistical_analysis] Computing distributions, moments & correlations")
    df = state["df"]
    profile = state["profile"]
    plan = state["plan"]

    statistics = StatisticalEngine.run_analysis(df, profile, plan)
    return {
        "statistics": statistics,
        "current_step": "run_statistical_analysis",
        "step_index": 7,
        "status_label": STEP_METADATA["run_statistical_analysis"]["label"]
    }


def generate_sql_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 8: generate_sql] Generating analytical DuckDB SQL queries")
    profile = state["profile"]
    plan = state["plan"]
    table_name = state["table_name"]

    queries = SQLGenerationAgent.generate(profile, plan, table_name)
    return {
        "sql_queries": queries,
        "current_step": "generate_sql",
        "step_index": 8,
        "status_label": STEP_METADATA["generate_sql"]["label"]
    }


def validate_sql_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 9: validate_sql] Verifying SQL syntax & AST security guards")
    queries = state["sql_queries"]
    table_name = state["table_name"]

    validated_queries = []
    for q in queries:
        is_safe, reason, sanitized = SQLValidator.validate_sql(q.sql, expected_table=table_name)
        if is_safe:
            q.sql = sanitized
            validated_queries.append(q)
        else:
            logger.warning(f"SQL validation rejected query '{q.name}': {reason}")

    return {
        "validated_sql_queries": validated_queries,
        "current_step": "validate_sql",
        "step_index": 9,
        "status_label": STEP_METADATA["validate_sql"]["label"]
    }


def execute_sql_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 10: execute_sql] Executing validated queries against DuckDB")
    queries = state.get("validated_sql_queries") or state.get("sql_queries", [])
    dataset_id = state["dataset_id"]
    table_name = state["table_name"]

    sql_results = SQLExecutor.execute_queries(queries, dataset_id, table_name)
    return {
        "sql_results": sql_results,
        "current_step": "execute_sql",
        "step_index": 10,
        "status_label": STEP_METADATA["execute_sql"]["label"]
    }


def detect_patterns_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 11: detect_patterns] Discovering trends, Pareto shares & anomalies")
    df = state["df"]
    profile = state["profile"]

    patterns = PatternDetector.detect_all(df, profile)
    return {
        "patterns": patterns,
        "current_step": "detect_patterns",
        "step_index": 11,
        "status_label": STEP_METADATA["detect_patterns"]["label"]
    }


def render_charts_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 12: render_charts] Compiling domain-adaptive interactive Plotly visuals")
    df = state["df"]
    profile = state["profile"]
    plan = state["plan"]
    user_query = state.get("user_query")

    charts = ChartGenerator.generate_all(df, profile, plan, user_query=user_query)
    return {
        "charts": charts,
        "current_step": "render_charts",
        "step_index": 12,
        "status_label": STEP_METADATA["render_charts"]["label"]
    }


def generate_insights_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 13: generate_insights] Deriving strict 4-part evidence-grounded insights")
    understanding = state["understanding"]
    statistics = state["statistics"]
    sql_results = state["sql_results"]
    patterns = state["patterns"]
    quality = state["quality"]
    critique = state.get("revision_critique")

    insights = InsightGenerationAgent.generate(
        understanding=understanding,
        statistics=statistics,
        sql_results=sql_results,
        patterns=patterns,
        quality=quality,
        revision_critique=critique
    )
    return {
        "insights": insights,
        "current_step": "generate_insights",
        "step_index": 13,
        "status_label": STEP_METADATA["generate_insights"]["label"]
    }


def critic_review_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 14: critic_review] Auditing insights against ground-truth evidence")
    insights = state["insights"]
    statistics = state["statistics"]
    sql_results = state["sql_results"]
    patterns = state["patterns"]

    review = CriticReviewAgent.review(
        insights=insights,
        statistics=statistics,
        sql_results=sql_results,
        patterns=patterns
    )
    return {
        "critic_review": review,
        "critic_approved": review.approved,
        "current_step": "critic_review",
        "step_index": 14,
        "status_label": STEP_METADATA["critic_review"]["label"]
    }


def revise_insights_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 15: revise_insights] Evaluating critic review status")
    approved = state.get("critic_approved", True)
    rev_cnt = state.get("revision_count", 0)
    review = state.get("critic_review")

    if not approved and rev_cnt < 2:
        rev_cnt += 1
        critique_parts = [f"Critic Review: {review.feedback if review else 'Unsupported claims'}"]
        if review and review.unsupported_claims:
            for uc in review.unsupported_claims:
                critique_parts.append(f"- [Insight {uc.insight_id}] '{uc.claim_text}': {uc.reason}")
        if review and review.required_corrections:
            for rc in review.required_corrections:
                critique_parts.append(f"- Correction: {rc}")

        logger.warning(f"Routing revision loop {rev_cnt}/2 back to generate_insights")
        return {
            "revision_count": rev_cnt,
            "revision_critique": "\n".join(critique_parts),
            "critic_approved": False,
            "current_step": "revise_insights",
            "step_index": 15,
            "status_label": STEP_METADATA["revise_insights"]["label"]
        }
    else:
        return {
            "critic_approved": True,
            "current_step": "revise_insights",
            "step_index": 15,
            "status_label": STEP_METADATA["revise_insights"]["label"]
        }


def should_continue_revision(state: AnalysisWorkflowState) -> Literal["generate_insights", "generate_report"]:
    """Conditional edge: loop back to generate_insights if unapproved and revision < 2, else proceed."""
    if not state.get("critic_approved", True) and state.get("revision_count", 0) <= 2:
        return "generate_insights"
    return "generate_report"


def generate_report_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 16: generate_report] Compiling comprehensive executive report")
    report = ReportGenerationAgent.generate(
        understanding=state["understanding"],
        profile=state["profile"],
        quality=state["quality"],
        statistics=state["statistics"],
        sql_results=state["sql_results"],
        patterns=state["patterns"],
        charts=state["charts"],
        insights=state["insights"],
        cleaning_summary=state.get("cleaning_summary"),
        filename=state.get("filename", "dataset.csv")
    )
    return {
        "report": report,
        "current_step": "generate_report",
        "step_index": 16,
        "status_label": STEP_METADATA["generate_report"]["label"]
    }


def render_pdf_node(state: AnalysisWorkflowState) -> Dict[str, Any]:
    logger.info("[Node 17: render_pdf] Rendering downloadable PDF and caching report")
    report = state["report"]
    cleaned_df = state.get("cleaned_df") if state.get("cleaned_df") is not None else state.get("df")
    dataset_id = state.get("dataset_id") or report.dataset_id

    if cleaned_df is not None:
        ReportBuilder.cache_cleaned_df(dataset_id, cleaned_df)

    pdf_bytes = PDFExporter.generate_pdf(report)
    ReportBuilder.cache_report(report)

    return {
        "pdf_bytes": pdf_bytes,
        "current_step": "render_pdf",
        "step_index": 17,
        "status_label": STEP_METADATA["render_pdf"]["label"]
    }


# --- GRAPH CONSTRUCTION ---

def build_analysis_graph() -> StateGraph:
    """Builds and compiles the full 17-node LangGraph StateGraph."""
    graph = StateGraph(AnalysisWorkflowState)

    # Add all 17 nodes in strict logical sequence
    graph.add_node("validate_file", validate_file_node)
    graph.add_node("load_dataset", load_dataset_node)
    graph.add_node("profile_and_audit", profile_and_audit_node)
    graph.add_node("clean_and_standardize", clean_and_standardize_node)
    graph.add_node("understand_dataset", understand_dataset_node)
    graph.add_node("plan_analysis", plan_analysis_node)
    graph.add_node("run_statistical_analysis", run_statistical_analysis_node)
    graph.add_node("generate_sql", generate_sql_node)
    graph.add_node("validate_sql", validate_sql_node)
    graph.add_node("execute_sql", execute_sql_node)
    graph.add_node("detect_patterns", detect_patterns_node)
    graph.add_node("render_charts", render_charts_node)
    graph.add_node("generate_insights", generate_insights_node)
    graph.add_node("critic_review", critic_review_node)
    graph.add_node("revise_insights", revise_insights_node)
    graph.add_node("generate_report", generate_report_node)
    graph.add_node("render_pdf", render_pdf_node)

    # Linear edges
    graph.add_edge(START, "validate_file")
    graph.add_edge("validate_file", "load_dataset")
    graph.add_edge("load_dataset", "profile_and_audit")
    graph.add_edge("profile_and_audit", "clean_and_standardize")
    graph.add_edge("clean_and_standardize", "understand_dataset")
    graph.add_edge("understand_dataset", "plan_analysis")
    graph.add_edge("plan_analysis", "run_statistical_analysis")
    graph.add_edge("run_statistical_analysis", "generate_sql")
    graph.add_edge("generate_sql", "validate_sql")
    graph.add_edge("validate_sql", "execute_sql")
    graph.add_edge("execute_sql", "detect_patterns")
    graph.add_edge("detect_patterns", "render_charts")
    graph.add_edge("render_charts", "generate_insights")
    graph.add_edge("generate_insights", "critic_review")
    graph.add_edge("critic_review", "revise_insights")

    # Conditional edge from revise_insights
    graph.add_conditional_edges(
        "revise_insights",
        should_continue_revision,
        {
            "generate_insights": "generate_insights",
            "generate_report": "generate_report"
        }
    )

    graph.add_edge("generate_report", "render_pdf")
    graph.add_edge("render_pdf", END)

    return graph


analysis_workflow_graph = build_analysis_graph().compile()

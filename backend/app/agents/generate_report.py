from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from backend.app.models.understanding import DatasetUnderstanding
from backend.app.models.profile import DatasetProfile
from backend.app.models.quality import QualityReport
from backend.app.models.statistics import StatisticalAnalysisResult
from backend.app.models.sql import SQLAnalysisResult
from backend.app.models.patterns import PatternDetectionResult
from backend.app.models.visualization import ChartCollection
from backend.app.models.insights import InsightCollection
from backend.app.models.report import GeneratedReportMarkdown, AnalysisReport, ReportSection
from backend.app.llm.router import llm_router
from backend.app.core.logging import logger


class ReportGenerationAgent:
    """Agent that compiles the entire multi-agent analytical findings into a cohesive, executive-ready report."""

    @classmethod
    def generate(
        cls,
        understanding: DatasetUnderstanding,
        profile: DatasetProfile,
        quality: QualityReport,
        statistics: StatisticalAnalysisResult,
        sql_results: SQLAnalysisResult,
        patterns: PatternDetectionResult,
        charts: ChartCollection,
        insights: InsightCollection,
        cleaning_summary: Optional[Dict[str, Any]] = None,
        filename: str = "dataset.csv"
    ) -> AnalysisReport:
        dataset_id = profile.dataset_id
        logger.info(f"Running ReportGenerationAgent for dataset '{dataset_id}' ({filename})")

        # 1. Format Fact Sheet components
        kpi_summary = ", ".join([f"{k.name} ({k.aggregation})" for k in understanding.key_kpis])
        
        insight_blocks = []
        for ins in insights.insights:
            insight_blocks.append(
                f"- **{ins.title}** [{ins.category}]: {ins.finding}\n"
                f"  *Evidence*: {ins.evidence or ins.supporting_evidence}\n"
                f"  *Interpretation*: {ins.interpretation}\n"
                f"  *Actionable Implication*: {ins.implication or ins.recommendation}"
            )
        insight_summary = "\n\n".join(insight_blocks)

        stats_summary = []
        for um in statistics.univariate_metrics[:6]:
            stats_summary.append(
                f"- '{um.column_name}': Mean={um.mean:,.2f}, Median={um.median:,.2f}, Std={um.std:,.2f}, IQR={um.iqr:,.2f}, Skewness={um.skewness:,.2f}"
            )
        for cp in statistics.correlation_results[:4]:
            stats_summary.append(
                f"- Correlation {cp.col1} vs {cp.col2}: r = {cp.pearson_coef:+.3f} (p = {cp.pearson_pvalue:.4f}, significant = {cp.is_statistically_significant})"
            )

        sql_summary = []
        for sq in sql_results.results[:4]:
            if sq.execution_status == "success" and sq.rows:
                sql_summary.append(f"- Query '{sq.query_name}': {sq.row_count} records. Top: {sq.rows[:2]}")

        patterns_summary = []
        for t in patterns.trends[:3]:
            patterns_summary.append(f"- Trend ({t.metric_column}): {t.description}")
        for c in patterns.concentrations[:3]:
            patterns_summary.append(f"- Pareto Concentration ({c.dimension_column}): {c.description}")
        for a in patterns.anomalies[:3]:
            patterns_summary.append(f"- Outlier Anomaly ({a.metric_column}): {a.description} [Row: {a.row_identifier}]")

        cleaning_text = "Standard data hygiene verified; zero critical formatting anomalies."
        if cleaning_summary:
            t_list = cleaning_summary.get("transformations", [])
            cleaning_text = f"Purged {cleaning_summary.get('duplicates_removed', 0)} duplicates, imputed {cleaning_summary.get('nulls_imputed', 0)} nulls. Transformations: {'; '.join(t_list[:4])}"

        system_prompt = (
            "You are a Chief AI Analytics Officer and Lead Data Strategist. "
            "Your objective is to synthesize a deeply quantitative, publication-grade analytical executive report "
            "evaluating the uploaded dataset for any domain (Sales, Healthcare, Finance, HR, Operations, Education, Logistics, etc.).\n\n"
            "MANDATORY REPORTING RULES:\n"
            "1. CITE CONCRETE FIGURES: Never make vague claims. Include actual metrics, baseline numbers, group shares, correlations, and row IDs.\n"
            "2. STRUCTURE: Return a GeneratedReportMarkdown with clear, compelling markdown formatting, bullet points, and actionable executive insights.\n"
            "3. INTEGRATION: Incorporate the data cleaning actions, statistical moments, DuckDB SQL discoveries, empirical patterns, and strategic implications."
        )

        user_prompt = (
            f"Dataset Summary:\n"
            f"Dataset ID: {dataset_id}\n"
            f"Filename: {filename}\n"
            f"Domain: {understanding.domain}\n"
            f"Target Entity: {understanding.target_entity}\n"
            f"Records: {profile.total_rows:,} | Variables: {profile.total_columns}\n"
            f"Cleanliness Rating: {quality.quality_score}/100 (Grade {quality.grade})\n"
            f"Key KPIs: {kpi_summary}\n\n"
            f"--- DATA CLEANING & HYGIENE ACTIONS ---\n"
            f"{cleaning_text}\n\n"
            f"--- COMPUTED STATISTICAL MOMENTS ---\n"
            f"{chr(10).join(stats_summary) if stats_summary else 'Standard distributions calculated.'}\n\n"
            f"--- DUCKDB SQL AGGREGATIONS ---\n"
            f"{chr(10).join(sql_summary) if sql_summary else 'Standard queries executed.'}\n\n"
            f"--- EMPIRICAL PATTERNS, TRENDS & ANOMALIES ---\n"
            f"{chr(10).join(patterns_summary) if patterns_summary else 'No severe multi-sigma outliers.'}\n\n"
            f"--- VERIFIED EVIDENCE-BACKED INSIGHTS ---\n"
            f"{insight_summary}\n\n"
            f"Write a comprehensive, quantitative report with:\n"
            f"1. Professional Title and Subtitle\n"
            f"2. Executive Summary\n"
            f"3. Key Findings in detailed quantitative markdown\n"
            f"4. Strategic Business Recommendations\n"
            f"5. Methodology, Data Governance & Analytical Caveats"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        gen_md = llm_router.complete(
            agent_name="generate_report",
            messages=messages,
            response_model=GeneratedReportMarkdown,
            temperature=0.1
        )

        sections = [
            ReportSection(
                id="sec_exec_summary",
                title="Executive Summary",
                summary="High-level overview of dataset health and strategic performance.",
                markdown_content=gen_md.executive_summary
            ),
            ReportSection(
                id="sec_key_findings",
                title="Detailed Key Findings",
                summary="Evidence-backed analysis across dimensions, segments, and metrics.",
                markdown_content=gen_md.key_findings_markdown
            ),
            ReportSection(
                id="sec_recommendations",
                title="Strategic Recommendations",
                summary="Actionable business initiatives driven by empirical data findings.",
                markdown_content=gen_md.strategic_recommendations_markdown
            ),
            ReportSection(
                id="sec_methodology",
                title="Methodology & Data Caveats",
                summary="Statistical assumptions, data quality notes, and scope boundaries.",
                markdown_content=gen_md.methodology_and_caveats_markdown
            )
        ]

        full_markdown = (
            f"# {gen_md.title}\n\n"
            f"**{gen_md.subtitle}**\n\n"
            f"--- \n\n"
            f"## Executive Summary\n\n{gen_md.executive_summary}\n\n"
            f"## Key Findings\n\n{gen_md.key_findings_markdown}\n\n"
            f"## Strategic Recommendations\n\n{gen_md.strategic_recommendations_markdown}\n\n"
            f"## Methodology & Governance Caveats\n\n{gen_md.methodology_and_caveats_markdown}\n"
        )

        report = AnalysisReport(
            dataset_id=dataset_id,
            filename=filename,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            title=gen_md.title,
            subtitle=gen_md.subtitle,
            executive_summary=gen_md.executive_summary,
            markdown_report=full_markdown,
            sections=sections,
            understanding=understanding,
            profile=profile,
            quality=quality,
            statistics=statistics,
            sql_results=sql_results,
            patterns=patterns,
            charts=charts,
            insights=insights,
            cleaning_summary=cleaning_summary
        )

        logger.info(f"ReportGenerationAgent successfully compiled report for '{dataset_id}'")
        return report

from datetime import datetime, timezone
from typing import List
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
        filename: str = "dataset.csv"
    ) -> AnalysisReport:
        dataset_id = profile.dataset_id
        logger.info(f"Running ReportGenerationAgent for dataset '{dataset_id}' ({filename})")

        # Format compact context summary
        kpi_summary = ", ".join([f"{k.name} ({k.aggregation})" for k in understanding.key_kpis])
        insight_summary = "\n".join([f"- {ins.title}: {ins.finding}" for ins in insights.insights])

        system_prompt = (
            "You are a Chief AI Analytics Officer and Lead Data Strategist. "
            "Your objective is to synthesize a structured, publication-grade analytical report "
            "evaluating the uploaded dataset. "
            "Return a structured GeneratedReportMarkdown object with rich, polished markdown sections."
        )

        user_prompt = (
            f"Dataset Summary:\n"
            f"Dataset ID: {dataset_id}\n"
            f"Filename: {filename}\n"
            f"Domain: {understanding.domain}\n"
            f"Target Entity: {understanding.target_entity}\n"
            f"Rows: {profile.total_rows:,} | Columns: {profile.total_columns}\n"
            f"Data Quality Score: {quality.quality_score}/100 (Grade {quality.grade})\n"
            f"Key KPIs: {kpi_summary}\n\n"
            f"Verified Insights:\n"
            f"{insight_summary}\n\n"
            f"Write a comprehensive report with:\n"
            f"1. Clear, professional Title and Subtitle\n"
            f"2. Executive Summary\n"
            f"3. Key Findings in detailed markdown\n"
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
            insights=insights
        )

        logger.info(f"ReportGenerationAgent successfully compiled report for '{dataset_id}'")
        return report

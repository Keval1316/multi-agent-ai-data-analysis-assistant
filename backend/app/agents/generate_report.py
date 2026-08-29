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
    """Agent that compiles the multi-agent analytical findings into a statistically responsible 13-section report."""

    @classmethod
    def build_quality_breakdown_table(
        cls,
        profile: DatasetProfile,
        quality: QualityReport,
        cleaning_summary: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Constructs a transparent, compact breakdown table explaining how the quality score was determined."""
        dup_count = profile.duplicate_rows_count
        null_count = sum(cp.null_count for cp in profile.column_profiles)
        
        # Calculate invalid/out-of-range counts from quality issues or cleaning summary
        invalid_count = 0
        cat_norm_status = "Not required"
        supp_norm_status = "Not required"
        imputed_count = 0

        if cleaning_summary:
            invalid_count = cleaning_summary.get("out_of_range_corrected", 0)
            imputed_count = cleaning_summary.get("nulls_imputed", 0)
            t_list = cleaning_summary.get("transformations", [])
            for t in t_list:
                if "category" in t.lower() or "casing" in t.lower():
                    cat_norm_status = "Completed"
                if "supplier" in t.lower():
                    supp_norm_status = "Completed"

        # Check issues for invalid/inconsistent labels if cleaning summary absent
        for issue in quality.issues:
            if issue.category == "invalid_values":
                invalid_count += issue.affected_count
            elif issue.category == "inconsistent_labels":
                cat_norm_status = "Detected & Reconciled"

        breakdown = [
            {"check": "Duplicate records", "result": str(dup_count), "status": "Clean" if dup_count == 0 else f"{dup_count} removed"},
            {"check": "Missing values", "result": str(null_count), "status": f"{imputed_count} imputed (median/mode)" if imputed_count > 0 else ("0 missing" if null_count == 0 else f"{null_count} observed")},
            {"check": "Invalid / out-of-range values", "result": str(invalid_count), "status": "Resolved" if invalid_count > 0 else "None detected"},
            {"check": "Category normalization", "result": cat_norm_status, "status": "Standardized"},
            {"check": "Supplier / Entity normalization", "result": supp_norm_status, "status": "Standardized"},
            {"check": "Overall quality score", "result": f"{quality.quality_score}/100", "status": f"Grade {quality.grade}"}
        ]
        return breakdown

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

        # 1. Build Quality Breakdown Table
        quality_breakdown = cls.build_quality_breakdown_table(profile, quality, cleaning_summary)
        quality_table_md = "| Check | Result | Status |\n| :--- | :--- | :--- |\n"
        for row in quality_breakdown:
            quality_table_md += f"| {row['check']} | {row['result']} | {row['status']} |\n"

        # 2. Format Statistical Moments and Distributions
        stats_summary = []
        for um in statistics.univariate_metrics:
            symm = um.distribution_symmetry or "Symmetry undetermined"
            plain = um.plain_english_summary or ""
            stats_summary.append(
                f"- **{um.column_name}**: Count={um.count}, Mean={um.mean:,.2f}, Median={um.median:,.2f}, Min={um.min:,.2f}, Max={um.max:,.2f}, Std Dev={um.std:,.2f}, IQR={um.iqr:,.2f}, Skewness={um.skewness} ({symm}). Meaning: {plain}"
            )

        # 3. Format Relationships / Correlations
        corr_summary = []
        for cp in statistics.correlation_results:
            sig_str = "Statistically Significant (p < 0.05)" if cp.is_statistically_significant else f"Not Statistically Significant (p = {cp.pearson_pvalue})"
            interp_str = cp.plain_english_interpretation or ""
            corr_summary.append(
                f"- **{cp.col1} vs {cp.col2}**: Pearson r = {cp.pearson_coef:+.3f} (p = {cp.pearson_pvalue}). Direction: {cp.direction}. Strength: {cp.strength}. Significance: {sig_str}. Practical Effect: {cp.practical_significance}. Plain-English: {interp_str}"
            )

        # 4. Format SQL Queries and Mismatch Warnings
        sql_summary = []
        query_warnings = []
        for sq in sql_results.results:
            if sq.execution_status == "success" and sq.rows:
                top_rows = str(sq.rows[:2])
                warn_txt = ""
                if sq.query_validation_warning:
                    warn_txt = f"\n  *Query Validation Warning*: {sq.query_validation_warning}"
                    query_warnings.append(f"Query '{sq.query_name}': {sq.query_validation_warning}")
                sql_summary.append(f"- **Query '{sq.query_name}'** ({sq.purpose}): {sq.row_count} rows returned. Top: {top_rows}{warn_txt}")

        # 5. Format Patterns (Trends, Concentrations, Anomalies)
        patterns_summary = []
        for t in patterns.trends:
            patterns_summary.append(f"- **Trend ({t.metric_column})**: {t.description}")
        for c in patterns.concentrations:
            patterns_summary.append(f"- **{c.pattern_label} ({c.dimension_column})**: {c.description}")
        for a in patterns.anomalies:
            patterns_summary.append(f"- **Anomaly ({a.metric_column})**: {a.description} [Row: {a.row_identifier}, Severity: {a.severity}]")

        # 6. Format Verified Insights
        insight_blocks = []
        for ins in insights.insights:
            insight_blocks.append(
                f"### {ins.title}\n"
                f"- **Finding**: {ins.finding}\n"
                f"- **Evidence**: {ins.evidence or ins.supporting_evidence}\n"
                f"- **What This Means**: {ins.what_this_means or ins.interpretation}\n"
                f"- **Business Implication**: {ins.interpretation}\n"
                f"- **Recommended Action**: {ins.implication or ins.recommendation}\n"
                f"- **Confidence**: {ins.confidence} ({ins.confidence_rationale or 'Grounded in observed data'})\n"
            )
        insight_summary = "\n\n".join(insight_blocks)

        system_prompt = (
            "You are a Senior Quantitative AI Data Analyst and Business Intelligence Officer.\n"
            "Your objective is to generate a comprehensive, highly accurate, evidence-based 13-section data analysis report.\n\n"
            "MANDATORY REPORTING GUIDELINES:\n"
            "1. REASONING ORDER: Data → Analysis → Finding → Evidence → Interpretation → Business Impact → Recommendation → Confidence.\n"
            "2. NEVER CONFUSE HIGH STOCK WITH HIGH PERFORMANCE: Without sales/revenue/turnover data, never describe high stock as 'high-performing', 'profitable', or 'successful'. Use 'inventory concentration' or 'high-stock category'.\n"
            "3. CORRELATION != CAUSATION: Always emphasize that correlation does not establish causation. Distinguish statistical significance from practical effect size (e.g. r=0.15 is weak and not a strong pricing signal).\n"
            "4. ACCURATE SKEWNESS & DISTRIBUTIONS: Never claim 'high values pull average upward' if mean < median. Use the calculated skewness.\n"
            "5. SUPPLIER ANALYSIS: Evaluate supplier inventory contribution, NOT supplier performance (mention that delivery/defect/fulfillment data is absent).\n"
            "6. TREND INTERPRETATION: If R² ≈ 0 or p >= 0.05, state that no meaningful time-based trend was detected. Do not cite raw endpoint percentage differences as confirmed growth.\n"
            "7. PLAIN ENGLISH & TWO-LAYER EXPLANATIONS: Provide both technical statistics and simple 'What this means' explanations.\n"
            "8. PRUDENT RECOMMENDATIONS: Use prudent verbs ('investigate', 'review', 'monitor', 'validate') and avoid overly aggressive directives ('immediately change pricing').\n"
            "9. NO HALLUCINATIONS: If data is insufficient for a business conclusion, state 'The available data is insufficient to determine this.'\n"
            "10. Return a structured GeneratedReportMarkdown covering all 13 canonical sections."
        )

        user_prompt = (
            f"Dataset Context:\n"
            f"Dataset ID: {dataset_id}\n"
            f"Filename: {filename}\n"
            f"Domain: {understanding.domain}\n"
            f"Target Entity: {understanding.target_entity}\n"
            f"Total Records: {profile.total_rows:,} | Total Columns: {profile.total_columns}\n"
            f"Data Cleanliness Score: {quality.quality_score}/100 (Grade {quality.grade})\n\n"
            f"--- DATA QUALITY BREAKDOWN TABLE ---\n"
            f"{quality_table_md}\n\n"
            f"--- COMPUTED STATISTICAL MOMENTS ---\n"
            f"{chr(10).join(stats_summary) if stats_summary else 'Standard distributions calculated.'}\n\n"
            f"--- BIVARIATE CORRELATION PAIRS ---\n"
            f"{chr(10).join(corr_summary) if corr_summary else 'No numeric correlation pairs evaluated.'}\n\n"
            f"--- DUCKDB SQL AGGREGATIONS & VALIDATION ---\n"
            f"{chr(10).join(sql_summary) if sql_summary else 'Standard queries executed.'}\n\n"
            f"--- EMPIRICAL PATTERNS, CONCENTRATIONS & ANOMALIES ---\n"
            f"{chr(10).join(patterns_summary) if patterns_summary else 'No multi-sigma outliers detected.'}\n\n"
            f"--- VERIFIED EVIDENCE-BACKED INSIGHTS ---\n"
            f"{insight_summary}\n\n"
            f"Generate a publication-grade, plain-English, technically accurate GeneratedReportMarkdown with all 13 canonical sections."
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

        # Build 13 Structured Sections
        sections = [
            ReportSection(
                id="sec_1_exec_summary",
                title="1. Executive Summary",
                summary="Overall dataset summary, key findings, main risks, and recommended next steps in plain English.",
                markdown_content=gen_md.executive_summary_markdown
            ),
            ReportSection(
                id="sec_2_dataset_overview",
                title="2. Dataset Overview",
                summary="High-level dimensions, entity definitions, and summary counts.",
                markdown_content=gen_md.dataset_overview_markdown
            ),
            ReportSection(
                id="sec_3_quality_validation",
                title="3. Data Quality & Validation",
                summary="Data hygiene score breakdown table, missing value treatments, and query validation warnings.",
                markdown_content=gen_md.data_quality_and_validation_markdown
            ),
            ReportSection(
                id="sec_4_key_findings",
                title="4. Key Findings",
                summary="Evidence-backed findings with two-layer explanations and confidence ratings.",
                markdown_content=gen_md.key_findings_markdown
            ),
            ReportSection(
                id="sec_5_distribution_analysis",
                title="5. Distribution Analysis",
                summary="Parametric moments, median benchmarks, spread (IQR), and skewness interpretations.",
                markdown_content=gen_md.distribution_analysis_markdown
            ),
            ReportSection(
                id="sec_6_category_analysis",
                title="6. Category Analysis",
                summary="Category inventory concentration and segment distributions.",
                markdown_content=gen_md.category_analysis_markdown
            ),
            ReportSection(
                id="sec_7_product_analysis",
                title="7. Product / Item Analysis",
                summary="Highest/lowest volume products, concentration, and item-level inventory risks.",
                markdown_content=gen_md.product_analysis_markdown
            ),
            ReportSection(
                id="sec_8_supplier_analysis",
                title="8. Supplier Analysis",
                summary="Supplier inventory contribution analysis with performance metric caveats.",
                markdown_content=gen_md.supplier_analysis_markdown
            ),
            ReportSection(
                id="sec_9_relationship_analysis",
                title="9. Relationship & Correlation Analysis",
                summary="Pearson correlations, direction, strength, statistical vs practical significance, and causality disclaimers.",
                markdown_content=gen_md.relationship_analysis_markdown
            ),
            ReportSection(
                id="sec_10_trend_analysis",
                title="10. Trend Analysis",
                summary="Regression trajectories, R² effect sizes, p-values, and plain-English interpretations.",
                markdown_content=gen_md.trend_analysis_markdown
            ),
            ReportSection(
                id="sec_11_recommendations",
                title="11. Recommendations",
                summary="Structured recommendations following Finding → Evidence → Business Implication → Action → Confidence.",
                markdown_content=gen_md.recommendations_markdown
            ),
            ReportSection(
                id="sec_12_limitations",
                title="12. Limitations",
                summary="Dataset-specific analytical boundaries and missing variable constraints.",
                markdown_content=gen_md.limitations_markdown
            ),
            ReportSection(
                id="sec_13_next_analysis",
                title="13. Suggested Next Analysis",
                summary="Recommended future analyses, required data integrations, and validation initiatives.",
                markdown_content=gen_md.suggested_next_analysis_markdown
            )
        ]

        full_markdown = (
            f"# {gen_md.title}\n\n"
            f"**{gen_md.subtitle}**\n\n"
            f"---\n\n"
            f"## 1. Executive Summary\n\n{gen_md.executive_summary_markdown}\n\n"
            f"## 2. Dataset Overview\n\n{gen_md.dataset_overview_markdown}\n\n"
            f"## 3. Data Quality & Validation\n\n{gen_md.data_quality_and_validation_markdown}\n\n"
            f"## 4. Key Findings\n\n{gen_md.key_findings_markdown}\n\n"
            f"## 5. Distribution Analysis\n\n{gen_md.distribution_analysis_markdown}\n\n"
            f"## 6. Category Analysis\n\n{gen_md.category_analysis_markdown}\n\n"
            f"## 7. Product Analysis\n\n{gen_md.product_analysis_markdown}\n\n"
            f"## 8. Supplier Analysis\n\n{gen_md.supplier_analysis_markdown}\n\n"
            f"## 9. Relationship Analysis\n\n{gen_md.relationship_analysis_markdown}\n\n"
            f"## 10. Trend Analysis\n\n{gen_md.trend_analysis_markdown}\n\n"
            f"## 11. Recommendations\n\n{gen_md.recommendations_markdown}\n\n"
            f"## 12. Limitations\n\n{gen_md.limitations_markdown}\n\n"
            f"## 13. Suggested Next Analysis\n\n{gen_md.suggested_next_analysis_markdown}\n"
        )

        report = AnalysisReport(
            dataset_id=dataset_id,
            filename=filename,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            title=gen_md.title,
            subtitle=gen_md.subtitle,
            executive_summary=gen_md.executive_summary_markdown,
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
            cleaning_summary=cleaning_summary,
            data_quality_breakdown=quality_breakdown
        )

        logger.info(f"ReportGenerationAgent successfully compiled 13-section report for '{dataset_id}'")
        return report

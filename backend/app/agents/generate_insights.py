import json
from typing import Optional
from backend.app.models.understanding import DatasetUnderstanding
from backend.app.models.statistics import StatisticalAnalysisResult
from backend.app.models.sql import SQLAnalysisResult
from backend.app.models.patterns import PatternDetectionResult
from backend.app.models.quality import QualityReport
from backend.app.models.insights import InsightCollection
from backend.app.llm.router import llm_router
from backend.app.core.logging import logger


class InsightGenerationAgent:
    """Agent that translates deterministic computations and SQL query results into evidence-grounded insights."""

    @classmethod
    def generate(
        cls,
        understanding: DatasetUnderstanding,
        statistics: StatisticalAnalysisResult,
        sql_results: SQLAnalysisResult,
        patterns: PatternDetectionResult,
        quality: QualityReport,
        revision_critique: Optional[str] = None
    ) -> InsightCollection:
        dataset_id = statistics.dataset_id
        logger.info(f"Running InsightGenerationAgent for dataset '{dataset_id}' (Revision active: {bool(revision_critique)})")

        # 1. Summarize statistical evidence
        stats_evidence = []
        for um in statistics.univariate_metrics:
            stats_evidence.append(
                f"- Metric '{um.column_name}': Mean={um.mean:,.2f}, Median={um.median:,.2f}, Min={um.min:,.2f}, Max={um.max:,.2f}, Std={um.std:,.2f}, IQR={um.iqr:,.2f}, Skewness={um.skewness:,.2f}"
            )
        for cp in statistics.correlation_results:
            stats_evidence.append(
                f"- Correlation '{cp.col1}' vs '{cp.col2}': Pearson r={cp.pearson_coef:+.3f} (p-value={cp.pearson_pvalue:.4f}), Statistically Significant={cp.is_statistically_significant}, Strength={cp.strength}"
            )
        for gr in statistics.groupby_results:
            top_items = [f"{it.group_value}: {it.sum or it.mean:,.2f} ({it.share_percentage:.1f}%)" for it in gr.items[:5]]
            stats_evidence.append(
                f"- GroupBy '{gr.group_column}' by '{gr.metric_column}' ({gr.aggregation}): {', '.join(top_items)}"
            )

        # 2. Summarize SQL query results
        sql_evidence = []
        for sq in sql_results.results:
            if sq.execution_status == "success" and sq.rows:
                top_rows_str = ", ".join([str(r) for r in sq.rows[:3]])
                sql_evidence.append(
                    f"- Query '{sq.query_name}' ({sq.purpose}): {sq.row_count} rows. Top results: [{top_rows_str}]"
                )

        # 3. Summarize Pattern results
        pattern_evidence = []
        for t in patterns.trends:
            pattern_evidence.append(f"- Trend ({t.metric_column}): {t.description}")
        for c in patterns.concentrations:
            pattern_evidence.append(f"- Concentration ({c.dimension_column}): {c.description} (Share: {c.top_categories_share_pct:.1f}%)")
        for a in patterns.anomalies:
            pattern_evidence.append(f"- Anomaly ({a.metric_column}): {a.description} [Severity: {a.severity}]")
        for s in patterns.seasonality:
            pattern_evidence.append(f"- Seasonality ({s.metric_column}): {s.description}")

        system_prompt = (
            "You are a Lead Quantitative AI Data Strategist and Senior Quantitative Auditor. "
            "Your objective is to generate 3 to 6 high-impact, deeply quantitative insights for any dataset domain "
            "(Sales, Finance, Healthcare, HR, Operations, Education, Logistics, Customer, etc.).\n\n"
            "MANDATORY INSIGHT STRUCTURE:\n"
            "For every insight, you MUST populate:\n"
            "1. 'question_answered': The explicit, concrete business or analytical question this insight answers based on the real dataset columns and discovered patterns.\n"
            "2. 'empirical_answer': Concise quantitative direct answer to the question backed by empirical data.\n"
            "3. 'finding': Direct analytical finding stating exactly what occurred in the data.\n"
            "4. 'evidence': The EXACT numbers, percentages, baseline figures, p-values, or query rows from the computed data.\n"
            "5. 'interpretation': The operational or domain meaning of these numbers.\n"
            "6. 'implication': Concrete, actionable recommendation or strategic next step for decision-makers.\n\n"
            "STRICT GROUNDING RULES:\n"
            "- NEVER formulate generic or disconnected questions. Every question MUST directly reference the actual column names, metrics, segments, or correlations.\n"
            "- NEVER use vague phrases like 'significant growth', 'certain categories', or 'outliers were found' without citing the exact category names, periods, and figures.\n"
            "- Every figure cited in 'evidence' must match the computed evidence tables.\n"
            "- DO NOT assert causality unless statistically proven (use 'is correlated with', 'is associated with', 'suggests').\n"
            "- Return a structured InsightCollection."
        )

        critique_block = ""
        if revision_critique:
            critique_block = (
                f"\n\nCRITICAL REVIEW FEEDBACK FROM PREVIOUS ATTEMPT (YOU MUST FIX THESE):\n"
                f"{revision_critique}\n"
                f"Carefully correct the rejected claims to strictly match the ground-truth evidence."
            )

        user_prompt = (
            f"Dataset Context:\n"
            f"Dataset ID: {dataset_id}\n"
            f"Domain: {understanding.domain}\n"
            f"Summary: {understanding.dataset_summary}\n"
            f"Target Entity: {understanding.target_entity}\n"
            f"Data Quality Score: {quality.quality_score}/100 (Grade {quality.grade})\n\n"
            f"--- COMPUTED STATISTICAL EVIDENCE ---\n"
            f"{chr(10).join(stats_evidence[:12]) if stats_evidence else 'Standard variance moments computed.'}\n\n"
            f"--- EXECUTED DUCKDB SQL QUERY EVIDENCE ---\n"
            f"{chr(10).join(sql_evidence[:8]) if sql_evidence else 'Standard analytical aggregations executed.'}\n\n"
            f"--- DETECTED PATTERNS, TRENDS & ANOMALIES ---\n"
            f"{chr(10).join(pattern_evidence[:8]) if pattern_evidence else 'No extreme multi-sigma outliers detected.'}"
            f"{critique_block}\n\n"
            f"Generate an InsightCollection with 3 to 6 evidence-grounded insights. "
            f"For each insight, clearly define 'question_answered', 'empirical_answer', 'finding', 'evidence', 'interpretation', and 'implication' directly grounded in the computed data."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        insights = llm_router.complete(
            agent_name="generate_insights",
            messages=messages,
            response_model=InsightCollection,
            temperature=0.1
        )

        logger.info(f"InsightGenerationAgent completed: {len(insights.insights)} insights generated for '{dataset_id}'")
        return insights

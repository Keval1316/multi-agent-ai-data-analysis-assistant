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
                f"- Metric '{um.column_name}': Mean={um.mean:,.2f}, Median={um.median:,.2f}, Min={um.min:,.2f}, Max={um.max:,.2f}, Std={um.std:,.2f}, IQR={um.iqr:,.2f}"
            )
        for cp in statistics.correlation_results:
            stats_evidence.append(
                f"- Correlation '{cp.col1}' vs '{cp.col2}': Pearson={cp.pearson_coef} (p={cp.pearson_pvalue}), Strength={cp.strength}"
            )
        for gr in statistics.groupby_results:
            top_items = [f"{it.group_value}: {it.sum or it.mean:,.2f} ({it.share_percentage}%)" for it in gr.items[:4]]
            stats_evidence.append(
                f"- GroupBy '{gr.group_column}' by '{gr.metric_column}' ({gr.aggregation}): {', '.join(top_items)}"
            )

        # 2. Summarize SQL query results
        sql_evidence = []
        for sq in sql_results.results:
            if sq.execution_status == "success" and sq.rows:
                sql_evidence.append(
                    f"- Query '{sq.query_name}' ({sq.purpose}): {sq.row_count} rows returned. Sample top row: {json.dumps(sq.rows[0])}"
                )

        # 3. Summarize Pattern results
        pattern_evidence = []
        for t in patterns.trends:
            pattern_evidence.append(f"- Trend: {t.description}")
        for c in patterns.concentrations:
            pattern_evidence.append(f"- Concentration: {c.description}")
        for a in patterns.anomalies:
            pattern_evidence.append(f"- Anomaly: {a.description}")
        for s in patterns.seasonality:
            pattern_evidence.append(f"- Seasonality: {s.description}")

        system_prompt = (
            "You are a Principal AI Data Strategist. "
            "Your objective is to generate 3 to 6 high-impact, evidence-grounded business insights. "
            "CRITICAL EVIDENCE GROUNDING RULES:\n"
            "1. Every single finding MUST be strictly grounded in the provided computed statistics, SQL results, or patterns.\n"
            "2. Cite the exact figures in the 'supporting_evidence' field.\n"
            "3. DO NOT assert causality unless statistically proven (use 'is associated with', 'suggests', 'may indicate').\n"
            "4. NEVER fabricate numbers or invent metrics that are not in the evidence.\n"
            "5. Provide actionable, realistic business recommendations for each finding."
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
            f"Quality Rating: {quality.quality_score}/100 (Grade {quality.grade})\n\n"
            f"Computed Statistical Evidence:\n"
            f"{chr(10).join(stats_evidence[:10])}\n\n"
            f"Executed SQL Query Evidence:\n"
            f"{chr(10).join(sql_evidence[:6])}\n\n"
            f"Detected Pattern Evidence:\n"
            f"{chr(10).join(pattern_evidence[:8])}"
            f"{critique_block}\n\n"
            f"Generate an InsightCollection containing structured insights and executive takeaways."
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

import json
from typing import List
from backend.app.models.insights import InsightCollection
from backend.app.models.statistics import StatisticalAnalysisResult
from backend.app.models.sql import SQLAnalysisResult
from backend.app.models.patterns import PatternDetectionResult
from backend.app.models.critic import CriticReviewResult, UnsupportedClaim
from backend.app.llm.router import llm_router
from backend.app.core.logging import logger


class CriticReviewAgent:
    """Adversarial critic agent that audits generated insights against ground-truth evidence tables."""

    @classmethod
    def review(
        cls,
        insights: InsightCollection,
        statistics: StatisticalAnalysisResult,
        sql_results: SQLAnalysisResult,
        patterns: PatternDetectionResult
    ) -> CriticReviewResult:
        logger.info(f"Running CriticReviewAgent for dataset '{insights.dataset_id}' on {len(insights.insights)} insights")

        # 1. Format Ground Truth Evidence
        stats_lines = []
        for um in statistics.univariate_metrics:
            stats_lines.append(f"Stat '{um.column_name}': mean={um.mean}, median={um.median}, min={um.min}, max={um.max}, iqr={um.iqr}")
        for cp in statistics.correlation_results:
            stats_lines.append(f"Corr '{cp.col1}' & '{cp.col2}': r={cp.pearson_coef}, p={cp.pearson_pvalue}, sig={cp.is_statistically_significant}")
        for gr in statistics.groupby_results:
            summary = ", ".join([f"{it.group_value}: {it.sum}" for it in gr.items[:3]])
            stats_lines.append(f"GroupBy '{gr.group_column}' ({gr.aggregation} {gr.metric_column}): {summary}")

        sql_lines = []
        for sq in sql_results.results:
            if sq.execution_status == "success" and sq.rows:
                sql_lines.append(f"SQL '{sq.query_name}': {json.dumps(sq.rows[:2])}")

        pattern_lines = [t.description for t in patterns.trends] + [c.description for c in patterns.concentrations] + [a.description for a in patterns.anomalies]

        # 2. Format Insights Under Review
        insights_lines = []
        for ins in insights.insights:
            insights_lines.append(
                f"[Insight ID: {ins.id}]\n"
                f"Title: {ins.title}\n"
                f"Finding: {ins.finding}\n"
                f"Supporting Evidence: {ins.supporting_evidence}\n"
                f"Recommendation: {ins.recommendation}\n"
            )

        system_prompt = (
            "You are a rigorous, adversarial AI Critic and Senior Quantitative Auditor. "
            "Your job is to audit data insights against the ground-truth computed evidence. "
            "STRICT CRITIC RULES:\n"
            "1. Check every number, percentage, and metric mentioned in the insights against the ground truth.\n"
            "2. Flag any hallucinated numbers, fabricated figures, or unverified claims.\n"
            "3. Reject causal claims that are not statistically justified.\n"
            "4. If all claims are truthful and supported, set approved=true.\n"
            "5. If ANY claim is hallucinated or contradicts evidence, set approved=false, list the unsupported_claims, and specify required_corrections."
        )

        user_prompt = (
            f"--- GROUND TRUTH COMPUTED EVIDENCE ---\n\n"
            f"Statistical Results:\n{chr(10).join(stats_lines[:12])}\n\n"
            f"SQL Query Results:\n{chr(10).join(sql_lines[:6])}\n\n"
            f"Detected Patterns:\n{chr(10).join(pattern_lines[:6])}\n\n"
            f"--- INSIGHTS UNDER REVIEW ---\n\n"
            f"{chr(10).join(insights_lines)}\n\n"
            f"Conduct an audit and return a CriticReviewResult."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        review = llm_router.complete(
            agent_name="critic_review",
            messages=messages,
            response_model=CriticReviewResult,
            temperature=0.0
        )

        logger.info(f"CriticReviewAgent review completed: Approved={review.approved}, Unsupported Claims={len(review.unsupported_claims)}")
        return review

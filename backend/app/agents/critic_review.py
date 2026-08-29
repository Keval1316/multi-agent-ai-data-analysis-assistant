import json
from backend.app.models.insights import InsightCollection
from backend.app.models.statistics import StatisticalAnalysisResult
from backend.app.models.sql import SQLAnalysisResult
from backend.app.models.patterns import PatternDetectionResult
from backend.app.models.critic import CriticReviewResult
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
            skew_str = f"skew={um.skewness} ({um.distribution_symmetry})" if um.skewness is not None else "skew=N/A"
            stats_lines.append(f"Stat '{um.column_name}': mean={um.mean}, median={um.median}, min={um.min}, max={um.max}, iqr={um.iqr}, {skew_str}")
        for cp in statistics.correlation_results:
            stats_lines.append(f"Corr '{cp.col1}' & '{cp.col2}': r={cp.pearson_coef:+.3f}, p={cp.pearson_pvalue}, sig={cp.is_statistically_significant}, practical_effect='{cp.practical_significance}'")
        for gr in statistics.groupby_results:
            summary = ", ".join([f"{it.group_value}: {it.sum or it.mean} ({it.share_percentage:.1f}%)" for it in gr.items[:3]])
            stats_lines.append(f"GroupBy '{gr.group_column}' ({gr.aggregation} {gr.metric_column}): {summary}")

        sql_lines = []
        for sq in sql_results.results:
            if sq.execution_status == "success" and sq.rows:
                warn = f" [WARNING: {sq.query_validation_warning}]" if sq.query_validation_warning else ""
                sql_lines.append(f"SQL '{sq.query_name}'{warn}: {json.dumps(sq.rows[:2])}")

        pattern_lines = [t.description for t in patterns.trends] + [c.description for c in patterns.concentrations] + [a.description for a in patterns.anomalies]

        # 2. Format Insights Under Review
        insights_lines = []
        for ins in insights.insights:
            insights_lines.append(
                f"[Insight ID: {ins.id}]\n"
                f"Title: {ins.title}\n"
                f"Finding: {ins.finding}\n"
                f"Supporting Evidence: {ins.evidence or ins.supporting_evidence}\n"
                f"What This Means: {ins.what_this_means}\n"
                f"Interpretation: {ins.interpretation}\n"
                f"Recommendation: {ins.implication or ins.recommendation}\n"
                f"Confidence: {ins.confidence} ({ins.confidence_rationale})\n"
            )

        system_prompt = (
            "You are a rigorous, adversarial AI Critic and Senior Quantitative Auditor.\n"
            "Your job is to audit data insights against the ground-truth computed evidence before final report generation.\n\n"
            "MANDATORY 10-POINT EVIDENCE VALIDATION CHECKLIST:\n"
            "1. Is the claim directly supported by the ground truth dataset values and metrics?\n"
            "2. Is the statistic correctly interpreted (e.g. mean vs median, skewness direction)?\n"
            "3. Is the conclusion stronger than what the evidence warrants?\n"
            "4. Is correlation being confused with causation (e.g. claiming X drives or causes Y)?\n"
            "5. Is statistical significance confused with practical significance (e.g. treating r = 0.15 as a strong pricing signal)?\n"
            "6. Are variable names and concepts interpreted correctly (e.g. stock quantity != profitability/performance, stock != supplier reliability)?\n"
            "7. Is the recommendation directly supported by the observed finding (no wild leaps)?\n"
            "8. Is the sample size and evidence sufficient for the stated confidence rating?\n"
            "9. Are claims claiming 'Pareto' strictly backed by >= 75-80% concentration?\n"
            "10. Is the language clear, simple, and free of unnecessary pretentious jargon?\n\n"
            "DECISION RULES:\n"
            "- If all insights pass the 10 checks, set approved=true, unsupported_claims=[], and severity_of_discrepancy='None'.\n"
            "- If ANY insight fails one or more checks (e.g. asserts causality, calls high stock 'high performing', confuses statistical with practical significance, fabricates numbers), set approved=false, list the unsupported_claims with exact reasons, and provide required_corrections."
        )

        user_prompt = (
            f"--- GROUND TRUTH COMPUTED EVIDENCE ---\n\n"
            f"Statistical Results:\n{chr(10).join(stats_lines[:12])}\n\n"
            f"SQL Query Results:\n{chr(10).join(sql_lines[:6])}\n\n"
            f"Detected Patterns:\n{chr(10).join(pattern_lines[:6])}\n\n"
            f"--- INSIGHTS UNDER REVIEW ---\n\n"
            f"{chr(10).join(insights_lines)}\n\n"
            f"Execute the 10-point Evidence Validation Audit and return a CriticReviewResult."
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

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
            skew_desc = um.distribution_symmetry or f"Skewness={um.skewness}"
            stats_evidence.append(
                f"- Metric '{um.column_name}': Count={um.count}, Mean={um.mean:,.2f}, Median={um.median:,.2f}, Min={um.min:,.2f}, Max={um.max:,.2f}, Std={um.std:,.2f}, IQR={um.iqr:,.2f}, Skewness={um.skewness} ({skew_desc})"
            )
        for cp in statistics.correlation_results:
            stats_evidence.append(
                f"- Correlation '{cp.col1}' vs '{cp.col2}': Pearson r={cp.pearson_coef:+.3f} (p={cp.pearson_pvalue}), Direction={cp.direction}, Strength={cp.strength}, Practical Effect={cp.practical_significance}, Stat Significant={cp.is_statistically_significant}"
            )
        for gr in statistics.groupby_results:
            top_items = [f"{it.group_value}: {it.sum or it.mean:,.2f} ({it.share_percentage:.1f}%)" for it in gr.items[:5]]
            stats_evidence.append(
                f"- GroupBy '{gr.group_column}' by '{gr.metric_column}' ({gr.aggregation}): {', '.join(top_items)}"
            )

        # 2. Summarize SQL query results with validation warnings
        sql_evidence = []
        for sq in sql_results.results:
            if sq.execution_status == "success" and sq.rows:
                top_rows_str = ", ".join([str(r) for r in sq.rows[:3]])
                warn_str = f" [WARNING: {sq.query_validation_warning}]" if sq.query_validation_warning else ""
                sql_evidence.append(
                    f"- Query '{sq.query_name}' ({sq.purpose}){warn_str}: {sq.row_count} rows. Top results: [{top_rows_str}]"
                )

        # 3. Summarize Pattern results
        pattern_evidence = []
        for t in patterns.trends:
            pattern_evidence.append(f"- Trend ({t.metric_column}): {t.description} [R²={t.r_squared}, p={t.p_value}, Sig={t.is_statistically_significant}]")
        for c in patterns.concentrations:
            pattern_evidence.append(f"- {c.pattern_label} ({c.dimension_column}): {c.description} (Share: {c.top_categories_share_pct:.1f}%)")
        for a in patterns.anomalies:
            pattern_evidence.append(f"- Anomaly ({a.metric_column}): {a.description} [Severity: {a.severity}]")
        for s in patterns.seasonality:
            pattern_evidence.append(f"- Seasonality ({s.metric_column}): {s.description}")

        system_prompt = (
            "You are a Senior Quantitative AI Data Analyst and Statistical Auditor.\n"
            "Your objective is to generate 3 to 6 evidence-grounded, statistically responsible insights.\n\n"
            "MANDATORY REASONING CHAIN:\n"
            "Data → Analysis → Finding → Evidence → Interpretation → Business Impact → Recommendation → Confidence\n\n"
            "STRICT STATISTICAL & INTERPRETATION RULES:\n"
            "1. CORRELATION IS NOT CAUSATION: Never claim variable X drives or causes variable Y based on correlation.\n"
            "2. STATISTICAL VS PRACTICAL SIGNIFICANCE: A statistically significant correlation with small effect size (|r| < 0.30) is NOT a strong predictive or pricing signal. State this clearly.\n"
            "3. DO NOT CONFUSE HIGH STOCK WITH HIGH PERFORMANCE: Never call high-stock categories 'high-performing', 'profitable', or 'successful' without sales/margin data. Use 'inventory concentration' or 'high-stock category'.\n"
            "4. SUPPLIER ANALYSIS: Never evaluate supplier performance based on stock quantity alone. Use 'supplier inventory contribution' and state that supplier reliability/fulfillment data is absent.\n"
            "5. MEAN VS MEDIAN & SKEWNESS: Never claim 'high values pull average upward' if mean < median. Use calculated skewness. Positive skew means right-tailed with higher values; negative skew means left-tailed.\n"
            "6. CONCENTRATION VS PARETO: Do NOT call every concentration 'Pareto'. Only use Pareto when top ~20% account for ~80% of volume. Otherwise call it 'Inventory concentration'.\n"
            "7. PRUDENT RECOMMENDATIONS: Avoid aggressive directives ('immediately change pricing', 'replace supplier'). Prefer 'investigate', 'review', 'monitor', 'validate', 'conduct further analysis'.\n"
            "8. PLAIN ENGLISH: Avoid convoluted jargon. Provide simple explanations in 'what_this_means'.\n"
            "9. CONFIDENCE RATING: Assign 'High', 'Moderate', or 'Low' based on sample size and variable completeness, and provide 'confidence_rationale'."
        )

        critique_block = ""
        if revision_critique:
            critique_block = (
                f"\n\nCRITICAL AUDIT FEEDBACK FROM PREVIOUS PASS (YOU MUST RESOLVE THESE):\n"
                f"{revision_critique}\n"
                f"Carefully correct the rejected claims to strictly align with ground-truth evidence."
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
            f"Generate an InsightCollection with 3 to 6 evidence-grounded insights following the mandatory reasoning chain."
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

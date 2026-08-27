import re
from typing import List, Dict, Type, TypeVar
from pydantic import BaseModel
from backend.app.llm.base import LLMProvider
from backend.app.models.understanding import DatasetUnderstanding, KPICandidate, DimensionCandidate
from backend.app.models.plan import AnalysisPlan, GroupByAnalysisPlan, SQLQueryGoal, RecommendedChart

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """High-fidelity deterministic mock provider for testing and offline execution."""

    def __init__(self, name: str = "mock"):
        self._name = name

    @property
    def provider_name(self) -> str:
        return self._name

    def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: float = 0.1,
    ) -> T:
        prompt_text = " ".join([m.get("content", "") for m in messages])

        # 1. DatasetUnderstanding
        if response_model == DatasetUnderstanding:
            # Extract column names if present in prompt
            cols = re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]", prompt_text)
            numeric_cols = [c for c in cols if any(k in c.lower() for k in ["revenue", "price", "quantity", "cost", "score", "rate", "amount"])]
            cat_cols = [c for c in cols if any(k in c.lower() for k in ["region", "category", "product", "status", "country", "segment", "type"])]

            kpis = []
            if numeric_cols:
                for col in numeric_cols[:3]:
                    kpis.append(KPICandidate(
                        name=f"Total {col.replace('_', ' ').title()}",
                        column_name=col,
                        aggregation="SUM" if "rate" not in col else "AVG",
                        description=f"Aggregate tracking of {col}",
                        importance="High"
                    ))
            else:
                kpis.append(KPICandidate(
                    name="Total Record Count",
                    column_name=None,
                    aggregation="COUNT",
                    description="Total volume of transaction records",
                    importance="High"
                ))

            dimensions = []
            if cat_cols:
                for col in cat_cols[:3]:
                    dimensions.append(DimensionCandidate(
                        column_name=col,
                        dimension_name=col.replace('_', ' ').title(),
                        role="segmentation"
                    ))
            else:
                dimensions.append(DimensionCandidate(
                    column_name="category",
                    dimension_name="Category Breakdown",
                    role="segmentation"
                ))

            return DatasetUnderstanding(
                domain="E-Commerce & Commercial Operations",
                dataset_summary="A structured transaction dataset tracking orders, product categories, revenues, quantities, and regional distributions.",
                target_entity="Order Transaction",
                key_kpis=kpis,
                important_dimensions=dimensions,
                core_questions=[
                    "What are the top-performing categories and regions by total revenue?",
                    "What is the distribution of transaction volume across customer segments?",
                    "Are there noticeable correlation patterns between pricing, quantities, and return rates?"
                ],
                data_limitations_note="Some categories may require standardizing whitespace or casing before categorical grouping."
            )  # type: ignore

        # 2. AnalysisPlan
        if response_model == AnalysisPlan:
            cols = re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]", prompt_text)
            numeric_cols = [c for c in cols if any(k in c.lower() for k in ["revenue", "price", "quantity", "cost", "score", "rate", "amount"])]
            cat_cols = [c for c in cols if any(k in c.lower() for k in ["region", "category", "product", "status", "country", "segment", "type"])]

            num1 = numeric_cols[0] if numeric_cols else "total_revenue"
            num2 = numeric_cols[1] if len(numeric_cols) > 1 else (numeric_cols[0] if numeric_cols else "quantity")
            cat1 = cat_cols[0] if cat_cols else "region"

            group_plans = [
                GroupByAnalysisPlan(
                    group_column=cat1,
                    metric_column=num1,
                    aggregation="SUM",
                    purpose=f"Evaluate {num1} performance across {cat1}"
                )
            ]

            sql_goals = [
                SQLQueryGoal(
                    name=f"top_{cat1}_by_{num1}",
                    purpose=f"Aggregate {num1} aggregated by {cat1} in descending order",
                    columns_needed=[cat1, num1]
                ),
                SQLQueryGoal(
                    name="overall_metric_summary",
                    purpose="Compute dataset-level summary KPIs (total rows, avg revenue)",
                    columns_needed=[num1]
                )
            ]

            charts = [
                RecommendedChart(
                    chart_type="bar",
                    x_column=cat1,
                    y_column=num1,
                    title=f"Total {num1.replace('_', ' ').title()} by {cat1.replace('_', ' ').title()}",
                    purpose=f"Compare {num1} across {cat1} categories"
                ),
                RecommendedChart(
                    chart_type="scatter" if len(numeric_cols) > 1 else "histogram",
                    x_column=num1,
                    y_column=num2 if len(numeric_cols) > 1 else None,
                    title=f"{num1.replace('_', ' ').title()} vs {num2.replace('_', ' ').title()}" if len(numeric_cols) > 1 else f"{num1} Distribution",
                    purpose="Explore statistical relationship and outliers"
                )
            ]

            return AnalysisPlan(
                primary_goal="Maximize analytical insights into commercial revenue drivers and operational anomalies.",
                descriptive_numeric_columns=numeric_cols[:4] if numeric_cols else [num1],
                correlation_pairs=[[num1, num2]] if len(numeric_cols) >= 2 else [],
                group_by_analyses=group_plans,
                sql_query_goals=sql_goals,
                pattern_detection_targets=[f"{num1} trends across segments"],
                recommended_charts=charts
            )  # type: ignore

        # 3. SQLGenerationResponse
        from backend.app.models.sql import SQLGenerationResponse, GeneratedSQLQuery
        if response_model == SQLGenerationResponse:
            cols = re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]", prompt_text)
            numeric_cols = [c for c in cols if any(k in c.lower() for k in ["revenue", "price", "quantity", "cost", "score", "rate", "amount"])]
            cat_cols = [c for c in cols if any(k in c.lower() for k in ["region", "category", "product", "status", "country", "segment", "type"])]

            # Extract table name if present
            table_match = re.search(r"table\s+['\"]?([a-zA-Z0-9_]+)['\"]?", prompt_text, re.IGNORECASE)
            tbl = table_match.group(1) if table_match else "dataset"

            num1 = numeric_cols[0] if numeric_cols else "total_revenue"
            cat1 = cat_cols[0] if cat_cols else "region"

            queries = [
                GeneratedSQLQuery(
                    name=f"top_{cat1}_by_{num1}",
                    purpose=f"Aggregate total {num1} grouped by {cat1} in descending order",
                    sql=f"SELECT {cat1}, SUM({num1}) AS total_{num1}, COUNT(*) AS transaction_count FROM {tbl} GROUP BY {cat1} ORDER BY total_{num1} DESC LIMIT 10",
                    expected_columns=[cat1, f"total_{num1}", "transaction_count"]
                ),
                GeneratedSQLQuery(
                    name="overall_dataset_summary",
                    purpose=f"Compute overall average, min, and max for {num1}",
                    sql=f"SELECT COUNT(*) AS total_records, AVG({num1}) AS avg_{num1}, MIN({num1}) AS min_{num1}, MAX({num1}) AS max_{num1} FROM {tbl}",
                    expected_columns=["total_records", f"avg_{num1}", f"min_{num1}", f"max_{num1}"]
                )
            ]
            return SQLGenerationResponse(queries=queries)  # type: ignore

        # 4. InsightCollection
        from backend.app.models.insights import InsightCollection, InsightItem
        if response_model == InsightCollection:
            dataset_id = "dataset"
            id_match = re.search(r"dataset[\s_]*id[:\s]+['\"]?([a-zA-Z0-9_]+)['\"]?", prompt_text, re.IGNORECASE)
            if id_match:
                dataset_id = id_match.group(1)

            # Extract numbers/metrics from prompt if present
            stat_matches = re.findall(r"- Metric '([^']+)': Mean=([\d,\.]+), Median=([\d,\.]+)", prompt_text)
            corr_matches = re.findall(r"- Correlation '([^']+)' vs '([^']+)': Pearson r=([+-]?[\d\.]+)", prompt_text)
            group_matches = re.findall(r"- GroupBy '([^']+)' by '([^']+)'.*?: ([^,\n]+)", prompt_text)

            m1_name, m1_mean, m1_med = stat_matches[0] if stat_matches else ("Value Metric", "1,250.00", "980.00")
            c1_name, c2_name, c_val = corr_matches[0] if corr_matches else ("Primary Metric", "Secondary Metric", "+0.72")
            g_dim, g_met, g_top = group_matches[0] if group_matches else ("Category", "Volume", "Top Segment (45.2%)")

            insights = [
                InsightItem(
                    id="ins_1",
                    title=f"Segment Performance & {g_dim} Concentration",
                    finding=f"Operational metrics demonstrate pronounced concentration across {g_dim}, with leading segments dominating overall volume.",
                    evidence=f"Top segment distribution in {g_dim}: {g_top}. Group aggregation confirms statistically significant variance across segments.",
                    interpretation=f"The dataset reveals that high-performing {g_dim} segments drive the vast majority of {g_met}, creating concentrated exposure.",
                    implication=f"Focus strategic resource allocation and operational monitoring on top-performing {g_dim} groups while developing targeted growth initiatives for secondary segments.",
                    category="Growth Driver",
                    importance="High",
                    confidence="High"
                ),
                InsightItem(
                    id="ins_2",
                    title=f"Distribution Skewness in {m1_name}",
                    finding=f"Statistical analysis of '{m1_name}' indicates an asymmetric distribution where mean values diverge from the median baseline.",
                    evidence=f"Computed parametric moments for '{m1_name}': Mean = {m1_mean}, Median = {m1_med}. Skewness reflects an extended right-tail distribution.",
                    interpretation=f"A standard average significantly overstates baseline typical performance; median figures ({m1_med}) provide a more robust operational benchmark.",
                    implication=f"Adopt median-based KPI targets rather than simple arithmetic means to prevent high-value outliers from distorting performance targets.",
                    category="Performance",
                    importance="Medium",
                    confidence="High"
                ),
                InsightItem(
                    id="ins_3",
                    title=f"Empirical Association: {c1_name} vs {c2_name}",
                    finding=f"Detected a strong, statistically significant correlation between '{c1_name}' and '{c2_name}'.",
                    evidence=f"Pearson correlation coefficient r = {c_val} (statistically significant at p < 0.05). Verified across all cleaned dataset rows.",
                    interpretation=f"Movement in '{c1_name}' consistently tracks variations in '{c2_name}', indicating an underlying operational linkage.",
                    implication=f"Leverage '{c1_name}' as a leading indicator to forecast and optimize '{c2_name}' resource planning.",
                    category="Performance",
                    importance="High",
                    confidence="High"
                )
            ]

            summary_points = [
                f"Significant concentration across leading {g_dim} segments driving primary {g_met} volume.",
                f"Distribution skewness in {m1_name} (Mean={m1_mean} vs Median={m1_med}) necessitates median-based benchmarking.",
                f"Statistically significant correlation (r = {c_val}) identified between {c1_name} and {c2_name}."
            ]

            return InsightCollection(
                dataset_id=dataset_id,
                insights=insights,
                executive_summary_points=summary_points,
                overall_confidence_rating="High"
            )  # type: ignore

        # 5. CriticReviewResult
        from backend.app.models.critic import CriticReviewResult, UnsupportedClaim
        if response_model == CriticReviewResult:
            user_msg = "\n".join([m["content"] for m in messages if m.get("role") == "user"])
            is_reject = "ins_fake" in user_msg or "9999%" in user_msg or "fabricated profit" in user_msg.lower()

            if is_reject:
                return CriticReviewResult(
                    approved=False,
                    feedback="Detected unsupported numerical claims and overgeneralized assertions not backed by computed statistics.",
                    unsupported_claims=[
                        UnsupportedClaim(
                            insight_id="ins_fake",
                            claim_text="Revenue grew by 9999% without baseline data",
                            reason="Fabricated percentage not present in computed statistical results",
                            ground_truth_fact="Actual growth rate is within standard bounds"
                        )
                    ],
                    required_corrections=[
                        "Remove the unsupported 9999% growth claim and reference only validated group totals."
                    ],
                    severity_of_discrepancy="Critical"
                )  # type: ignore

            return CriticReviewResult(
                approved=True,
                feedback="All insight findings are rigorously grounded in computed statistical moments, SQL results, and pattern metrics. Causal language is appropriately moderated.",
                unsupported_claims=[],
                required_corrections=[],
                severity_of_discrepancy="None"
            )  # type: ignore

        # 6. GeneratedReportMarkdown
        from backend.app.models.report import GeneratedReportMarkdown
        if response_model == GeneratedReportMarkdown:
            return GeneratedReportMarkdown(
                title="Commercial & Operational Dataset Analysis Report",
                subtitle="Executive Insights, Statistical Distributions, SQL Discoveries & Strategic Recommendations",
                executive_summary=(
                    "This comprehensive analytical report evaluates the uploaded dataset structure, statistical properties, "
                    "and operational dimensions. Our multi-agent pipeline processed the dataset across profiling, quality auditing, "
                    "deterministic statistical modeling, SQL execution, pattern detection, and adversarial insight verification."
                ),
                key_findings_markdown=(
                    "### 1. Revenue Concentration & Product Performance\n"
                    "- Commercial transaction volume shows pronounced category concentration.\n"
                    "- Leading product categories generate the primary share of total gross revenue.\n\n"
                    "### 2. Statistical Distribution & Outlier Behavior\n"
                    "- Transaction distributions exhibit positive skewness, with the mean order value exceeding the median.\n"
                    "- Extreme value anomalies were isolated and verified for audit integrity."
                ),
                strategic_recommendations_markdown=(
                    "1. **Inventory & Promotion Optimization**: Prioritize high-performing categories for inventory stocking.\n"
                    "2. **Order Tiering & Upselling**: Introduce structured loyalty programs to boost average order value.\n"
                    "3. **Data Quality Governance**: Deploy point-of-entry validation to prevent anomalous transaction inputs."
                ),
                methodology_and_caveats_markdown=(
                    "Analysis was conducted using deterministic computation (DuckDB SQL, SciPy moments, Pearson/Spearman correlations) "
                    "combined with evidence-grounded AI synthesis. Caveats: Group differences reflect observed historical records."
                )
            )  # type: ignore

        # Generic fallback using response model defaults or empty construction
        try:
            return response_model()
        except Exception:
            raise ValueError(f"Mock provider cannot construct response_model '{response_model.__name__}'")

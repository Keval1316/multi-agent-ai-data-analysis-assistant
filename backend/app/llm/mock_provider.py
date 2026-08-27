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
        prompt_lower = prompt_text.lower()

        # Dynamic Domain & Entity Detection
        if any(k in prompt_lower for k in ["patient", "diagnosis", "blood", "heart", "clinical", "disease", "treatment", "glucose", "bp", "symptom"]):
            domain = "Healthcare & Clinical Outcomes"
            entity = "Patient Case"
        elif any(k in prompt_lower for k in ["employee", "salary", "tenure", "department", "attrition", "hire", "performance_rating", "staff", "hr"]):
            domain = "Human Resources & Workforce Analytics"
            entity = "Employee Profile"
        elif any(k in prompt_lower for k in ["student", "grade", "exam", "gpa", "course", "attendance", "teacher", "academic", "score"]):
            domain = "Education & Academic Performance"
            entity = "Student Record"
        elif any(k in prompt_lower for k in ["shipment", "delivery", "warehouse", "vehicle", "freight", "logistics", "carrier", "route"]):
            domain = "Supply Chain & Logistics"
            entity = "Logistics Shipment"
        elif any(k in prompt_lower for k in ["credit", "debit", "balance", "loan", "interest", "stock", "portfolio", "banking", "asset", "investment"]):
            domain = "Financial Services & Banking"
            entity = "Financial Account"
        elif any(k in prompt_lower for k in ["revenue", "order", "product", "discount", "sale", "store", "customer", "retail", "cart", "unit_price"]):
            domain = "Sales & Commercial Operations"
            entity = "Sales Transaction"
        else:
            domain = "Quantitative Multi-Variable Analysis"
            entity = "Data Record"

        # Extract column metadata from prompt
        col_matches = re.findall(r"-\s*'([^']+)'\s*\(([^,]+),\s*([^)]+)\)", prompt_text)
        if col_matches:
            numeric_cols = [c[0] for c in col_matches if any(t in c[1].lower() or t in c[2].lower() for t in ["numeric", "int", "float", "double", "decimal", "moment"])]
            cat_cols = [c[0] for c in col_matches if any(t in c[1].lower() or t in c[2].lower() for t in ["categorical", "string", "object", "text", "segment"])]
        else:
            all_cols = re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]", prompt_text)
            numeric_cols = [c for c in all_cols if any(k in c.lower() for k in ["revenue", "price", "quantity", "cost", "score", "rate", "amount", "age", "salary", "value", "total", "count", "metric", "weight", "height", "duration", "hours", "points", "gpa"])]
            cat_cols = [c for c in all_cols if c not in numeric_cols and any(k in c.lower() for k in ["region", "category", "product", "status", "country", "segment", "type", "dept", "department", "grade", "role", "gender", "class", "name", "city", "state"])]
            if not numeric_cols and all_cols:
                numeric_cols = [all_cols[0]]
            if not cat_cols and len(all_cols) > 1:
                cat_cols = [all_cols[1]]

        primary_num = numeric_cols[0] if numeric_cols else "primary_metric"
        secondary_num = numeric_cols[1] if len(numeric_cols) > 1 else primary_num
        primary_cat = cat_cols[0] if cat_cols else "segment_category"

        # 1. DatasetUnderstanding
        if response_model == DatasetUnderstanding:
            kpis = []
            if numeric_cols:
                for col in numeric_cols[:4]:
                    kpis.append(KPICandidate(
                        name=f"Total {col.replace('_', ' ').title()}",
                        column_name=col,
                        aggregation="SUM" if "rate" not in col and "score" not in col and "age" not in col else "AVG",
                        description=f"Aggregate tracking and moment distribution of {col}",
                        importance="High"
                    ))
            else:
                kpis.append(KPICandidate(
                    name=f"Total {entity} Count",
                    column_name=None,
                    aggregation="COUNT",
                    description=f"Total volume of recorded {entity.lower()}s",
                    importance="High"
                ))

            dimensions = []
            if cat_cols:
                for col in cat_cols[:4]:
                    dimensions.append(DimensionCandidate(
                        column_name=col,
                        dimension_name=col.replace('_', ' ').title(),
                        role="segmentation"
                    ))
            else:
                dimensions.append(DimensionCandidate(
                    column_name=primary_cat,
                    dimension_name=primary_cat.replace('_', ' ').title(),
                    role="segmentation"
                ))

            core_q = [
                f"How is {primary_num.replace('_', ' ')} distributed across {primary_cat.replace('_', ' ')} segments?",
                f"Is there a statistically significant association between {primary_num.replace('_', ' ')} and {secondary_num.replace('_', ' ')}?",
                f"What data quality anomalies, skewness, or outliers characterize {primary_num.replace('_', ' ')}?"
            ]

            return DatasetUnderstanding(
                domain=domain,
                dataset_summary=f"A structured {domain.lower()} dataset capturing {entity.lower()} entries across {len(numeric_cols)} quantitative metrics and {len(cat_cols)} categorical dimensions.",
                target_entity=entity,
                key_kpis=kpis,
                important_dimensions=dimensions,
                core_questions=core_q,
                data_limitations_note="Standard cross-sectional data hygiene verified. Category grouping standardizations applied."
            )  # type: ignore

        # 2. AnalysisPlan
        if response_model == AnalysisPlan:
            group_plans = [
                GroupByAnalysisPlan(
                    group_column=primary_cat,
                    metric_column=primary_num,
                    aggregation="SUM" if "rate" not in primary_num and "score" not in primary_num else "AVG",
                    purpose=f"Evaluate {primary_num} performance across {primary_cat}"
                )
            ]

            sql_goals = [
                SQLQueryGoal(
                    name=f"top_{primary_cat}_by_{primary_num}",
                    purpose=f"Aggregate {primary_num} grouped by {primary_cat} in descending order",
                    columns_needed=[primary_cat, primary_num]
                ),
                SQLQueryGoal(
                    name="overall_metric_summary",
                    purpose=f"Compute dataset-level summary KPIs (total rows, avg/min/max {primary_num})",
                    columns_needed=[primary_num]
                )
            ]

            charts = [
                RecommendedChart(
                    chart_type="bar",
                    x_column=primary_cat,
                    y_column=primary_num,
                    title=f"Total {primary_num.replace('_', ' ').title()} by {primary_cat.replace('_', ' ').title()}",
                    purpose=f"Compare {primary_num} across {primary_cat} categories"
                ),
                RecommendedChart(
                    chart_type="scatter" if len(numeric_cols) > 1 else "histogram",
                    x_column=primary_num,
                    y_column=secondary_num if len(numeric_cols) > 1 else None,
                    title=f"{primary_num.replace('_', ' ').title()} vs {secondary_num.replace('_', ' ').title()}" if len(numeric_cols) > 1 else f"{primary_num.replace('_', ' ').title()} Distribution",
                    purpose="Explore statistical relationship and outliers"
                )
            ]

            return AnalysisPlan(
                primary_goal=f"Maximize empirical insights into {domain.lower()} performance drivers, distributions, and anomalies.",
                descriptive_numeric_columns=numeric_cols[:4] if numeric_cols else [primary_num],
                correlation_pairs=[[primary_num, secondary_num]] if len(numeric_cols) >= 2 else [],
                group_by_analyses=group_plans,
                sql_query_goals=sql_goals,
                pattern_detection_targets=[f"{primary_num} trends across {primary_cat}"],
                recommended_charts=charts
            )  # type: ignore

        # 3. SQLGenerationResponse
        from backend.app.models.sql import SQLGenerationResponse, GeneratedSQLQuery
        if response_model == SQLGenerationResponse:
            table_match = re.search(r"table\s+['\"]?([a-zA-Z0-9_]+)['\"]?", prompt_text, re.IGNORECASE)
            tbl = table_match.group(1) if table_match else "dataset"

            agg_func = "SUM" if "rate" not in primary_num and "score" not in primary_num else "AVG"
            queries = [
                GeneratedSQLQuery(
                    name=f"top_{primary_cat}_by_{primary_num}",
                    purpose=f"Aggregate total {primary_num} grouped by {primary_cat} in descending order",
                    sql=f"SELECT {primary_cat}, {agg_func}({primary_num}) AS total_{primary_num}, COUNT(*) AS record_count FROM {tbl} GROUP BY {primary_cat} ORDER BY total_{primary_num} DESC LIMIT 10",
                    expected_columns=[primary_cat, f"total_{primary_num}", "record_count"]
                ),
                GeneratedSQLQuery(
                    name="overall_dataset_summary",
                    purpose=f"Compute overall average, min, and max for {primary_num}",
                    sql=f"SELECT COUNT(*) AS total_records, AVG({primary_num}) AS avg_{primary_num}, MIN({primary_num}) AS min_{primary_num}, MAX({primary_num}) AS max_{primary_num} FROM {tbl}",
                    expected_columns=["total_records", f"avg_{primary_num}", f"min_{primary_num}", f"max_{primary_num}"]
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

            m1_name, m1_mean, m1_med = stat_matches[0] if stat_matches else (primary_num, "1,250.00", "980.00")
            c1_name, c2_name, c_val = corr_matches[0] if corr_matches else (primary_num, secondary_num, "+0.72")
            g_dim, g_met, g_top = group_matches[0] if group_matches else (primary_cat, primary_num, "Top Segment (45.2%)")

            insights = [
                InsightItem(
                    id="ins_1",
                    title=f"Segment Performance & {g_dim.replace('_', ' ').title()} Concentration",
                    finding=f"Operational metrics demonstrate pronounced concentration across {g_dim}, with leading segments dominating overall volume.",
                    evidence=f"Top segment distribution in {g_dim}: {g_top}. Group aggregation confirms statistically significant variance across segments.",
                    interpretation=f"The dataset reveals that high-performing {g_dim} segments drive the vast majority of {g_met}, creating concentrated exposure.",
                    implication=f"Focus strategic resource allocation and operational monitoring on top-performing {g_dim} groups while developing targeted growth initiatives for secondary segments.",
                    question_answered=f"How is {g_met.replace('_', ' ')} distributed across {g_dim.replace('_', ' ')}, and do top segments concentrate the majority share?",
                    empirical_answer=f"Yes, {g_dim.replace('_', ' ')} demonstrates high Pareto concentration, where leading segments account for {g_top}.",
                    category="Growth Driver",
                    importance="High",
                    confidence="High"
                ),
                InsightItem(
                    id="ins_2",
                    title=f"Distribution Skewness in {m1_name.replace('_', ' ').title()}",
                    finding=f"Statistical analysis of '{m1_name}' indicates an asymmetric distribution where mean values diverge from the median baseline.",
                    evidence=f"Computed parametric moments for '{m1_name}': Mean = {m1_mean}, Median = {m1_med}. Skewness reflects an extended right-tail distribution.",
                    interpretation=f"A standard average significantly overstates baseline typical performance; median figures ({m1_med}) provide a more robust operational benchmark.",
                    implication=f"Adopt median-based KPI targets rather than simple arithmetic means to prevent high-value outliers from distorting performance targets.",
                    question_answered=f"Does '{m1_name.replace('_', ' ')}' exhibit significant distribution skewness between arithmetic average and median benchmarks?",
                    empirical_answer=f"Yes, Mean ({m1_mean}) noticeably diverges from Median ({m1_med}), demonstrating positive distribution skewness.",
                    category="Performance",
                    importance="Medium",
                    confidence="High"
                ),
                InsightItem(
                    id="ins_3",
                    title=f"Empirical Association: {c1_name.replace('_', ' ').title()} vs {c2_name.replace('_', ' ').title()}",
                    finding=f"Detected a strong, statistically significant correlation between '{c1_name}' and '{c2_name}'.",
                    evidence=f"Pearson correlation coefficient r = {c_val} (statistically significant at p < 0.05). Verified across all cleaned dataset rows.",
                    interpretation=f"Movement in '{c1_name}' consistently tracks variations in '{c2_name}', indicating an underlying operational linkage.",
                    implication=f"Leverage '{c1_name}' as a leading indicator to forecast and optimize '{c2_name}' resource planning.",
                    question_answered=f"Is there an empirical, statistically significant relationship linking '{c1_name.replace('_', ' ')}' with '{c2_name.replace('_', ' ')}'?",
                    empirical_answer=f"Yes, Pearson r = {c_val} confirms a statistically significant empirical correlation (p < 0.05).",
                    category="Performance",
                    importance="High",
                    confidence="High"
                )
            ]

            summary_points = [
                f"Significant concentration across leading {g_dim} segments driving primary {g_met} volume ({g_top}).",
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
                            claim_text="Growth rate grew by 9999% without baseline data",
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
                title=f"{domain} Executive Intelligence Report",
                subtitle=f"Quantitative Profiling, Empirical Distributions, SQL Aggregations & Strategic Recommendations for {entity}",
                executive_summary=(
                    f"This comprehensive analytical report evaluates the uploaded {domain.lower()} dataset structure, statistical moments, "
                    f"and categorical dimensions. Our multi-agent pipeline processed the dataset across profiling, quality auditing, "
                    f"deterministic statistical modeling ({primary_num}), DuckDB SQL execution, pattern detection, and adversarial insight verification."
                ),
                key_findings_markdown=(
                    f"### 1. Empirical Questions Answered & Segment Concentration\n"
                    f"- Quantitative analysis of '{primary_num}' demonstrates significant variance across '{primary_cat}'.\n"
                    f"- Leading '{primary_cat}' categories concentrate the primary volume share of '{primary_num}'.\n\n"
                    f"### 2. Statistical Moments & Distribution Skewness\n"
                    f"- '{primary_num}' exhibits positive distribution skewness, where arithmetic averages exceed median benchmarks.\n"
                    f"- Extreme value anomalies and boundary outliers were isolated and verified for audit integrity."
                ),
                strategic_recommendations_markdown=(
                    f"1. **Targeted Segment Optimization**: Prioritize high-performing '{primary_cat}' groups for resource allocation and monitoring.\n"
                    f"2. **Median-Based Benchmarking**: Adopt median metrics for '{primary_num}' to prevent outlier distortion in operational reviews.\n"
                    f"3. **Data Hygiene Governance**: Maintain data entry validation rules to preserve quality score standards."
                ),
                methodology_and_caveats_markdown=(
                    "Analysis was conducted using deterministic computation (DuckDB SQL, SciPy moments, Pearson/Spearman correlations) "
                    "combined with evidence-grounded AI multi-agent synthesis. Group differences reflect empirical historical records."
                )
            )  # type: ignore

        # Generic fallback using response model defaults or empty construction
        try:
            return response_model()
        except Exception:
            raise ValueError(f"Mock provider cannot construct response_model '{response_model.__name__}'")


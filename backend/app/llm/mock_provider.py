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

        # Extract table name if present
        table_match = re.search(r"table\s+['\"]?([a-zA-Z0-9_]+)['\"]?", prompt_text, re.IGNORECASE)
        tbl = table_match.group(1) if table_match else "dataset"

        # Extract column metadata from prompt (handles with or without leading dash '-')
        col_matches = re.findall(r"['\"]([^'\"]+)['\"]\s*\(([^,]+),\s*([^)]+)\)", prompt_text)
        # Filter out table name if captured accidentally
        valid_col_matches = [c for c in col_matches if c[0] != tbl and not c[0].startswith("dataset_")]

        if valid_col_matches:
            numeric_cols = [c[0] for c in valid_col_matches if any(t in c[1].lower() or t in c[2].lower() for t in ["numeric", "int", "float", "double", "decimal", "moment", "real", "hugeint"])]
            cat_cols = [c[0] for c in valid_col_matches if c[0] not in numeric_cols]
        else:
            all_raw = re.findall(r"['\"]([a-zA-Z0-9_]+)['\"]", prompt_text)
            ignore_tokens = {tbl, "dataset", "dataset_id", "generate_sql", "true", "false", "null", "none", "table"}
            all_cols = [c for c in all_raw if c.lower() not in ignore_tokens and not c.startswith("dataset_") and not c.startswith("top_") and not c.startswith("overall_")]
            numeric_cols = [c for c in all_cols if any(k in c.lower() for k in ["revenue", "price", "quantity", "cost", "score", "rate", "amount", "age", "salary", "value", "total", "count", "metric", "weight", "height", "duration", "hours", "points", "gpa"])]
            cat_cols = [c for c in all_cols if c not in numeric_cols and any(k in c.lower() for k in ["region", "category", "product", "status", "country", "segment", "type", "dept", "department", "grade", "role", "gender", "class", "name", "city", "state", "page"])]
            if not numeric_cols and all_cols:
                # If only 1 column and it's not a known cat keyword, check if other
                if len(all_cols) == 1 and all_cols[0] in cat_cols:
                    pass
                else:
                    cat_cols = [c for c in all_cols if c not in numeric_cols]
            if not cat_cols and len(all_cols) > len(numeric_cols):
                cat_cols = [c for c in all_cols if c not in numeric_cols]

        primary_num = numeric_cols[0] if numeric_cols else None
        secondary_num = numeric_cols[1] if len(numeric_cols) > 1 else (primary_num or "primary_metric")
        primary_cat = cat_cols[0] if cat_cols else (numeric_cols[0] if numeric_cols else "segment_category")

        # Fallback names for understanding & plan
        safe_num = primary_num or "total_volume"
        safe_cat = primary_cat or "segment"

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
                    column_name=safe_cat,
                    dimension_name=safe_cat.replace('_', ' ').title(),
                    role="segmentation"
                ))

            core_q = [
                f"How is {safe_num.replace('_', ' ')} distributed across {safe_cat.replace('_', ' ')} segments?",
                f"Is there a statistically significant association between {safe_num.replace('_', ' ')} and {secondary_num.replace('_', ' ')}?",
                f"What data quality anomalies, skewness, or outliers characterize {safe_num.replace('_', ' ')}?"
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
                    group_column=safe_cat,
                    metric_column=safe_num,
                    aggregation="SUM" if "rate" not in safe_num and "score" not in safe_num else "AVG",
                    purpose=f"Evaluate {safe_num} performance across {safe_cat}"
                )
            ]

            sql_goals = [
                SQLQueryGoal(
                    name=f"top_{safe_cat}_by_{safe_num}",
                    purpose=f"Aggregate {safe_num} grouped by {safe_cat} in descending order",
                    columns_needed=[safe_cat, safe_num] if primary_num else [safe_cat]
                ),
                SQLQueryGoal(
                    name="overall_metric_summary",
                    purpose=f"Compute dataset-level summary KPIs (total rows, avg/min/max {safe_num})",
                    columns_needed=[safe_num] if primary_num else []
                )
            ]

            charts = [
                RecommendedChart(
                    chart_type="bar",
                    x_column=safe_cat,
                    y_column=primary_num,
                    title=f"Total {safe_num.replace('_', ' ').title()} by {safe_cat.replace('_', ' ').title()}",
                    purpose=f"Compare {safe_num} across {safe_cat} categories"
                ),
                RecommendedChart(
                    chart_type="scatter" if len(numeric_cols) > 1 else "histogram",
                    x_column=safe_num,
                    y_column=secondary_num if len(numeric_cols) > 1 else None,
                    title=f"{safe_num.replace('_', ' ').title()} vs {secondary_num.replace('_', ' ').title()}" if len(numeric_cols) > 1 else f"{safe_num.replace('_', ' ').title()} Distribution",
                    purpose="Explore statistical relationship and outliers"
                )
            ]

            return AnalysisPlan(
                primary_goal=f"Maximize empirical insights into {domain.lower()} performance drivers, distributions, and anomalies.",
                descriptive_numeric_columns=numeric_cols[:4] if numeric_cols else [safe_num],
                correlation_pairs=[[primary_num, secondary_num]] if len(numeric_cols) >= 2 and primary_num else [],
                group_by_analyses=group_plans,
                sql_query_goals=sql_goals,
                pattern_detection_targets=[f"{safe_num} trends across {safe_cat}"],
                recommended_charts=charts
            )  # type: ignore

        # 3. SQLGenerationResponse
        from backend.app.models.sql import SQLGenerationResponse, GeneratedSQLQuery
        if response_model == SQLGenerationResponse:
            queries = []
            if primary_cat and primary_num:
                agg_func = "SUM" if "rate" not in primary_num.lower() and "score" not in primary_num.lower() and "age" not in primary_num.lower() else "AVG"
                queries.append(GeneratedSQLQuery(
                    name=f"top_{primary_cat}_by_{primary_num}",
                    purpose=f"Aggregate {agg_func.lower()} of {primary_num} grouped by {primary_cat} in descending order",
                    sql=f'SELECT "{primary_cat}", {agg_func}("{primary_num}") AS total_{primary_num}, COUNT(*) AS record_count FROM "{tbl}" GROUP BY "{primary_cat}" ORDER BY total_{primary_num} DESC LIMIT 10',
                    expected_columns=[primary_cat, f"total_{primary_num}", "record_count"]
                ))
                queries.append(GeneratedSQLQuery(
                    name="overall_dataset_summary",
                    purpose=f"Compute overall average, min, and max for {primary_num}",
                    sql=f'SELECT COUNT(*) AS total_records, AVG("{primary_num}") AS avg_{primary_num}, MIN("{primary_num}") AS min_{primary_num}, MAX("{primary_num}") AS max_{primary_num} FROM "{tbl}"',
                    expected_columns=["total_records", f"avg_{primary_num}", f"min_{primary_num}", f"max_{primary_num}"]
                ))
            elif primary_cat:
                queries.append(GeneratedSQLQuery(
                    name=f"top_{primary_cat}_distribution",
                    purpose=f"Frequency distribution of top {primary_cat} segments",
                    sql=f'SELECT "{primary_cat}", COUNT(*) AS record_count FROM "{tbl}" GROUP BY "{primary_cat}" ORDER BY record_count DESC LIMIT 10',
                    expected_columns=[primary_cat, "record_count"]
                ))
                queries.append(GeneratedSQLQuery(
                    name="overall_dataset_summary",
                    purpose="Dataset-level total record count and distinct categories",
                    sql=f'SELECT COUNT(*) AS total_records, COUNT(DISTINCT "{primary_cat}") AS distinct_{primary_cat} FROM "{tbl}"',
                    expected_columns=["total_records", f"distinct_{primary_cat}"]
                ))
            elif primary_num:
                queries.append(GeneratedSQLQuery(
                    name=f"{primary_num}_distribution_summary",
                    purpose=f"Summary moments and distribution for {primary_num}",
                    sql=f'SELECT COUNT(*) AS total_records, AVG("{primary_num}") AS avg_{primary_num}, MIN("{primary_num}") AS min_{primary_num}, MAX("{primary_num}") AS max_{primary_num} FROM "{tbl}"',
                    expected_columns=["total_records", f"avg_{primary_num}", f"min_{primary_num}", f"max_{primary_num}"]
                ))
                queries.append(GeneratedSQLQuery(
                    name=f"{primary_num}_summary_percentiles",
                    purpose=f"Key percentiles for {primary_num}",
                    sql=f'SELECT COUNT(*) AS total_records, MIN("{primary_num}") AS min_val, MAX("{primary_num}") AS max_val FROM "{tbl}"',
                    expected_columns=["total_records", "min_val", "max_val"]
                ))
            else:
                queries.append(GeneratedSQLQuery(
                    name="overall_dataset_summary",
                    purpose="Dataset-level total row count",
                    sql=f'SELECT COUNT(*) AS total_records FROM "{tbl}"',
                    expected_columns=["total_records"]
                ))
            return SQLGenerationResponse(queries=queries)  # type: ignore

        # 4. InsightCollection
        from backend.app.models.insights import InsightCollection, InsightItem
        if response_model == InsightCollection:
            dataset_id = "dataset"
            id_match = re.search(r"dataset[\s_]*id[:\s]+['\"]?([a-zA-Z0-9_]+)['\"]?", prompt_text, re.IGNORECASE)
            if id_match:
                dataset_id = id_match.group(1)

            # Extract numbers/metrics from prompt if present
            stat_matches = re.findall(r"- Metric '([^']+)': Count=(\d+), Mean=([\d,\.]+), Median=([\d,\.]+)", prompt_text)
            corr_matches = re.findall(r"- Correlation '([^']+)' vs '([^']+)': Pearson r=([+-]?[\d\.]+)", prompt_text)
            group_matches = re.findall(r"- GroupBy '([^']+)' by '([^']+)'.*?: ([^,\n]+)", prompt_text)

            m1_name = stat_matches[0][0] if stat_matches else (primary_num or "stock_quantity")
            m1_mean = stat_matches[0][2] if stat_matches else "125.00"
            m1_med = stat_matches[0][3] if stat_matches else "104.00"
            c1_name = corr_matches[0][0] if corr_matches else (primary_num or "stock_quantity")
            c2_name = corr_matches[0][1] if corr_matches else (secondary_num or "unit_price")
            c_val = corr_matches[0][2] if corr_matches else "+0.152"
            g_dim = group_matches[0][0] if group_matches else (primary_cat or "category")
            g_met = group_matches[0][1] if group_matches else (primary_num or "stock_quantity")
            g_top = group_matches[0][2] if group_matches else "Top Categories (43.5%)"

            insights = [
                InsightItem(
                    id="ins_1",
                    title=f"Inventory Concentration in {g_dim.replace('_', ' ').title()}",
                    finding=f"Inventory volume is concentrated in a relatively small number of {g_dim} categories.",
                    evidence=f"The top {g_dim} categories account for {g_top} of total {g_met}.",
                    what_this_means=f"A large share of inventory sits in a few categories. Note: High stock indicates inventory volume, not product profitability or sales success.",
                    interpretation=f"Concentration in these categories means inventory holding risk and warehouse capacity are heavily exposed to them.",
                    implication=f"Review stock turnover and customer demand rates for top {g_dim} categories to ensure inventory matches actual sales velocity.",
                    confidence="High",
                    confidence_rationale="Computed deterministically across all records.",
                    question_answered=f"How is {g_met.replace('_', ' ')} distributed across {g_dim.replace('_', ' ')}?",
                    empirical_answer=f"The top categories account for {g_top} of total volume, reflecting inventory concentration.",
                    category="Inventory & Operations",
                    importance="High"
                ),
                InsightItem(
                    id="ins_2",
                    title=f"Distribution Profile for {m1_name.replace('_', ' ').title()}",
                    finding=f"The distribution of '{m1_name}' has an extended upper tail, resulting in a mean that is higher than the median.",
                    evidence=f"Computed parametric moments: Mean = {m1_mean}, Median = {m1_med}. Skewness indicates a right-skewed distribution.",
                    what_this_means=f"The median ({m1_med}) represents typical items better than the average ({m1_mean}) because a few high-volume items pull the average up.",
                    interpretation=f"Using the average alone could create unrealistic inventory targets for typical items.",
                    implication=f"Consider using the median alongside sales velocity and demand forecasts when establishing inventory guidelines.",
                    confidence="High",
                    confidence_rationale="Supported by complete univariate moment calculations.",
                    question_answered=f"Does '{m1_name.replace('_', ' ')}' exhibit significant distribution skewness?",
                    empirical_answer=f"Yes, Mean ({m1_mean}) exceeds Median ({m1_med}) due to right-skewed values.",
                    category="Distribution Profile",
                    importance="Medium"
                ),
                InsightItem(
                    id="ins_3",
                    title=f"Relationship Assessment: {c1_name.replace('_', ' ').title()} vs {c2_name.replace('_', ' ').title()}",
                    finding=f"There is a weak linear relationship between '{c1_name}' and '{c2_name}' (r = {c_val}).",
                    evidence=f"Pearson correlation r = {c_val}. Although statistically evaluated, the effect size is weak.",
                    what_this_means=f"Changes in '{c1_name}' do not reliably predict '{c2_name}'. Correlation does not imply that one causes the other.",
                    interpretation=f"The weak association indicates that these two variables should not be assumed to have an operational or pricing dependency.",
                    implication=f"Do not adjust '{c2_name}' strategy based on '{c1_name}' levels alone; validate with separate demand and margin data.",
                    confidence="Moderate",
                    confidence_rationale="Linear correlation measured across dataset sample; no causal relationship inferred.",
                    question_answered=f"Is there a meaningful relationship between '{c1_name.replace('_', ' ')}' and '{c2_name.replace('_', ' ')}'?",
                    empirical_answer=f"The relationship is weak (r = {c_val}) with minimal practical effect size.",
                    category="Relationships & Trends",
                    importance="Medium"
                )
            ]

            summary_points = [
                f"Inventory is concentrated in top {g_dim} segments ({g_top}).",
                f"Right-skewed distribution in {m1_name} (Mean={m1_mean} vs Median={m1_med}) makes median a useful operational reference point.",
                f"Weak correlation between {c1_name} and {c2_name} (r = {c_val}) should not be interpreted as a causal or strong pricing signal."
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
                subtitle=f"Evidence-Based Analysis, Distribution Profiling & Operational Recommendations",
                executive_summary_markdown=(
                    f"### Overall Summary\n"
                    f"This report presents an evidence-based analysis of the {domain.lower()} dataset. "
                    f"All findings follow a strict data-to-evidence reasoning order and avoid unverified assumptions.\n\n"
                    f"### Key Findings (Top 3-5)\n"
                    f"1. **Inventory Concentration**: A substantial share of volume is concentrated in leading categories.\n"
                    f"2. **Distribution Profile**: Metrics exhibit positive skewness where mean exceeds median.\n"
                    f"3. **Relationship Evaluation**: Measured correlations exhibit weak practical effect sizes and do not establish causation.\n\n"
                    f"### Main Risks\n"
                    f"- Inventory imbalance across categories without corresponding demand validation.\n"
                    f"- Absence of sales velocity and supplier lead-time data to confirm performance.\n\n"
                    f"### Recommended Next Steps\n"
                    f"1. Review turnover and demand rates for concentrated categories.\n"
                    f"2. Utilize median reference points alongside demand forecasts for inventory planning.\n"
                    f"3. Integrate point-of-sale and supplier fulfillment metrics before making operational changes."
                ),
                dataset_overview_markdown=(
                    f"The dataset contains structured {domain.lower()} records. Key variables include numerical measurements "
                    f"('{primary_num or 'metric'}') and categorical groupings ('{primary_cat or 'category'}'). "
                    f"Data hygiene audits verified completeness, record uniqueness, and standardization."
                ),
                data_quality_and_validation_markdown=(
                    f"### Data Hygiene & Validation Audit\n"
                    f"| Check | Result | Status |\n"
                    f"| :--- | :--- | :--- |\n"
                    f"| Duplicate records | 0 | Clean |\n"
                    f"| Missing values | 0 | None detected |\n"
                    f"| Invalid / out-of-range values | 0 | None detected |\n"
                    f"| Category normalization | Completed | Standardized |\n"
                    f"| Overall quality score | 100/100 | Grade A |\n\n"
                    f"*Methodology*: The data quality score reflects automated audits for row duplication, null rates, range boundaries, and label standardization."
                ),
                key_findings_markdown=(
                    f"### 1. Inventory Concentration Across Categories\n"
                    f"- **Finding**: Stock quantity is concentrated in a small number of categories.\n"
                    f"- **Evidence**: Top categories account for over 40% of total stock.\n"
                    f"- **What This Means**: A few categories hold most warehouse volume. High stock reflects inventory volume, not product success or profitability.\n"
                    f"- **Confidence**: High (supported by total dataset aggregation).\n\n"
                    f"### 2. Metric Distribution & Skewness\n"
                    f"- **Finding**: The distribution is right-skewed with an extended upper tail.\n"
                    f"- **Evidence**: The arithmetic mean exceeds the median.\n"
                    f"- **What This Means**: Median values better represent typical items without outlier distortion.\n"
                    f"- **Confidence**: High (supported by calculated skewness moments)."
                ),
                distribution_analysis_markdown=(
                    f"Univariate analysis indicates that numerical variables exhibit moderate positive skewness. "
                    f"The median provides a reliable representation of typical baseline values, while the mean reflects the influence of high-volume observations."
                ),
                category_analysis_markdown=(
                    f"Categorical evaluation reveals that inventory is concentrated in a limited number of segments. "
                    f"Note: These categories are described as inventory-heavy rather than 'high-performing' because sales, margins, and turnover data are not present in this dataset."
                ),
                product_analysis_markdown=(
                    f"Item-level examination highlights specific products with elevated stock levels. "
                    f"These items represent inventory holding concentration and should be monitored for holding costs and turnover."
                ),
                supplier_analysis_markdown=(
                    f"Supplier analysis reflects the total inventory volume associated with each vendor ('Supplier inventory contribution'). "
                    f"Note: True supplier performance (such as lead times, defect rates, and fulfillment reliability) cannot be evaluated because those variables are not in the dataset."
                ),
                relationship_analysis_markdown=(
                    f"Bivariate correlation analysis indicates weak linear relationships between numerical variables. "
                    f"While statistically evaluated, effect sizes are weak and should not be used as independent pricing or forecasting signals. "
                    f"**Important**: Correlation does not establish causation."
                ),
                trend_analysis_markdown=(
                    f"Temporal analysis indicates no statistically significant time-based trend (R² ≈ 0, p >= 0.05). "
                    f"Observed percentage differences across periods reflect normal operational variation rather than a confirmed growth trajectory."
                ),
                recommendations_markdown=(
                    f"### Recommendation 1: Review Inventory Concentration\n"
                    f"- **Finding**: Inventory is concentrated in top categories.\n"
                    f"- **Evidence**: Leading categories hold a disproportionate share of volume.\n"
                    f"- **Business Implication**: Potential overstocking risk or working capital tie-up.\n"
                    f"- **Recommended Action**: Review sales turnover and customer demand before reordering.\n"
                    f"- **Confidence**: High.\n\n"
                    f"### Recommendation 2: Adopt Balanced Inventory Reference Points\n"
                    f"- **Finding**: Skewed distribution makes mean higher than median.\n"
                    f"- **Evidence**: Mean exceeds median across item quantities.\n"
                    f"- **Business Implication**: Relying solely on averages distorts inventory targets.\n"
                    f"- **Recommended Action**: Use the median as a reference point while incorporating demand velocity and safety stock requirements.\n"
                    f"- **Confidence**: High."
                ),
                limitations_markdown=(
                    f"- **Cross-Sectional Scope**: Data represents a single snapshot without multi-year historical depth.\n"
                    f"- **Absence of Commercial Metrics**: Sales velocity, profit margins, and revenue figures are not present, preventing profitability assessments.\n"
                    f"- **Supplier Metrics**: Vendor reliability, defect rates, and delivery lead times are unrecorded."
                ),
                suggested_next_analysis_markdown=(
                    f"1. **Point-of-Sale Integration**: Merge transaction logs to evaluate true inventory turnover and product performance.\n"
                    f"2. **Supplier Scorecard Integration**: Capture lead times and order defect rates for supplier performance benchmarking.\n"
                    f"3. **Demand Elasticity Modeling**: Model price sensitivity and seasonal demand fluctuations."
                )
            )  # type: ignore

        # Generic fallback using response model defaults or empty construction
        try:
            return response_model()
        except Exception:
            raise ValueError(f"Mock provider cannot construct response_model '{response_model.__name__}'")


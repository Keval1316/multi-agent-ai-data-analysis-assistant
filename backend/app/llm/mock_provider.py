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

        # Generic fallback using response model defaults or empty construction
        try:
            return response_model()
        except Exception:
            raise ValueError(f"Mock provider cannot construct response_model '{response_model.__name__}'")

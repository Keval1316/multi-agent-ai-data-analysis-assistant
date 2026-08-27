import json
from typing import List, Set
from backend.app.models.profile import DatasetProfile
from backend.app.models.understanding import DatasetUnderstanding
from backend.app.models.plan import AnalysisPlan, GroupByAnalysisPlan, SQLQueryGoal
from backend.app.llm.router import llm_router
from backend.app.core.logging import logger


class AnalysisPlanningAgent:
    """Agent that creates an analytical plan for statistical and SQL computation, validating all column references."""

    @classmethod
    def validate_and_clean_plan(cls, plan: AnalysisPlan, valid_columns: Set[str], numeric_columns: Set[str]) -> AnalysisPlan:
        """
        Post-validates the LLM-generated plan to guarantee zero hallucinated columns.
        Removes any non-existent columns from statistical tasks and SQL query requirements.
        """
        valid_cols_lower = {c.lower(): c for c in valid_columns}
        num_cols_lower = {c.lower(): c for c in numeric_columns}

        # 1. Clean descriptive numeric columns
        clean_num_cols = []
        for col in plan.descriptive_numeric_columns:
            if col.lower() in num_cols_lower:
                clean_num_cols.append(num_cols_lower[col.lower()])
        if not clean_num_cols and numeric_columns:
            clean_num_cols = list(numeric_columns)[:4]
        plan.descriptive_numeric_columns = clean_num_cols

        # 2. Clean correlation pairs
        clean_corr_pairs = []
        for pair in plan.correlation_pairs:
            if len(pair) == 2 and pair[0].lower() in num_cols_lower and pair[1].lower() in num_cols_lower:
                clean_corr_pairs.append([num_cols_lower[pair[0].lower()], num_cols_lower[pair[1].lower()]])
        plan.correlation_pairs = clean_corr_pairs

        # 3. Clean group by analyses
        clean_group_plans = []
        for gp in plan.group_by_analyses:
            if gp.group_column.lower() in valid_cols_lower and gp.metric_column.lower() in num_cols_lower:
                clean_group_plans.append(
                    GroupByAnalysisPlan(
                        group_column=valid_cols_lower[gp.group_column.lower()],
                        metric_column=num_cols_lower[gp.metric_column.lower()],
                        aggregation=gp.aggregation.upper() if gp.aggregation.upper() in ["SUM", "AVG", "COUNT", "MEDIAN", "MIN", "MAX"] else "SUM",
                        purpose=gp.purpose
                    )
                )
        plan.group_by_analyses = clean_group_plans

        # 4. Clean SQL query goals
        clean_sql_goals = []
        for sq in plan.sql_query_goals:
            clean_needed = [valid_cols_lower[c.lower()] for c in sq.columns_needed if c.lower() in valid_cols_lower]
            if clean_needed:
                clean_sql_goals.append(
                    SQLQueryGoal(
                        name=sq.name,
                        purpose=sq.purpose,
                        columns_needed=clean_needed
                    )
                )
        if not clean_sql_goals:
            # Fallback goal
            sample_col = list(valid_columns)[0]
            clean_sql_goals.append(
                SQLQueryGoal(
                    name="dataset_overview_metrics",
                    purpose="Aggregate core volume and key metrics",
                    columns_needed=[sample_col]
                )
            )
        plan.sql_query_goals = clean_sql_goals

        return plan

    @classmethod
    def plan(
        cls,
        profile: DatasetProfile,
        understanding: DatasetUnderstanding
    ) -> AnalysisPlan:
        logger.info(f"Running AnalysisPlanningAgent for dataset '{profile.dataset_id}'")

        valid_column_names = {c.name for c in profile.column_profiles}
        numeric_column_names = set(profile.numeric_column_names)
        categorical_column_names = set(profile.categorical_column_names)

        system_prompt = (
            "You are a Senior Quantitative Data Strategist and SQL Architect. "
            "Your objective is to generate an executable analysis plan for a structured dataset. "
            "CRITICAL REQUIREMENT: You must ONLY reference real column names provided in the schema. "
            "Do NOT invent, rename, or assume nonexistent columns. Return an AnalysisPlan object."
        )

        user_prompt = (
            f"Dataset Context & Understanding:\n"
            f"Domain: {understanding.domain}\n"
            f"Summary: {understanding.dataset_summary}\n"
            f"Target Entity: {understanding.target_entity}\n"
            f"Candidate KPIs: {', '.join([k.name for k in understanding.key_kpis])}\n"
            f"Key Questions: {json.dumps(understanding.core_questions)}\n\n"
            f"Available Verified Columns:\n"
            f"- Numeric Columns: {list(numeric_column_names)}\n"
            f"- Categorical Columns: {list(categorical_column_names)}\n"
            f"- Datetime Columns: {profile.datetime_column_names}\n"
            f"- All Columns: {list(valid_column_names)}\n\n"
            f"Generate an AnalysisPlan with:\n"
            f"1. Primary analytical goal.\n"
            f"2. List of numeric columns to compute descriptive distribution statistics for.\n"
            f"3. Valid pairs of numeric columns to assess correlation.\n"
            f"4. 2-4 Group-By aggregation plans (e.g. group by category/region and aggregate revenue/quantity).\n"
            f"5. 2-4 SQL Query Goals targeting high-value business questions.\n"
            f"6. Recommended interactive charts (bar, line, scatter, box, histogram).\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        raw_plan = llm_router.complete(
            agent_name="plan_analysis",
            messages=messages,
            response_model=AnalysisPlan,
            temperature=0.1
        )

        # Strictly validate all column references
        validated_plan = cls.validate_and_clean_plan(raw_plan, valid_column_names, numeric_column_names)
        logger.info(
            f"AnalysisPlanningAgent completed: {len(validated_plan.group_by_analyses)} group plans, "
            f"{len(validated_plan.sql_query_goals)} SQL goals, {len(validated_plan.recommended_charts)} charts."
        )
        return validated_plan

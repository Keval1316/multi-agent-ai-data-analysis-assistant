import json
from typing import List
from backend.app.models.profile import DatasetProfile
from backend.app.models.plan import AnalysisPlan
from backend.app.models.sql import GeneratedSQLQuery, SQLGenerationResponse
from backend.app.llm.router import llm_router
from backend.app.core.logging import logger


class SQLGenerationAgent:
    """Agent that translates analytical goals from the AnalysisPlan into valid, safe DuckDB SQL queries."""

    @classmethod
    def generate(
        cls,
        profile: DatasetProfile,
        plan: AnalysisPlan,
        table_name: str
    ) -> List[GeneratedSQLQuery]:
        logger.info(f"Running SQLGenerationAgent for table '{table_name}' with {len(plan.sql_query_goals)} query goals")

        valid_columns = [f"- '{c.name}' ({c.semantic_type}, {c.dtype})" for c in profile.column_profiles]
        numeric_cols = [c.name for c in profile.column_profiles if c.semantic_type == "numeric" or any(t in c.dtype.lower() for t in ["int", "float", "double", "decimal", "real", "hugeint"])]
        cat_cols = [c.name for c in profile.column_profiles if c.name not in numeric_cols]

        goals_text = "\n".join([
            f"- Goal '{g.name}': {g.purpose} (Columns: {', '.join(g.columns_needed)})"
            for g in plan.sql_query_goals
        ])

        system_prompt = (
            "You are an expert DuckDB SQL Architect and Senior Data Analyst.\n"
            "Your objective is to generate highly optimized, clean, safe analytical DuckDB SQL queries.\n\n"
            "STRICT RULES:\n"
            f"1. You MUST query ONLY the table '{table_name}'. Do not use any other table name.\n"
            f"2. The table name '{table_name}' must ONLY appear in the FROM clause. NEVER select '{table_name}' as a column or use it in GROUP BY, WHERE, or ORDER BY.\n"
            "3. You MUST only reference the real column names provided in the schema.\n"
            "4. Always enclose column names in double quotes (e.g. \"column_name\") to safely handle spaces and reserved keywords.\n"
            "5. You MUST only use SELECT or WITH (CTEs). NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, COPY, ATTACH, PRAGMA.\n"
            "6. Mathematical aggregations (SUM, AVG, MIN, MAX, MEDIAN) are ONLY allowed on verified numeric columns. For categorical/string columns, ONLY use COUNT(*) or COUNT(DISTINCT \"column\").\n"
            "7. Do NOT include trailing semicolons or multiple statements.\n"
            "8. Always use clean column aliases (e.g. AS record_count, AS total_revenue) and handle division by zero (NULLIF).\n"
            "9. Output a valid JSON object matching the SQLGenerationResponse schema."
        )

        user_prompt = (
            f"Dataset Target Table: '{table_name}'\n\n"
            f"Verified Available Columns:\n"
            f"{chr(10).join(valid_columns)}\n\n"
            f"Numeric Columns (safe for SUM, AVG, MIN, MAX): {numeric_cols}\n"
            f"Categorical/Text Columns (safe for GROUP BY, COUNT): {cat_cols}\n\n"
            f"Analytical SQL Goals to generate queries for:\n"
            f"{goals_text}\n\n"
            f"Generate a SQL query for each goal that delivers actionable data."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = llm_router.complete(
            agent_name="generate_sql",
            messages=messages,
            response_model=SQLGenerationResponse,
            temperature=0.1
        )

        logger.info(f"SQLGenerationAgent generated {len(response.queries)} SQL queries for '{table_name}'")
        return response.queries

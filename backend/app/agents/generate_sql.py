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

        valid_columns = [f"'{c.name}' ({c.semantic_type}, {c.dtype})" for c in profile.column_profiles]
        goals_text = "\n".join([
            f"- Goal '{g.name}': {g.purpose} (Columns: {', '.join(g.columns_needed)})"
            for g in plan.sql_query_goals
        ])

        system_prompt = (
            "You are an expert DuckDB SQL Architect and Senior Data Analyst. "
            "Your objective is to generate highly optimized, clean, safe analytical DuckDB SQL queries. "
            "STRICT RULES:\n"
            f"1. You MUST query ONLY the table '{table_name}'. Do not use any other table name.\n"
            "2. You MUST only use SELECT or WITH (CTEs). NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, COPY, ATTACH, PRAGMA.\n"
            "3. You MUST only reference the real column names provided in the schema.\n"
            "4. Do NOT include trailing semicolons or multiple statements.\n"
            "5. Always use descriptive column aliases and handle division by zero (e.g. NULLIF).\n"
            "6. Output a valid JSON object matching the SQLGenerationResponse schema."
        )

        user_prompt = (
            f"Dataset Target Table: '{table_name}'\n\n"
            f"Verified Available Columns:\n"
            f"{chr(10).join(valid_columns)}\n\n"
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

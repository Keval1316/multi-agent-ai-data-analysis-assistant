import json
from typing import List, Dict
from backend.app.models.profile import DatasetProfile
from backend.app.models.quality import QualityReport
from backend.app.models.understanding import DatasetUnderstanding
from backend.app.llm.router import llm_router
from backend.app.core.logging import logger


class DatasetUnderstandingAgent:
    """Agent that infers domain, candidate KPIs, entities, and strategic business questions from dataset metadata."""

    @classmethod
    def analyze(
        cls,
        profile: DatasetProfile,
        quality: QualityReport,
        filename: str = "dataset"
    ) -> DatasetUnderstanding:
        logger.info(f"Running DatasetUnderstandingAgent on table '{profile.table_name}' ({profile.total_rows} rows)")

        # Prepare compact structural summary
        col_summaries = []
        for col in profile.column_profiles:
            stats_snippet = ""
            if col.numeric_stats:
                stats_snippet = f" | min={col.numeric_stats.min}, max={col.numeric_stats.max}, mean={col.numeric_stats.mean:.2f}"
            elif col.categorical_stats:
                top_v = [f"{v.value}({v.count})" for v in col.categorical_stats.top_values[:3]]
                stats_snippet = f" | top: {', '.join(top_v)}"

            samples_str = ", ".join([str(x) for x in col.sample_values[:3]])
            col_summaries.append(
                f"- '{col.name}' ({col.semantic_type}, {col.dtype}) - nulls: {col.null_percentage}%{stats_snippet} [samples: {samples_str}]"
            )

        columns_block = "\n".join(col_summaries)

        system_prompt = (
            "You are an expert Chief Data Scientist and AI Business Analyst. "
            "Your objective is to interpret the real-world business meaning of a dataset based strictly on its schema, "
            "column statistics, and data quality metrics. "
            "Do NOT hallucinate or assume columns that do not exist. Return a structured DatasetUnderstanding object."
        )

        user_prompt = (
            f"Please analyze the following dataset structure:\n\n"
            f"Filename: {filename}\n"
            f"Total Rows: {profile.total_rows:,}\n"
            f"Total Columns: {profile.total_columns}\n"
            f"Duplicate Rows: {profile.duplicate_rows_count} ({profile.duplicate_rows_percentage}%)\n"
            f"Data Quality Score: {quality.quality_score}/100 (Grade {quality.grade})\n\n"
            f"Columns & Characteristics:\n"
            f"{columns_block}\n\n"
            f"Determine:\n"
            f"1. Likely business domain and operational context.\n"
            f"2. Concise narrative summary of what this data captures.\n"
            f"3. The primary entity / unit of observation.\n"
            f"4. Key candidate KPIs to compute (referencing only actual numeric/calculable columns).\n"
            f"5. Important categorical/temporal dimensions for segmentation.\n"
            f"6. 3-5 core business questions this dataset can answer.\n"
            f"7. Any practical data limitations or caveats based on the quality score."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        understanding = llm_router.complete(
            agent_name="understand_dataset",
            messages=messages,
            response_model=DatasetUnderstanding,
            temperature=0.1
        )

        logger.info(f"DatasetUnderstandingAgent completed for '{profile.table_name}': Domain='{understanding.domain}', KPIs={len(understanding.key_kpis)}")
        return understanding

import re
from typing import Dict, List, Set, Any
import pandas as pd
from backend.app.models.profile import DatasetProfile, ColumnProfile


class ColumnRoleProfile:
    """Semantic role metadata for a single dataset column."""

    def __init__(
        self,
        name: str,
        data_type: str,
        role: str,  # 'identifier', 'datetime', 'measure_additive', 'measure_rate', 'category_low', 'category_medium', 'category_high', 'binary', 'text'
        unique_count: int,
        null_count: int,
        is_identifier: bool = False,
        is_datetime: bool = False,
        is_measure: bool = False,
        is_category: bool = False,
        is_binary: bool = False,
    ):
        self.name = name
        self.data_type = data_type
        self.role = role
        self.unique_count = unique_count
        self.null_count = null_count
        self.is_identifier = is_identifier
        self.is_datetime = is_datetime
        self.is_measure = is_measure
        self.is_category = is_category
        self.is_binary = is_binary

    def __repr__(self):
        return f"<ColumnRole '{self.name}': role={self.role}, unique={self.unique_count}>"


class SemanticRoleClassifier:
    """Classifies dataset columns into semantic analytical roles to drive intelligent visualization selection."""

    IDENTIFIER_REGEX = re.compile(
        r"^(id|_id|.*_id|.*_key|.*_uuid|.*_guid|.*_code|index|row_id|order_id|customer_id|"
        r"user_id|student_id|employee_id|patient_id|trans_id|transaction_id|sku|isbn|serial.*)$",
        re.IGNORECASE
    )

    RATE_MEASURE_REGEX = re.compile(
        r".*(rate|score|ratio|margin|pct|percent|percentage|gpa|avg|average|index|yield|frequency).*",
        re.IGNORECASE
    )

    @classmethod
    def classify_column(
        cls,
        col_prof: ColumnProfile,
        total_rows: int,
        sample_series: pd.Series
    ) -> ColumnRoleProfile:
        name = col_prof.name
        name_clean = name.strip()
        data_type = (col_prof.dtype or "").lower()
        semantic_type = (col_prof.semantic_type or "").lower()
        unique_cnt = col_prof.unique_count
        null_cnt = col_prof.null_count

        is_id_name = bool(cls.IDENTIFIER_REGEX.match(name_clean))
        is_unique_key = (total_rows > 5 and unique_cnt >= total_rows * 0.95)
        is_rate = bool(cls.RATE_MEASURE_REGEX.match(name_clean))

        # 1. Check Datetime first
        if (
            semantic_type == "datetime"
            or col_prof.datetime_stats is not None
            or any(t in data_type for t in ["date", "time", "timestamp"])
            or (any(w in name_clean.lower() for w in ["_date", "date_", "timestamp", "datetime", "order_date", "created_at"]) and not is_id_name)
        ):
            return ColumnRoleProfile(
                name=name,
                data_type=data_type,
                role="datetime",
                unique_count=unique_cnt,
                null_count=null_cnt,
                is_datetime=True
            )

        # 2. Check Explicit Identifier (by name regex or semantic_type == 'identifier')
        # Continuous numeric measures (like total_revenue, income, age) are NEVER identifiers unless explicitly named *_id
        if (
            (semantic_type == "identifier" or is_id_name)
            or (is_unique_key and semantic_type not in ["numeric", "datetime"] and not any(t in data_type for t in ["float", "double", "int", "decimal", "numeric"]))
        ):
            return ColumnRoleProfile(
                name=name,
                data_type=data_type,
                role="identifier",
                unique_count=unique_cnt,
                null_count=null_cnt,
                is_identifier=True
            )

        # 3. Check Boolean / Binary Category
        if semantic_type == "boolean" or "bool" in data_type or (unique_cnt == 2 and total_rows > 10):
            return ColumnRoleProfile(
                name=name,
                data_type=data_type,
                role="binary",
                unique_count=unique_cnt,
                null_count=null_cnt,
                is_binary=True,
                is_category=True
            )

        # 4. Check Numeric Measures
        is_numeric_type = (
            semantic_type == "numeric"
            or col_prof.numeric_stats is not None
            or any(t in data_type for t in ["int", "float", "double", "decimal", "numeric", "real", "hugeint"])
        )
        if is_numeric_type and not is_id_name:
            # Low unique integer (e.g. rating 1-5 or class 1-3) can be treated as category
            if unique_cnt <= 5 and "int" in data_type and total_rows > 20 and not is_rate:
                return ColumnRoleProfile(
                    name=name,
                    data_type=data_type,
                    role="category_low",
                    unique_count=unique_cnt,
                    null_count=null_cnt,
                    is_category=True
                )

            return ColumnRoleProfile(
                name=name,
                data_type=data_type,
                role="measure_rate" if is_rate else "measure_additive",
                unique_count=unique_cnt,
                null_count=null_cnt,
                is_measure=True
            )

        # 5. Categorical Dimensions (String / Categorical)
        if unique_cnt <= 8:
            return ColumnRoleProfile(
                name=name,
                data_type=data_type,
                role="category_low",
                unique_count=unique_cnt,
                null_count=null_cnt,
                is_category=True
            )
        elif unique_cnt <= 25:
            return ColumnRoleProfile(
                name=name,
                data_type=data_type,
                role="category_medium",
                unique_count=unique_cnt,
                null_count=null_cnt,
                is_category=True
            )
        elif unique_cnt <= 60:
            return ColumnRoleProfile(
                name=name,
                data_type=data_type,
                role="category_high",
                unique_count=unique_cnt,
                null_count=null_cnt,
                is_category=True
            )
        else:
            return ColumnRoleProfile(
                name=name,
                data_type=data_type,
                role="text",
                unique_count=unique_cnt,
                null_count=null_cnt
            )

    @classmethod
    def profile_all_columns(
        cls,
        df: pd.DataFrame,
        profile: DatasetProfile
    ) -> Dict[str, ColumnRoleProfile]:
        total_rows = profile.total_rows
        roles = {}
        for cp in profile.column_profiles:
            series = df[cp.name] if cp.name in df.columns else pd.Series()
            roles[cp.name] = cls.classify_column(cp, total_rows, series)
        return roles

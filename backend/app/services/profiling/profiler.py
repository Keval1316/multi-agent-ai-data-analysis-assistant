import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from backend.app.core.logging import logger
from backend.app.models.profile import (
    NumericStats,
    CategoricalValueFreq,
    CategoricalStats,
    DatetimeStats,
    ColumnProfile,
    DatasetProfile,
)


class DatasetProfiler:
    """Deterministic dataset profiler computing distributions, types, nulls, and statistics."""

    @classmethod
    def infer_semantic_type(cls, series: pd.Series, col_name: str) -> Tuple[str, Optional[pd.Series]]:
        """
        Determines the semantic type of a column:
        'boolean', 'datetime', 'numeric', 'identifier', or 'categorical'.
        Returns (semantic_type, converted_series_or_none).
        """
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        total_len = len(series)
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return "categorical", None

        # 1. Check Boolean
        if series.dtype == bool:
            return "boolean", series

        unique_vals_lower = {str(x).strip().lower() for x in non_null_series.head(100)}
        bool_sets = [
            {"true", "false"},
            {"0", "1"},
            {"yes", "no"},
            {"y", "n"},
            {"t", "f"}
        ]
        if any(unique_vals_lower.issubset(b_set) for b_set in bool_sets):
            return "boolean", None

        # 2. Check Numeric
        if pd.api.types.is_numeric_dtype(series):
            # Check if it's an ID candidate (all unique ints)
            if (
                series.nunique() == total_len
                and ("id" in col_name.lower() or "code" in col_name.lower() or "key" in col_name.lower())
            ):
                return "identifier", series
            return "numeric", series

        # 3. Check Datetime
        # Look for date patterns (YYYY-MM-DD, DD/MM/YYYY, etc.)
        first_few = [str(x).strip() for x in non_null_series.head(20)]
        has_date_delims = any("-" in x or "/" in x or ":" in x for x in first_few)
        if has_date_delims:
            try:
                converted_dt = pd.to_datetime(non_null_series, errors="coerce", format="mixed")
                valid_rate = converted_dt.notna().sum() / len(non_null_series)
                if valid_rate >= 0.8:
                    return "datetime", converted_dt
            except Exception:
                pass

        # 4. Check if string with numeric values (e.g. "$1,200.50" or "45%")
        # Try stripping currency, commas, percentages
        sample_str = [re.sub(r"[$,% ]", "", str(x).strip()) for x in non_null_series.head(30)]
        num_convertible = sum(1 for s in sample_str if re.match(r"^-?\d+(\.\d+)?$", s))
        if num_convertible / len(sample_str) >= 0.8:
            try:
                clean_num_series = pd.to_numeric(
                    non_null_series.astype(str).str.replace(r"[$,% ]", "", regex=True),
                    errors="coerce"
                )
                if clean_num_series.notna().sum() / len(non_null_series) >= 0.8:
                    return "numeric", clean_num_series
            except Exception:
                pass

        # 5. Check Identifier (e.g. ORD-1001, UUID, unique codes)
        if non_null_series.nunique() == total_len and (
            "id" in col_name.lower() or "code" in col_name.lower() or "key" in col_name.lower() or "uuid" in col_name.lower()
        ):
            return "identifier", None

        # Default: Categorical
        return "categorical", None

    @classmethod
    def compute_numeric_stats(cls, series: pd.Series) -> Optional[NumericStats]:
        """Calculates deterministic numerical summary statistics."""
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        clean_s = pd.to_numeric(series, errors="coerce").dropna()
        if len(clean_s) == 0:
            return None

        q25 = float(np.percentile(clean_s, 25))
        median = float(np.percentile(clean_s, 50))
        q75 = float(np.percentile(clean_s, 75))
        iqr = float(q75 - q25)
        std_val = float(clean_s.std()) if len(clean_s) > 1 else 0.0
        skew_val = float(clean_s.skew()) if len(clean_s) > 2 and std_val > 0 else 0.0

        return NumericStats(
            min=float(clean_s.min()),
            max=float(clean_s.max()),
            mean=float(clean_s.mean()),
            median=median,
            std=std_val,
            q25=q25,
            q75=q75,
            iqr=iqr,
            skewness=round(skew_val, 3) if not np.isnan(skew_val) else None
        )

    @classmethod
    def compute_categorical_stats(cls, series: pd.Series, total_rows: int) -> CategoricalStats:
        """Calculates frequency table and cardinality for categorical columns."""
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        non_null = series.dropna().astype(str)
        unique_cnt = int(non_null.nunique())
        val_counts = non_null.value_counts().head(5)

        top_values = [
            CategoricalValueFreq(
                value=str(val),
                count=int(cnt),
                percentage=round((int(cnt) / total_rows) * 100, 2)
            )
            for val, cnt in val_counts.items()
        ]

        is_high_card = unique_cnt > 50 or (total_rows > 10 and (unique_cnt / total_rows) > 0.6)

        return CategoricalStats(
            cardinality=unique_cnt,
            unique_count=unique_cnt,
            top_values=top_values,
            is_high_cardinality=is_high_card
        )

    @classmethod
    def compute_datetime_stats(cls, dt_series: pd.Series) -> Optional[DatetimeStats]:
        """Calculates temporal min, max, and duration."""
        if isinstance(dt_series, pd.DataFrame):
            dt_series = dt_series.iloc[:, 0]
        clean_dt = pd.to_datetime(dt_series, errors="coerce", format="mixed").dropna()
        if len(clean_dt) == 0:
            return None

        min_d = clean_dt.min()
        max_d = clean_dt.max()
        days = (max_d - min_d).total_seconds() / (24 * 3600)

        return DatetimeStats(
            min_date=min_d.isoformat(),
            max_date=max_d.isoformat(),
            days_range=round(days, 2)
        )

    @classmethod
    def profile_dataset(cls, df: pd.DataFrame, dataset_id: str, table_name: str) -> DatasetProfile:
        """Profiles a complete pandas DataFrame deterministically."""
        total_rows = len(df)
        total_cols = len(df.columns)

        # Duplicate rows
        dup_count = int(df.duplicated().sum())
        dup_pct = round((dup_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

        column_profiles: List[ColumnProfile] = []
        num_cols: List[str] = []
        cat_cols: List[str] = []
        dt_cols: List[str] = []
        bool_cols: List[str] = []
        id_cols: List[str] = []

        for idx, col in enumerate(df.columns):
            raw_series = df.iloc[:, idx] if isinstance(df[col], pd.DataFrame) else df[col]
            series = raw_series.iloc[:, 0] if isinstance(raw_series, pd.DataFrame) else raw_series
            null_count = int(series.isna().sum())
            null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            unique_count = int(series.nunique(dropna=True))
            unique_pct = round((unique_count / total_rows) * 100, 2) if total_rows > 0 else 0.0

            semantic_type, converted_series = cls.infer_semantic_type(series, str(col))

            is_id_candidate = (
                (unique_count == total_rows and null_count == 0 and total_rows > 1)
                or semantic_type == "identifier"
            )

            numeric_stats = None
            categorical_stats = None
            datetime_stats = None

            if semantic_type == "numeric":
                target_s = converted_series if converted_series is not None else series
                numeric_stats = cls.compute_numeric_stats(target_s)
                num_cols.append(str(col))
            elif semantic_type == "datetime":
                target_s = converted_series if converted_series is not None else series
                datetime_stats = cls.compute_datetime_stats(target_s)
                dt_cols.append(str(col))
            elif semantic_type == "boolean":
                bool_cols.append(str(col))
            elif semantic_type == "identifier":
                id_cols.append(str(col))
            else:
                cat_cols.append(str(col))

            # Provide categorical stats for all non-numeric columns and low-cardinality numerics
            if semantic_type in ["categorical", "boolean", "identifier"] or (numeric_stats and unique_count <= 10):
                categorical_stats = cls.compute_categorical_stats(series, total_rows)

            sample_vals = [
                str(x) if not isinstance(x, (int, float, bool, str)) else x
                for x in series.dropna().head(3).tolist()
            ]

            column_profiles.append(
                ColumnProfile(
                    name=str(col),
                    original_name=str(col),
                    semantic_type=semantic_type,
                    dtype=str(series.dtype),
                    total_count=total_rows,
                    null_count=null_count,
                    null_percentage=null_pct,
                    unique_count=unique_count,
                    unique_percentage=unique_pct,
                    is_identifier_candidate=is_id_candidate,
                    numeric_stats=numeric_stats,
                    categorical_stats=categorical_stats,
                    datetime_stats=datetime_stats,
                    sample_values=sample_vals
                )
            )

        logger.info(
            f"Profiled dataset '{dataset_id}': {total_rows} rows, {total_cols} cols "
            f"({len(num_cols)} numeric, {len(cat_cols)} categorical, {len(dt_cols)} datetime, {len(bool_cols)} bool, {len(id_cols)} id)"
        )

        return DatasetProfile(
            dataset_id=dataset_id,
            table_name=table_name,
            total_rows=total_rows,
            total_columns=total_cols,
            duplicate_rows_count=dup_count,
            duplicate_rows_percentage=dup_pct,
            column_profiles=column_profiles,
            numeric_column_names=num_cols,
            categorical_column_names=cat_cols,
            datetime_column_names=dt_cols,
            boolean_column_names=bool_cols,
            identifier_column_names=id_cols
        )

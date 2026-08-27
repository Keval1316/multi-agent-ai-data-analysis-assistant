import uuid
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy import stats
from backend.app.core.logging import logger
from backend.app.models.profile import DatasetProfile
from backend.app.models.patterns import (
    TrendPattern,
    ParetoConcentrationPattern,
    AnomalyPattern,
    SeasonalityPattern,
    PatternDetectionResult,
)


class PatternDetector:
    """Deterministic pattern and anomaly detection engine discovering trends, concentrations, and irregularities."""

    @classmethod
    def detect_trends(
        cls,
        df: pd.DataFrame,
        dt_cols: List[str],
        num_cols: List[str]
    ) -> List[TrendPattern]:
        trends = []
        if not num_cols:
            return trends

        # If a datetime column exists, use temporal trend
        time_col = dt_cols[0] if dt_cols else None
        target_df = df.copy()

        if time_col and time_col in target_df.columns:
            raw_t = target_df[time_col]
            t_s = raw_t.iloc[:, 0] if isinstance(raw_t, pd.DataFrame) else raw_t
            target_df[time_col] = pd.to_datetime(t_s, errors="coerce", format="mixed")
            target_df = target_df.dropna(subset=[time_col]).sort_values(by=time_col)

        for n_col in num_cols[:3]:
            if n_col not in target_df.columns or (time_col and n_col == time_col):
                continue

            raw_n = target_df[n_col]
            n_s = raw_n.iloc[:, 0] if isinstance(raw_n, pd.DataFrame) else raw_n
            s = pd.to_numeric(n_s, errors="coerce").dropna()
            if len(s) < 4:
                continue

            x = np.arange(len(s))
            y = s.values

            try:
                slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
                r_sq = round(float(r_val ** 2), 3) if not np.isnan(r_val) else 0.0
                is_sig = bool(p_val < 0.05) if not np.isnan(p_val) else False

                mean_val = float(np.mean(y))
                first_val = float(y[0]) if len(y) > 0 else 1.0
                last_val = float(y[-1]) if len(y) > 0 else 1.0
                growth_pct = round(((last_val - first_val) / max(abs(first_val), 1e-4)) * 100, 2)

                # Classify direction
                normalized_slope = slope / max(mean_val, 1e-4)
                if normalized_slope > 0.02:
                    direction = "increasing"
                elif normalized_slope < -0.02:
                    direction = "decreasing"
                else:
                    direction = "stable"

                dim_label = time_col if time_col else "Sequential Timeline"
                desc = (
                    f"'{n_col}' demonstrates a {direction} trajectory over {dim_label} "
                    f"(growth: {growth_pct:+0.1f}%, R²={r_sq}, p={p_val:.4f})."
                )

                trends.append(
                    TrendPattern(
                        metric_column=n_col,
                        dimension_column=time_col,
                        direction=direction,
                        slope=round(float(slope), 4),
                        r_squared=r_sq,
                        growth_rate_pct=growth_pct,
                        description=desc,
                        is_statistically_significant=is_sig
                    )
                )
            except Exception as e:
                logger.warning(f"Trend detection failed for '{n_col}': {str(e)}")

        return trends

    @classmethod
    def detect_pareto_concentration(
        cls,
        df: pd.DataFrame,
        cat_cols: List[str],
        num_cols: List[str]
    ) -> List[ParetoConcentrationPattern]:
        concentrations = []
        if not cat_cols or not num_cols:
            return concentrations

        for c_col in cat_cols[:2]:
            for n_col in num_cols[:2]:
                if c_col not in df.columns or n_col not in df.columns or c_col == n_col:
                    continue

                raw_c = df[c_col]
                raw_n = df[n_col]
                c_s = raw_c.iloc[:, 0] if isinstance(raw_c, pd.DataFrame) else raw_c
                n_s = raw_n.iloc[:, 0] if isinstance(raw_n, pd.DataFrame) else raw_n

                clean_df = pd.DataFrame({
                    c_col: c_s,
                    n_col: pd.to_numeric(n_s, errors="coerce")
                }).dropna()

                if len(clean_df) < 3:
                    continue

                grouped = clean_df.groupby(c_col)[n_col].sum().sort_values(ascending=False)
                total_sum = grouped.sum()
                if total_sum <= 0 or len(grouped) <= 1:
                    continue

                total_categories = len(grouped)
                # Take top 20% of categories (or top 1 if small)
                top_k = max(1, int(np.ceil(total_categories * 0.2)))
                top_sum = grouped.iloc[:top_k].sum()
                share_pct = round((top_sum / total_sum) * 100, 2)
                top_names = [str(x) for x in grouped.index[:top_k].tolist()]

                # Pareto dominated if top 20% holds >= 50-60% of volume
                is_pareto = share_pct >= 50.0

                desc = (
                    f"Top {top_k} of {total_categories} {c_col} categories ({', '.join(top_names[:2])}) "
                    f"account for {share_pct}% of total {n_col}."
                )

                concentrations.append(
                    ParetoConcentrationPattern(
                        dimension_column=c_col,
                        metric_column=n_col,
                        top_categories_count=top_k,
                        top_categories_share_pct=share_pct,
                        total_categories_count=total_categories,
                        top_category_names=top_names,
                        is_pareto_dominated=is_pareto,
                        description=desc
                    )
                )

        return concentrations

    @classmethod
    def detect_anomalies(
        cls,
        df: pd.DataFrame,
        num_cols: List[str],
        id_cols: List[str]
    ) -> List[AnomalyPattern]:
        anomalies = []
        id_col = id_cols[0] if id_cols and id_cols[0] in df.columns else None

        for n_col in num_cols[:3]:
            if n_col not in df.columns:
                continue

            raw_n = df[n_col]
            n_s = raw_n.iloc[:, 0] if isinstance(raw_n, pd.DataFrame) else raw_n
            s = pd.to_numeric(n_s, errors="coerce").dropna()
            if len(s) < 5:
                continue

            mean_val = float(s.mean())
            std_val = float(s.std())
            median_val = float(s.median())

            if std_val == 0:
                continue

            # Z-score computation
            z_scores = (s - mean_val) / std_val
            outlier_indices = s[z_scores.abs() >= 2.8].index

            for idx in outlier_indices[:3]:  # Top 3 per column
                val = float(s.loc[idx])
                z = float(z_scores.loc[idx])
                row_id = str(df.loc[idx, id_col]) if id_col else f"Row {idx + 1}"
                factor = round(val / max(abs(median_val), 1e-4), 1)

                severity = "high" if abs(z) >= 4.0 or factor > 10 else "medium"
                desc = (
                    f"Extreme anomalous value of {val:,.2f} detected in '{n_col}' ({row_id}) "
                    f"with a z-score of {z:+.2f} ({factor}x the median)."
                )

                anomalies.append(
                    AnomalyPattern(
                        id=f"anomaly_{uuid.uuid4().hex[:6]}",
                        metric_column=n_col,
                        row_identifier=row_id,
                        value=val,
                        z_score=round(z, 2),
                        deviation_factor=factor,
                        description=desc,
                        severity=severity
                    )
                )

        return anomalies

    @classmethod
    def detect_seasonality(
        cls,
        df: pd.DataFrame,
        dt_cols: List[str],
        num_cols: List[str]
    ) -> List[SeasonalityPattern]:
        seasonality = []
        if not dt_cols or not num_cols:
            return seasonality

        time_col = dt_cols[0]
        if time_col not in df.columns:
            return seasonality

        for n_col in num_cols[:2]:
            if n_col not in df.columns or n_col == time_col:
                continue

            raw_t = df[time_col]
            raw_n = df[n_col]
            t_s = raw_t.iloc[:, 0] if isinstance(raw_t, pd.DataFrame) else raw_t
            n_s = raw_n.iloc[:, 0] if isinstance(raw_n, pd.DataFrame) else raw_n

            valid_df = pd.DataFrame({
                time_col: pd.to_datetime(t_s, errors="coerce", format="mixed"),
                n_col: pd.to_numeric(n_s, errors="coerce")
            }).dropna()

            if len(valid_df) < 7:
                continue

            # Day of week analysis
            valid_df["day_of_week"] = valid_df[time_col].dt.day_name()
            dow_grouped = valid_df.groupby("day_of_week")[n_col].mean()

            if len(dow_grouped) >= 3:
                peak_day = str(dow_grouped.idxmax())
                trough_day = str(dow_grouped.idxmin())
                peak_val = float(dow_grouped.max())
                trough_val = float(dow_grouped.min())

                ratio = round(peak_val / max(trough_val, 1e-4), 2) if trough_val > 0 else 1.0

                desc = (
                    f"Day-of-week pattern in '{n_col}': Peak activity occurs on {peak_day} "
                    f"({peak_val:,.2f} avg) compared to lowest on {trough_day} ({trough_val:,.2f} avg), a {ratio}x variance."
                )

                seasonality.append(
                    SeasonalityPattern(
                        datetime_column=time_col,
                        metric_column=n_col,
                        period_type="day_of_week",
                        peak_period=peak_day,
                        trough_period=trough_day,
                        peak_to_trough_ratio=ratio,
                        description=desc
                    )
                )

        return seasonality

    @classmethod
    def detect_all(
        cls,
        df: pd.DataFrame,
        profile: DatasetProfile
    ) -> PatternDetectionResult:
        logger.info(f"Running deterministic pattern detection on table '{profile.table_name}'")

        dt_cols = profile.datetime_column_names
        num_cols = profile.numeric_column_names
        cat_cols = profile.categorical_column_names
        id_cols = profile.identifier_column_names

        trends = cls.detect_trends(df, dt_cols, num_cols)
        concentrations = cls.detect_pareto_concentration(df, cat_cols, num_cols)
        anomalies = cls.detect_anomalies(df, num_cols, id_cols)
        seasonality = cls.detect_seasonality(df, dt_cols, num_cols)

        # Synthesize top key findings
        findings = []
        for t in trends[:2]:
            findings.append(t.description)
        for c in concentrations[:2]:
            findings.append(c.description)
        for a in anomalies[:2]:
            findings.append(a.description)
        for s in seasonality[:1]:
            findings.append(s.description)

        logger.info(
            f"Pattern detection completed: {len(trends)} trends, {len(concentrations)} concentrations, "
            f"{len(anomalies)} anomalies, {len(seasonality)} seasonal patterns."
        )

        return PatternDetectionResult(
            dataset_id=profile.dataset_id,
            trends=trends,
            concentrations=concentrations,
            anomalies=anomalies,
            seasonality=seasonality,
            key_findings=findings
        )

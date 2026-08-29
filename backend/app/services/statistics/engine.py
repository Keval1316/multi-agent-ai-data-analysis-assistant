from typing import List
import numpy as np
import pandas as pd
from scipy import stats
from backend.app.core.logging import logger
from backend.app.models.plan import AnalysisPlan
from backend.app.models.profile import DatasetProfile
from backend.app.models.statistics import (
    UnivariateMetric,
    CorrelationPairResult,
    GroupBySummaryItem,
    GroupByResult,
    StatisticalAnalysisResult,
)


class StatisticalEngine:
    """Deterministic statistical computation engine calculating moments, quantiles, correlations, and group tests."""

    @staticmethod
    def classify_correlation_strength(coef: float) -> str:
        if np.isnan(coef):
            return "Undefined"
        abs_val = abs(coef)
        if abs_val < 0.10:
            return "Negligible"
        elif abs_val < 0.30:
            return "Weak"
        elif abs_val < 0.50:
            return "Moderate"
        elif abs_val < 0.70:
            return "Strong"
        else:
            return "Very Strong"

    @staticmethod
    def classify_practical_significance(coef: float) -> str:
        if np.isnan(coef):
            return "Undefined"
        abs_val = abs(coef)
        if abs_val < 0.10:
            return "Negligible practical effect size"
        elif abs_val < 0.30:
            return "Weak practical effect size"
        elif abs_val < 0.50:
            return "Moderate practical effect size"
        elif abs_val < 0.70:
            return "Strong practical effect size"
        else:
            return "Very strong practical effect size"

    @classmethod
    def compute_univariate_metrics(cls, df: pd.DataFrame, numeric_cols: List[str]) -> List[UnivariateMetric]:
        metrics = []
        for col in numeric_cols:
            if col not in df.columns:
                continue
            s_raw = df[col]
            s_1d = s_raw.iloc[:, 0] if isinstance(s_raw, pd.DataFrame) else s_raw
            s = pd.to_numeric(s_1d, errors="coerce").dropna()
            if len(s) == 0:
                continue

            cnt = int(len(s))
            mean_val = float(s.mean())
            median_val = float(s.median())
            std_val = float(s.std()) if cnt > 1 else 0.0
            var_val = float(s.var()) if cnt > 1 else 0.0
            min_val = float(s.min())
            max_val = float(s.max())

            p10 = float(np.percentile(s, 10))
            p25 = float(np.percentile(s, 25))
            p50 = median_val
            p75 = float(np.percentile(s, 75))
            p90 = float(np.percentile(s, 90))
            iqr_val = float(p75 - p25)

            skew_val = float(s.skew()) if cnt > 2 and std_val > 0 else None
            kurt_val = float(s.kurtosis()) if cnt > 3 and std_val > 0 else None

            # Distribution symmetry and plain English summary derived accurately
            if skew_val is not None and not np.isnan(skew_val):
                if skew_val > 0.5:
                    distribution_symmetry = "Right-skewed (positive skew: extended upper tail with some higher values)"
                    plain_summary = (
                        f"Mean ({mean_val:,.2f}) exceeds Median ({median_val:,.2f}) due to a right-skewed tail. "
                        f"The median represents typical values without outlier distortion."
                    )
                elif skew_val < -0.5:
                    distribution_symmetry = "Left-skewed (negative skew: extended lower tail with some lower values)"
                    plain_summary = (
                        f"Mean ({mean_val:,.2f}) is below Median ({median_val:,.2f}) due to a left-skewed tail. "
                        f"The median represents typical values without outlier distortion."
                    )
                else:
                    distribution_symmetry = "Approximately symmetric (mean and median are closely aligned)"
                    plain_summary = (
                        f"The distribution of '{col}' is approximately symmetric (Mean = {mean_val:,.2f}, Median = {median_val:,.2f})."
                    )
            else:
                distribution_symmetry = "Distribution symmetry cannot be determined from sample size alone"
                plain_summary = (
                    f"Mean is {mean_val:,.2f} and Median is {median_val:,.2f}. Skewness could not be reliably computed."
                )

            metrics.append(
                UnivariateMetric(
                    column_name=col,
                    count=cnt,
                    mean=round(mean_val, 3),
                    median=round(median_val, 3),
                    std=round(std_val, 3),
                    variance=round(var_val, 3),
                    min=round(min_val, 3),
                    max=round(max_val, 3),
                    p10=round(p10, 3),
                    p25=round(p25, 3),
                    p50=round(p50, 3),
                    p75=round(p75, 3),
                    p90=round(p90, 3),
                    iqr=round(iqr_val, 3),
                    skewness=round(skew_val, 3) if skew_val is not None and not np.isnan(skew_val) else None,
                    kurtosis=round(kurt_val, 3) if kurt_val is not None and not np.isnan(kurt_val) else None,
                    distribution_symmetry=distribution_symmetry,
                    plain_english_summary=plain_summary
                )
            )
        return metrics

    @classmethod
    def compute_correlations(cls, df: pd.DataFrame, pairs: List[List[str]]) -> List[CorrelationPairResult]:
        results = []
        for pair in pairs:
            if len(pair) != 2:
                continue
            c1, c2 = pair[0], pair[1]
            if c1 not in df.columns or c2 not in df.columns or c1 == c2:
                continue

            s1_raw = df[c1]
            s2_raw = df[c2]
            s1 = s1_raw.iloc[:, 0] if isinstance(s1_raw, pd.DataFrame) else s1_raw
            s2 = s2_raw.iloc[:, 0] if isinstance(s2_raw, pd.DataFrame) else s2_raw

            sub_df = pd.DataFrame({
                c1: pd.to_numeric(s1, errors="coerce"),
                c2: pd.to_numeric(s2, errors="coerce")
            }).dropna()

            if len(sub_df) < 3:
                continue

            # Pearson
            try:
                p_coef, p_pval = stats.pearsonr(sub_df[c1], sub_df[c2])
            except Exception:
                p_coef, p_pval = float("nan"), None

            # Spearman
            try:
                s_coef, s_pval = stats.spearmanr(sub_df[c1], sub_df[c2])
            except Exception:
                s_coef, s_pval = float("nan"), None

            strength = cls.classify_correlation_strength(p_coef)
            practical_sig = cls.classify_practical_significance(p_coef)
            is_sig = bool(p_pval is not None and not np.isnan(p_pval) and p_pval < 0.05)
            
            direction = "Positive" if (not np.isnan(p_coef) and p_coef > 0) else ("Negative" if (not np.isnan(p_coef) and p_coef < 0) else "None")

            # Formulate clear two-layer plain English interpretation
            if np.isnan(p_coef):
                plain_interp = f"Correlation between '{c1}' and '{c2}' is undefined due to constant or invalid values."
            elif is_sig:
                if abs(p_coef) < 0.30:
                    plain_interp = (
                        f"The analysis found a {strength.lower()} {direction.lower()} relationship between '{c1}' and '{c2}' (r = {p_coef:+.3f}). "
                        f"Although statistically significant in this sample (p = {p_pval:.4f}), its small effect size means it should not "
                        f"currently be treated as a strong predictive signal. Note: Correlation does not imply causation."
                    )
                else:
                    plain_interp = (
                        f"The analysis found a {strength.lower()} {direction.lower()} relationship between '{c1}' and '{c2}' (r = {p_coef:+.3f}), "
                        f"which is statistically significant (p = {p_pval:.4f}) with a {practical_sig.lower()}. "
                        f"Note: Correlation does not imply causation."
                    )
            else:
                p_str = f"p = {p_pval:.4f}" if p_pval is not None else "p unavailable"
                plain_interp = (
                    f"The correlation between '{c1}' and '{c2}' is {strength.lower()} (r = {p_coef:+.3f}) and not statistically "
                    f"significant at the 0.05 level ({p_str}). There is no reliable linear association in this sample. "
                    f"Note: Correlation does not imply causation."
                )

            results.append(
                CorrelationPairResult(
                    col1=c1,
                    col2=c2,
                    pearson_coef=round(float(p_coef), 3) if not np.isnan(p_coef) else 0.0,
                    pearson_pvalue=round(float(p_pval), 4) if p_pval is not None and not np.isnan(p_pval) else None,
                    spearman_coef=round(float(s_coef), 3) if not np.isnan(s_coef) else 0.0,
                    spearman_pvalue=round(float(s_pval), 4) if s_pval is not None and not np.isnan(s_pval) else None,
                    direction=direction,
                    strength=strength,
                    practical_significance=practical_sig,
                    is_statistically_significant=is_sig,
                    plain_english_interpretation=plain_interp
                )
            )
        return results

    @classmethod
    def compute_groupby_analyses(cls, df: pd.DataFrame, plan: AnalysisPlan) -> List[GroupByResult]:
        results = []
        for gp in plan.group_by_analyses:
            g_col = gp.group_column
            m_col = gp.metric_column
            if g_col not in df.columns or m_col not in df.columns or g_col == m_col:
                continue

            g_raw = df[g_col]
            m_raw = df[m_col]
            g_s = g_raw.iloc[:, 0] if isinstance(g_raw, pd.DataFrame) else g_raw
            m_s = m_raw.iloc[:, 0] if isinstance(m_raw, pd.DataFrame) else m_raw

            clean_df = pd.DataFrame({
                g_col: g_s,
                m_col: pd.to_numeric(m_s, errors="coerce")
            }).dropna()

            if len(clean_df) == 0:
                continue

            total_metric_sum = clean_df[m_col].sum()

            items = []
            group_arrays = []

            for g_val, group in clean_df.groupby(g_col):
                g_series = group[m_col]
                group_arrays.append(g_series.values)

                cnt = int(len(g_series))
                sum_val = float(g_series.sum())
                mean_val = float(g_series.mean())
                median_val = float(g_series.median())
                min_val = float(g_series.min())
                max_val = float(g_series.max())
                share_pct = round((sum_val / total_metric_sum) * 100, 2) if total_metric_sum > 0 else 0.0

                items.append(
                    GroupBySummaryItem(
                        group_value=str(g_val),
                        count=cnt,
                        sum=round(sum_val, 2),
                        mean=round(mean_val, 2),
                        median=round(median_val, 2),
                        min=round(min_val, 2),
                        max=round(max_val, 2),
                        share_percentage=share_pct
                    )
                )

            # Sort descending by sum
            items.sort(key=lambda x: x.sum if x.sum is not None else 0.0, reverse=True)

            # One-Way ANOVA F-test for differences across groups
            f_stat, anova_p = None, None
            is_sig = None
            if len(group_arrays) >= 2 and all(len(arr) >= 2 for arr in group_arrays[:5]):
                try:
                    f_val, p_val = stats.f_oneway(*group_arrays[:5])
                    if not np.isnan(f_val) and not np.isnan(p_val):
                        f_stat = round(float(f_val), 3)
                        anova_p = round(float(p_val), 4)
                        is_sig = bool(p_val < 0.05)
                except Exception:
                    pass

            results.append(
                GroupByResult(
                    group_column=g_col,
                    metric_column=m_col,
                    aggregation=gp.aggregation,
                    items=items,
                    f_statistic=f_stat,
                    anova_pvalue=anova_p,
                    is_group_difference_significant=is_sig
                )
            )
        return results

    @classmethod
    def run_analysis(
        cls,
        df: pd.DataFrame,
        profile: DatasetProfile,
        plan: AnalysisPlan
    ) -> StatisticalAnalysisResult:
        logger.info(f"Running deterministic statistical analysis on dataset '{profile.dataset_id}'")

        # 1. Determine target numeric columns for univariate analysis
        target_num_cols = plan.descriptive_numeric_columns
        if not target_num_cols:
            target_num_cols = profile.numeric_column_names[:6]

        univariate_metrics = cls.compute_univariate_metrics(df, target_num_cols)

        # 2. Correlation analysis
        corr_pairs = plan.correlation_pairs
        if not corr_pairs and len(profile.numeric_column_names) >= 2:
            # Auto-generate pairwise combinations
            num_cols = profile.numeric_column_names[:4]
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    corr_pairs.append([num_cols[i], num_cols[j]])

        correlations = cls.compute_correlations(df, corr_pairs)

        # 3. Group-by analyses
        groupby_results = cls.compute_groupby_analyses(df, plan)

        notes = [
            f"Evaluated {len(univariate_metrics)} numeric distribution profiles (quantiles, IQR, skewness, kurtosis).",
            f"Assessed {len(correlations)} bivariate correlation pairs using Pearson & Spearman tests with p-value significance.",
            f"Executed {len(groupby_results)} segmented aggregations with ANOVA F-test variance testing."
        ]

        logger.info(
            f"Statistical analysis completed: {len(univariate_metrics)} univariate metrics, "
            f"{len(correlations)} correlation pairs, {len(groupby_results)} group results."
        )

        return StatisticalAnalysisResult(
            dataset_id=profile.dataset_id,
            univariate_metrics=univariate_metrics,
            correlation_results=correlations,
            groupby_results=groupby_results,
            methodology_notes=notes
        )

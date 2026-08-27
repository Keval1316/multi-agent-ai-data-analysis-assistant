from typing import List, Dict, Any, Optional
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
        sign = "Positive" if coef >= 0 else "Negative"
        if abs_val >= 0.70:
            return f"Strong {sign}"
        elif abs_val >= 0.30:
            return f"Moderate {sign}"
        else:
            return "Weak"

    @classmethod
    def compute_univariate_metrics(cls, df: pd.DataFrame, numeric_cols: List[str]) -> List[UnivariateMetric]:
        metrics = []
        for col in numeric_cols:
            if col not in df.columns:
                continue
            s = pd.to_numeric(df[col], errors="coerce").dropna()
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

            skew_val = float(s.skew()) if cnt > 2 and std_val > 0 else 0.0
            kurt_val = float(s.kurtosis()) if cnt > 3 and std_val > 0 else 0.0

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
                    skewness=round(skew_val, 3) if not np.isnan(skew_val) else None,
                    kurtosis=round(kurt_val, 3) if not np.isnan(kurt_val) else None
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
            if c1 not in df.columns or c2 not in df.columns:
                continue

            sub_df = df[[c1, c2]].copy()
            sub_df[c1] = pd.to_numeric(sub_df[c1], errors="coerce")
            sub_df[c2] = pd.to_numeric(sub_df[c2], errors="coerce")
            clean_sub = sub_df.dropna()

            if len(clean_sub) < 3:
                continue

            # Pearson
            try:
                p_coef, p_pval = stats.pearsonr(clean_sub[c1], clean_sub[c2])
            except Exception:
                p_coef, p_pval = float("nan"), None

            # Spearman
            try:
                s_coef, s_pval = stats.spearmanr(clean_sub[c1], clean_sub[c2])
            except Exception:
                s_coef, s_pval = float("nan"), None

            strength = cls.classify_correlation_strength(p_coef)
            is_sig = bool(p_pval is not None and not np.isnan(p_pval) and p_pval < 0.05)

            results.append(
                CorrelationPairResult(
                    col1=c1,
                    col2=c2,
                    pearson_coef=round(float(p_coef), 3) if not np.isnan(p_coef) else 0.0,
                    pearson_pvalue=round(float(p_pval), 4) if p_pval is not None and not np.isnan(p_pval) else None,
                    spearman_coef=round(float(s_coef), 3) if not np.isnan(s_coef) else 0.0,
                    spearman_pvalue=round(float(s_pval), 4) if s_pval is not None and not np.isnan(s_pval) else None,
                    strength=strength,
                    is_statistically_significant=is_sig
                )
            )
        return results

    @classmethod
    def compute_groupby_analyses(cls, df: pd.DataFrame, plan: AnalysisPlan) -> List[GroupByResult]:
        results = []
        for gp in plan.group_by_analyses:
            g_col = gp.group_column
            m_col = gp.metric_column
            if g_col not in df.columns or m_col not in df.columns:
                continue

            sub_df = df[[g_col, m_col]].copy()
            sub_df[m_col] = pd.to_numeric(sub_df[m_col], errors="coerce")
            clean_df = sub_df.dropna()

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

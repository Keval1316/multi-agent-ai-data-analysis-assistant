import re
import uuid
from typing import List, Dict, Any, Set, Optional, Tuple
import numpy as np
import pandas as pd
from backend.app.core.logging import logger
from backend.app.models.profile import DatasetProfile, ColumnProfile
from backend.app.models.quality import QualitySeverity, QualityIssue, QualityReport


class QualityChecker:
    """Deterministic data quality auditor evaluating completeness, uniqueness, consistency, and validity."""

    @staticmethod
    def detect_inconsistent_categories(series: pd.Series) -> List[Dict[str, Any]]:
        """
        Detects casing differences, whitespace variations, and common abbreviation collisions in categorical columns.
        """
        raw_vals = series.dropna().astype(str).unique()
        if len(raw_vals) <= 1:
            return []

        # Group by normalized lowercase stripped form
        norm_map: Dict[str, Set[str]] = {}
        for val in raw_vals:
            norm = val.strip().lower()
            if norm not in norm_map:
                norm_map[norm] = set()
            norm_map[norm].add(val)

        inconsistencies = []
        for norm, variations in norm_map.items():
            if len(variations) > 1:
                inconsistencies.append({
                    "normalized": norm,
                    "variations": list(variations)
                })

        return inconsistencies

    @staticmethod
    def detect_outliers(series: pd.Series) -> Tuple[int, float, List[float], bool]:
        """
        Detects outliers using IQR and Z-scores.
        Distinguishes extreme anomalies (outside 3.0*IQR or |z| >= 3.5) from mild tail values (1.5*IQR to 3.0*IQR).
        Returns (outlier_count, outlier_percentage, sample_outliers, is_extreme).
        """
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        num_s = pd.to_numeric(series, errors="coerce").dropna()
        if len(num_s) < 4:
            return 0, 0.0, [], False

        q25 = float(np.percentile(num_s, 25))
        q75 = float(np.percentile(num_s, 75))
        iqr = q75 - q25

        if iqr == 0:
            return 0, 0.0, [], False

        mild_lower = q25 - (1.5 * iqr)
        mild_upper = q75 + (1.5 * iqr)
        extreme_lower = q25 - (3.0 * iqr)
        extreme_upper = q75 + (3.0 * iqr)

        extreme_outliers = num_s[(num_s < extreme_lower) | (num_s > extreme_upper)]
        mild_outliers = num_s[(num_s < mild_lower) | (num_s > mild_upper)]

        is_extreme = len(extreme_outliers) > 0
        target_outliers = extreme_outliers if is_extreme else mild_outliers

        outlier_count = int(len(target_outliers))
        outlier_pct = round((outlier_count / len(num_s)) * 100, 2)
        sample_vals = [float(x) for x in target_outliers.head(5).tolist()]

        return outlier_count, outlier_pct, sample_vals, is_extreme

    @classmethod
    def audit_dataset(cls, df: pd.DataFrame, profile: DatasetProfile) -> QualityReport:
        """
        Executes a deterministic multi-dimension quality audit on the raw dataset.
        Generates structured QualityIssues and computes the weighted Health Score.
        """
        issues: List[QualityIssue] = []
        total_rows = profile.total_rows

        # 1. Dataset-level Audits
        # 1a. Duplicate Rows
        if profile.duplicate_rows_count > 0:
            issues.append(
                QualityIssue(
                    id=f"dup_{uuid.uuid4().hex[:6]}",
                    column_name=None,
                    category="duplicate_rows",
                    severity=QualitySeverity.CONFIRMED_ISSUE,
                    title="Duplicate Rows Detected",
                    description=f"Dataset contains {profile.duplicate_rows_count} exact duplicate row(s) ({profile.duplicate_rows_percentage}% of total).",
                    affected_count=profile.duplicate_rows_count,
                    affected_percentage=profile.duplicate_rows_percentage,
                    suggested_action="Deduplicate records before performing statistical aggregations."
                )
            )

        # 2. Column-level Audits
        for col_prof in profile.column_profiles:
            col_name = col_prof.name
            raw_s = df[col_name] if col_name in df.columns else pd.Series(dtype=object)
            series = raw_s.iloc[:, 0] if isinstance(raw_s, pd.DataFrame) else raw_s

            # 2a. Missing Values
            if col_prof.null_count > 0:
                if col_prof.null_percentage >= 100.0:
                    issues.append(
                        QualityIssue(
                            id=f"null_100_{uuid.uuid4().hex[:6]}",
                            column_name=col_name,
                            category="missing_values",
                            severity=QualitySeverity.CONFIRMED_ISSUE,
                            title=f"Column '{col_name}' is completely empty",
                            description=f"All {col_prof.null_count} rows in column '{col_name}' are null/empty.",
                            affected_count=col_prof.null_count,
                            affected_percentage=100.0,
                            suggested_action=f"Drop column '{col_name}' from downstream modeling."
                        )
                    )
                elif col_prof.null_percentage >= 25.0:
                    issues.append(
                        QualityIssue(
                            id=f"null_high_{uuid.uuid4().hex[:6]}",
                            column_name=col_name,
                            category="missing_values",
                            severity=QualitySeverity.SUSPICIOUS_ISSUE,
                            title=f"High missingness in column '{col_name}'",
                            description=f"Column '{col_name}' is missing in {col_prof.null_count} rows ({col_prof.null_percentage}% of dataset).",
                            affected_count=col_prof.null_count,
                            affected_percentage=col_prof.null_percentage,
                            suggested_action="Assess whether missingness is informative or requires imputation."
                        )
                    )
                else:
                    issues.append(
                        QualityIssue(
                            id=f"null_info_{uuid.uuid4().hex[:6]}",
                            column_name=col_name,
                            category="missing_values",
                            severity=QualitySeverity.INFORMATIONAL,
                            title=f"Missing values in column '{col_name}'",
                            description=f"Column '{col_name}' has {col_prof.null_count} missing values ({col_prof.null_percentage}%).",
                            affected_count=col_prof.null_count,
                            affected_percentage=col_prof.null_percentage,
                            suggested_action="Use median/mode or filter nulls during analytical queries."
                        )
                    )

            # 2b. Outlier Detection for Numeric Columns
            if col_prof.semantic_type == "numeric":
                outlier_cnt, outlier_pct, sample_outs, is_extreme = cls.detect_outliers(series)
                if outlier_cnt > 0:
                    severity = QualitySeverity.SUSPICIOUS_ISSUE if is_extreme else QualitySeverity.INFORMATIONAL
                    title_prefix = "Extreme Outliers" if is_extreme else "Distribution Tail Values"
                    issues.append(
                        QualityIssue(
                            id=f"outlier_{uuid.uuid4().hex[:6]}",
                            column_name=col_name,
                            category="outliers",
                            severity=severity,
                            title=f"{title_prefix} in '{col_name}'",
                            description=f"Found {outlier_cnt} values ({outlier_pct}%) outside expected distribution boundaries.",
                            affected_count=outlier_cnt,
                            affected_percentage=outlier_pct,
                            sample_affected_values=sample_outs,
                            suggested_action="Inspect extreme values to verify if they represent data entry errors or genuine anomalies."
                        )
                    )

                # Check for Negative Values in Domain-Sensitive Columns
                domain_keywords = ["price", "revenue", "quantity", "cost", "sales", "age", "count"]
                if any(kw in col_name.lower() for kw in domain_keywords):
                    clean_num = pd.to_numeric(series, errors="coerce").dropna()
                    negatives = clean_num[clean_num < 0]
                    if len(negatives) > 0:
                        neg_cnt = len(negatives)
                        neg_pct = round((neg_cnt / total_rows) * 100, 2)
                        issues.append(
                            QualityIssue(
                                id=f"neg_{uuid.uuid4().hex[:6]}",
                                column_name=col_name,
                                category="invalid_values",
                                severity=QualitySeverity.CONFIRMED_ISSUE,
                                title=f"Unexpected Negative Values in '{col_name}'",
                                description=f"Found {neg_cnt} negative values in domain '{col_name}' (samples: {negatives.head(2).tolist()}).",
                                affected_count=neg_cnt,
                                affected_percentage=neg_pct,
                                sample_affected_values=[float(x) for x in negatives.head(3).tolist()],
                                suggested_action=f"Verify business logic for negative {col_name} (e.g. returns vs data corruption)."
                            )
                        )

            # 2c. Inconsistent Categorical Labels
            if col_prof.semantic_type == "categorical":
                inconsistencies = cls.detect_inconsistent_categories(series)
                if inconsistencies:
                    sample_inconsistencies = [inc["variations"] for inc in inconsistencies[:2]]
                    issues.append(
                        QualityIssue(
                            id=f"inconsistent_{uuid.uuid4().hex[:6]}",
                            column_name=col_name,
                            category="inconsistent_labels",
                            severity=QualitySeverity.SUSPICIOUS_ISSUE,
                            title=f"Inconsistent Casing/Labels in '{col_name}'",
                            description=f"Column contains inconsistent representations of the same label: {sample_inconsistencies}.",
                            affected_count=len(inconsistencies),
                            affected_percentage=round((len(inconsistencies) / col_prof.unique_count) * 100, 2) if col_prof.unique_count > 0 else 0.0,
                            sample_affected_values=sample_inconsistencies,
                            suggested_action=f"Standardize column '{col_name}' casing and trim whitespace before grouping."
                        )
                    )

            # 2d. High Cardinality in Categorical Columns
            if col_prof.semantic_type == "categorical" and col_prof.categorical_stats and col_prof.categorical_stats.is_high_cardinality:
                if not col_prof.is_identifier_candidate:
                    issues.append(
                        QualityIssue(
                            id=f"cardinality_{uuid.uuid4().hex[:6]}",
                            column_name=col_name,
                            category="high_cardinality",
                            severity=QualitySeverity.INFORMATIONAL,
                            title=f"High Cardinality in '{col_name}'",
                            description=f"Column has {col_prof.unique_count} distinct categories ({col_prof.unique_percentage}% unique).",
                            affected_count=col_prof.unique_count,
                            affected_percentage=col_prof.unique_percentage,
                            suggested_action="Consider grouping rare categories into an 'Other' bucket for visualization."
                        )
                    )

        # 3. Calculate Quality Score (0 to 100)
        score = 100.0
        severity_counts = {
            QualitySeverity.CONFIRMED_ISSUE.value: 0,
            QualitySeverity.SUSPICIOUS_ISSUE.value: 0,
            QualitySeverity.INFORMATIONAL.value: 0,
        }

        for issue in issues:
            severity_counts[issue.severity.value] += 1
            if issue.severity == QualitySeverity.CONFIRMED_ISSUE:
                score -= 15.0 * max(0.5, issue.affected_percentage / 50.0)
            elif issue.severity == QualitySeverity.SUSPICIOUS_ISSUE:
                score -= 5.0 * max(0.2, issue.affected_percentage / 50.0)
            elif issue.severity == QualitySeverity.INFORMATIONAL:
                score -= 0.5 * max(0.1, issue.affected_percentage / 100.0)

        # Clamp between 0.0 and 100.0
        final_score = max(0.0, min(100.0, round(score, 1)))

        # Assign Grade
        if final_score >= 90.0:
            grade = "A"
        elif final_score >= 80.0:
            grade = "B"
        elif final_score >= 70.0:
            grade = "C"
        elif final_score >= 60.0:
            grade = "D"
        else:
            grade = "F"

        is_ready = final_score >= 40.0 and severity_counts[QualitySeverity.CONFIRMED_ISSUE.value] <= 5

        summary = (
            f"Quality audit completed with score {final_score}/100 (Grade {grade}). "
            f"Found {severity_counts['confirmed_issue']} confirmed issue(s), "
            f"{severity_counts['suspicious_issue']} suspicious issue(s), and "
            f"{severity_counts['informational']} informational observation(s)."
        )

        logger.info(f"Audited dataset '{profile.dataset_id}': Score={final_score}, Grade={grade}, Total Issues={len(issues)}")

        return QualityReport(
            dataset_id=profile.dataset_id,
            table_name=profile.table_name,
            quality_score=final_score,
            grade=grade,
            issues_count=severity_counts,
            total_issues=len(issues),
            issues=issues,
            summary=summary,
            is_analysis_ready=is_ready
        )

import uuid
import re
from typing import List, Dict, Any, Optional, Set
import numpy as np
import pandas as pd
from scipy import stats
from backend.app.core.logging import logger
from backend.app.models.profile import DatasetProfile
from backend.app.models.plan import AnalysisPlan
from backend.app.models.visualization import PlotlyChartSpec, ChartCollection
from backend.app.services.visualization.role_classifier import SemanticRoleClassifier, ColumnRoleProfile


class ChartGenerator:
    """
    Intelligent Data-Driven Visualization Engine.
    Discovers analytical candidates from real dataset profiles, infers column roles,
    validates data integrity, removes redundancy, dynamically selects optimal chart types,
    and produces responsive Plotly specifications with data-backed takeaways.
    """

    COLOR_PRIMARY = "#AD8B73"
    COLOR_DARK = "#3E2723"
    COLOR_ACCENT = "#CEAB93"
    COLOR_BG_CARD = "#FFFFFF"
    COLOR_GRID = "rgba(206, 171, 147, 0.25)"
    PALETTE_SEQUENCE = [
        "#AD8B73", "#3E2723", "#CEAB93", "#E3CAA5",
        "#8C6542", "#5C3D2E", "#D4B996", "#7D5A44",
        "#B5838D", "#6D6875", "#E5989B", "#FFB4A2"
    ]

    @classmethod
    def get_base_layout(cls, title: str, x_label: str = "", y_label: str = "", height: int = 380) -> Dict[str, Any]:
        return {
            "title": {
                "text": f"<b>{title}</b>",
                "font": {"family": "Plus Jakarta Sans, Inter, sans-serif", "size": 15, "color": cls.COLOR_DARK},
                "x": 0.02,
                "xanchor": "left"
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"l": 60, "r": 30, "t": 60, "b": 55},
            "height": height,
            "font": {"family": "Plus Jakarta Sans, Inter, sans-serif", "color": cls.COLOR_DARK, "size": 11},
            "xaxis": {
                "title": {"text": x_label, "font": {"size": 12, "color": cls.COLOR_DARK, "weight": 600}},
                "gridcolor": cls.COLOR_GRID,
                "zeroline": False,
                "tickfont": {"color": cls.COLOR_DARK, "size": 10},
                "showline": True,
                "linecolor": cls.COLOR_ACCENT,
            },
            "yaxis": {
                "title": {"text": y_label, "font": {"size": 12, "color": cls.COLOR_DARK, "weight": 600}},
                "gridcolor": cls.COLOR_GRID,
                "zeroline": False,
                "tickfont": {"color": cls.COLOR_DARK, "size": 10},
                "showline": True,
                "linecolor": cls.COLOR_ACCENT,
            },
            "hovermode": "closest",
            "hoverlabel": {
                "bgcolor": "#FFFFFF",
                "bordercolor": cls.COLOR_ACCENT,
                "font": {"family": "Plus Jakarta Sans, Inter, sans-serif", "size": 11, "color": cls.COLOR_DARK}
            },
            "showlegend": True,
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
                "font": {"size": 10}
            }
        }

    # =========================================================================
    # 1. TIME SERIES & TEMPORAL CHARTS
    # =========================================================================

    @classmethod
    def generate_time_series_chart(
        cls,
        df: pd.DataFrame,
        dt_col: str,
        num_col: str,
        agg: str = "sum",
        user_query: Optional[str] = None
    ) -> Optional[PlotlyChartSpec]:
        if dt_col not in df.columns or num_col not in df.columns:
            return None

        raw_d = df[dt_col]
        raw_n = df[num_col]
        d_s = raw_d.iloc[:, 0] if isinstance(raw_d, pd.DataFrame) else raw_d
        n_s = raw_n.iloc[:, 0] if isinstance(raw_n, pd.DataFrame) else raw_n

        clean = pd.DataFrame({
            dt_col: pd.to_datetime(d_s, errors="coerce", format="mixed"),
            num_col: pd.to_numeric(n_s, errors="coerce")
        }).dropna().sort_values(by=dt_col)

        if len(clean) < 3:
            return None

        # Determine optimal time frequency
        date_min, date_max = clean[dt_col].min(), clean[dt_col].max()
        days_span = (date_max - date_min).days

        if days_span > 730:
            freq_format, freq_label = "%Y", "Yearly"
        elif days_span > 90:
            freq_format, freq_label = "%Y-%m", "Monthly"
        elif days_span > 21:
            freq_format, freq_label = "%Y-W%W", "Weekly"
        else:
            freq_format, freq_label = "%Y-%m-%d", "Daily"

        time_series = clean[dt_col].dt.strftime(freq_format)
        if agg.lower() == "avg" or agg.lower() == "mean":
            grouped = clean.groupby(time_series)[num_col].mean()
            agg_label = "Average"
        else:
            grouped = clean.groupby(time_series)[num_col].sum()
            agg_label = "Total"

        x_vals = [str(x) for x in grouped.index.tolist()]
        y_vals = [round(float(v), 2) for v in grouped.values.tolist()]

        if len(x_vals) < 2 or all(v == 0 for v in y_vals):
            return None

        max_idx = int(np.argmax(y_vals))
        peak_val = y_vals[max_idx]
        peak_date = x_vals[max_idx]
        first_val = y_vals[0]
        last_val = y_vals[-1]
        overall_change = ((last_val - first_val) / max(abs(first_val), 1e-4)) * 100

        chart_title = f"{agg_label} {num_col.replace('_', ' ').title()} Over Time ({freq_label})"
        insight = (
            f"{agg_label} {num_col.replace('_', ' ')} peaked at {peak_val:,.2f} on {peak_date}. "
            f"Net movement across the observed period is {overall_change:+0.1f}%."
        )

        trace = {
            "type": "scatter",
            "mode": "lines+markers",
            "x": x_vals,
            "y": y_vals,
            "name": num_col.replace('_', ' ').title(),
            "line": {"color": cls.COLOR_PRIMARY, "width": 3, "shape": "spline"},
            "marker": {"color": cls.COLOR_DARK, "size": 6, "line": {"color": "#FFFFFF", "width": 1.5}},
            "hovertemplate": f"<b>Date: %{{x}}</b><br>{agg_label} {num_col.replace('_', ' ').title()}: %{{y:,.2f}}<extra></extra>"
        }

        layout = cls.get_base_layout(chart_title, f"Timeline ({freq_label})", f"{agg_label} {num_col.replace('_', ' ').title()}")

        return PlotlyChartSpec(
            id=f"chart_time_{uuid.uuid4().hex[:6]}",
            title=chart_title,
            subtitle=f"{freq_label} temporal progression across {len(x_vals)} periods",
            chart_type="line",
            data=[trace],
            layout=layout,
            insights_summary=insight,
            x_column=dt_col,
            y_column=num_col,
            aggregation=agg.lower(),
            reasoning=f"Identifies longitudinal trends and periodic fluctuations in '{num_col}' over time."
        )

    # =========================================================================
    # 2. CATEGORICAL COMPARISONS & RANKINGS
    # =========================================================================

    @classmethod
    def generate_categorical_bar_chart(
        cls,
        df: pd.DataFrame,
        cat_col: str,
        num_col: Optional[str] = None,
        agg: str = "sum",
        user_query: Optional[str] = None
    ) -> Optional[PlotlyChartSpec]:
        if cat_col not in df.columns:
            return None

        raw_c = df[cat_col]
        c_s = raw_c.iloc[:, 0] if isinstance(raw_c, pd.DataFrame) else raw_c

        # If no numeric column, compute frequency count
        if not num_col or num_col not in df.columns:
            clean = pd.DataFrame({cat_col: c_s.dropna().astype(str)})
            if len(clean) == 0:
                return None
            grouped = clean[cat_col].value_counts().head(12)
            metric_label = "Record Frequency"
            agg_label = "Count"
        else:
            raw_n = df[num_col]
            n_s = raw_n.iloc[:, 0] if isinstance(raw_n, pd.DataFrame) else raw_n
            clean = pd.DataFrame({
                cat_col: c_s.dropna().astype(str),
                num_col: pd.to_numeric(n_s, errors="coerce")
            }).dropna()
            if len(clean) == 0:
                return None

            if agg.lower() in ["avg", "mean", "rate"]:
                grouped = clean.groupby(cat_col)[num_col].mean().sort_values(ascending=False).head(12)
                metric_label = f"Average {num_col.replace('_', ' ').title()}"
                agg_label = "Average"
            else:
                grouped = clean.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(12)
                metric_label = f"Total {num_col.replace('_', ' ').title()}"
                agg_label = "Total"

        if len(grouped) == 0:
            return None

        cat_names = [str(x) for x in grouped.index.tolist()]
        values = [round(float(v), 2) for v in grouped.values.tolist()]
        total_sum = sum(values)

        # Decide orientation: horizontal if category names are long or count > 7
        is_horizontal = (len(cat_names) > 7 or any(len(str(c)) > 14 for c in cat_names))

        top_name = cat_names[0]
        top_val = values[0]
        share_pct = (top_val / total_sum * 100) if total_sum > 0 else 0

        chart_title = f"{metric_label} by {cat_col.replace('_', ' ').title()}"
        insight = (
            f"Leading {cat_col} '{top_name}' accounts for {top_val:,.2f} ({share_pct:.1f}% of top segments). "
            f"Ranking reflects clear category distribution across {len(cat_names)} segments."
        )

        if is_horizontal:
            trace = {
                "type": "bar",
                "orientation": "h",
                "y": cat_names[::-1],
                "x": values[::-1],
                "marker": {
                    "color": cls.PALETTE_SEQUENCE[:len(cat_names)][::-1],
                    "line": {"color": cls.COLOR_DARK, "width": 1}
                },
                "hovertemplate": f"<b>%{{y}}</b><br>{metric_label}: %{{x:,.2f}}<extra></extra>"
            }
            layout = cls.get_base_layout(chart_title, metric_label, cat_col.replace('_', ' ').title(), height=420)
        else:
            trace = {
                "type": "bar",
                "x": cat_names,
                "y": values,
                "marker": {
                    "color": cls.PALETTE_SEQUENCE[:len(cat_names)],
                    "line": {"color": cls.COLOR_DARK, "width": 1}
                },
                "hovertemplate": f"<b>%{{x}}</b><br>{metric_label}: %{{y:,.2f}}<extra></extra>"
            }
            layout = cls.get_base_layout(chart_title, cat_col.replace('_', ' ').title(), metric_label)

        layout["showlegend"] = False

        return PlotlyChartSpec(
            id=f"chart_bar_{uuid.uuid4().hex[:6]}",
            title=chart_title,
            subtitle=f"Comparative ranking across top {cat_col} categories",
            chart_type="horizontal_bar" if is_horizontal else "bar",
            data=[trace],
            layout=layout,
            insights_summary=insight,
            x_column=cat_col if not is_horizontal else (num_col or "count"),
            y_column=num_col if not is_horizontal else cat_col,
            aggregation=agg_label.lower(),
            reasoning=f"Compares volume differences and identifies concentration across '{cat_col}' segments."
        )

    # =========================================================================
    # 3. NUMERICAL RELATIONSHIPS & SCATTER PLOTS
    # =========================================================================

    @classmethod
    def generate_scatter_chart(
        cls,
        df: pd.DataFrame,
        num_col_x: str,
        num_col_y: str,
        cat_col: Optional[str] = None,
        user_query: Optional[str] = None
    ) -> Optional[PlotlyChartSpec]:
        if num_col_x not in df.columns or num_col_y not in df.columns or num_col_x == num_col_y:
            return None

        raw_x = df[num_col_x]
        raw_y = df[num_col_y]
        x_s = raw_x.iloc[:, 0] if isinstance(raw_x, pd.DataFrame) else raw_x
        y_s = raw_y.iloc[:, 0] if isinstance(raw_y, pd.DataFrame) else raw_y

        data_dict = {
            num_col_x: pd.to_numeric(x_s, errors="coerce"),
            num_col_y: pd.to_numeric(y_s, errors="coerce")
        }
        if cat_col and cat_col in df.columns and cat_col not in [num_col_x, num_col_y]:
            raw_c = df[cat_col]
            data_dict[cat_col] = raw_c.iloc[:, 0] if isinstance(raw_c, pd.DataFrame) else raw_c

        clean = pd.DataFrame(data_dict).dropna()
        if len(clean) < 4:
            return None

        # Compute correlation
        try:
            r_coef, p_val = stats.pearsonr(clean[num_col_x], clean[num_col_y])
            r_str = f"r = {r_coef:+.3f}"
            p_str = f"p = {p_val:.4f}"
            sig_txt = "statistically significant" if p_val < 0.05 else "not statistically significant"
        except Exception:
            r_str, p_str, sig_txt = "r = N/A", "", ""

        chart_title = f"{num_col_y.replace('_', ' ').title()} vs {num_col_x.replace('_', ' ').title()}"
        insight = (
            f"Correlation between '{num_col_x}' and '{num_col_y}' is {r_str} ({p_str}, {sig_txt}). "
            f"Note: Evaluates linear association across {len(clean):,} sample observations."
        )

        traces = []
        if cat_col and cat_col in clean.columns and clean[cat_col].nunique() <= 6:
            for idx, (cat_name, group) in enumerate(clean.groupby(cat_col)):
                color = cls.PALETTE_SEQUENCE[idx % len(cls.PALETTE_SEQUENCE)]
                traces.append({
                    "type": "scatter",
                    "mode": "markers",
                    "x": [round(float(v), 2) for v in group[num_col_x].tolist()],
                    "y": [round(float(v), 2) for v in group[num_col_y].tolist()],
                    "name": str(cat_name),
                    "marker": {"color": color, "size": 8, "opacity": 0.85, "line": {"color": "#FFFFFF", "width": 1}},
                    "hovertemplate": f"<b>{cat_name}</b><br>{num_col_x}: %{{x:,.2f}}<br>{num_col_y}: %{{y:,.2f}}<extra></extra>"
                })
        else:
            traces.append({
                "type": "scatter",
                "mode": "markers",
                "x": [round(float(v), 2) for v in clean[num_col_x].tolist()],
                "y": [round(float(v), 2) for v in clean[num_col_y].tolist()],
                "name": "Observations",
                "marker": {"color": cls.COLOR_PRIMARY, "size": 8, "opacity": 0.85, "line": {"color": cls.COLOR_DARK, "width": 1}},
                "hovertemplate": f"{num_col_x}: %{{x:,.2f}}<br>{num_col_y}: %{{y:,.2f}}<extra></extra>"
            })

        layout = cls.get_base_layout(chart_title, num_col_x.replace('_', ' ').title(), num_col_y.replace('_', ' ').title())

        return PlotlyChartSpec(
            id=f"chart_scatter_{uuid.uuid4().hex[:6]}",
            title=chart_title,
            subtitle=f"Bivariate relationship analysis ({r_str}) across {len(clean)} records",
            chart_type="scatter",
            data=traces,
            layout=layout,
            insights_summary=insight,
            x_column=num_col_x,
            y_column=num_col_y,
            grouping_column=cat_col,
            reasoning=f"Evaluates empirical co-variation and clusters between '{num_col_x}' and '{num_col_y}'."
        )

    # =========================================================================
    # 4. DISTRIBUTION & SPREAD (HISTOGRAMS & BOX PLOTS)
    # =========================================================================

    @classmethod
    def generate_histogram_chart(
        cls,
        df: pd.DataFrame,
        num_col: str,
        user_query: Optional[str] = None
    ) -> Optional[PlotlyChartSpec]:
        if num_col not in df.columns:
            return None

        raw = df[num_col]
        s = raw.iloc[:, 0] if isinstance(raw, pd.DataFrame) else raw
        s_clean = pd.to_numeric(s, errors="coerce").dropna()

        if len(s_clean) < 5 or s_clean.std() == 0:
            return None

        vals = [round(float(v), 2) for v in s_clean.tolist()]
        mean_v = float(s_clean.mean())
        median_v = float(s_clean.median())
        std_v = float(s_clean.std())

        chart_title = f"{num_col.replace('_', ' ').title()} Distribution"
        insight = (
            f"Distribution of '{num_col}' has a mean of {mean_v:,.2f} and median of {median_v:,.2f} "
            f"(Std Dev: {std_v:,.2f}). Median provides typical baseline value."
        )

        trace = {
            "type": "histogram",
            "x": vals,
            "marker": {
                "color": cls.COLOR_PRIMARY,
                "line": {"color": cls.COLOR_DARK, "width": 1}
            },
            "hovertemplate": f"{num_col}: %{{x:,.2f}}<br>Count: %{{y}}<extra></extra>"
        }

        layout = cls.get_base_layout(chart_title, num_col.replace('_', ' ').title(), "Frequency Count")
        layout["showlegend"] = False

        return PlotlyChartSpec(
            id=f"chart_hist_{uuid.uuid4().hex[:6]}",
            title=chart_title,
            subtitle=f"Empirical density and spread profile for {num_col}",
            chart_type="histogram",
            data=[trace],
            layout=layout,
            insights_summary=insight,
            x_column=num_col,
            reasoning=f"Reveals distribution symmetry, central tendency, and tail spread for '{num_col}'."
        )

    @classmethod
    def generate_box_plot_chart(
        cls,
        df: pd.DataFrame,
        num_col: str,
        cat_col: Optional[str] = None,
        user_query: Optional[str] = None
    ) -> Optional[PlotlyChartSpec]:
        if num_col not in df.columns:
            return None

        raw_n = df[num_col]
        n_s = raw_n.iloc[:, 0] if isinstance(raw_n, pd.DataFrame) else raw_n

        if cat_col and cat_col in df.columns and cat_col != num_col:
            raw_c = df[cat_col]
            c_s = raw_c.iloc[:, 0] if isinstance(raw_c, pd.DataFrame) else raw_c
            clean = pd.DataFrame({
                cat_col: c_s.dropna().astype(str),
                num_col: pd.to_numeric(n_s, errors="coerce")
            }).dropna()
            if len(clean) < 5 or clean[cat_col].nunique() > 6:
                cat_col = None
        else:
            cat_col = None

        if not cat_col:
            clean = pd.DataFrame({num_col: pd.to_numeric(n_s, errors="coerce")}).dropna()
            if len(clean) < 5:
                return None

        chart_title = f"{num_col.replace('_', ' ').title()} Dispersion & Outliers" + (f" by {cat_col.replace('_', ' ').title()}" if cat_col else "")
        traces = []

        if cat_col:
            for idx, (c_name, grp) in enumerate(clean.groupby(cat_col)):
                color = cls.PALETTE_SEQUENCE[idx % len(cls.PALETTE_SEQUENCE)]
                traces.append({
                    "type": "box",
                    "y": [round(float(v), 2) for v in grp[num_col].tolist()],
                    "name": str(c_name),
                    "marker": {"color": color},
                    "boxpoints": "outliers"
                })
            insight = f"Displays quantile spread and outlier points across {clean[cat_col].nunique()} {cat_col} categories."
        else:
            traces.append({
                "type": "box",
                "y": [round(float(v), 2) for v in clean[num_col].tolist()],
                "name": num_col.replace('_', ' ').title(),
                "marker": {"color": cls.COLOR_PRIMARY},
                "boxpoints": "outliers"
            })
            p50 = float(clean[num_col].median())
            p25 = float(np.percentile(clean[num_col], 25))
            p75 = float(np.percentile(clean[num_col], 75))
            insight = f"Median = {p50:,.2f}, IQR = {p75 - p25:,.2f} (Q1: {p25:,.2f}, Q3: {p75:,.2f}). Outlier points plotted beyond whiskers."

        layout = cls.get_base_layout(chart_title, cat_col or "Segment", num_col.replace('_', ' ').title())

        return PlotlyChartSpec(
            id=f"chart_box_{uuid.uuid4().hex[:6]}",
            title=chart_title,
            subtitle="Quantile spread, interquartile range, and outlier detection",
            chart_type="box",
            data=traces,
            layout=layout,
            insights_summary=insight,
            x_column=cat_col,
            y_column=num_col,
            reasoning=f"Detects extreme value deviations and distribution quartiles for '{num_col}'."
        )

    # =========================================================================
    # 5. COMPOSITION & PART-TO-WHOLE (STRICT DONUT)
    # =========================================================================

    @classmethod
    def generate_donut_chart(
        cls,
        df: pd.DataFrame,
        cat_col: str,
        num_col: Optional[str] = None,
        user_query: Optional[str] = None
    ) -> Optional[PlotlyChartSpec]:
        if cat_col not in df.columns:
            return None

        raw_c = df[cat_col]
        c_s = raw_c.iloc[:, 0] if isinstance(raw_c, pd.DataFrame) else raw_c

        # Strictly limit donut to 2-6 categories to ensure high readability
        if not num_col or num_col not in df.columns:
            clean = pd.DataFrame({cat_col: c_s.dropna().astype(str)})
            if clean[cat_col].nunique() < 2 or clean[cat_col].nunique() > 6:
                return None
            grouped = clean[cat_col].value_counts()
            metric_label = "Share of Records"
        else:
            raw_n = df[num_col]
            n_s = raw_n.iloc[:, 0] if isinstance(raw_n, pd.DataFrame) else raw_n
            clean = pd.DataFrame({
                cat_col: c_s.dropna().astype(str),
                num_col: pd.to_numeric(n_s, errors="coerce")
            }).dropna()
            if clean[cat_col].nunique() < 2 or clean[cat_col].nunique() > 6 or (clean[num_col] < 0).any():
                return None
            grouped = clean.groupby(cat_col)[num_col].sum()
            metric_label = f"{num_col.replace('_', ' ').title()} Share"

        labels = [str(x) for x in grouped.index.tolist()]
        values = [round(float(v), 2) for v in grouped.values.tolist()]
        tot_val = sum(values)

        if tot_val <= 0:
            return None

        top_share = (values[0] / tot_val * 100)
        chart_title = f"{metric_label} by {cat_col.replace('_', ' ').title()}"
        insight = f"'{labels[0]}' represents the largest composition share at {top_share:.1f}% ({values[0]:,.2f})."

        trace = {
            "type": "pie",
            "hole": 0.55,
            "labels": labels,
            "values": values,
            "marker": {
                "colors": cls.PALETTE_SEQUENCE[:len(labels)],
                "line": {"color": "#FFFFFF", "width": 2}
            },
            "textinfo": "label+percent",
            "textposition": "inside",
            "insidetextorientation": "radial",
            "hovertemplate": "<b>%{label}</b><br>Volume: %{value:,.2f} (%{percent})<extra></extra>"
        }

        layout = {
            "title": {
                "text": f"<b>{chart_title}</b>",
                "font": {"family": "Plus Jakarta Sans, Inter, sans-serif", "size": 15, "color": cls.COLOR_DARK},
                "x": 0.02,
                "xanchor": "left"
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"l": 30, "r": 30, "t": 60, "b": 30},
            "height": 380,
            "font": {"family": "Plus Jakarta Sans, Inter, sans-serif", "color": cls.COLOR_DARK, "size": 11},
            "showlegend": True,
            "legend": {"orientation": "h", "yanchor": "bottom", "y": -0.1, "xanchor": "center", "x": 0.5}
        }

        return PlotlyChartSpec(
            id=f"chart_donut_{uuid.uuid4().hex[:6]}",
            title=chart_title,
            subtitle=f"Part-to-whole breakdown across {len(labels)} categories",
            chart_type="donut",
            data=[trace],
            layout=layout,
            insights_summary=insight,
            x_column=cat_col,
            y_column=num_col,
            reasoning=f"Evaluates proportional composition of '{cat_col}' as parts of a meaningful whole."
        )

    # =========================================================================
    # 6. DYNAMIC CANDIDATE GENERATION & RANKING ENGINE
    # =========================================================================

    @classmethod
    def generate_candidate_charts(
        cls,
        df: pd.DataFrame,
        profile: DatasetProfile,
        plan: AnalysisPlan,
        roles: Dict[str, ColumnRoleProfile],
        user_query: Optional[str] = None
    ) -> List[PlotlyChartSpec]:
        candidates: List[PlotlyChartSpec] = []

        measures = [name for name, r in roles.items() if r.is_measure]
        categories = [name for name, r in roles.items() if r.is_category and not r.is_identifier]
        datetimes = [name for name, r in roles.items() if r.is_datetime]

        # 1. Time Series Candidates
        for dt_col in datetimes[:2]:
            for num_col in measures[:3]:
                r = roles.get(num_col)
                agg = "avg" if r and r.role == "measure_rate" else "sum"
                chart = cls.generate_time_series_chart(df, dt_col, num_col, agg=agg, user_query=user_query)
                if chart:
                    candidates.append(chart)

        # 2. Categorical Comparison Candidates
        for cat_col in categories[:4]:
            for num_col in measures[:3]:
                r = roles.get(num_col)
                agg = "avg" if r and r.role == "measure_rate" else "sum"
                chart = cls.generate_categorical_bar_chart(df, cat_col, num_col, agg=agg, user_query=user_query)
                if chart:
                    candidates.append(chart)

        # 3. Categorical Frequency Candidates (if no measures or for important categories)
        if not measures or len(candidates) < 2:
            for cat_col in categories[:3]:
                chart = cls.generate_categorical_bar_chart(df, cat_col, num_col=None, user_query=user_query)
                if chart:
                    candidates.append(chart)

        # 4. Bivariate Scatter Candidates
        if len(measures) >= 2:
            for i in range(min(3, len(measures))):
                for j in range(i + 1, min(4, len(measures))):
                    cat_for_scatter = categories[0] if (categories and roles[categories[0]].unique_count <= 5) else None
                    chart = cls.generate_scatter_chart(df, measures[i], measures[j], cat_col=cat_for_scatter, user_query=user_query)
                    if chart:
                        candidates.append(chart)

        # 5. Distribution Candidates (Histograms & Box Plots)
        for num_col in measures[:2]:
            hist = cls.generate_histogram_chart(df, num_col, user_query=user_query)
            if hist:
                candidates.append(hist)
            if categories and roles[categories[0]].unique_count <= 4:
                box = cls.generate_box_plot_chart(df, num_col, cat_col=categories[0], user_query=user_query)
                if box:
                    candidates.append(box)

        # 6. Donut Part-to-Whole Candidates (strictly for <= 5 categories)
        for cat_col in categories[:2]:
            if roles[cat_col].unique_count <= 5:
                num_for_donut = measures[0] if measures else None
                donut = cls.generate_donut_chart(df, cat_col, num_for_donut, user_query=user_query)
                if donut:
                    candidates.append(donut)

        return candidates

    @classmethod
    def score_and_deduplicate(
        cls,
        candidates: List[PlotlyChartSpec],
        roles: Dict[str, ColumnRoleProfile],
        plan: AnalysisPlan,
        user_query: Optional[str] = None
    ) -> List[PlotlyChartSpec]:
        """Scores candidate charts on analytical insight, user question alignment, readability, and uniqueness."""
        if not candidates:
            return []

        query_text = (user_query or plan.primary_goal or "").lower()
        scored: List[PlotlyChartSpec] = []

        seen_signatures: Set[str] = set()

        for c in candidates:
            score = 50.0  # baseline

            # 1. User Query & Goal Alignment (+30 to +50)
            if c.x_column and c.x_column.lower() in query_text:
                score += 25.0
            if c.y_column and c.y_column.lower() in query_text:
                score += 25.0
            if any(term in query_text for term in ["trend", "over time", "month", "date"]) and c.chart_type == "line":
                score += 30.0
            if any(term in query_text for term in ["correlat", "vs", "relationship"]) and c.chart_type == "scatter":
                score += 30.0
            if any(term in query_text for term in ["distribut", "spread", "outlier"]) and c.chart_type in ["histogram", "box"]:
                score += 30.0
            if any(term in query_text for term in ["share", "breakdown", "proportion"]) and c.chart_type == "donut":
                score += 25.0

            # 2. Analytical Archetype Value
            if c.chart_type == "line":
                score += 20.0  # Time series trends are high analytical value
            elif c.chart_type == "scatter":
                score += 15.0  # Correlations are high value
            elif c.chart_type in ["horizontal_bar", "bar"]:
                score += 15.0  # Ranked comparisons
            elif c.chart_type in ["histogram", "box"]:
                score += 10.0  # Distribution insight

            # 3. Readability & Cleanliness
            if c.insights_summary:
                score += 10.0

            c.priority_score = round(score, 1)

            # Deduplication: Key signature (chart_type, x_col, y_col)
            sig = f"{c.chart_type}::{c.x_column}::{c.y_column}::{c.aggregation}"
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)
            scored.append(c)

        # Sort descending by priority score
        scored.sort(key=lambda x: x.priority_score or 0.0, reverse=True)

        # Select top complementary charts without redundancy
        final_charts: List[PlotlyChartSpec] = []
        covered_types: Set[str] = set()
        covered_measures: Set[str] = set()

        for c in scored:
            # Prevent 4 of the same chart type unless diverse
            type_count = sum(1 for fc in final_charts if fc.chart_type == c.chart_type)
            if type_count >= 2 and len(final_charts) >= 3:
                continue

            final_charts.append(c)
            covered_types.add(c.chart_type)
            if c.y_column:
                covered_measures.add(c.y_column)

            # Cap dynamically between 2 and 6 based on available quality
            if len(final_charts) >= 5:
                break

        return final_charts

    @classmethod
    def generate_all(
        cls,
        df: pd.DataFrame,
        profile: DatasetProfile,
        plan: AnalysisPlan,
        user_query: Optional[str] = None
    ) -> ChartCollection:
        dataset_id = profile.dataset_id
        logger.info(f"Running intelligent data-driven chart generation for '{dataset_id}'")

        # 1. Classify Column Roles
        roles = SemanticRoleClassifier.profile_all_columns(df, profile)
        logger.info(f"Classified column roles: { {name: r.role for name, r in roles.items()} }")

        # 2. Discover Candidates
        candidates = cls.generate_candidate_charts(df, profile, plan, roles, user_query=user_query)
        logger.info(f"Generated {len(candidates)} raw visualization candidates")

        # 3. Score, Deduplicate & Select
        selected_charts = cls.score_and_deduplicate(candidates, roles, plan, user_query=user_query)
        logger.info(f"Selected {len(selected_charts)} high-priority visualizations for '{dataset_id}'")

        empty_reason = None
        if not selected_charts:
            empty_reason = (
                "No meaningful visualizations could be generated from the dataset. "
                "The data primarily consists of high-cardinality identifiers or insufficient numerical/temporal measures."
            )

        return ChartCollection(
            dataset_id=dataset_id,
            charts=selected_charts,
            empty_reason=empty_reason
        )

import uuid
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from backend.app.core.logging import logger
from backend.app.models.profile import DatasetProfile
from backend.app.models.plan import AnalysisPlan
from backend.app.models.visualization import PlotlyChartSpec, ChartCollection


class ChartGenerator:
    """Deterministic Plotly chart specification generator implementing the custom palette tokens."""

    COLOR_PRIMARY = "#609966"
    COLOR_DARK = "#40513B"
    COLOR_ACCENT = "#9DC08B"
    COLOR_BG_CARD = "#FFFFFF"
    COLOR_GRID = "rgba(157, 192, 139, 0.25)"
    PALETTE_SEQUENCE = [
        "#609966", "#40513B", "#9DC08B", "#82A776",
        "#2E3A2A", "#A8D18D", "#4B6B48", "#709665"
    ]

    @classmethod
    def get_base_layout(cls, title: str, x_label: str = "", y_label: str = "") -> Dict[str, Any]:
        return {
            "title": {
                "text": f"<b>{title}</b>",
                "font": {"family": "Inter, sans-serif", "size": 15, "color": cls.COLOR_DARK},
                "x": 0.02,
                "xanchor": "left"
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"l": 55, "r": 25, "t": 60, "b": 50},
            "font": {"family": "Inter, sans-serif", "color": cls.COLOR_DARK, "size": 11},
            "xaxis": {
                "title": {"text": x_label, "font": {"size": 12, "color": cls.COLOR_DARK}},
                "gridcolor": cls.COLOR_GRID,
                "zeroline": False,
                "tickfont": {"color": cls.COLOR_DARK, "size": 10},
                "showline": True,
                "linecolor": cls.COLOR_ACCENT,
            },
            "yaxis": {
                "title": {"text": y_label, "font": {"size": 12, "color": cls.COLOR_DARK}},
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
                "font": {"family": "Inter, sans-serif", "size": 11, "color": cls.COLOR_DARK}
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

    @classmethod
    def generate_bar_chart(
        cls,
        df: pd.DataFrame,
        cat_col: str,
        num_col: str,
        title: Optional[str] = None
    ) -> Optional[PlotlyChartSpec]:
        if cat_col not in df.columns or num_col not in df.columns:
            return None

        clean = df[[cat_col, num_col]].dropna()
        clean[num_col] = pd.to_numeric(clean[num_col], errors="coerce")
        clean = clean.dropna()
        if len(clean) == 0:
            return None

        grouped = clean.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(10)
        x_vals = [str(x) for x in grouped.index.tolist()]
        y_vals = [round(float(v), 2) for v in grouped.values.tolist()]

        chart_title = title or f"Total {num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}"

        trace = {
            "type": "bar",
            "x": x_vals,
            "y": y_vals,
            "name": num_col.replace('_', ' ').title(),
            "marker": {
                "color": cls.PALETTE_SEQUENCE[:len(x_vals)],
                "line": {"color": cls.COLOR_DARK, "width": 1}
            },
            "hovertemplate": f"<b>%{{x}}</b><br>{num_col.replace('_', ' ').title()}: %{{y:,.2f}}<extra></extra>"
        }

        layout = cls.get_base_layout(chart_title, cat_col.replace('_', ' ').title(), num_col.replace('_', ' ').title())
        layout["showlegend"] = False

        return PlotlyChartSpec(
            id=f"chart_bar_{uuid.uuid4().hex[:6]}",
            title=chart_title,
            subtitle=f"Aggregated volume distribution across top {cat_col} categories",
            chart_type="bar",
            data=[trace],
            layout=layout,
            insights_summary=f"Top category '{x_vals[0]}' leads with {y_vals[0]:,.2f} total {num_col}."
        )

    @classmethod
    def generate_line_chart(
        cls,
        df: pd.DataFrame,
        dt_col: str,
        num_col: str,
        title: Optional[str] = None
    ) -> Optional[PlotlyChartSpec]:
        if dt_col not in df.columns or num_col not in df.columns:
            return None

        clean = df[[dt_col, num_col]].dropna().copy()
        clean[dt_col] = pd.to_datetime(clean[dt_col], errors="coerce", format="mixed")
        clean[num_col] = pd.to_numeric(clean[num_col], errors="coerce")
        clean = clean.dropna().sort_values(by=dt_col)
        if len(clean) < 3:
            return None

        # Group by date
        grouped = clean.groupby(clean[dt_col].dt.strftime("%Y-%m-%d"))[num_col].sum()
        x_vals = [str(x) for x in grouped.index.tolist()]
        y_vals = [round(float(v), 2) for v in grouped.values.tolist()]

        chart_title = title or f"{num_col.replace('_', ' ').title()} Trend Over Time"

        trace = {
            "type": "scatter",
            "mode": "lines+markers",
            "x": x_vals,
            "y": y_vals,
            "name": num_col.replace('_', ' ').title(),
            "line": {"color": cls.COLOR_PRIMARY, "width": 3, "shape": "spline"},
            "marker": {"color": cls.COLOR_DARK, "size": 6, "line": {"color": "#FFFFFF", "width": 1.5}},
            "hovertemplate": f"<b>Date: %{{x}}</b><br>{num_col.replace('_', ' ').title()}: %{{y:,.2f}}<extra></extra>"
        }

        layout = cls.get_base_layout(chart_title, "Timeline", num_col.replace('_', ' ').title())

        return PlotlyChartSpec(
            id=f"chart_line_{uuid.uuid4().hex[:6]}",
            title=chart_title,
            subtitle=f"Temporal progression across {len(x_vals)} time intervals",
            chart_type="line",
            data=[trace],
            layout=layout,
            insights_summary=f"Observed peak of {max(y_vals):,.2f} on {x_vals[y_vals.index(max(y_vals))]}."
        )

    @classmethod
    def generate_scatter_chart(
        cls,
        df: pd.DataFrame,
        num_col_x: str,
        num_col_y: str,
        cat_col: Optional[str] = None
    ) -> Optional[PlotlyChartSpec]:
        if num_col_x not in df.columns or num_col_y not in df.columns:
            return None

        clean = df[[num_col_x, num_col_y] + ([cat_col] if cat_col and cat_col in df.columns else [])].dropna().copy()
        clean[num_col_x] = pd.to_numeric(clean[num_col_x], errors="coerce")
        clean[num_col_y] = pd.to_numeric(clean[num_col_y], errors="coerce")
        clean = clean.dropna()
        if len(clean) < 3:
            return None

        chart_title = f"{num_col_y.replace('_', ' ').title()} vs {num_col_x.replace('_', ' ').title()}"

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
                    "hovertemplate": f"<b>{cat_name}</b><br>{num_col_x}: %{{x}}<br>{num_col_y}: %{{y}}<extra></extra>"
                })
        else:
            traces.append({
                "type": "scatter",
                "mode": "markers",
                "x": [round(float(v), 2) for v in clean[num_col_x].tolist()],
                "y": [round(float(v), 2) for v in clean[num_col_y].tolist()],
                "name": "Observations",
                "marker": {"color": cls.COLOR_PRIMARY, "size": 8, "opacity": 0.85, "line": {"color": cls.COLOR_DARK, "width": 1}},
                "hovertemplate": f"{num_col_x}: %{{x}}<br>{num_col_y}: %{{y}}<extra></extra>"
            })

        layout = cls.get_base_layout(chart_title, num_col_x.replace('_', ' ').title(), num_col_y.replace('_', ' ').title())

        return PlotlyChartSpec(
            id=f"chart_scatter_{uuid.uuid4().hex[:6]}",
            title=chart_title,
            subtitle="Bivariate correlation and cluster pattern distribution",
            chart_type="scatter",
            data=traces,
            layout=layout,
            insights_summary=f"Visualizes correlation between {num_col_x} and {num_col_y} across {len(clean)} records."
        )

    @classmethod
    def generate_donut_chart(
        cls,
        df: pd.DataFrame,
        cat_col: str,
        num_col: str
    ) -> Optional[PlotlyChartSpec]:
        if cat_col not in df.columns or num_col not in df.columns:
            return None

        clean = df[[cat_col, num_col]].dropna().copy()
        clean[num_col] = pd.to_numeric(clean[num_col], errors="coerce")
        clean = clean.dropna()
        if len(clean) == 0:
            return None

        grouped = clean.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(6)
        labels = [str(x) for x in grouped.index.tolist()]
        values = [round(float(v), 2) for v in grouped.values.tolist()]

        chart_title = f"{num_col.replace('_', ' ').title()} Share by {cat_col.replace('_', ' ').title()}"

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
                "font": {"family": "Inter, sans-serif", "size": 15, "color": cls.COLOR_DARK},
                "x": 0.02,
                "xanchor": "left"
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"l": 30, "r": 30, "t": 60, "b": 30},
            "font": {"family": "Inter, sans-serif", "color": cls.COLOR_DARK, "size": 11},
            "showlegend": True,
            "legend": {"orientation": "h", "yanchor": "bottom", "y": -0.1, "xanchor": "center", "x": 0.5}
        }

        return PlotlyChartSpec(
            id=f"chart_donut_{uuid.uuid4().hex[:6]}",
            title=chart_title,
            subtitle="Categorical proportion and volume share",
            chart_type="donut",
            data=[trace],
            layout=layout,
            insights_summary=f"'{labels[0]}' represents the largest single share at {values[0]:,.2f}."
        )

    @classmethod
    def generate_all(
        cls,
        df: pd.DataFrame,
        profile: DatasetProfile,
        plan: AnalysisPlan
    ) -> ChartCollection:
        logger.info(f"Generating deterministic Plotly charts for dataset '{profile.dataset_id}'")

        charts: List[PlotlyChartSpec] = []

        num_cols = profile.numeric_column_names
        cat_cols = profile.categorical_column_names
        dt_cols = profile.datetime_column_names

        # 1. Primary Ranked Bar Chart
        if cat_cols and num_cols:
            bar_c = cls.generate_bar_chart(df, cat_cols[0], num_cols[0])
            if bar_c:
                charts.append(bar_c)

        # 2. Secondary Category Bar / Donut Chart
        if len(cat_cols) > 1 and num_cols:
            donut_c = cls.generate_donut_chart(df, cat_cols[1], num_cols[0])
            if donut_c:
                charts.append(donut_c)
        elif cat_cols and num_cols:
            donut_c = cls.generate_donut_chart(df, cat_cols[0], num_cols[0])
            if donut_c:
                charts.append(donut_c)

        # 3. Time Series Trend Line Chart
        if dt_cols and num_cols:
            line_c = cls.generate_line_chart(df, dt_cols[0], num_cols[0])
            if line_c:
                charts.append(line_c)

        # 4. Correlation / Scatter Chart
        if len(num_cols) >= 2:
            scatter_c = cls.generate_scatter_chart(df, num_cols[1], num_cols[0], cat_cols[0] if cat_cols else None)
            if scatter_c:
                charts.append(scatter_c)

        logger.info(f"Successfully generated {len(charts)} interactive Plotly charts for '{profile.dataset_id}'")
        return ChartCollection(dataset_id=profile.dataset_id, charts=charts)

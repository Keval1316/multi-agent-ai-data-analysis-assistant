import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas
from backend.app.core.logging import logger
from backend.app.models.report import AnalysisReport


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render total page numbers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#AD8B73"))

        # Running footer line
        self.setStrokeColor(colors.HexColor("#CEAB93"))
        self.setLineWidth(0.5)
        self.line(40, 35, 572, 35)

        # Footer text
        self.drawString(40, 24, "DataPilot:Multi-Agent Data Analyst — Confidential Executive Report")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 24, page_str)
        self.restoreState()


class PDFExporter:
    """Deterministic PDF generation service producing pixel-perfect executive reports with custom design palette."""

    # Color Palette Tokens
    C_DARK = colors.HexColor("#3E2723")
    C_PRIMARY = colors.HexColor("#AD8B73")
    C_ACCENT = colors.HexColor("#CEAB93")
    C_LIGHT = colors.HexColor("#FFFBE9")
    C_CARD_BG = colors.HexColor("#FDFBF7")
    C_WHITE = colors.HexColor("#FFFFFF")
    C_TEXT = colors.HexColor("#4A3525")

    @classmethod
    def generate_pdf(cls, report: AnalysisReport) -> bytes:
        logger.info(f"Generating PDF for dataset '{report.dataset_id}' ({report.filename})")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=50
        )

        styles = getSampleStyleSheet()

        # Custom Paragraph Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=cls.C_DARK,
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            textColor=cls.C_PRIMARY,
            spaceAfter=14
        )

        h1_style = ParagraphStyle(
            "SectionH1",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=cls.C_DARK,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        )

        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=cls.C_PRIMARY,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        )

        body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12.5,
            textColor=cls.C_TEXT,
            spaceAfter=6
        )

        callout_style = ParagraphStyle(
            "CalloutText",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9.5,
            leading=13.5,
            textColor=cls.C_DARK
        )

        meta_style = ParagraphStyle(
            "MetaText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=cls.C_DARK
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10.5,
            textColor=cls.C_WHITE
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=cls.C_TEXT
        )

        story = []

        # 1. Header Banner Table
        meta_left = f"<b>Dataset:</b> {report.filename}<br/><b>Domain:</b> {report.understanding.domain}<br/><b>Rows:</b> {report.profile.total_rows:,} | <b>Columns:</b> {report.profile.total_columns}"
        meta_right = f"<b>Generated:</b> {report.generated_at}<br/><b>Quality Score:</b> {report.quality.quality_score}/100 (Grade {report.quality.grade})<br/><b>Duplicate Rows:</b> {report.profile.duplicate_rows_count}"

        banner_data = [
            [
                Paragraph(meta_left, meta_style),
                Paragraph(meta_right, meta_style)
            ]
        ]
        banner_table = Table(banner_data, colWidths=[270, 262])
        banner_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), cls.C_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, cls.C_ACCENT),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

        story.append(Paragraph(report.title, title_style))
        story.append(Paragraph(report.subtitle, subtitle_style))
        story.append(banner_table)
        story.append(Spacer(1, 14))

        # 2. Executive Summary Box
        story.append(Paragraph("1. Executive Summary", h1_style))
        exec_table = Table([[Paragraph(report.executive_summary.replace('\n', '<br/>'), callout_style)]], colWidths=[532])
        exec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), cls.C_CARD_BG),
            ("LINELEFT", (0, 0), (0, -1), 4, cls.C_PRIMARY),
            ("BOX", (0, 0), (-1, -1), 0.5, cls.C_ACCENT),
            ("PADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(exec_table)
        story.append(Spacer(1, 14))

        # 3. Data Quality Breakdown Table
        if report.data_quality_breakdown:
            story.append(Paragraph("Data Quality & Hygiene Audit Breakdown", h1_style))
            q_headers = ["Check", "Result", "Status"]
            q_rows = [[Paragraph(h, table_header_style) for h in q_headers]]
            for item in report.data_quality_breakdown:
                q_rows.append([
                    Paragraph(item.get("check", ""), table_cell_style),
                    Paragraph(item.get("result", ""), table_cell_style),
                    Paragraph(item.get("status", ""), table_cell_style),
                ])
            q_table = Table(q_rows, colWidths=[220, 160, 152])
            q_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), cls.C_DARK),
                ("BOX", (0, 0), (-1, -1), 0.5, cls.C_ACCENT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, cls.C_LIGHT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [cls.C_WHITE, cls.C_CARD_BG]),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(q_table)
            story.append(Spacer(1, 14))

        # 4. Verified Insights & Findings Cards
        story.append(Paragraph("Verified Strategic Insights & Evidence", h1_style))
        for ins in report.insights.insights:
            q_text = ins.question_answered or f"What key empirical pattern is revealed regarding {ins.category} in {ins.title}?"
            means_p = f"<br/><b>What This Means:</b> {ins.what_this_means}" if ins.what_this_means else ""
            card_content = [
                Paragraph(f"<b>{ins.title}</b> <font color='#AD8B73'>({ins.category} • {ins.importance} Priority • {ins.confidence} Confidence)</font>", h2_style),
                Paragraph(f"<b>Investigated Question:</b> <i>{q_text}</i>", meta_style),
                Spacer(1, 2),
                Paragraph(f"<b>Finding:</b> {ins.finding}{means_p}", body_style),
                Paragraph(f"<b>Evidence:</b> {ins.evidence or ins.supporting_evidence}", meta_style),
            ]
            rec_text = ins.implication or ins.recommendation
            if rec_text:
                card_content.append(Spacer(1, 3))
                card_content.append(Paragraph(f"<b>Recommended Action:</b> {rec_text}", body_style))

            ins_table = Table([[card_content]], colWidths=[532])
            ins_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), cls.C_CARD_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, cls.C_ACCENT),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(ins_table)
            story.append(Spacer(1, 6))

        story.append(Spacer(1, 8))

        # 5. Statistical Moments & Quantiles Summary Table
        if report.statistics.univariate_metrics:
            story.append(Paragraph("Parametric Moments & Quantile Distributions", h1_style))
            stat_headers = ["Metric", "Mean", "Median", "Min", "Max", "Std Dev", "IQR", "Skewness"]
            stat_rows = [[Paragraph(h, table_header_style) for h in stat_headers]]

            for um in report.statistics.univariate_metrics[:6]:
                skew_str = f"{um.skewness:.2f}" if um.skewness is not None else "N/A"
                row = [
                    Paragraph(um.column_name, table_cell_style),
                    Paragraph(f"{um.mean:,.2f}", table_cell_style),
                    Paragraph(f"{um.median:,.2f}", table_cell_style),
                    Paragraph(f"{um.min:,.2f}", table_cell_style),
                    Paragraph(f"{um.max:,.2f}", table_cell_style),
                    Paragraph(f"{um.std:,.2f}", table_cell_style),
                    Paragraph(f"{um.iqr:,.2f}", table_cell_style),
                    Paragraph(skew_str, table_cell_style),
                ]
                stat_rows.append(row)

            stat_table = Table(stat_rows, colWidths=[100, 60, 60, 60, 60, 60, 60, 72])
            stat_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), cls.C_DARK),
                ("BOX", (0, 0), (-1, -1), 0.5, cls.C_ACCENT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, cls.C_LIGHT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [cls.C_WHITE, cls.C_CARD_BG]),
                ("PADDING", (0, 0), (-1, -1), 4.5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(stat_table)
            story.append(Spacer(1, 14))

        # 6. Detailed Structured Sections (if available)
        if report.sections:
            for sec in report.sections:
                if sec.id in ["sec_1_exec_summary", "sec_exec_summary"]:
                    continue  # already rendered in callout box above
                story.append(Paragraph(sec.title, h1_style))
                story.append(Paragraph(f"<i>{sec.summary}</i>", meta_style))
                story.append(Spacer(1, 3))
                formatted_md = sec.markdown_content.replace("\n\n", "<br/><br/>").replace("\n", "<br/>")
                story.append(Paragraph(formatted_md, body_style))
                story.append(Spacer(1, 10))

        # Build document
        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"Successfully rendered PDF ({len(pdf_bytes):,} bytes)")
        return pdf_bytes

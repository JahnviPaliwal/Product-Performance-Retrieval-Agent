import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

from .charts import chart_to_png_bytes, generate_chart
from .quality import QualityReport

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        HRFlowable,
        Image,
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False



def _clean_table_data(data: Any, max_rows: int = 8, max_cols: int = 5) -> List[List[str]]:
    """Format diverse analysis outputs (DataFrames, dicts) into safe string matrices for ReportLab Table."""
    if isinstance(data, pd.DataFrame):
        df_sub = data.iloc[:max_rows, :max_cols]
        header = ["Index"] + [str(c)[:18] for c in df_sub.columns]
        rows = [header]
        for idx, row in df_sub.iterrows():
            row_str = [str(idx)[:15]] + [str(v)[:15] for v in row.values]
            rows.append(row_str)
        return rows

    elif isinstance(data, dict):
        rows = [["Metric / Key", "Value"]]
        for k, v in list(data.items())[:max_rows]:
            val_str = str(v)
            if len(val_str) > 40:
                val_str = val_str[:37] + "..."
            rows.append([str(k)[:25], val_str])
        return rows

    else:
        return [["Result Summary"], [str(data)[:80]]]


def generate_pdf_report(
    dataset_name: str,
    df: pd.DataFrame,
    quality_report: QualityReport,
    insights: List[Dict[str, Any]],
    executed_results: Optional[Dict[str, Any]] = None,
    qa_history: Optional[List[Dict[str, str]]] = None,
) -> bytes:
    """Generate a publication-grade PDF report using ReportLab.

    Args:
        dataset_name: Name of the uploaded file.
        df: The pandas DataFrame.
        quality_report: Detailed QualityReport object from quality.py.
        insights: List of recommended insights.
        executed_results: Dict mapping insight_type to its computation result.
        qa_history: Optional list of {"question": ..., "answer": ...} dicts.

    Returns:
        Raw PDF document bytes.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError(
            "ReportLab is not installed in the current Python environment. "
            "Please install it with: pip install reportlab"
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e3a8a"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
    )
    h2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("Dataset Performance & Analytics Report", title_style))
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"Dataset: <b>{dataset_name}</b> | Generated: {now_str}", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=12))

    # 2. Executive Overview & Data Quality Score
    story.append(Paragraph("Executive Overview & Quality Score", h2_style))

    overview_data = [
        ["Metric", "Value", "Quality Component", "Ratio / Penalty"],
        ["Total Rows", f"{len(df):,}", "Missing Cells", f"{quality_report.missing_ratio:.2%} (-{quality_report.penalties.get('missing_penalty', 0):.1f} pts)"],
        ["Total Columns", f"{len(df.columns)}", "Duplicate Rows", f"{quality_report.duplicate_ratio:.2%} (-{quality_report.penalties.get('duplicate_penalty', 0):.1f} pts)"],
        ["Numeric Columns", f"{quality_report.numeric_columns}", "IQR Outliers", f"{quality_report.outlier_ratio:.2%} (-{quality_report.penalties.get('outlier_penalty', 0):.1f} pts)"],
        ["Quality Score", f"<b>{quality_report.score} / 100</b>", "Weights Used", f"Missing: {quality_report.weights.missing_weight}, Dup: {quality_report.weights.duplicate_weight}, Out: {quality_report.weights.outlier_weight}"],
    ]

    overview_table = Table(
        [[Paragraph(cell, body_style) for cell in row] for row in overview_data],
        colWidths=[90, 110, 140, 200],
    )
    overview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 14))

    # 3. Recommended Insights Plan
    story.append(Paragraph("Recommended Insights Plan", h2_style))
    plan_data = [["#", "Insight Title", "Type", "Description"]]
    for i, ins in enumerate(insights, 1):
        plan_data.append([
            str(i),
            str(ins.get("title", "")),
            str(ins.get("insight_type", "")),
            str(ins.get("description", "")),
        ])

    plan_table = Table(
        [[Paragraph(cell, body_style) for cell in row] for row in plan_data],
        colWidths=[20, 130, 100, 290],
    )
    plan_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(plan_table)
    story.append(Spacer(1, 16))

    # 4. Executed Analytics & Charts
    if executed_results:
        story.append(PageBreak())
        story.append(Paragraph("Executed Insight Analyses & Visualizations", h2_style))

        for itype, res in executed_results.items():
            section_elements = []
            title_text = f"Analysis: {itype.replace('_', ' ').title()}"
            section_elements.append(Paragraph(f"<b>{title_text}</b>", ParagraphStyle("H3", parent=h2_style, fontSize=11, spaceBefore=8)))

            # Generate chart image
            fig = generate_chart(itype, df)
            if fig is not None:
                png_bytes = chart_to_png_bytes(fig)
                img = Image(io.BytesIO(png_bytes), width=480, height=220)
                section_elements.append(img)
                section_elements.append(Spacer(1, 6))

            # Table of numerical/tabular results
            matrix = _clean_table_data(res)
            res_table = Table(
                [[Paragraph(cell, body_style) for cell in row] for row in matrix],
                colWidths=[120] + [70] * (len(matrix[0]) - 1) if len(matrix[0]) > 1 else [480],
            )
            res_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]))
            section_elements.append(res_table)
            section_elements.append(Spacer(1, 12))

            story.append(KeepTogether(section_elements))

    # 5. Follow-Up Q&A Transcript
    if qa_history:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Follow-Up Q&A Transcript", h2_style))
        for item in qa_history:
            q_p = Paragraph(f"<b>Q: {item.get('question', '')}</b>", body_style)
            a_p = Paragraph(f"A: {item.get('answer', '')}", body_style)
            story.append(KeepTogether([q_p, Spacer(1, 2), a_p, Spacer(1, 6)]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

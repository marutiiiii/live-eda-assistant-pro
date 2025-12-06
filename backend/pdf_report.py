# backend/pdf_report.py

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import textwrap
import datetime
import io

def _draw_wrapped(c, text, x, y, width_chars=90, line_height=14):
    """
    Helper: wrap long text lines within the page width.
    width_chars is roughly character width, not exact pixels.
    """
    wrapper = textwrap.TextWrapper(width=width_chars)
    lines = wrapper.wrap(text)
    for line in lines:
        c.drawString(x, y, line)
        y -= line_height
    return y

def generate_pdf(
    overview: dict,
    col_summaries: dict,
    outliers: dict,
    overview_insights: list,
    col_insights: list,
    corr_insights: list,
    file_name: str,
) -> bytes:
    """
    Build a PDF report and return it as raw bytes.
    Backend will decide where to save it.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin_x = 2 * cm
    y = height - 2 * cm

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin_x, y, "Live EDA Assistant - Automated Report")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(margin_x, y, f"Dataset: {file_name}")
    y -= 14
    c.drawString(margin_x, y, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 30

    # 1. Dataset Overview
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y, "1. Dataset Overview")
    y -= 20

    c.setFont("Helvetica", 10)
    lines = [
        f"Rows: {overview.get('n_rows', 0)}",
        f"Columns: {overview.get('n_cols', 0)}",
        f"Missing Cells: {overview.get('missing_cells', 0)} ({overview.get('missing_pct', 0):.2f}%)",
        f"Duplicate Rows: {overview.get('duplicate_rows', 0)}",
    ]
    for line in lines:
        c.drawString(margin_x, y, line)
        y -= 14

    # Overview Insights
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin_x, y, "Overview Insights:")
    y -= 18

    c.setFont("Helvetica", 10)
    for ins in overview_insights:
        y = _draw_wrapped(c, f"- {ins}", margin_x, y)
        y -= 4
        if y < 100:
            c.showPage()
            y = height - 2 * cm

    # 2. Column-Level Insights
    y -= 10
    if y < 120:
        c.showPage()
        y = height - 2 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y, "2. Column-Level Insights")
    y -= 20

    c.setFont("Helvetica", 10)
    # Limit to avoid huge PDFs
    for ins in col_insights[:60]:
        y = _draw_wrapped(c, f"- {ins}", margin_x, y)
        y -= 4
        if y < 100:
            c.showPage()
            y = height - 2 * cm

    # 3. Correlation Insights
    y -= 10
    if y < 120:
        c.showPage()
        y = height - 2 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y, "3. Correlation Insights")
    y -= 20

    c.setFont("Helvetica", 10)
    for ins in corr_insights:
        y = _draw_wrapped(c, f"- {ins}", margin_x, y)
        y -= 4
        if y < 100:
            c.showPage()
            y = height - 2 * cm

    # 4. Outlier Summary
    y -= 10
    if y < 120:
        c.showPage()
        y = height - 2 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y, "4. Outlier Summary (Preview)")
    y -= 20

    c.setFont("Helvetica", 10)
    for col, info in outliers.items():
        line = (
            f"{col}: {info['outlier_count']} outliers "
            f"({info['outlier_pct']:.1f}% of values), "
            f"normal range ≈ [{info['lower_bound']:.2f}, {info['upper_bound']:.2f}]"
        )
        y = _draw_wrapped(c, f"- {line}", margin_x, y)
        y -= 4
        if y < 100:
            c.showPage()
            y = height - 2 * cm

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

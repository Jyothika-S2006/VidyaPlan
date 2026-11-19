"""Decision memo PDF export using reportlab.

Generates a decision memo with:
- Title, date, data-as-of statement
- Assumptions table (costs, weights — all SIMULATED)
- Funded recommendations table
- Deferred items with reason codes
- Verify-First list (if available)
- Robustness summary (if stress-test has been run)
- Human review status and reviewer names
- Signature lines
- Footer disclaimer
- Diagonal DRAFT watermark unless plan is final

Uses only standard reportlab fonts to avoid Unicode issues.
Uses "Rs." not the rupee symbol.
"""
import io
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def generate_memo_pdf(
    plan: dict,
    recommendations: list[dict],
    costs: dict,
    weights: dict,
    voi_entries: Optional[list[dict]] = None,
    is_final: bool = False,
) -> bytes:
    """
    Generate a decision memo PDF for the given plan.

    Args:
        plan: Plan run dict (id, budget, budget_used, objective, status, created_at).
        recommendations: List of recommendation dicts.
        costs: Cost config dict (SIMULATED).
        weights: Weight config dict (SIMULATED).
        voi_entries: Optional list of VOI queue entries.
        is_final: If False, add DRAFT watermark.

    Returns:
        PDF bytes.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.pdfgen import canvas as pdfcanvas
    except ImportError:
        logger.error("reportlab not installed. Run: pip install reportlab")
        return b""

    buffer = io.BytesIO()

    # Custom canvas for watermark
    class WatermarkCanvas(pdfcanvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._is_final = is_final

        def showPage(self):
            if not self._is_final:
                self.saveState()
                self.setFont("Helvetica-Bold", 72)
                self.setFillColorRGB(0.85, 0.85, 0.85)
                self.setFillAlpha(0.25)
                self.translate(A4[0] / 2, A4[1] / 2)
                self.rotate(45)
                self.drawCentredString(0, 0, "DRAFT")
                self.restoreState()
            super().showPage()

        def save(self):
            super().save()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    h1 = styles["h1"]
    h2 = styles["h2"]
    normal = styles["Normal"]
    small = ParagraphStyle("small", parent=normal, fontSize=9, textColor=colors.grey)
    bold_style = ParagraphStyle("bold", parent=normal, fontName="Helvetica-Bold")

    story = []

    # ── Title ─────────────────────────────────────────────────────────────
    story.append(Paragraph("VidyaPlan — Infrastructure Investment Decision Memo", h1))
    story.append(Spacer(1, 0.3 * cm))

    plan_date = plan.get("created_at", datetime.now().isoformat())[:10]
    story.append(Paragraph(f"Plan ID: {plan.get('id', '?')}  |  Date: {plan_date}  |  Status: {plan.get('status', 'draft').upper()}", small))
    story.append(Spacer(1, 0.2 * cm))

    if not is_final:
        story.append(Paragraph("[DRAFT — Not yet finalised. All items pending human review.]", ParagraphStyle("warn", parent=normal, textColor=colors.red, fontName="Helvetica-Bold")))
        story.append(Spacer(1, 0.2 * cm))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.3 * cm))

    # ── Data-as-of statement ──────────────────────────────────────────────
    story.append(Paragraph("Data Notice", h2))
    story.append(Paragraph(
        "Official data observed 2017-18 (Karnataka Schools Facilities Survey). "
        "All cost and weight assumptions are SIMULATED hypothetical values, not official government figures. "
        "Verify all data before making real-world decisions.",
        normal,
    ))
    story.append(Spacer(1, 0.4 * cm))

    # ── Budget summary ────────────────────────────────────────────────────
    story.append(Paragraph("Budget Summary", h2))
    budget = plan.get("budget", 0)
    used = plan.get("budget_used", 0)
    pct = round(used / budget * 100, 1) if budget > 0 else 0
    summary_data = [
        ["Total Budget", f"Rs. {int(budget):,}"],
        ["Budget Used", f"Rs. {int(used):,} ({pct}%)"],
        ["Budget Remaining", f"Rs. {int(budget - used):,}"],
        ["Plan Objective Value", f"{plan.get('objective', 0):.2f}"],
    ]
    summary_table = Table(summary_data, colWidths=[8 * cm, 8 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.98)),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Cost assumptions ──────────────────────────────────────────────────
    story.append(Paragraph("Cost and Weight Assumptions [SIMULATED]", h2))
    story.append(Paragraph("All costs and priority weights are hypothetical. They are NOT official government estimates.", small))
    story.append(Spacer(1, 0.2 * cm))
    assumptions = [["Intervention", "Cost (SIMULATED)", "Priority Weight (SIMULATED)"]]
    for facility in ["electricity", "library", "computers"]:
        assumptions.append([
            facility.capitalize(),
            f"Rs. {int(costs.get(facility, 0)):,}",
            str(weights.get(facility, 0)),
        ])
    tbl = Table(assumptions, colWidths=[6 * cm, 6 * cm, 6 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.78, 0.71, 0.86)),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.4 * cm))

    # ── Funded recommendations ────────────────────────────────────────────
    selected = [r for r in recommendations if r.get("status") == "selected"]
    story.append(Paragraph(f"Funded Interventions ({len(selected)})", h2))
    if selected:
        funded_data = [["School", "Facility", "Cost", "Review Status"]]
        for rec in selected:
            funded_data.append([
                rec.get("school_name", f"School {rec.get('school_id', '?')}"),
                rec.get("facility_type", "").capitalize(),
                f"Rs. {int(rec.get('cost', 0)):,}",
                rec.get("review_status", "pending").upper(),
            ])
        tbl2 = Table(funded_data, colWidths=[7 * cm, 4 * cm, 4 * cm, 4 * cm])
        tbl2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.65, 0.82, 0.65)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
        ]))
        story.append(tbl2)
    else:
        story.append(Paragraph("No interventions funded in this plan.", small))
    story.append(Spacer(1, 0.4 * cm))

    # ── Deferred items ────────────────────────────────────────────────────
    deferred = [r for r in recommendations if r.get("status") == "deferred"]
    story.append(Paragraph(f"Deferred Items ({len(deferred)})", h2))
    if deferred:
        deferred_data = [["School", "Facility", "Cost", "Reason Code"]]
        for rec in deferred[:20]:  # cap to 20 for page length
            deferred_data.append([
                rec.get("school_name", f"School {rec.get('school_id', '?')}"),
                rec.get("facility_type", "").capitalize(),
                f"Rs. {int(rec.get('cost', 0)):,}",
                rec.get("reason_code", "OUT_OF_BUDGET"),
            ])
        tbl3 = Table(deferred_data, colWidths=[7 * cm, 4 * cm, 4 * cm, 4 * cm])
        tbl3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.9, 0.57, 0.57)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl3)
    story.append(Spacer(1, 0.4 * cm))

    # ── VOI Verify-First Queue ────────────────────────────────────────────
    if voi_entries:
        story.append(Paragraph("Verify-First Queue [SIMULATED]", h2))
        story.append(Paragraph("These field verifications could most improve the plan. Ranked by expected value of information.", small))
        story.append(Spacer(1, 0.2 * cm))
        voi_data = [["School", "Facility", "Action"]]
        for entry in voi_entries[:10]:
            voi_data.append([
                entry.get("school_name", ""),
                entry.get("facility", ""),
                entry.get("action_text", "")[:60],
            ])
        tbl4 = Table(voi_data, colWidths=[5 * cm, 3 * cm, 10 * cm])
        tbl4.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.95, 0.85, 0.65)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl4)
        story.append(Spacer(1, 0.4 * cm))

    # ── Signature lines ───────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Authorised by:", normal))
    story.append(Spacer(1, 1.5 * cm))
    sig_data = [
        ["Name: ____________________________", "Date: ____________________________"],
        ["Designation: _____________________", "Signature: _______________________"],
    ]
    sig_table = Table(sig_data, colWidths=[9 * cm, 9 * cm])
    sig_table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 10)]))
    story.append(sig_table)

    # ── Footer disclaimer ─────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "DISCLAIMER: Estimates are simulated; human review is required before real-world decisions. "
        "Official data observed 2017-18. Costs and weights are hypothetical (SIMULATED). "
        "Generated by VidyaPlan — School Infrastructure Planner.",
        small,
    ))

    doc.build(story, canvasmaker=WatermarkCanvas)
    return buffer.getvalue()

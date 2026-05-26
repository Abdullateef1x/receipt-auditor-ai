import uuid
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

REPORTS_DIR = Path("audit_reports")
REPORTS_DIR.mkdir(exist_ok=True)

STATUS_COLORS = {
    "approved": colors.HexColor("#27ae60"),
    "flagged": colors.HexColor("#e67e22"),
    "rejected": colors.HexColor("#e74c3c"),
}

SEVERITY_COLORS = {
    "low": colors.HexColor("#f1c40f"),
    "medium": colors.HexColor("#e67e22"),
    "high": colors.HexColor("#e74c3c"),
}


def generate_audit_report(
    extracted_data: dict,
    audit_result: dict,
    original_filename: str,
) -> str:
    report_id = str(uuid.uuid4())[:8].upper()
    report_name = f"audit_{report_id}_{original_filename}"
    report_path = REPORTS_DIR / report_name

    doc = SimpleDocTemplate(
        str(report_path),
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=18, spaceAfter=4)
    heading = ParagraphStyle("heading", parent=styles["Heading2"], fontSize=12, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=4)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=12, textColor=colors.HexColor("#666666"))

    story = []
    status = audit_result.get("status", "unknown").lower()
    status_color = STATUS_COLORS.get(status, colors.grey)

    # ── Header ──────────────────────────────────────────────
    story.append(Paragraph("ACME Corp — Expense Audit Report", title_style))
    story.append(Paragraph(f"Report ID: {report_id}  |  Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", small))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2c3e50")))
    story.append(Spacer(1, 10))

    # ── Status Banner ────────────────────────────────────────
    status_table = Table(
        [[Paragraph(f"AUDIT STATUS: {status.upper()}", ParagraphStyle(
            "status", parent=styles["Normal"],
            fontSize=14, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=1
        ))]],
        colWidths=[6.5 * inch],
    )
    status_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), status_color),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 16))

    # ── Invoice Details ──────────────────────────────────────
    story.append(Paragraph("Invoice Details", heading))
    invoice_data = [
        ["Field", "Value"],
        ["Vendor", extracted_data.get("vendor_name") or "N/A"],
        ["Invoice Number", extracted_data.get("invoice_number") or "N/A"],
        ["Date", extracted_data.get("date") or "N/A"],
        ["Payment Method", extracted_data.get("payment_method") or "N/A"],
        ["Currency", extracted_data.get("currency") or "USD"],
        ["Tax", f"${extracted_data.get('tax', 0):,.2f}"],
        ["Total Amount", f"${extracted_data.get('total_amount', 0):,.2f}"],
    ]
    invoice_table = Table(invoice_data, colWidths=[2.5 * inch, 4 * inch])
    invoice_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 14))

    # ── Line Items ───────────────────────────────────────────
    line_items = extracted_data.get("line_items", [])
    if line_items:
        story.append(Paragraph("Line Items", heading))
        line_data = [["Description", "Qty", "Unit Price", "Total"]]
        for item in line_items:
            line_data.append([
                item.get("description", ""),
                str(item.get("quantity", "")),
                f"${item.get('unit_price', 0):,.2f}",
                f"${item.get('total', 0):,.2f}",
            ])
        line_table = Table(line_data, colWidths=[3.2 * inch, 0.8 * inch, 1.2 * inch, 1.3 * inch])
        line_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 14))

    # ── Anomalies ────────────────────────────────────────────
    story.append(Paragraph("Anomaly Analysis", heading))
    anomalies = audit_result.get("anomalies", [])

    if not anomalies:
        story.append(Paragraph("No anomalies detected. This expense appears compliant.", body))
    else:
        anomaly_data = [["Field", "Issue", "Severity"]]
        for a in anomalies:
            anomaly_data.append([
                a.get("field", ""),
                a.get("issue", ""),
                a.get("severity", "").upper(),
            ])
        anomaly_table = Table(anomaly_data, colWidths=[1.5 * inch, 4 * inch, 1 * inch])
        anomaly_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff8f8")]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            *[
                ("TEXTCOLOR", (2, i + 1), (2, i + 1),
                 SEVERITY_COLORS.get(anomalies[i].get("severity", "low"), colors.grey))
                for i in range(len(anomalies))
            ],
            *[
                ("FONTNAME", (2, i + 1), (2, i + 1), "Helvetica-Bold")
                for i in range(len(anomalies))
            ],
        ]))
        story.append(anomaly_table)

    story.append(Spacer(1, 14))

    # ── Recommendation & Confidence ──────────────────────────
    story.append(Paragraph("Recommendation", heading))
    story.append(Paragraph(audit_result.get("recommendation", "N/A"), body))
    story.append(Spacer(1, 6))

    confidence = audit_result.get("confidence", 0)
    confidence_pct = f"{confidence * 100:.0f}%"
    story.append(Paragraph(f"AI Confidence Score: {confidence_pct}", body))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report was generated automatically by the ACME Corp Receipt Auditor AI. "
        "Final approval decisions remain with the designated approver per company policy.",
        small
    ))

    doc.build(story)
    return str(report_path)



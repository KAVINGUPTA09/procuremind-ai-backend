"""
===========================================================================
File: report_service.py

Project: ProcureMind AI

Purpose:
--------
Generates a professional procurement analysis PDF report.

The report contains:
1. RFQ summary
2. Vendor comparison
3. Vendor ranking
4. Compliance information
5. Selected vendor
6. AI executive summary
7. Strengths
8. Risks
9. Negotiation suggestions
10. Final procurement decision
===========================================================================
"""

from pathlib import Path

from reportlab.lib import colors

from reportlab.lib.enums import (
    TA_CENTER,
    TA_LEFT
)

from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.units import mm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)


# =========================================================================
# Report Directory
# =========================================================================

REPORT_DIR = Path(
    "app/reports"
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================================
# Helper Function
#
# Converts any value into safe printable text.
# =========================================================================

def safe_text(
    value
) -> str:

    if value is None:
        return "-"

    return str(value)


# =========================================================================
# Main PDF Generator
# =========================================================================

def generate_procurement_report(
    analysis_id: int,
    rfq_data: dict,
    vendors: list[dict],
    comparison: dict
) -> Path:

    """
    Generates one procurement analysis PDF
    and returns its file path.
    """

    # ---------------------------------------------------------------------
    # Final PDF path
    # ---------------------------------------------------------------------

    report_path = (
        REPORT_DIR
        /
        f"procurement_report_{analysis_id}.pdf"
    )


    # ---------------------------------------------------------------------
    # Create PDF document
    # ---------------------------------------------------------------------

    document = SimpleDocTemplate(
        str(report_path),

        pagesize=A4,

        rightMargin=18 * mm,
        leftMargin=18 * mm,

        topMargin=18 * mm,
        bottomMargin=18 * mm,

        title=(
            f"ProcureMind Procurement Report "
            f"{analysis_id}"
        ),

        author="ProcureMind AI"
    )


    # =========================================================================
    # Styles
    # =========================================================================

    styles = getSampleStyleSheet()


    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=27,
        alignment=TA_CENTER,
        spaceAfter=8
    )


    subtitle_style = ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=18
    )


    heading_style = ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=15,
        leading=19,
        spaceBefore=12,
        spaceAfter=8
    )


    body_style = ParagraphStyle(
        name="BodyTextCustom",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=6
    )


    small_style = ParagraphStyle(
        name="SmallText",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11
    )


    decision_style = ParagraphStyle(
        name="Decision",
        parent=styles["Heading2"],
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=10
    )


    # =========================================================================
    # Story
    # =========================================================================

    story = []


    # =========================================================================
    # TITLE
    # =========================================================================

    story.append(
        Paragraph(
            "ProcureMind AI",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Procurement Evaluation & Vendor Recommendation Report",
            subtitle_style
        )
    )


    story.append(
        Paragraph(
            f"Analysis ID: {analysis_id}",
            body_style
        )
    )


    story.append(
        Spacer(
            1,
            8
        )
    )


    # =========================================================================
    # RFQ SUMMARY
    # =========================================================================

    story.append(
        Paragraph(
            "1. RFQ Summary",
            heading_style
        )
    )


    rfq_summary = [

        [
            "Field",
            "Value"
        ],

        [
            "RFQ Title",
            safe_text(
                rfq_data.get(
                    "rfq_title"
                )
            )
        ],

        [
            "Department",
            safe_text(
                rfq_data.get(
                    "department"
                )
            )
        ],

        [
            "Currency",
            safe_text(
                rfq_data.get(
                    "currency"
                )
            )
        ],

        [
            "Required Delivery",
            (
                f"{safe_text(rfq_data.get('required_delivery_days'))} days"
            )
        ],

        [
            "Required Warranty",
            (
                f"{safe_text(rfq_data.get('required_warranty_months'))} months"
            )
        ]
    ]


    rfq_table = Table(
        rfq_summary,

        colWidths=[
            55 * mm,
            105 * mm
        ],

        repeatRows=1
    )


    rfq_table.setStyle(
        TableStyle(
            [

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ]
        )
    )


    story.append(
        rfq_table
    )


    story.append(
        Spacer(
            1,
            14
        )
    )


    # =========================================================================
    # RFQ ITEMS
    # =========================================================================

    story.append(
        Paragraph(
            "2. RFQ Items",
            heading_style
        )
    )


    item_rows = [

        [
            "Item",
            "Quantity",
            "Specifications"
        ]
    ]


    for item in rfq_data.get(
        "items",
        []
    ):

        specifications = item.get(
            "specifications",
            {}
        )


        specification_text = ", ".join(
            [
                f"{key}: {value}"

                for key, value
                in specifications.items()
            ]
        )


        item_rows.append(
            [

                safe_text(
                    item.get(
                        "item_name"
                    )
                ),

                safe_text(
                    item.get(
                        "required_quantity"
                    )
                ),

                Paragraph(
                    specification_text,
                    small_style
                )
            ]
        )


    item_table = Table(

        item_rows,

        colWidths=[
            42 * mm,
            30 * mm,
            88 * mm
        ],

        repeatRows=1
    )


    item_table.setStyle(
        TableStyle(
            [

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ]
        )
    )


    story.append(
        item_table
    )


    story.append(
        Spacer(
            1,
            16
        )
    )


    # =========================================================================
    # VENDOR RANKING
    # =========================================================================

    story.append(
        Paragraph(
            "3. Vendor Ranking & Scoring",
            heading_style
        )
    )


    scoring_result = comparison.get(
        "scoring_result",
        {}
    )


    rankings = scoring_result.get(
        "rankings",
        []
    )


    ranking_rows = [

        [
            "Rank",
            "Vendor",
            "Subtotal",
            "Compliance",
            "Delivery",
            "Warranty",
            "Final Score"
        ]
    ]


    for vendor in rankings:

        ranking_rows.append(
            [

                safe_text(
                    vendor.get(
                        "rank"
                    )
                ),

                Paragraph(
                    safe_text(
                        vendor.get(
                            "vendor_name"
                        )
                    ),
                    small_style
                ),

                safe_text(
                    vendor.get(
                        "subtotal"
                    )
                ),

                safe_text(
                    vendor.get(
                        "compliance_score"
                    )
                ),

                safe_text(
                    vendor.get(
                        "delivery_score"
                    )
                ),

                safe_text(
                    vendor.get(
                        "warranty_score"
                    )
                ),

                safe_text(
                    vendor.get(
                        "final_score"
                    )
                )
            ]
        )


    ranking_table = Table(

        ranking_rows,

        colWidths=[
            12 * mm,
            40 * mm,
            27 * mm,
            23 * mm,
            20 * mm,
            20 * mm,
            20 * mm
        ],

        repeatRows=1
    )


    ranking_table.setStyle(
        TableStyle(
            [

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7.5
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (0, -1),
                    "CENTER"
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ]
        )
    )


    story.append(
        ranking_table
    )


    story.append(
        Spacer(
            1,
            16
        )
    )


    # =========================================================================
    # VENDOR COMPLIANCE SUMMARY
    # =========================================================================

    story.append(
        Paragraph(
            "4. Vendor Compliance Summary",
            heading_style
        )
    )


    compliance_rows = [

        [
            "Vendor",
            "Subtotal",
            "Compliance %",
            "Final Score",
            "Rank"
        ]
    ]


    for vendor in vendors:

        vendor_structured_data = vendor.get(
            "structured_data",
            {}
        )


        compliance_rows.append(
            [

                Paragraph(
                    safe_text(
                        vendor_structured_data.get(
                            "vendor_name"
                        )
                    ),
                    small_style
                ),

                safe_text(
                    vendor.get(
                        "subtotal"
                    )
                ),

                safe_text(
                    vendor.get(
                        "compliance_percentage"
                    )
                ),

                safe_text(
                    vendor.get(
                        "final_score"
                    )
                ),

                safe_text(
                    vendor.get(
                        "rank"
                    )
                )
            ]
        )


    compliance_table = Table(

        compliance_rows,

        colWidths=[
            55 * mm,
            32 * mm,
            30 * mm,
            30 * mm,
            15 * mm
        ],

        repeatRows=1
    )


    compliance_table.setStyle(
        TableStyle(
            [

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "CENTER"
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ]
        )
    )


    story.append(
        compliance_table
    )


    story.append(
        PageBreak()
    )


    # =========================================================================
    # FINAL RECOMMENDATION
    # =========================================================================

    story.append(
        Paragraph(
            "5. AI Procurement Recommendation",
            heading_style
        )
    )


    ai_recommendation = comparison.get(
        "ai_recommendation",
        {}
    )


    best_vendor = ai_recommendation.get(
        "best_vendor",
        comparison.get(
            "best_vendor",
            "Not Available"
        )
    )


    story.append(
        Paragraph(
            f"<b>Recommended Vendor:</b> "
            f"{safe_text(best_vendor)}",
            body_style
        )
    )


    story.append(
        Spacer(
            1,
            5
        )
    )


    # =========================================================================
    # Executive Summary
    # =========================================================================

    story.append(
        Paragraph(
            "Executive Summary",
            heading_style
        )
    )


    story.append(
        Paragraph(
            safe_text(
                ai_recommendation.get(
                    "executive_summary",
                    comparison.get(
                        "executive_summary",
                        ""
                    )
                )
            ),
            body_style
        )
    )


    # =========================================================================
    # Selection Reasons
    # =========================================================================

    story.append(
        Paragraph(
            "Selection Reasons",
            heading_style
        )
    )


    selection_reasons = ai_recommendation.get(
        "selection_reasons",
        []
    )


    if selection_reasons:

        for reason in selection_reasons:

            story.append(
                Paragraph(
                    f"- {safe_text(reason)}",
                    body_style
                )
            )

    else:

        story.append(
            Paragraph(
                "No selection reasons provided.",
                body_style
            )
        )


    # =========================================================================
    # Strengths
    # =========================================================================

    story.append(
        Paragraph(
            "Strengths",
            heading_style
        )
    )


    strengths = ai_recommendation.get(
        "strengths",
        []
    )


    if strengths:

        for strength in strengths:

            story.append(
                Paragraph(
                    f"- {safe_text(strength)}",
                    body_style
                )
            )

    else:

        story.append(
            Paragraph(
                "No strengths provided.",
                body_style
            )
        )


    # =========================================================================
    # Risks
    # =========================================================================

    story.append(
        Paragraph(
            "Risks",
            heading_style
        )
    )


    risks = ai_recommendation.get(
        "risks",
        []
    )


    if risks:

        for risk in risks:

            story.append(
                Paragraph(
                    f"- {safe_text(risk)}",
                    body_style
                )
            )

    else:

        story.append(
            Paragraph(
                "No major risks identified.",
                body_style
            )
        )


    # =========================================================================
    # Other Vendor Analysis
    # =========================================================================

    story.append(
        Paragraph(
            "Other Vendor Analysis",
            heading_style
        )
    )


    other_vendor_analysis = ai_recommendation.get(
        "other_vendor_analysis",
        []
    )


    if other_vendor_analysis:

        for analysis in other_vendor_analysis:

            story.append(
                Paragraph(
                    f"- {safe_text(analysis)}",
                    body_style
                )
            )

    else:

        story.append(
            Paragraph(
                "No additional vendor analysis available.",
                body_style
            )
        )


    # =========================================================================
    # Negotiation Suggestions
    # =========================================================================

    story.append(
        Paragraph(
            "Negotiation Suggestions",
            heading_style
        )
    )


    negotiation_suggestions = (
        ai_recommendation.get(
            "negotiation_suggestions",
            []
        )
    )


    if negotiation_suggestions:

        for suggestion in negotiation_suggestions:

            story.append(
                Paragraph(
                    f"- {safe_text(suggestion)}",
                    body_style
                )
            )

    else:

        story.append(
            Paragraph(
                "No negotiation suggestions available.",
                body_style
            )
        )


    # =========================================================================
    # Final Decision
    # =========================================================================

    story.append(
        Spacer(
            1,
            10
        )
    )


    story.append(
        Paragraph(
            "6. Final Procurement Decision",
            heading_style
        )
    )


    final_decision = ai_recommendation.get(
        "final_decision",
        comparison.get(
            "final_decision",
            "Manual Review"
        )
    )


    story.append(
        Paragraph(
            f"<b>{safe_text(final_decision)}</b>",
            decision_style
        )
    )


    story.append(
        Spacer(
            1,
            15
        )
    )


    # =========================================================================
    # Footer Text
    # =========================================================================

    story.append(
        Paragraph(
            (
                "This report was automatically generated "
                "by ProcureMind AI using structured RFQ analysis, "
                "vendor compliance evaluation, scoring and "
                "AI-assisted procurement recommendations."
            ),
            small_style
        )
    )


    # =========================================================================
    # Build PDF
    # =========================================================================

    document.build(
        story
    )


    return report_path
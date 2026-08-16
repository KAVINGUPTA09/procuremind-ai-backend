"""
===========================================================================
File: procurement_crud.py

Project: ProcureMind AI

Purpose:
--------
Handles database operations for procurement analysis.

Responsibilities:
-----------------
1. Save processed RFQ data.
2. Save vendor quotation data.
3. Save compliance and score data.
4. Save final comparison result.
5. Save AI recommendation.
===========================================================================
"""

from sqlalchemy.orm import Session

from app.database.models import (
    RFQRecord,
    Vendor,
    VendorQuotationRecord,
    ComparisonResultRecord
)


# -------------------------------------------------------------------------
# Save RFQ
# -------------------------------------------------------------------------

def create_rfq_record(
    db: Session,
    user_id: int,
    filename: str,
    structured_rfq: dict
) -> RFQRecord:

    new_rfq = RFQRecord(
        user_id=user_id,
        filename=filename,
        rfq_title=structured_rfq.get(
            "rfq_title",
            "Untitled RFQ"
        ),
        department=structured_rfq.get(
            "department",
            "General"
        ),
        structured_data=structured_rfq
    )

    db.add(new_rfq)

    db.commit()

    db.refresh(new_rfq)

    return new_rfq


# -------------------------------------------------------------------------
# Save / Get Vendor
# -------------------------------------------------------------------------

def get_or_create_vendor(
    db: Session,
    company_name: str
) -> Vendor:

    vendor = (
        db.query(Vendor)
        .filter(
            Vendor.company_name == company_name
        )
        .first()
    )

    if vendor:
        return vendor

    vendor = Vendor(
        company_name=company_name
    )

    db.add(vendor)

    db.commit()

    db.refresh(vendor)

    return vendor


# -------------------------------------------------------------------------
# Save Vendor Quotation
# -------------------------------------------------------------------------

def create_vendor_quotation_record(
    db: Session,
    rfq_id: int,
    vendor_id: int,
    filename: str,
    vendor_data: dict,
    compliance_report: dict,
    score_data: dict
) -> VendorQuotationRecord:

    quotation = VendorQuotationRecord(
        rfq_id=rfq_id,
        vendor_id=vendor_id,
        filename=filename,

        subtotal=score_data.get(
            "subtotal",
            0.0
        ),

        compliance_percentage=(
            compliance_report.get(
                "compliance_percentage",
                0.0
            )
        ),

        final_score=score_data.get(
            "final_score",
            0.0
        ),

        rank=score_data.get(
            "rank",
            0
        ),

        structured_data=vendor_data,

        compliance_report=compliance_report
    )

    db.add(quotation)

    db.commit()

    db.refresh(quotation)

    return quotation


# -------------------------------------------------------------------------
# Save Final Comparison Result
# -------------------------------------------------------------------------

def create_comparison_result(
    db: Session,
    rfq_id: int,
    scoring_result: dict,
    ai_recommendation: dict
) -> ComparisonResultRecord:

    comparison = ComparisonResultRecord(
        rfq_id=rfq_id,

        best_vendor=scoring_result.get(
            "best_vendor",
            "Unknown"
        ),

        final_decision=ai_recommendation.get(
            "final_decision",
            "Manual Review Required"
        ),

        executive_summary=ai_recommendation.get(
            "executive_summary",
            ""
        ),

        scoring_result=scoring_result,

        ai_recommendation=ai_recommendation
    )

    db.add(comparison)

    db.commit()

    db.refresh(comparison)

    return comparison
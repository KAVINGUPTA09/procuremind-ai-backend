"""
===========================================================================
File: report_routes.py

Project: ProcureMind AI

Purpose:
--------
Provides API endpoints for generating and downloading
procurement analysis reports.

Security:
---------
Only the owner of the procurement analysis
can generate/download its PDF report.
===========================================================================
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from fastapi.responses import FileResponse

from sqlalchemy import select

from sqlalchemy.orm import Session

from app.database.database import (
    get_db
)

from app.database.models import (
    User,
    RFQRecord,
    VendorQuotationRecord,
    ComparisonResultRecord
)

from app.dependencies.auth_dependencies import (
    get_current_user
)

from app.services.report_services import (
    generate_procurement_report
)


# =========================================================================
# Router
# =========================================================================

router = APIRouter(
    prefix="/reports",
    tags=["Procurement Reports"]
)


# =========================================================================
# Dependencies
# =========================================================================

DatabaseSession = Annotated[
    Session,
    Depends(get_db)
]


CurrentUser = Annotated[
    User,
    Depends(get_current_user)
]


# =========================================================================
# GET /reports/{analysis_id}/pdf
#
# Purpose:
# Generates and downloads a PDF procurement report.
# =========================================================================

@router.get(
    "/{analysis_id}/pdf"
)
def download_procurement_report(

    analysis_id: int,

    db: DatabaseSession,

    current_user: CurrentUser
):

    """
    Generates and downloads a professional
    procurement report for one saved analysis.
    """


    # =====================================================================
    # STEP 1
    # Find RFQ belonging to logged-in user
    # =====================================================================

    role = (current_user.role or "buyer").lower()

    rfq_statement = select(RFQRecord).where(RFQRecord.id == analysis_id)

    # Buyers can only download their own reports. Approvers/admins can review
    # organisation-wide analyses as part of the B2B approval workflow.
    if role == "buyer":
        rfq_statement = rfq_statement.where(RFQRecord.user_id == current_user.id)


    rfq_result = db.execute(
        rfq_statement
    )


    rfq = (
        rfq_result.scalar_one_or_none()
    )


    if rfq is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Procurement analysis not found."
            )
        )


    # =====================================================================
    # STEP 2
    # Get vendor quotations
    # =====================================================================

    vendor_statement = (

        select(
            VendorQuotationRecord
        )

        .where(

            VendorQuotationRecord.rfq_id
            ==
            rfq.id
        )

        .order_by(
            VendorQuotationRecord.rank
        )
    )


    vendor_result = db.execute(
        vendor_statement
    )


    vendor_records = (
        vendor_result.scalars().all()
    )


    # =====================================================================
    # STEP 3
    # Get final comparison
    # =====================================================================

    comparison_statement = (

        select(
            ComparisonResultRecord
        )

        .where(

            ComparisonResultRecord.rfq_id
            ==
            rfq.id
        )
    )


    comparison_result = db.execute(
        comparison_statement
    )


    comparison = (
        comparison_result.scalar_one_or_none()
    )


    if comparison is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Comparison result not found."
            )
        )


    # =====================================================================
    # STEP 4
    # Prepare RFQ Data
    # =====================================================================

    rfq_data = (
        rfq.structured_data
    )


    # =====================================================================
    # STEP 5
    # Prepare Vendor Data
    # =====================================================================

    vendors = []


    for vendor in vendor_records:

        vendors.append(
            {

                "id": (
                    vendor.id
                ),

                "vendor_id": (
                    vendor.vendor_id
                ),

                "filename": (
                    vendor.filename
                ),

                "subtotal": (
                    vendor.subtotal
                ),

                "compliance_percentage": (
                    vendor.compliance_percentage
                ),

                "final_score": (
                    vendor.final_score
                ),

                "rank": (
                    vendor.rank
                ),

                "structured_data": (
                    vendor.structured_data
                ),

                "compliance_report": (
                    vendor.compliance_report
                )
            }
        )


    # =====================================================================
    # STEP 6
    # Prepare Comparison Data
    # =====================================================================

    comparison_data = {

        "id": comparison.id,

        "best_vendor": (
            comparison.best_vendor
        ),

        "final_decision": (
            comparison.final_decision
        ),

        "executive_summary": (
            comparison.executive_summary
        ),

        "scoring_result": (
            comparison.scoring_result
        ),

        "ai_recommendation": (
            comparison.ai_recommendation
        )
    }


    # =====================================================================
    # STEP 7
    # Generate PDF
    # =====================================================================

    try:

        report_path = (
            generate_procurement_report(

                analysis_id=(
                    analysis_id
                ),

                rfq_data=(
                    rfq_data
                ),

                vendors=(
                    vendors
                ),

                comparison=(
                    comparison_data
                )
            )
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate procurement report: "
                f"{type(error).__name__}: {str(error)}"
            )
        ) from error


    # =====================================================================
    # STEP 8
    # Download PDF
    # =====================================================================

    return FileResponse(

        path=str(
            report_path
        ),

        media_type="application/pdf",

        filename=(
            f"ProcureMind_Report_{analysis_id}.pdf"
        )
    )
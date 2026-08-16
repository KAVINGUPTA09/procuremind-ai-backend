from fastapi.encoders import jsonable_encoder

from app.graph.state import ProcurementState

from app.services.pdf_service import (
    extract_text_from_pdf
)

from app.services.llm_services import (
    extract_rfq_data,
    extract_vendor_data
)

from app.services.compilance_services import (
    calculate_vendor_compliance
)

from app.services.scoring import (
    calculate_vendor_scores
)

from app.services.recommendation_service import (
    generate_vendor_recommendation
)

from app.database.database import (
    SessionLocal
)

from app.crud.procurement_crud import (
    create_rfq_record,
    get_or_create_vendor,
    create_vendor_quotation_record,
    create_comparison_result
)


# =========================================================
# NODE 1
# RFQ Extraction
# =========================================================

def extract_rfq_node(
    state: ProcurementState
) -> dict:

    rfq_text = extract_text_from_pdf(
        state["rfq_file_path"]
    )

    structured_rfq = extract_rfq_data(
        rfq_text
    )

    # IMPORTANT:
    # Do NOT convert this to dict here.
    # Existing compliance service expects
    # Pydantic-object attribute access.
    return {
        "rfq_data": structured_rfq,
        "workflow_status": "RFQ extracted"
    }


# =========================================================
# NODE 2
# Vendor Extraction
# =========================================================

def extract_vendors_node(
    state: ProcurementState
) -> dict:

    vendors = []

    for vendor_path in state[
        "vendor_file_paths"
    ]:

        vendor_text = extract_text_from_pdf(
            vendor_path
        )

        structured_vendor = (
            extract_vendor_data(
                vendor_text
            )
        )

        # Keep Pydantic object as-is.
        vendors.append(
            structured_vendor
        )

    return {
        "vendors": vendors,
        "workflow_status": "Vendors extracted"
    }


# =========================================================
# NODE 3
# Data Validation
# =========================================================

def data_validation_node(
    state: ProcurementState
) -> dict:

    rfq_data = state.get(
        "rfq_data"
    )

    vendors = state.get(
        "vendors",
        []
    )

    reasons = []


    # RFQ validation
    if rfq_data is None:

        reasons.append(
            "RFQ data missing"
        )

    else:

        if not getattr(
            rfq_data,
            "items",
            None
        ):

            reasons.append(
                "RFQ items missing"
            )


    # Vendor count validation
    if len(vendors) < 2:

        reasons.append(
            "At least two vendors required"
        )


    # Vendor validation
    for index, vendor in enumerate(
        vendors
    ):

        if not getattr(
            vendor,
            "vendor_name",
            None
        ):

            reasons.append(
                f"Vendor {index + 1} name missing"
            )

        if not getattr(
            vendor,
            "line_items",
            None
        ):

            reasons.append(
                f"Vendor {index + 1} items missing"
            )


    if reasons:

        return {
            "data_complete": False,
            "missing_data_reason": (
                " | ".join(reasons)
            ),
            "requires_manual_review": True,
            "review_reason": (
                "Incomplete procurement data"
            ),
            "workflow_status": (
                "Data validation failed"
            )
        }


    return {
        "data_complete": True,
        "missing_data_reason": "",
        "workflow_status": (
            "Data validation passed"
        )
    }


# =========================================================
# NODE 4
# Compliance Calculation
# =========================================================

def compliance_node(
    state: ProcurementState
) -> dict:

    rfq_data = state[
        "rfq_data"
    ]

    vendors = state[
        "vendors"
    ]

    reports = []

    updated_vendors = []


    for vendor in vendors:

        report = (
            calculate_vendor_compliance(
                rfq_data,
                vendor
            )
        )


        # Keep vendor as a Pydantic object.
        updated_vendor = vendor.model_copy(
            update={
                "technical_compliance_percent": (
                    report[
                        "compliance_percentage"
                    ]
                )
            }
        )


        updated_vendors.append(
            updated_vendor
        )


        reports.append(
            {
                "vendor_name": (
                    vendor.vendor_name
                ),

                "report": jsonable_encoder(
                    report
                )
            }
        )


    return {
        "vendors": updated_vendors,
        "compliance_reports": reports,
        "workflow_status": (
            "Compliance calculated"
        )
    }


# =========================================================
# NODE 5
# Compliance Validation
# =========================================================

def compliance_validation_node(
    state: ProcurementState
) -> dict:

    reports = state.get(
        "compliance_reports",
        []
    )

    percentages = []


    for item in reports:

        report = item.get(
            "report",
            {}
        )

        percentages.append(
            report.get(
                "compliance_percentage",
                0
            )
        )


    if not percentages:

        return {
            "compliance_passed": False,
            "compliance_reason": (
                "No compliance data"
            ),
            "requires_manual_review": True,
            "review_reason": (
                "Compliance unavailable"
            ),
            "workflow_status": (
                "Compliance validation failed"
            )
        }


    best_compliance = max(
        percentages
    )


    if best_compliance < 70:

        return {
            "compliance_passed": False,
            "compliance_reason": (
                "No vendor crossed 70% compliance"
            ),
            "requires_manual_review": True,
            "review_reason": (
                "All vendors have low compliance"
            ),
            "workflow_status": (
                "Compliance validation failed"
            )
        }


    return {
        "compliance_passed": True,
        "compliance_reason": (
            "Acceptable vendor exists"
        ),
        "workflow_status": (
            "Compliance validation passed"
        )
    }


# =========================================================
# NODE 6
# Scoring
# =========================================================

def scoring_node(
    state: ProcurementState
) -> dict:

    scoring_result = (
        calculate_vendor_scores(
            state["vendors"]
        )
    )

    return {
        "scoring_result": (
            jsonable_encoder(
                scoring_result
            )
        ),
        "workflow_status": (
            "Vendor scoring completed"
        )
    }


# =========================================================
# NODE 7
# AI Recommendation
# =========================================================

def recommendation_node(
    state: ProcurementState
) -> dict:

    vendor_details = [

        jsonable_encoder(
            vendor
        )

        for vendor in state["vendors"]
    ]


    recommendation = (
        generate_vendor_recommendation(

            scoring_result=(
                state["scoring_result"]
            ),

            compliance_reports=(
                state[
                    "compliance_reports"
                ]
            ),

            vendor_details=(
                vendor_details
            )
        )
    )


    return {
        "ai_recommendation": (
            jsonable_encoder(
                recommendation
            )
        ),
        "workflow_status": (
            "AI recommendation generated"
        )
    }


# =========================================================
# NODE 8
# Final Risk Check
# =========================================================

def final_risk_node(
    state: ProcurementState
) -> dict:

    recommendation = state.get(
        "ai_recommendation",
        {}
    )

    scoring = state.get(
        "scoring_result",
        {}
    )


    final_decision = (
        recommendation.get(
            "final_decision",
            ""
        )
    )


    rankings = scoring.get(
        "rankings",
        []
    )


    top_score = 0


    if rankings:

        top_score = rankings[
            0
        ].get(
            "final_score",
            0
        )


    if (
        final_decision.lower()
        !=
        "approve"
        or
        top_score < 70
    ):

        return {
            "requires_manual_review": True,
            "review_reason": (
                "Final risk check failed"
            ),
            "workflow_status": (
                "Manual review required"
            )
        }


    return {
        "requires_manual_review": False,
        "review_reason": "",
        "workflow_status": (
            "Final risk check passed"
        )
    }


# =========================================================
# NODE 9
# Manual Review
# =========================================================

def manual_review_node(
    state: ProcurementState
) -> dict:

    return {
        "requires_manual_review": True,
        "workflow_status": (
            "Sent for manual review"
        ),
        "review_reason": state.get(
            "review_reason",
            "Manual review required"
        )
    }


# =========================================================
# NODE 10
# Database Persistence
# =========================================================

def database_node(
    state: ProcurementState
) -> dict:

    db = SessionLocal()

    try:

        # Convert Pydantic RFQ into JSON-safe dict
        rfq_dict = jsonable_encoder(
            state["rfq_data"]
        )


        saved_rfq = create_rfq_record(
            db=db,
            user_id=state["user_id"],
            filename=state["rfq_filename"],
            structured_rfq=rfq_dict
        )


        vendors = state.get(
            "vendors",
            []
        )

        compliance_reports = state.get(
            "compliance_reports",
            []
        )

        scoring_result = state.get(
            "scoring_result",
            {}
        )

        rankings = scoring_result.get(
            "rankings",
            []
        )

        vendor_filenames = state.get(
            "vendor_filenames",
            []
        )


        for index, vendor in enumerate(
            vendors
        ):

            vendor_dict = jsonable_encoder(
                vendor
            )


            vendor_record = (
                get_or_create_vendor(
                    db=db,
                    company_name=(
                        vendor.vendor_name
                    )
                )
            )


            score_data = {}


            for ranking in rankings:

                if (
                    ranking.get(
                        "vendor_name"
                    )
                    ==
                    vendor.vendor_name
                ):

                    score_data = ranking

                    break


            compliance_report = {}


            if index < len(
                compliance_reports
            ):

                compliance_entry = (
                    compliance_reports[
                        index
                    ]
                )

                compliance_report = (
                    compliance_entry.get(
                        "report",
                        {}
                    )
                )


            vendor_filename = (
                f"vendor_{index + 1}.pdf"
            )


            if index < len(
                vendor_filenames
            ):

                vendor_filename = (
                    vendor_filenames[
                        index
                    ]
                )


            create_vendor_quotation_record(
                db=db,
                rfq_id=saved_rfq.id,
                vendor_id=vendor_record.id,
                filename=vendor_filename,
                vendor_data=vendor_dict,
                compliance_report=(
                    compliance_report
                ),
                score_data=score_data
            )


        saved_comparison = (
            create_comparison_result(
                db=db,
                rfq_id=saved_rfq.id,
                scoring_result=(
                    scoring_result
                ),
                ai_recommendation=(
                    state.get(
                        "ai_recommendation",
                        {}
                    )
                )
            )
        )


        return {
            "analysis_id": (
                saved_rfq.id
            ),
            "comparison_id": (
                saved_comparison.id
            ),
            "workflow_status": (
                "Procurement analysis "
                "saved successfully"
            )
        }


    except Exception as error:

        db.rollback()

        return {
            "workflow_status": (
                "Database persistence failed"
            ),
            "error_message": str(
                error
            ),
            "requires_manual_review": True,
            "review_reason": (
                "Procurement analysis "
                "could not be saved"
            )
        }


    finally:

        db.close()
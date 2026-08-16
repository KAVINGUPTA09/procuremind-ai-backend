from typing import (
    TypedDict,
    Any
)


class ProcurementState(
    TypedDict,
    total=False
):
    """
    Shared state for the ProcureMind LangGraph workflow.
    """

    # ---------------------------------------------------------
    # User / Request Information
    # ---------------------------------------------------------

    user_id: int

    rfq_file_path: str

    vendor_file_paths: list[str]

    rfq_filename: str

    vendor_filenames: list[str]


    # ---------------------------------------------------------
    # Extracted Procurement Data
    #
    # Important:
    # RFQ data and vendor data may remain as
    # Pydantic objects because existing services
    # use attribute access such as:
    #
    # rfq.required_delivery_days
    # vendor.vendor_name
    # ---------------------------------------------------------

    rfq_data: Any

    vendors: list[Any]


    # ---------------------------------------------------------
    # Compliance Results
    # ---------------------------------------------------------

    compliance_reports: list[
        dict[str, Any]
    ]


    # ---------------------------------------------------------
    # Scoring / Ranking
    # ---------------------------------------------------------

    scoring_result: dict[
        str,
        Any
    ]


    # ---------------------------------------------------------
    # AI Recommendation
    # ---------------------------------------------------------

    ai_recommendation: dict[
        str,
        Any
    ]


    # ---------------------------------------------------------
    # CONDITION 1
    # Data completeness
    # ---------------------------------------------------------

    data_complete: bool

    missing_data_reason: str


    # ---------------------------------------------------------
    # CONDITION 2
    # Compliance validation
    # ---------------------------------------------------------

    compliance_passed: bool

    compliance_reason: str


    # ---------------------------------------------------------
    # CONDITION 3
    # Final risk / approval
    # ---------------------------------------------------------

    requires_manual_review: bool

    review_reason: str


    # ---------------------------------------------------------
    # Workflow Status
    # ---------------------------------------------------------

    workflow_status: str

    error_message: str


    # ---------------------------------------------------------
    # Database Results
    # ---------------------------------------------------------

    analysis_id: int

    comparison_id: int
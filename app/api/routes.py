"""
===========================================================================
File: routes.py

Project: ProcureMind AI
Author : Kavin Gupta

Purpose:
--------
Defines all procurement-related API endpoints.

Responsibilities:
-----------------
1. Receive procurement API requests.
2. Protect procurement APIs using JWT authentication.
3. Process RFQ and Vendor PDFs.
4. Extract structured information using LLM.
5. Calculate compliance.
6. Score and rank vendors.
7. Run LangGraph orchestration for multi-vendor analysis.
8. Save procurement analysis in PostgreSQL through LangGraph database node.
9. Return structured API responses.
10. Invalidate Redis history cache after a new analysis is saved.
===========================================================================
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    UploadFile as FastAPIUploadFile,
    File,
    HTTPException,
    Depends
)

from fastapi.encoders import jsonable_encoder

from pydantic import WithJsonSchema


# =========================================================================
# Pydantic Models
# =========================================================================

from app.models.schemas import (
    VendorQuotation,
    ComparisonResult
)


# =========================================================================
# PDF Service
# =========================================================================

from app.services.pdf_service import (
    save_uploaded_file,
    extract_text_from_pdf
)


# =========================================================================
# LLM Extraction Service
# =========================================================================

from app.services.llm_services import (
    extract_rfq_data,
    extract_vendor_data
)


# =========================================================================
# Compliance Service
# =========================================================================

from app.services.compilance_services import (
    calculate_vendor_compliance
)


# =========================================================================
# Scoring Service
# =========================================================================

from app.services.scoring import (
    calculate_vendor_scores
)


# =========================================================================
# Redis Service
# =========================================================================

from app.services.redis_service import (
    redis_client
)


# =========================================================================
# Database Models
# =========================================================================

from app.database.models import (
    User
)


# =========================================================================
# Authentication
# =========================================================================

from app.dependencies.auth_dependencies import (
    get_current_user
)


# =========================================================================
# LangGraph Workflow
# =========================================================================

from app.graph.workflow import (
    procurement_graph
)


# =========================================================================
# Swagger Compatible File Type
# =========================================================================

SwaggerUploadFile = Annotated[
    FastAPIUploadFile,
    WithJsonSchema(
        {
            "type": "string",
            "format": "binary"
        }
    )
]


# =========================================================================
# Procurement Router
#
# Every procurement API requires authentication.
# =========================================================================

router = APIRouter(
    prefix="/procurement",
    tags=["Procurement AI"],
    dependencies=[
        Depends(get_current_user)
    ]
)


# =========================================================================
# 1. Compare Structured Vendor Quotations
#
# POST /procurement/compare
# =========================================================================

@router.post(
    "/compare",
    response_model=ComparisonResult
)
def compare_vendor_quotations(
    quotations: list[VendorQuotation]
) -> ComparisonResult:

    """
    Compares already structured vendor quotations.
    """

    if len(quotations) < 2:

        raise HTTPException(
            status_code=400,
            detail=(
                "At least two vendor quotations are required."
            )
        )

    result = calculate_vendor_scores(
        quotations
    )

    return result


# =========================================================================
# 2. Upload RFQ PDF
#
# POST /procurement/upload-rfq
# =========================================================================

@router.post("/upload-rfq")
async def upload_rfq_pdf(

    file: SwaggerUploadFile = File(
        ...,
        description="Upload one RFQ PDF"
    )
):

    """
    Uploads one RFQ PDF and converts it
    into structured RFQ information.
    """

    saved_file = await save_uploaded_file(
        file
    )

    extracted_text = extract_text_from_pdf(
        saved_file
    )

    structured_rfq = extract_rfq_data(
        extracted_text
    )

    return {

        "message": (
            "RFQ processed successfully."
        ),

        "filename": file.filename,

        "structured_data": jsonable_encoder(
            structured_rfq
        )
    }


# =========================================================================
# 3. Upload Vendor PDF
#
# POST /procurement/upload-vendor
# =========================================================================

@router.post("/upload-vendor")
async def upload_vendor_pdf(

    file: SwaggerUploadFile = File(
        ...,
        description="Upload one vendor quotation PDF"
    )
):

    """
    Uploads one vendor PDF and converts it
    into structured vendor information.
    """

    saved_file = await save_uploaded_file(
        file
    )

    extracted_text = extract_text_from_pdf(
        saved_file
    )

    structured_vendor = extract_vendor_data(
        extracted_text
    )

    return {

        "message": (
            "Vendor quotation processed successfully."
        ),

        "filename": file.filename,

        "structured_data": jsonable_encoder(
            structured_vendor
        )
    }


# =========================================================================
# 4. Compare One RFQ With One Vendor
#
# POST /procurement/compare-pdf
# =========================================================================

@router.post("/compare-pdf")
async def compare_pdf_quotation(

    rfq_file: SwaggerUploadFile = File(
        ...,
        description="Upload one RFQ PDF"
    ),

    vendor_file: SwaggerUploadFile = File(
        ...,
        description="Upload one vendor quotation PDF"
    )
):

    """
    Compares one RFQ PDF with one vendor quotation PDF.

    This endpoint calculates compliance only.
    Ranking requires multiple vendors.
    """

    # ---------------------------------------------------------------------
    # Save PDFs
    # ---------------------------------------------------------------------

    saved_rfq_file = await save_uploaded_file(
        rfq_file
    )

    saved_vendor_file = await save_uploaded_file(
        vendor_file
    )


    # ---------------------------------------------------------------------
    # Extract text
    # ---------------------------------------------------------------------

    rfq_text = extract_text_from_pdf(
        saved_rfq_file
    )

    vendor_text = extract_text_from_pdf(
        saved_vendor_file
    )


    # ---------------------------------------------------------------------
    # Structured Extraction
    # ---------------------------------------------------------------------

    structured_rfq = extract_rfq_data(
        rfq_text
    )

    structured_vendor = extract_vendor_data(
        vendor_text
    )


    # ---------------------------------------------------------------------
    # Compliance Calculation
    # ---------------------------------------------------------------------

    compliance_report = calculate_vendor_compliance(
        structured_rfq,
        structured_vendor
    )


    # ---------------------------------------------------------------------
    # Update actual compliance
    # ---------------------------------------------------------------------

    updated_vendor = structured_vendor.model_copy(
        update={
            "technical_compliance_percent": (
                compliance_report[
                    "compliance_percentage"
                ]
            )
        }
    )


    return {

        "message": (
            "RFQ and vendor quotation "
            "compared successfully."
        ),

        "rfq_filename": (
            rfq_file.filename
        ),

        "vendor_filename": (
            vendor_file.filename
        ),

        "structured_rfq": jsonable_encoder(
            structured_rfq
        ),

        "structured_vendor": jsonable_encoder(
            updated_vendor
        ),

        "compliance_report": jsonable_encoder(
            compliance_report
        )
    }


# =========================================================================
# 5. MAIN LANGGRAPH PROCUREMENT PIPELINE
#
# POST /procurement/compare-multiple-pdfs
#
# Flow:
#
# User
#   ↓
# FastAPI
#   ↓
# Save RFQ + Vendor PDFs
#   ↓
# Initial LangGraph State
#   ↓
# RFQ Extraction Node
#   ↓
# Vendor Extraction Node
#   ↓
# Data Validation
#   ↓
# Conditional Routing
#   ↓
# Compliance
#   ↓
# Compliance Validation
#   ↓
# Conditional Routing
#   ↓
# Scoring
#   ↓
# AI Recommendation
#   ↓
# Final Risk Check
#   ↓
# Database OR Manual Review
#   ↓
# END
# =========================================================================

@router.post("/compare-multiple-pdfs")
async def compare_multiple_pdf_quotations(

    current_user: Annotated[
        User,
        Depends(get_current_user)
    ],

    rfq_file: SwaggerUploadFile = File(
        ...,
        description="Upload one RFQ PDF"
    ),

    vendor_files: list[
        SwaggerUploadFile
    ] = File(
        ...,
        description=(
            "Upload at least two vendor quotation PDFs"
        )
    )
):

    """
    Runs the complete ProcureMind procurement workflow
    using LangGraph orchestration.
    """


    # =====================================================================
    # STEP 1
    # Validate Vendor Count
    # =====================================================================

    if len(vendor_files) < 2:

        raise HTTPException(
            status_code=400,
            detail=(
                "At least two vendor PDF files are required."
            )
        )


    # =====================================================================
    # STEP 2
    # Save RFQ PDF
    # =====================================================================

    saved_rfq_path = await save_uploaded_file(
        rfq_file
    )


    # =====================================================================
    # STEP 3
    # Save Vendor PDFs
    # =====================================================================

    saved_vendor_paths = []

    for vendor_file in vendor_files:

        saved_vendor_path = await save_uploaded_file(
            vendor_file
        )

        saved_vendor_paths.append(
            str(saved_vendor_path)
        )


    # =====================================================================
    # STEP 4
    # Create Initial LangGraph State
    # =====================================================================

    initial_state = {

        "user_id": (
            current_user.id
        ),

        "rfq_file_path": (
            str(saved_rfq_path)
        ),

        "vendor_file_paths": (
            saved_vendor_paths
        ),

        "rfq_filename": (
            rfq_file.filename
        ),

        "vendor_filenames": [
            vendor_file.filename
            for vendor_file
            in vendor_files
        ],

        "requires_manual_review": False,

        "workflow_status": (
            "Procurement workflow started"
        ),

        "error_message": ""
    }


    # =====================================================================
    # STEP 5
    # Invoke LangGraph Workflow
    # =====================================================================

    try:

        result = procurement_graph.invoke(
            initial_state
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "LangGraph procurement workflow failed: "
                f"{type(error).__name__}: "
                f"{str(error)}"
            )
        ) from error


    # =====================================================================
    # STEP 6
    # Check Workflow Error
    # =====================================================================

    error_message = result.get(
        "error_message",
        ""
    )

    if error_message:

        raise HTTPException(
            status_code=500,
            detail=(
                "Procurement workflow failed: "
                f"{error_message}"
            )
        )


    # =====================================================================
    # STEP 7
    # Manual Review Branch
    # =====================================================================

    if result.get(
        "requires_manual_review",
        False
    ):

        return {

            "message": (
                "Procurement workflow completed "
                "but requires manual review."
            ),

            "workflow_status": (
                result.get(
                    "workflow_status"
                )
            ),

            "user_id": (
                current_user.id
            ),

            "rfq_filename": (
                rfq_file.filename
            ),

            "vendor_count": (
                len(vendor_files)
            ),

            "data_complete": (
                result.get(
                    "data_complete"
                )
            ),

            "missing_data_reason": (
                result.get(
                    "missing_data_reason",
                    ""
                )
            ),

            "compliance_passed": (
                result.get(
                    "compliance_passed"
                )
            ),

            "compliance_reason": (
                result.get(
                    "compliance_reason",
                    ""
                )
            ),

            "requires_manual_review": True,

            "analysis_id": result.get("analysis_id"),

            "comparison_id": result.get("comparison_id"),

            "review_reason": (
                result.get(
                    "review_reason",
                    "Manual review required."
                )
            )
        }


    # =====================================================================
    # STEP 8
    # INVALIDATE REDIS HISTORY CACHE
    #
    # LangGraph has already saved the new analysis to PostgreSQL.
    # The old cached history is now stale, so delete it.
    # =====================================================================

    try:

        redis_client.delete(
            f"history:user:{current_user.id}"
        )

    except Exception as redis_error:

        # Redis failure should NOT break procurement analysis.
        print(
            "Redis cache invalidation error:",
            redis_error
        )


    # =====================================================================
    # STEP 9
    # Successful LangGraph Response
    # =====================================================================

    return {

        "message": (
            "Procurement analysis completed "
            "successfully using LangGraph."
        ),

        "workflow_status": (
            result.get(
                "workflow_status"
            )
        ),


        # -------------------------------------------------------------
        # Database IDs
        # -------------------------------------------------------------

        "analysis_id": (
            result.get(
                "analysis_id"
            )
        ),

        "comparison_id": (
            result.get(
                "comparison_id"
            )
        ),

        "user_id": (
            current_user.id
        ),


        # -------------------------------------------------------------
        # Input Information
        # -------------------------------------------------------------

        "rfq_filename": (
            rfq_file.filename
        ),

        "vendor_count": (
            len(vendor_files)
        ),


        # -------------------------------------------------------------
        # LangGraph Conditions
        # -------------------------------------------------------------

        "data_complete": (
            result.get(
                "data_complete"
            )
        ),

        "compliance_passed": (
            result.get(
                "compliance_passed"
            )
        ),

        "requires_manual_review": (
            result.get(
                "requires_manual_review",
                False
            )
        ),

        "review_reason": (
            result.get(
                "review_reason",
                ""
            )
        ),


        # -------------------------------------------------------------
        # RFQ Result
        # -------------------------------------------------------------

        "structured_rfq": (
            jsonable_encoder(
                result.get(
                    "rfq_data"
                )
            )
        ),


        # -------------------------------------------------------------
        # Vendor Results
        # -------------------------------------------------------------

        "vendors": [

            jsonable_encoder(
                vendor
            )

            for vendor in result.get(
                "vendors",
                []
            )
        ],


        # -------------------------------------------------------------
        # Compliance Results
        # -------------------------------------------------------------

        "compliance_reports": (
            result.get(
                "compliance_reports",
                []
            )
        ),


        # -------------------------------------------------------------
        # Scoring Result
        # -------------------------------------------------------------

        "scoring_result": (
            result.get(
                "scoring_result",
                {}
            )
        ),


        # -------------------------------------------------------------
        # AI Recommendation
        # -------------------------------------------------------------

        "ai_recommendation": (
            result.get(
                "ai_recommendation",
                {}
            )
        )
    }


# =========================================================================
# FINAL PROCUREMIND ARCHITECTURE
#
# Login
#   ↓
# JWT Authentication
#   ↓
# FastAPI
#   ↓
# RFQ + Vendor PDFs
#   ↓
# LangGraph Orchestrator
#   │
#   ├── RFQ Extraction Node
#   ├── Vendor Extraction Node
#   ├── Data Validation Node
#   ├── Compliance Node
#   ├── Compliance Validation Node
#   ├── Scoring Node
#   ├── Recommendation Node
#   ├── Final Risk Node
#   ├── Manual Review Node
#   └── Database Node
#   ↓
# PostgreSQL
#   │
#   ├── users
#   ├── rfq_records
#   ├── vendors
#   ├── vendor_quotation_records
#   └── comparison_result_records
#   ↓
# Redis Cache
#   ↓
# History APIs
#   ↓
# PDF Procurement Report
# =========================================================================
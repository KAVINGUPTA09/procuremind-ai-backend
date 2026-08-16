import json

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from fastapi.encoders import jsonable_encoder

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.database.models import (
    User,
    RFQRecord,
    VendorQuotationRecord,
    ComparisonResultRecord
)

from app.dependencies.auth_dependencies import (
    get_current_user
)

from app.services.redis_service import redis_client


router = APIRouter(
    prefix="/history",
    tags=["Procurement History"]
)


DatabaseSession = Annotated[
    Session,
    Depends(get_db)
]


CurrentUser = Annotated[
    User,
    Depends(get_current_user)
]


# =========================================================
# REDIS SETTINGS
# =========================================================

CACHE_TTL = 300       # 5 minutes


def history_cache_key(user_id: int):
    return f"history:user:{user_id}"


def detail_cache_key(
    user_id: int,
    analysis_id: int
):
    return (
        f"history:detail:"
        f"{user_id}:{analysis_id}"
    )


# =========================================================
# GET /history
#
# Redis Cache Aside Flow:
#
# Redis
#   ↓ HIT
# Return immediately
#
# MISS
#   ↓
# PostgreSQL
#   ↓
# Save Redis 5 minutes
#   ↓
# Return
# =========================================================

@router.get("")
def get_history(
    db: DatabaseSession,
    current_user: CurrentUser
):

    cache_key = history_cache_key(
        current_user.id
    )


    # -----------------------------------------------------
    # 1. CHECK REDIS
    # -----------------------------------------------------

    try:

        cached_history = redis_client.get(
            cache_key
        )

        if cached_history:

            return json.loads(
                cached_history
            )

    except Exception as error:

        print(
            "Redis history read error:",
            error
        )


    # -----------------------------------------------------
    # 2. CACHE MISS → POSTGRESQL
    # -----------------------------------------------------

    statement = (
        select(RFQRecord)
        .where(
            RFQRecord.user_id
            == current_user.id
        )
        .order_by(
            RFQRecord.id.desc()
        )
    )


    result = db.execute(
        statement
    )


    rfqs = (
        result.scalars().all()
    )


    history = []


    for rfq in rfqs:

        comparison_statement = (
            select(
                ComparisonResultRecord
            )
            .where(
                ComparisonResultRecord.rfq_id
                == rfq.id
            )
        )


        comparison_result = db.execute(
            comparison_statement
        )


        comparison = (
            comparison_result
            .scalar_one_or_none()
        )


        history.append(
            {

                "analysis_id":
                    rfq.id,

                "filename":
                    rfq.filename,

                "rfq_title":
                    rfq.rfq_title,

                "department":
                    rfq.department,

                "created_at":
                    rfq.created_at,

                "best_vendor": (
                    comparison.best_vendor
                    if comparison
                    else None
                ),

                "final_decision": (
                    comparison.final_decision
                    if comparison
                    else None
                )
            }
        )


    response_data = {

        "user_id":
            current_user.id,

        "total_analyses":
            len(history),

        "history":
            history
    }


    # -----------------------------------------------------
    # 3. SAVE RESULT IN REDIS
    # -----------------------------------------------------

    try:

        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(
                jsonable_encoder(
                    response_data
                )
            )
        )

    except Exception as error:

        print(
            "Redis history write error:",
            error
        )


    return response_data


# =========================================================
# GET /history/{analysis_id}
#
# Full analysis detail caching
# =========================================================

@router.get("/{analysis_id}")
def get_history_detail(
    analysis_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):

    cache_key = detail_cache_key(
        current_user.id,
        analysis_id
    )


    # -----------------------------------------------------
    # CHECK REDIS
    # -----------------------------------------------------

    try:

        cached_detail = redis_client.get(
            cache_key
        )

        if cached_detail:

            return json.loads(
                cached_detail
            )

    except Exception as error:

        print(
            "Redis detail read error:",
            error
        )


    # -----------------------------------------------------
    # POSTGRESQL
    # -----------------------------------------------------

    rfq_statement = (
        select(RFQRecord)
        .where(
            RFQRecord.id
            == analysis_id,

            RFQRecord.user_id
            == current_user.id
        )
    )


    rfq_result = db.execute(
        rfq_statement
    )


    rfq = (
        rfq_result
        .scalar_one_or_none()
    )


    if rfq is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Procurement analysis not found."
        )


    vendor_statement = (
        select(
            VendorQuotationRecord
        )
        .where(
            VendorQuotationRecord.rfq_id
            == rfq.id
        )
        .order_by(
            VendorQuotationRecord.rank
        )
    )


    vendor_result = db.execute(
        vendor_statement
    )


    vendors = (
        vendor_result
        .scalars()
        .all()
    )


    comparison_statement = (
        select(
            ComparisonResultRecord
        )
        .where(
            ComparisonResultRecord.rfq_id
            == rfq.id
        )
    )


    comparison_result = db.execute(
        comparison_statement
    )


    comparison = (
        comparison_result
        .scalar_one_or_none()
    )


    response_data = {

        "analysis_id":
            rfq.id,


        "rfq": {

            "filename":
                rfq.filename,

            "rfq_title":
                rfq.rfq_title,

            "department":
                rfq.department,

            "structured_data":
                rfq.structured_data,

            "created_at":
                rfq.created_at
        },


        "vendors": [

            {

                "quotation_id":
                    vendor.id,

                "vendor_id":
                    vendor.vendor_id,

                "filename":
                    vendor.filename,

                "subtotal":
                    vendor.subtotal,

                "compliance_percentage":
                    vendor.compliance_percentage,

                "final_score":
                    vendor.final_score,

                "rank":
                    vendor.rank,

                "structured_data":
                    vendor.structured_data,

                "compliance_report":
                    vendor.compliance_report

            }

            for vendor in vendors
        ],


        "comparison": (

            {

                "comparison_id":
                    comparison.id,

                "best_vendor":
                    comparison.best_vendor,

                "final_decision":
                    comparison.final_decision,

                "executive_summary":
                    comparison.executive_summary,

                "scoring_result":
                    comparison.scoring_result,

                "ai_recommendation":
                    comparison.ai_recommendation,

                "created_at":
                    comparison.created_at
            }

            if comparison

            else None
        )
    }


    # -----------------------------------------------------
    # SAVE DETAIL TO REDIS
    # -----------------------------------------------------

    try:

        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(
                jsonable_encoder(
                    response_data
                )
            )
        )

    except Exception as error:

        print(
            "Redis detail write error:",
            error
        )


    return response_data


# =========================================================
# DELETE /history/{analysis_id}
#
# Delete PostgreSQL data
# +
# invalidate Redis cache
# =========================================================

@router.delete("/{analysis_id}")
def delete_history(
    analysis_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):

    rfq_statement = (
        select(RFQRecord)
        .where(
            RFQRecord.id
            == analysis_id,

            RFQRecord.user_id
            == current_user.id
        )
    )


    rfq_result = db.execute(
        rfq_statement
    )


    rfq = (
        rfq_result
        .scalar_one_or_none()
    )


    if rfq is None:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Procurement analysis not found."
        )


    try:

        db.execute(

            delete(
                VendorQuotationRecord
            )
            .where(
                VendorQuotationRecord.rfq_id
                == analysis_id
            )

        )


        db.execute(

            delete(
                ComparisonResultRecord
            )
            .where(
                ComparisonResultRecord.rfq_id
                == analysis_id
            )

        )


        db.delete(
            rfq
        )


        db.commit()


    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=
                "Failed to delete procurement analysis."
        )


    # -----------------------------------------------------
    # INVALIDATE REDIS CACHE
    # -----------------------------------------------------

    try:

        redis_client.delete(

            history_cache_key(
                current_user.id
            ),

            detail_cache_key(
                current_user.id,
                analysis_id
            )

        )

    except Exception as error:

        print(
            "Redis cache invalidation error:",
            error
        )


    return {

        "message":
            "Procurement analysis deleted successfully.",

        "analysis_id":
            analysis_id
    }
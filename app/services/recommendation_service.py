"""
===========================================================================
File: recommendation_service.py

Project: ProcureMind AI
Author : Kavin Gupta

Purpose:
--------
Generates an AI-powered procurement recommendation after multiple
vendors have been compared, scored, and ranked.

The service analyzes:

1. Vendor rankings
2. Final scores
3. Compliance reports
4. Price
5. Delivery time
6. Warranty
7. Past vendor rating

The service returns:

1. Best vendor
2. Executive summary
3. Selection reasons
4. Strengths
5. Risks
6. Analysis of other vendors
7. Negotiation suggestions
8. Final approval decision
===========================================================================
"""

import json
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.services.langchain_services import llm


# =========================================================================
# Recommendation Output Schema
# =========================================================================

class VendorRecommendation(BaseModel):
    """
    Defines the exact structured output expected
    from the AI recommendation chain.
    """

    best_vendor: str = Field(
        min_length=2,
        description="Name of the vendor selected by the scoring engine."
    )

    executive_summary: str = Field(
        min_length=20,
        description=(
            "Professional summary of the procurement decision "
            "and the overall vendor comparison."
        )
    )

    selection_reasons: list[str] = Field(
        min_length=1,
        description=(
            "Main reasons why the best vendor ranked first."
        )
    )

    strengths: list[str] = Field(
        min_length=1,
        description=(
            "Important strengths of the selected vendor."
        )
    )

    risks: list[str] = Field(
        default_factory=list,
        description=(
            "Potential risks, weaknesses, or concerns "
            "related to the selected vendor."
        )
    )

    other_vendor_analysis: list[str] = Field(
        default_factory=list,
        description=(
            "Reasons why the remaining vendors ranked lower."
        )
    )

    negotiation_suggestions: list[str] = Field(
        default_factory=list,
        description=(
            "Realistic commercial or contractual negotiation suggestions."
        )
    )

    final_decision: str = Field(
        description=(
            "Final decision: Approve, Approve with Conditions, "
            "or Manual Review Required."
        )
    )


# =========================================================================
# Recommendation Prompt
# =========================================================================

recommendation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a senior procurement decision analyst working "
                "inside an AI-powered procurement platform. Analyze the "
                "provided scoring results, compliance reports, and vendor "
                "details objectively. Never modify calculated scores. "
                "Never invent information. Use the vendor identified in "
                "the best_vendor field as the recommended vendor unless "
                "the supplied data contains a serious contradiction or "
                "critical risk. Clearly explain the recommendation in "
                "professional business language."
            )
        ),
        (
            "human",
            """
Analyze the following procurement comparison data.

SCORING RESULT:
{scoring_result}

COMPLIANCE REPORTS:
{compliance_reports}

VENDOR DETAILS:
{vendor_details}

Required analysis:

1. Read the best_vendor value from the scoring result.
2. Explain why that vendor ranked first.
3. Consider final score, subtotal, price score, delivery score,
   compliance score, warranty score, and past rating score.
4. Identify the strongest advantages of the selected vendor.
5. Identify genuine risks or weaknesses of the selected vendor.
6. Explain why every other vendor ranked lower.
7. Provide realistic negotiation suggestions.
8. Do not change, recalculate, or invent scores.
9. Do not invent missing facts.
10. Use "Approve" when the selected vendor is fully suitable.
11. Use "Approve with Conditions" when the selected vendor has
    manageable risks.
12. Use "Manual Review Required" when the data is incomplete,
    contradictory, or indicates serious risk.
"""
        )
    ]
)


# =========================================================================
# Structured LLM
# =========================================================================

structured_recommendation_llm = llm.with_structured_output(
    VendorRecommendation
)


# =========================================================================
# Recommendation Chain
# =========================================================================

recommendation_chain = (
    recommendation_prompt
    |
    structured_recommendation_llm
)


# =========================================================================
# Helper Function
# =========================================================================

def convert_to_json(
    value: Any,
    field_name: str
) -> str:
    """
    Converts Python dictionaries, lists, or Pydantic objects
    into readable JSON for the LLM prompt.
    """

    if hasattr(value, "model_dump"):
        value = value.model_dump()

    try:
        return json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{field_name} could not be converted to JSON."
        ) from error


# =========================================================================
# Main Recommendation Function
# =========================================================================

def generate_vendor_recommendation(
    scoring_result: dict,
    compliance_reports: list[dict],
    vendor_details: list[dict]
) -> VendorRecommendation:
    """
    Generates a validated AI procurement recommendation.

    Input:
    ------
    scoring_result:
        Contains the best vendor and complete vendor rankings.

    compliance_reports:
        Contains requirement-matching results for every vendor.

    vendor_details:
        Contains quotation, delivery, warranty, price, and rating data.

    Output:
    -------
    VendorRecommendation:
        A validated Pydantic recommendation object.
    """

    if not scoring_result:
        raise ValueError(
            "Scoring result cannot be empty."
        )

    if not isinstance(scoring_result, dict):
        if hasattr(scoring_result, "model_dump"):
            scoring_result = scoring_result.model_dump()
        else:
            raise TypeError(
                "Scoring result must be a dictionary "
                "or Pydantic model."
            )

    if not scoring_result.get("best_vendor"):
        raise ValueError(
            "Scoring result does not contain best_vendor."
        )

    rankings = scoring_result.get("rankings")

    if not rankings:
        raise ValueError(
            "Scoring result does not contain vendor rankings."
        )

    if not compliance_reports:
        raise ValueError(
            "Compliance reports cannot be empty."
        )

    if not vendor_details:
        raise ValueError(
            "Vendor details cannot be empty."
        )

    scoring_json = convert_to_json(
        scoring_result,
        "Scoring result"
    )

    compliance_json = convert_to_json(
        compliance_reports,
        "Compliance reports"
    )

    vendor_json = convert_to_json(
        vendor_details,
        "Vendor details"
    )

    try:
        recommendation = recommendation_chain.invoke(
            {
                "scoring_result": scoring_json,
                "compliance_reports": compliance_json,
                "vendor_details": vendor_json
            }
        )

    except Exception as error:
        raise RuntimeError(
            "AI recommendation generation failed."
        ) from error

    if recommendation is None:
        raise ValueError(
            "The recommendation chain returned an empty response."
        )

    if not isinstance(
        recommendation,
        VendorRecommendation
    ):
        recommendation = VendorRecommendation.model_validate(
            recommendation
        )

    scoring_best_vendor = scoring_result["best_vendor"]

    if (
        recommendation.best_vendor.strip().lower()
        != scoring_best_vendor.strip().lower()
    ):
        recommendation = recommendation.model_copy(
            update={
                "best_vendor": scoring_best_vendor,
                "final_decision": "Manual Review Required"
            }
        )

    return recommendation


# =========================================================================
# Temporary Test
# =========================================================================

if __name__ == "__main__":

    sample_scoring_result = {
        "best_vendor": "Lenovo Enterprise",
        "rankings": [
            {
                "vendor_name": "Lenovo Enterprise",
                "subtotal": 1360000,
                "price_score": 97.06,
                "delivery_score": 100,
                "compliance_score": 100,
                "past_rating_score": 94,
                "warranty_score": 100,
                "final_score": 98.37,
                "rank": 1
            },
            {
                "vendor_name": "Dell Technologies",
                "subtotal": 1350000,
                "price_score": 97.78,
                "delivery_score": 83.33,
                "compliance_score": 100,
                "past_rating_score": 90,
                "warranty_score": 75,
                "final_score": 92.39,
                "rank": 2
            },
            {
                "vendor_name": "HP Solutions",
                "subtotal": 1320000,
                "price_score": 100,
                "delivery_score": 71.43,
                "compliance_score": 87.5,
                "past_rating_score": 84,
                "warranty_score": 50,
                "final_score": 84.56,
                "rank": 3
            }
        ]
    }

    sample_compliance_reports = [
        {
            "vendor_name": "Lenovo Enterprise",
            "delivery_match": True,
            "warranty_match": True,
            "compliance_percentage": 100
        },
        {
            "vendor_name": "Dell Technologies",
            "delivery_match": True,
            "warranty_match": True,
            "compliance_percentage": 100
        },
        {
            "vendor_name": "HP Solutions",
            "delivery_match": True,
            "warranty_match": False,
            "compliance_percentage": 87.5
        }
    ]

    sample_vendor_details = [
        {
            "vendor_name": "Lenovo Enterprise",
            "subtotal": 1360000,
            "delivery_days": 10,
            "warranty_months": 48,
            "past_rating": 4.7
        },
        {
            "vendor_name": "Dell Technologies",
            "subtotal": 1350000,
            "delivery_days": 12,
            "warranty_months": 36,
            "past_rating": 4.5
        },
        {
            "vendor_name": "HP Solutions",
            "subtotal": 1320000,
            "delivery_days": 14,
            "warranty_months": 24,
            "past_rating": 4.2
        }
    ]

    result = generate_vendor_recommendation(
        scoring_result=sample_scoring_result,
        compliance_reports=sample_compliance_reports,
        vendor_details=sample_vendor_details
    )

    print("AI Vendor Recommendation:\n")

    print(
        result.model_dump_json(
            indent=2
        )
    )
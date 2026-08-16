"""
=============================================================
File:conditions.py

Project:ProcureMind AI
Purpose:
-----------
consist of all conditional routing used in the project

These fn donot do anything related to procurement work
in contrast in decides which node to run next.............

=============================================================
"""

from app.graph.state import ProcurementState

# =========================================================================
# CONDITION 1
# Data Completeness Routing
# =========================================================================

def route_after_data_validation(
        state:ProcurementState
)-> str:

    """
    if procurement data is valid.approach to compliance
    otherwise send for manual review
    """

    if state.get(
        "data_complete",
        False
    ):
        return "compliance"
    return "manual review"

# =========================================================================
# CONDITION 2
# Compliance Routing
# =========================================================================

def route_after_compliance_validation(
    state: ProcurementState
) -> str:

    """
    If at least one vendor passes
    the compliance threshold,
    continue to scoring.

    Otherwise send for manual review.
    """

    if state.get(
        "compliance_passed",
        False
    ):

        return "scoring"

    return "manual_review"


# =========================================================================
# CONDITION 3
# Final Risk Routing
# =========================================================================

def route_after_final_risk(
    state: ProcurementState
) -> str:

    """
    If workflow requires human review,
    route to manual review.

    Otherwise continue to database saving.
    """

    if state.get(
        "requires_manual_review",
        False
    ):

        return "manual_review"

    return "database"


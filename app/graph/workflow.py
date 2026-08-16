from langgraph.graph import (
    StateGraph,
    START,
    END
)


from app.graph.state import ProcurementState
from app.graph.nodes import (
    extract_rfq_node,
    extract_vendors_node,
    data_validation_node,
    compliance_node,
    compliance_validation_node,
    scoring_node,
    recommendation_node,
    final_risk_node,
    manual_review_node,
    database_node
)

from app.graph.conditions import (
    route_after_data_validation,
    route_after_compliance_validation,
    route_after_final_risk
)


# =========================================================
# 1. CREATE GRAPH
# =========================================================

workflow = StateGraph(
    ProcurementState
)


# =========================================================
# 2. ADD ALL NODES
# =========================================================

workflow.add_node(
    "extract_rfq",
    extract_rfq_node
)

workflow.add_node(
    "extract_vendors",
    extract_vendors_node
)

workflow.add_node(
    "data_validation",
    data_validation_node
)

workflow.add_node(
    "compliance",
    compliance_node
)

workflow.add_node(
    "compliance_validation",
    compliance_validation_node
)

workflow.add_node(
    "scoring",
    scoring_node
)

workflow.add_node(
    "recommendation",
    recommendation_node
)

workflow.add_node(
    "final_risk",
    final_risk_node
)

workflow.add_node(
    "manual_review",
    manual_review_node
)

workflow.add_node(
    "database",
    database_node
)


# =========================================================
# 3. NORMAL EDGES
# =========================================================

workflow.add_edge(
    START,
    "extract_rfq"
)

workflow.add_edge(
    "extract_rfq",
    "extract_vendors"
)

workflow.add_edge(
    "extract_vendors",
    "data_validation"
)


# =========================================================
# 4. CONDITION 1
# Data complete?
# =========================================================

workflow.add_conditional_edges(

    "data_validation",

    route_after_data_validation,

    {
        "compliance": "compliance",
        "manual_review": "manual_review"
    }
)


# =========================================================
# 5. Compliance calculation → validation
# =========================================================

workflow.add_edge(
    "compliance",
    "compliance_validation"
)


# =========================================================
# 6. CONDITION 2
# Compliance passed?
# =========================================================

workflow.add_conditional_edges(

    "compliance_validation",

    route_after_compliance_validation,

    {
        "scoring": "scoring",
        "manual_review": "manual_review"
    }
)


# =========================================================
# 7. Scoring → Recommendation → Final Risk
# =========================================================

workflow.add_edge(
    "scoring",
    "recommendation"
)

workflow.add_edge(
    "recommendation",
    "final_risk"
)


# =========================================================
# 8. CONDITION 3
# Final risk check
#
# Database integration next step me add hoga.
# =========================================================

workflow.add_conditional_edges(

    "final_risk",

    route_after_final_risk,

    {
        "manual_review": "manual_review",

        # Temporary:
        # Safe result ends here.
        "database": "database"
    }
)

workflow.add_edge(
    "database",
    END
)


# =========================================================
# 9. Manual Review → END
# =========================================================

workflow.add_edge(
    "manual_review",
    END
)


# =========================================================
# 10. COMPILE GRAPH
# =========================================================
procurement_graph = (
    workflow.compile()
)


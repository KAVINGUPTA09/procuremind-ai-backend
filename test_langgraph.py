from app.graph.workflow import procurement_graph


initial_state = {

    "user_id": 8,

    "rfq_file_path": (
        "app/uploads/"
        "0db9cf744b2c400897305f785a1971f2.pdf"
    ),

    "vendor_file_paths": [

        "app/uploads/"
        "80c4f01695f2449c9a5b80c285d0f206.pdf",

        "app/uploads/"
        "229f6a9fa5cf4186aed0b6dbbdca61f6.pdf",

        "app/uploads/"
        "9fcd51f42fca429a9cac7b760c0fb9d7.pdf"
    ],

    # Database me readable original names save honge
    "rfq_filename": "rfq.pdf",

    "vendor_filenames": [
        "vendor_dell.pdf",
        "vendor_hp.pdf",
        "vendor_lenovo.pdf"
    ]
}


result = procurement_graph.invoke(
    initial_state
)


print("\n==============================")
print("LANGGRAPH FINAL RESULT")
print("==============================\n")


print(
    "Workflow Status:",
    result.get("workflow_status")
)

print(
    "Data Complete:",
    result.get("data_complete")
)

print(
    "Compliance Passed:",
    result.get("compliance_passed")
)

print(
    "Manual Review:",
    result.get("requires_manual_review")
)

print(
    "Review Reason:",
    result.get("review_reason")
)

print(
    "Best Vendor:",
    result.get(
        "scoring_result",
        {}
    ).get(
        "best_vendor"
    )
)

print(
    "Final Decision:",
    result.get(
        "ai_recommendation",
        {}
    ).get(
        "final_decision"
    )
)

print(
    "Analysis ID:",
    result.get("analysis_id")
)

print(
    "Comparison ID:",
    result.get("comparison_id")
)

print(
    "Error:",
    result.get("error_message")
)
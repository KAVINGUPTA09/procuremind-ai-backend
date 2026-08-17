from app.services.b2b_intelligence import detect_risk_flags, explain_ranking, simulate_rankings


def test_what_if_can_change_winner():
    rankings = [
        {"vendor_name": "A", "price_score": 60, "delivery_score": 100, "compliance_score": 100, "warranty_score": 100, "past_rating_score": 100, "final_score": 86},
        {"vendor_name": "B", "price_score": 100, "delivery_score": 60, "compliance_score": 60, "warranty_score": 60, "past_rating_score": 60, "final_score": 74},
    ]
    result = simulate_rankings(rankings, {"price": 1, "delivery": 0, "compliance": 0, "warranty": 0, "past_rating": 0})
    assert result[0]["vendor_name"] == "B"


def test_explainability_contributions_exist():
    row = {"vendor_name": "A", "price_score": 90, "delivery_score": 80, "compliance_score": 100, "warranty_score": 75, "past_rating_score": 90, "final_score": 89}
    result = explain_ranking(row)
    assert len(result["contributions"]) == 5
    assert result["top_driver"] is not None


def test_risk_flags_noncompliant_vendor():
    flags = detect_risk_flags(
        [{"vendor_name": "RiskCo", "subtotal": 100, "delivery_days": 45, "warranty_months": 6, "past_rating": 2.5}],
        [{"vendor_name": "RiskCo", "overall_compliance": 50, "delivery_match": False, "warranty_match": False}],
    )
    types = {f["type"] for f in flags}
    assert "compliance_risk" in types
    assert "rfq_delivery_mismatch" in types

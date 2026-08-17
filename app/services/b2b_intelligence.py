from __future__ import annotations

from collections import defaultdict
from typing import Any

DEFAULT_WEIGHTS = {
    "price": 0.35,
    "delivery": 0.20,
    "compliance": 0.25,
    "warranty": 0.10,
    "past_rating": 0.10,
}


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    merged = {**DEFAULT_WEIGHTS, **(weights or {})}
    clean = {k: max(0.0, float(v)) for k, v in merged.items() if k in DEFAULT_WEIGHTS}
    total = sum(clean.values())
    if total <= 0:
        raise ValueError("At least one scoring weight must be greater than zero.")
    return {k: v / total for k, v in clean.items()}


def simulate_rankings(rankings: list[dict[str, Any]], weights: dict[str, float]) -> list[dict[str, Any]]:
    normalized = normalize_weights(weights)
    simulated: list[dict[str, Any]] = []
    for row in rankings:
        score = (
            float(row.get("price_score") or 0) * normalized["price"]
            + float(row.get("delivery_score") or 0) * normalized["delivery"]
            + float(row.get("compliance_score") or 0) * normalized["compliance"]
            + float(row.get("warranty_score") or 0) * normalized["warranty"]
            + float(row.get("past_rating_score") or 0) * normalized["past_rating"]
        )
        simulated.append({**row, "simulated_score": round(score, 2)})

    simulated.sort(key=lambda x: x["simulated_score"], reverse=True)
    for index, row in enumerate(simulated, start=1):
        row["simulated_rank"] = index
    return simulated


def explain_ranking(row: dict[str, Any], weights: dict[str, float] | None = None) -> dict[str, Any]:
    w = normalize_weights(weights or DEFAULT_WEIGHTS)
    labels = {
        "price": "Price",
        "delivery": "Delivery",
        "compliance": "Compliance",
        "warranty": "Warranty",
        "past_rating": "Past performance",
    }
    score_keys = {
        "price": "price_score",
        "delivery": "delivery_score",
        "compliance": "compliance_score",
        "warranty": "warranty_score",
        "past_rating": "past_rating_score",
    }
    contributions = []
    for key in DEFAULT_WEIGHTS:
        raw = float(row.get(score_keys[key]) or 0)
        weighted = raw * w[key]
        contributions.append(
            {
                "factor": key,
                "label": labels[key],
                "raw_score": round(raw, 2),
                "weight_percent": round(w[key] * 100, 2),
                "contribution": round(weighted, 2),
            }
        )
    contributions.sort(key=lambda x: x["contribution"], reverse=True)
    return {
        "vendor_name": row.get("vendor_name"),
        "final_score": row.get("final_score"),
        "rank": row.get("rank"),
        "contributions": contributions,
        "top_driver": contributions[0] if contributions else None,
        "weakest_driver": contributions[-1] if contributions else None,
    }


def detect_risk_flags(vendors: list[dict[str, Any]], compliance_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    prices = [float(v.get("subtotal") or 0) for v in vendors if float(v.get("subtotal") or 0) > 0]
    median_price = sorted(prices)[len(prices) // 2] if prices else 0

    normalized_signatures: dict[str, list[str]] = defaultdict(list)
    for vendor in vendors:
        name = str(vendor.get("vendor_name") or vendor.get("name") or "Unknown vendor")
        delivery = float(vendor.get("delivery_days") or 0)
        warranty = float(vendor.get("warranty_months") or 0)
        rating = float(vendor.get("past_rating") or 0)
        subtotal = float(vendor.get("subtotal") or 0)

        if median_price and subtotal and subtotal < median_price * 0.70:
            flags.append({"vendor": name, "severity": "high", "type": "abnormally_low_price", "message": "Quoted subtotal is more than 30% below the comparison median."})
        if delivery > 30:
            flags.append({"vendor": name, "severity": "medium", "type": "delivery_risk", "message": "Delivery timeline is longer than 30 days."})
        if warranty and warranty < 12:
            flags.append({"vendor": name, "severity": "medium", "type": "warranty_risk", "message": "Warranty is below 12 months."})
        if rating and rating < 3.0:
            flags.append({"vendor": name, "severity": "high", "type": "supplier_performance", "message": "Past supplier rating is below 3.0/5."})

        items = vendor.get("items") or vendor.get("line_items") or []
        signature_parts = []
        for item in items:
            signature_parts.append(
                f"{str(item.get('item_name') or item.get('name') or item.get('item') or '').lower()}|"
                f"{item.get('quantity') or item.get('quoted_quantity')}|{item.get('unit_price')}|"
                f"{str(item.get('specifications') or '').lower()}"
            )
        signature = "||".join(signature_parts)
        if signature:
            normalized_signatures[signature].append(name)

    for report in compliance_reports:
        name = str(report.get("vendor_name") or "Unknown vendor")
        compliance = float(report.get("overall_compliance") or report.get("compliance_percent") or 0)
        if compliance < 70:
            flags.append({"vendor": name, "severity": "high", "type": "compliance_risk", "message": f"Technical compliance is only {compliance:.1f}%."})
        if report.get("delivery_match") is False:
            flags.append({"vendor": name, "severity": "high", "type": "rfq_delivery_mismatch", "message": "Vendor does not meet the RFQ delivery requirement."})
        if report.get("warranty_match") is False:
            flags.append({"vendor": name, "severity": "medium", "type": "rfq_warranty_mismatch", "message": "Vendor does not meet the RFQ warranty requirement."})

    for names in normalized_signatures.values():
        if len(names) > 1:
            flags.append({
                "vendor": ", ".join(names),
                "severity": "medium",
                "type": "similar_quotation_pattern",
                "message": "Multiple quotations have an identical line-item/price/specification signature. Review for duplication or collusion risk.",
            })

    return flags


def build_negotiation_playbook(best_vendor: str, rankings: list[dict[str, Any]]) -> dict[str, Any]:
    winner = next((r for r in rankings if r.get("vendor_name") == best_vendor), rankings[0] if rankings else {})
    competitors = [r for r in rankings if r is not winner]
    suggestions: list[str] = []
    winner_price = float(winner.get("subtotal") or 0)
    cheapest = min((float(r.get("subtotal") or 0) for r in rankings if float(r.get("subtotal") or 0) > 0), default=0)
    if cheapest and winner_price > cheapest:
        gap = winner_price - cheapest
        pct = gap / winner_price * 100 if winner_price else 0
        suggestions.append(f"Ask for a commercial concession of about {pct:.1f}% (≈ {gap:,.0f}) to approach the lowest competing quote.")
    if float(winner.get("warranty_score") or 0) < 100:
        suggestions.append("Request a warranty extension to match the strongest competing warranty without increasing price.")
    if float(winner.get("delivery_score") or 0) < 100:
        suggestions.append("Negotiate an accelerated delivery SLA with milestone penalties for delay.")
    if float(winner.get("compliance_score") or 0) < 100:
        suggestions.append("Make award conditional on closing the remaining technical compliance gaps in writing.")
    suggestions.append("Request price validity, support SLA, and payment milestones in the final commercial offer.")
    return {
        "vendor": best_vendor,
        "suggestions": suggestions,
        "competitor_count": len(competitors),
        "email_subject": f"Commercial clarification and best-offer request — {best_vendor}",
        "email_draft": (
            f"Dear {best_vendor} Team,\n\n"
            "Thank you for your quotation. Your proposal is currently leading our evaluation. "
            "Before final award, please share your best and final commercial offer and confirm delivery, warranty, support SLA, and price validity. "
            "Where possible, please improve the commercial terms while preserving the submitted technical scope.\n\n"
            "Regards,\nProcurement Team"
        ),
    }


def ask_analysis_copilot(question: str, analysis_context: dict[str, Any]) -> str:
    from app.services.langchain_services import llm
    if not question.strip():
        raise ValueError("Question cannot be empty.")
    prompt = (
        "You are ProcureMind Copilot. Answer only from the supplied procurement analysis. "
        "If the answer is not in the data, say that clearly. Do not invent prices, scores, risks, vendors, or requirements. "
        "Be concise and explain reasoning in business language.\n\n"
        f"ANALYSIS DATA:\n{analysis_context}\n\nQUESTION:\n{question}"
    )
    response = llm.invoke(prompt)
    return str(response.content or "No answer could be generated.")

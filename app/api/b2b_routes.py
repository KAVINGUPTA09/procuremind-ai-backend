from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import (
    ApprovalRecord,
    ComparisonResultRecord,
    ContractRecord,
    RFQRecord,
    User,
    Vendor,
    VendorQuotationRecord,
)
from app.dependencies.auth_dependencies import get_current_user
from app.dependencies.role_dependencies import require_roles
from app.schemas.b2b_schema import (
    ApprovalDecisionRequest,
    CopilotRequest,
    ContractCreateRequest,
    UserRoleUpdateRequest,
    WeightSimulationRequest,
)
from app.services.b2b_intelligence import (
    DEFAULT_WEIGHTS,
    ask_analysis_copilot,
    build_negotiation_playbook,
    detect_risk_flags,
    explain_ranking,
    simulate_rankings,
)
from app.services.redis_service import redis_client

router = APIRouter(prefix="/b2b", tags=["B2B Procurement Intelligence"])
DatabaseSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _analysis_for_user(db: Session, analysis_id: int, user: User):
    query = select(RFQRecord).where(RFQRecord.id == analysis_id)
    if (user.role or "buyer").lower() == "buyer":
        query = query.where(RFQRecord.user_id == user.id)
    rfq = db.execute(query).scalar_one_or_none()
    if rfq is None:
        raise HTTPException(status_code=404, detail="Procurement analysis not found.")
    return rfq


def _analysis_context(db: Session, analysis_id: int, user: User) -> dict[str, Any]:
    rfq = _analysis_for_user(db, analysis_id, user)
    quotes = db.execute(
        select(VendorQuotationRecord)
        .where(VendorQuotationRecord.rfq_id == rfq.id)
        .order_by(VendorQuotationRecord.rank)
    ).scalars().all()
    comparison = db.execute(
        select(ComparisonResultRecord).where(ComparisonResultRecord.rfq_id == rfq.id)
    ).scalar_one_or_none()

    vendors = []
    compliance_reports = []
    for q in quotes:
        structured = dict(q.structured_data or {})
        structured.setdefault("subtotal", q.subtotal)
        structured.setdefault("vendor_name", structured.get("vendor_name") or structured.get("name"))
        vendors.append(structured)
        compliance_reports.append(dict(q.compliance_report or {}))

    return {
        "analysis_id": rfq.id,
        "owner_user_id": rfq.user_id,
        "rfq": rfq.structured_data,
        "rfq_title": rfq.rfq_title,
        "department": rfq.department,
        "vendors": vendors,
        "compliance_reports": compliance_reports,
        "comparison": {
            "best_vendor": comparison.best_vendor,
            "final_decision": comparison.final_decision,
            "executive_summary": comparison.executive_summary,
            "scoring_result": comparison.scoring_result,
            "ai_recommendation": comparison.ai_recommendation,
        } if comparison else None,
    }


def _ensure_approval(db: Session, rfq: RFQRecord) -> ApprovalRecord:
    record = db.execute(
        select(ApprovalRecord).where(ApprovalRecord.rfq_id == rfq.id)
    ).scalar_one_or_none()
    if record is None:
        record = ApprovalRecord(rfq_id=rfq.id, requested_by_user_id=rfq.user_id, status="pending")
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


@router.get("/dashboard")
def b2b_dashboard(db: DatabaseSession, current_user: CurrentUser):
    role = (current_user.role or "buyer").lower()
    rfq_query = select(RFQRecord)
    if role == "buyer":
        rfq_query = rfq_query.where(RFQRecord.user_id == current_user.id)
    rfqs = db.execute(rfq_query.order_by(RFQRecord.created_at.desc())).scalars().all()
    rfq_ids = [r.id for r in rfqs]

    comparisons = []
    quotes = []
    if rfq_ids:
        comparisons = db.execute(
            select(ComparisonResultRecord).where(ComparisonResultRecord.rfq_id.in_(rfq_ids))
        ).scalars().all()
        quotes = db.execute(
            select(VendorQuotationRecord).where(VendorQuotationRecord.rfq_id.in_(rfq_ids))
        ).scalars().all()

    total_evaluated_spend = round(sum(float(q.subtotal or 0) for q in quotes), 2)
    recommended_spend = round(sum(float(q.subtotal or 0) for q in quotes if q.rank == 1), 2)

    by_department: dict[str, float] = {}
    rfq_department = {r.id: r.department for r in rfqs}
    for quote in quotes:
        if quote.rank == 1:
            department = rfq_department.get(quote.rfq_id, "General")
            by_department[department] = by_department.get(department, 0) + float(quote.subtotal or 0)

    vendor_spend: dict[str, float] = {}
    for quote in quotes:
        if quote.rank == 1:
            data = quote.structured_data or {}
            name = str(data.get("vendor_name") or data.get("name") or f"Vendor #{quote.vendor_id}")
            vendor_spend[name] = vendor_spend.get(name, 0) + float(quote.subtotal or 0)

    pending = 0
    if role in {"approver", "admin"}:
        pending = db.execute(
            select(func.count(ApprovalRecord.id)).where(ApprovalRecord.status == "pending")
        ).scalar_one()
    else:
        pending = db.execute(
            select(func.count(ApprovalRecord.id)).where(
                ApprovalRecord.requested_by_user_id == current_user.id,
                ApprovalRecord.status == "pending",
            )
        ).scalar_one()

    return {
        "role": role,
        "analysis_count": len(rfqs),
        "vendor_quotes_evaluated": len(quotes),
        "total_evaluated_spend": total_evaluated_spend,
        "recommended_spend": recommended_spend,
        "pending_approvals": pending,
        "decision_counts": {
            "approve": sum(1 for c in comparisons if str(c.final_decision).lower() == "approve"),
            "conditional": sum(1 for c in comparisons if "condition" in str(c.final_decision).lower()),
            "manual_review": sum(1 for c in comparisons if "review" in str(c.final_decision).lower()),
        },
        "spend_by_department": [
            {"department": k, "amount": round(v, 2)}
            for k, v in sorted(by_department.items(), key=lambda x: x[1], reverse=True)
        ],
        "spend_by_vendor": [
            {"vendor": k, "amount": round(v, 2)}
            for k, v in sorted(vendor_spend.items(), key=lambda x: x[1], reverse=True)
        ],
    }


@router.get("/supplier-performance")
def supplier_performance(db: DatabaseSession, current_user: CurrentUser):
    role = (current_user.role or "buyer").lower()
    rfq_query = select(RFQRecord.id)
    if role == "buyer":
        rfq_query = rfq_query.where(RFQRecord.user_id == current_user.id)
    rfq_ids = list(db.execute(rfq_query).scalars().all())
    if not rfq_ids:
        return {"suppliers": []}

    quotes = db.execute(
        select(VendorQuotationRecord).where(VendorQuotationRecord.rfq_id.in_(rfq_ids))
    ).scalars().all()
    stats: dict[str, dict[str, Any]] = {}
    for q in quotes:
        data = q.structured_data or {}
        name = str(data.get("vendor_name") or data.get("name") or f"Vendor #{q.vendor_id}")
        row = stats.setdefault(name, {"vendor": name, "quotes": 0, "wins": 0, "score_sum": 0.0, "compliance_sum": 0.0, "delivery_sum": 0.0, "rating_sum": 0.0})
        row["quotes"] += 1
        row["wins"] += 1 if q.rank == 1 else 0
        row["score_sum"] += float(q.final_score or 0)
        row["compliance_sum"] += float(q.compliance_percentage or 0)
        row["delivery_sum"] += float(data.get("delivery_days") or 0)
        row["rating_sum"] += float(data.get("past_rating") or 0)

    suppliers = []
    for row in stats.values():
        n = row["quotes"] or 1
        suppliers.append({
            "vendor": row["vendor"],
            "quotations": row["quotes"],
            "wins": row["wins"],
            "win_rate": round(row["wins"] / n * 100, 2),
            "average_final_score": round(row["score_sum"] / n, 2),
            "average_compliance": round(row["compliance_sum"] / n, 2),
            "average_delivery_days": round(row["delivery_sum"] / n, 2),
            "average_past_rating": round(row["rating_sum"] / n, 2),
        })
    suppliers.sort(key=lambda x: (x["wins"], x["average_final_score"]), reverse=True)
    return {"suppliers": suppliers}


@router.get("/approvals")
def approvals_queue(
    db: DatabaseSession,
    current_user: User = Depends(require_roles("approver", "admin")),
):
    rfqs = db.execute(select(RFQRecord).order_by(RFQRecord.created_at.desc())).scalars().all()
    items = []
    for rfq in rfqs:
        approval = _ensure_approval(db, rfq)
        comparison = db.execute(
            select(ComparisonResultRecord).where(ComparisonResultRecord.rfq_id == rfq.id)
        ).scalar_one_or_none()
        items.append({
            "approval_id": approval.id,
            "analysis_id": rfq.id,
            "buyer_user_id": rfq.user_id,
            "rfq_title": rfq.rfq_title,
            "department": rfq.department,
            "best_vendor": comparison.best_vendor if comparison else None,
            "ai_decision": comparison.final_decision if comparison else None,
            "status": approval.status,
            "comment": approval.comment,
            "created_at": approval.created_at,
            "decided_at": approval.decided_at,
        })
    return {"approvals": items}


@router.post("/approvals/{analysis_id}/decision")
def decide_approval(
    analysis_id: int,
    payload: ApprovalDecisionRequest,
    db: DatabaseSession,
    current_user: User = Depends(require_roles("approver", "admin")),
):
    rfq = db.execute(select(RFQRecord).where(RFQRecord.id == analysis_id)).scalar_one_or_none()
    if rfq is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    approval = _ensure_approval(db, rfq)
    approval.status = payload.decision
    approval.comment = payload.comment
    approval.approver_user_id = current_user.id
    approval.decided_at = datetime.now(timezone.utc)
    db.commit()
    try:
        redis_client.delete(f"history:user:{rfq.user_id}")
        redis_client.delete(f"history:detail:{rfq.user_id}:{rfq.id}")
    except Exception:
        pass
    return {"analysis_id": analysis_id, "status": approval.status, "comment": approval.comment, "approver_user_id": current_user.id}


@router.post("/analysis/{analysis_id}/what-if")
def what_if(analysis_id: int, payload: WeightSimulationRequest, db: DatabaseSession, current_user: CurrentUser):
    context = _analysis_context(db, analysis_id, current_user)
    comparison = context.get("comparison") or {}
    rankings = (comparison.get("scoring_result") or {}).get("rankings") or []
    weights_pct = payload.model_dump()
    weights = {k: v / 100 for k, v in weights_pct.items()}
    simulated = simulate_rankings(rankings, weights)
    return {
        "analysis_id": analysis_id,
        "weights": weights_pct,
        "best_vendor": simulated[0].get("vendor_name") if simulated else None,
        "rankings": simulated,
        "winner_changed": bool(simulated and simulated[0].get("vendor_name") != comparison.get("best_vendor")),
    }


@router.get("/analysis/{analysis_id}/explainability")
def explainability(analysis_id: int, db: DatabaseSession, current_user: CurrentUser):
    context = _analysis_context(db, analysis_id, current_user)
    comparison = context.get("comparison") or {}
    rankings = (comparison.get("scoring_result") or {}).get("rankings") or []
    return {
        "analysis_id": analysis_id,
        "weights": {k: v * 100 for k, v in DEFAULT_WEIGHTS.items()},
        "vendors": [explain_ranking(row) for row in rankings],
    }


@router.get("/analysis/{analysis_id}/risk")
def risk_analysis(analysis_id: int, db: DatabaseSession, current_user: CurrentUser):
    context = _analysis_context(db, analysis_id, current_user)
    flags = detect_risk_flags(context["vendors"], context["compliance_reports"])
    return {
        "analysis_id": analysis_id,
        "risk_count": len(flags),
        "high_risk_count": sum(1 for f in flags if f["severity"] == "high"),
        "flags": flags,
        "note": "These are explainable rule-based procurement risk signals, not proof of fraud.",
    }


@router.get("/analysis/{analysis_id}/negotiation")
def negotiation(analysis_id: int, db: DatabaseSession, current_user: CurrentUser):
    context = _analysis_context(db, analysis_id, current_user)
    comparison = context.get("comparison") or {}
    rankings = (comparison.get("scoring_result") or {}).get("rankings") or []
    return build_negotiation_playbook(comparison.get("best_vendor") or "Selected vendor", rankings)


@router.post("/analysis/{analysis_id}/copilot")
def copilot(analysis_id: int, payload: CopilotRequest, db: DatabaseSession, current_user: CurrentUser):
    context = _analysis_context(db, analysis_id, current_user)
    try:
        answer = ask_analysis_copilot(payload.question, context)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Copilot is temporarily unavailable: {exc}") from exc
    return {"analysis_id": analysis_id, "question": payload.question, "answer": answer}


@router.get("/analysis/{analysis_id}/agent-pipeline")
def agent_pipeline(analysis_id: int, db: DatabaseSession, current_user: CurrentUser):
    context = _analysis_context(db, analysis_id, current_user)
    comparison = context.get("comparison") or {}
    return {
        "analysis_id": analysis_id,
        "pipeline": [
            {"id": "parser", "name": "Document Parser", "status": "complete", "output": "RFQ and quotation PDFs converted to structured data."},
            {"id": "compliance", "name": "Compliance Agent", "status": "complete", "output": f"{len(context['compliance_reports'])} supplier compliance reports generated."},
            {"id": "risk", "name": "Risk Agent", "status": "complete", "output": "Rule-based risk signals available on the Risk endpoint."},
            {"id": "scoring", "name": "Scoring Engine", "status": "complete", "output": f"Recommended vendor: {comparison.get('best_vendor') or 'N/A'}."},
            {"id": "recommendation", "name": "Recommendation Agent", "status": "complete", "output": comparison.get("final_decision") or "Recommendation generated."},
            {"id": "negotiation", "name": "Negotiation Agent", "status": "ready", "output": "Commercial negotiation playbook can be generated from the ranking."},
            {"id": "report", "name": "Report Agent", "status": "ready", "output": "Procurement report endpoint is available for saved analyses."},
        ],
    }


@router.get("/contracts")
def contract_analytics(db: DatabaseSession, current_user: CurrentUser):
    role = (current_user.role or "buyer").lower()
    query = select(ContractRecord)
    if role == "buyer":
        query = query.where(ContractRecord.created_by_user_id == current_user.id)
    contracts = db.execute(query.order_by(ContractRecord.end_date.asc().nullslast())).scalars().all()
    now = datetime.now(timezone.utc)
    warning_date = now + timedelta(days=60)
    return {
        "contracts": [
            {
                "id": c.id,
                "vendor_name": c.vendor_name,
                "title": c.title,
                "value": c.value,
                "currency": c.currency,
                "status": c.status,
                "start_date": c.start_date,
                "end_date": c.end_date,
                "expires_within_60_days": bool(c.end_date and now <= c.end_date <= warning_date),
                "terms": c.terms,
            }
            for c in contracts
        ]
    }


@router.post("/contracts", status_code=status.HTTP_201_CREATED)
def create_contract(payload: ContractCreateRequest, db: DatabaseSession, current_user: CurrentUser):
    def parse_date(value: str | None):
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Contract dates must be valid ISO-8601 values.") from exc

    record = ContractRecord(
        created_by_user_id=current_user.id,
        vendor_name=payload.vendor_name,
        title=payload.title,
        value=payload.value,
        currency=payload.currency.upper(),
        start_date=parse_date(payload.start_date),
        end_date=parse_date(payload.end_date),
        terms=payload.terms,
        status="active",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "vendor_name": record.vendor_name, "title": record.title, "status": record.status}


@router.get("/forecast")
def spend_forecast(db: DatabaseSession, current_user: CurrentUser):
    role = (current_user.role or "buyer").lower()
    rfq_query = select(RFQRecord)
    if role == "buyer":
        rfq_query = rfq_query.where(RFQRecord.user_id == current_user.id)
    rfqs = db.execute(rfq_query.order_by(RFQRecord.created_at.asc())).scalars().all()
    if not rfqs:
        return {"history_months": [], "forecast": [], "method": "insufficient_history"}

    ids = [r.id for r in rfqs]
    quotes = db.execute(select(VendorQuotationRecord).where(VendorQuotationRecord.rfq_id.in_(ids), VendorQuotationRecord.rank == 1)).scalars().all()
    created = {r.id: r.created_at for r in rfqs}
    monthly: dict[str, float] = {}
    for q in quotes:
        dt = created.get(q.rfq_id)
        if dt:
            key = dt.strftime("%Y-%m")
            monthly[key] = monthly.get(key, 0) + float(q.subtotal or 0)
    points = sorted(monthly.items())
    values = [v for _, v in points]
    if not values:
        return {"history_months": [], "forecast": [], "method": "insufficient_history"}

    # Transparent baseline forecast: recent moving average + simple trend.
    recent = values[-3:]
    avg = sum(recent) / len(recent)
    trend = (values[-1] - values[0]) / max(1, len(values) - 1) if len(values) > 1 else 0
    forecast = [max(0, avg + trend * step) for step in (1, 2, 3)]
    return {
        "history_months": [{"month": k, "recommended_spend": round(v, 2)} for k, v in points],
        "forecast": [{"period": f"+{i} month", "projected_spend": round(v, 2)} for i, v in enumerate(forecast, 1)],
        "method": "3-month moving average with linear trend",
        "warning": "Forecast is directional and becomes more reliable as procurement history grows.",
    }


@router.get("/admin/users")
def admin_users(
    db: DatabaseSession,
    current_user: User = Depends(require_roles("admin")),
):
    users = db.execute(select(User).order_by(User.created_at.desc())).scalars().all()
    return {"users": [{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "is_active": u.is_active, "created_at": u.created_at} for u in users]}


@router.patch("/admin/users/{user_id}/role")
def admin_update_role(
    user_id: int,
    payload: UserRoleUpdateRequest,
    db: DatabaseSession,
    current_user: User = Depends(require_roles("admin")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == current_user.id and payload.role != "admin":
        raise HTTPException(status_code=400, detail="You cannot remove your own admin role.")
    user.role = payload.role
    db.commit()
    return {"id": user.id, "email": user.email, "role": user.role}
